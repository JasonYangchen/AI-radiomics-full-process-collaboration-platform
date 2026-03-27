"""
Machine Learning API endpoints
"""
import io
import json
import pickle
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, roc_curve
)
import xgboost as xgb

from app.db.session import get_db
from app.models.user import User
from app.models.study import Study
from app.models.annotation import ROI
from app.models.feature import FeatureExtraction, FeatureResult
from app.models.ml import Dataset, MLModel, ModelEvaluation, Prediction
from app.schemas.ml import (
    DatasetCreate, DatasetUpdate, DatasetResponse,
    ModelCreate, ModelUpdate, ModelResponse, ModelListResponse,
    EvaluationResponse, PredictionRequest, PredictionResponse,
    TrainModelRequest, DatasetStats
)
from app.core.security import get_current_active_user, get_admin_user
from app.services.storage_service import StorageService

router = APIRouter()


def get_storage_service() -> StorageService:
    return StorageService()


# ==================== Dataset endpoints ====================

@router.post("/datasets", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    dataset_in: DatasetCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new dataset from feature extractions"""
    # Verify all extraction IDs exist and are completed
    for ext_id in dataset_in.feature_extraction_ids:
        result = await db.execute(
            select(FeatureExtraction).where(FeatureExtraction.id == ext_id)
        )
        extraction = result.scalar_one_or_none()
        if not extraction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Extraction {ext_id} not found"
            )
        if extraction.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Extraction {ext_id} is not completed"
            )
    
    dataset = Dataset(
        name=dataset_in.name,
        description=dataset_in.description,
        created_by=current_user.id,
        feature_extraction_ids=dataset_in.feature_extraction_ids,
        train_ratio=dataset_in.train_ratio,
        val_ratio=dataset_in.val_ratio,
        test_ratio=dataset_in.test_ratio
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    
    return dataset


@router.get("/datasets", response_model=list[DatasetResponse])
async def list_datasets(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all datasets"""
    result = await db.execute(
        select(Dataset).order_by(Dataset.created_at.desc())
    )
    datasets = result.scalars().all()
    
    return [DatasetResponse.model_validate(d) for d in datasets]


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dataset details"""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id)
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    return dataset


@router.get("/datasets/{dataset_id}/stats", response_model=DatasetStats)
async def get_dataset_stats(
    dataset_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dataset statistics"""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id)
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Get features from extractions
    features_df = await _get_features_dataframe(dataset.feature_extraction_ids, db)
    
    if features_df.empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No features found in dataset"
        )
    
    # Calculate stats
    total_samples = len(features_df)
    train_samples = int(total_samples * dataset.train_ratio)
    val_samples = int(total_samples * dataset.val_ratio)
    test_samples = total_samples - train_samples - val_samples
    
    return DatasetStats(
        total_samples=total_samples,
        train_samples=train_samples,
        val_samples=val_samples,
        test_samples=test_samples,
        feature_count=len(features_df.columns) - 1,  # Exclude label column if present
        class_distribution={"class_0": total_samples // 2, "class_1": total_samples - total_samples // 2}
    )


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete dataset"""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id)
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    await db.delete(dataset)
    await db.commit()
    
    return {"message": "Dataset deleted"}


# ==================== Model endpoints ====================

@router.post("/models", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    model_in: ModelCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new ML model"""
    # Verify dataset exists
    result = await db.execute(
        select(Dataset).where(Dataset.id == model_in.dataset_id)
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    model = MLModel(
        name=model_in.name,
        dataset_id=model_in.dataset_id,
        model_type=model_in.model_type,
        hyperparameters=model_in.hyperparameters,
        feature_columns=model_in.feature_columns,
        created_by=current_user.id
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    
    return model


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all ML models"""
    query = select(MLModel)
    count_query = select(func.count(MLModel.id))
    
    total = (await db.execute(count_query)).scalar()
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(MLModel.created_at.desc())
    
    result = await db.execute(query)
    models = result.scalars().all()
    
    return ModelListResponse(
        items=[ModelResponse.model_validate(m) for m in models],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get model details"""
    result = await db.execute(
        select(MLModel).where(MLModel.id == model_id)
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    return model


@router.post("/models/{model_id}/train")
async def train_model(
    model_id: UUID,
    train_request: TrainModelRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Train a model"""
    result = await db.execute(
        select(MLModel)
        .where(MLModel.id == model_id)
        .options(selectinload(MLModel.dataset))
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    if model.status == "training":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model is already training"
        )
    
    # Update model status
    model.status = "training"
    if train_request.hyperparameters:
        model.hyperparameters = train_request.hyperparameters
    if train_request.feature_columns:
        model.feature_columns = train_request.feature_columns
    await db.commit()
    
    # Run training in background
    async def run_training():
        try:
            await _train_model_task(model.id, db)
        except Exception as e:
            model.status = "error"
            model.error_message = str(e)
            await db.commit()
    
    background_tasks.add_task(run_training)
    
    return {"message": "Training started", "model_id": str(model_id)}


async def _train_model_task(model_id: UUID, db: AsyncSession):
    """Background task to train a model"""
    from datetime import datetime
    
    result = await db.execute(
        select(MLModel)
        .where(MLModel.id == model_id)
        .options(selectinload(MLModel.dataset))
    )
    model = result.scalar_one_or_none()
    
    if not model:
        return
    
    dataset = model.dataset
    
    # Get features
    features_df = await _get_features_dataframe(dataset.feature_extraction_ids, db)
    
    if features_df.empty:
        raise ValueError("No features available for training")
    
    # Prepare data
    # For demo, create synthetic labels if not present
    if 'label' not in features_df.columns:
        features_df['label'] = np.random.randint(0, 2, len(features_df))
    
    X = features_df.drop('label', axis=1).values
    y = features_df['label'].values
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        train_size=dataset.train_ratio,
        test_size=dataset.test_ratio,
        random_state=42,
        stratify=y
    )
    
    # Standardize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Create model
    hp = model.hyperparameters or {}
    
    if model.model_type == "logistic_regression":
        clf = LogisticRegression(**hp)
    elif model.model_type == "random_forest":
        clf = RandomForestClassifier(**hp)
    elif model.model_type == "svm":
        clf = SVC(probability=True, **hp)
    elif model.model_type == "xgboost":
        clf = xgb.XGBClassifier(**hp)
    else:
        raise ValueError(f"Unknown model type: {model.model_type}")
    
    # Train
    clf.fit(X_train_scaled, y_train)
    
    # Predict
    y_pred = clf.predict(X_test_scaled)
    y_prob = clf.predict_proba(X_test_scaled)[:, 1]
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    sensitivity = recall_score(y_test, y_pred, zero_division=0)
    specificity = recall_score(y_test, y_pred, pos_label=0, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    try:
        auc = roc_auc_score(y_test, y_prob)
    except ValueError:
        auc = 0.5
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred).tolist()
    
    # ROC curve data
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_data = [{"fpr": float(f), "tpr": float(t)} for f, t in zip(fpr, tpr)]
    
    # Feature importance
    feature_names = features_df.drop('label', axis=1).columns.tolist()
    feature_importance = {}
    
    if hasattr(clf, 'feature_importances_'):
        for name, imp in zip(feature_names, clf.feature_importances_):
            feature_importance[name] = float(imp)
    elif hasattr(clf, 'coef_'):
        for name, coef in zip(feature_names, clf.coef_[0]):
            feature_importance[name] = float(abs(coef))
    
    # Save model and scaler
    storage = StorageService()
    model_path = f"models/{model_id}/model.pkl"
    scaler_path = f"models/{model_id}/scaler.pkl"
    
    model_bytes = pickle.dumps(clf)
    scaler_bytes = pickle.dumps(scaler)
    
    await storage.upload_file(model_path, model_bytes, "application/octet-stream")
    await storage.upload_file(scaler_path, scaler_bytes, "application/octet-stream")
    
    # Update model
    model.model_path = model_path
    model.scaler_path = scaler_path
    model.status = "trained"
    model.trained_at = datetime.utcnow()
    model.feature_columns = feature_names
    
    # Create evaluation record
    evaluation = ModelEvaluation(
        model_id=model.id,
        accuracy=accuracy,
        sensitivity=sensitivity,
        specificity=specificity,
        precision=precision,
        f1_score=f1,
        auc=auc,
        confusion_matrix=cm,
        roc_data=roc_data,
        feature_importance=feature_importance
    )
    db.add(evaluation)
    
    await db.commit()


@router.get("/models/{model_id}/evaluation", response_model=EvaluationResponse)
async def get_model_evaluation(
    model_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get model evaluation results"""
    result = await db.execute(
        select(MLModel).where(MLModel.id == model_id)
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    if model.status != "trained":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model is not trained yet"
        )
    
    # Get latest evaluation
    result = await db.execute(
        select(ModelEvaluation)
        .where(ModelEvaluation.model_id == model_id)
        .order_by(ModelEvaluation.created_at.desc())
    )
    evaluation = result.scalar_one_or_none()
    
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found"
        )
    
    return evaluation


@router.post("/models/{model_id}/predict", response_model=PredictionResponse)
async def predict(
    model_id: UUID,
    request: PredictionRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Make prediction using trained model"""
    result = await db.execute(
        select(MLModel).where(MLModel.id == model_id)
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    if model.status != "trained":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model is not trained yet"
        )
    
    # Get ROI features (simplified - would extract actual features)
    # In production, would run feature extraction for the ROI first
    
    # For demo, create random features
    features = np.random.randn(1, len(model.feature_columns))
    
    # Load model and scaler
    storage = StorageService()
    
    model_bytes = await storage.download_file(model.model_path)
    scaler_bytes = await storage.download_file(model.scaler_path)
    
    clf = pickle.loads(model_bytes)
    scaler = pickle.loads(scaler_bytes)
    
    # Preprocess and predict
    features_scaled = scaler.transform(features)
    prediction_prob = clf.predict_proba(features_scaled)[0, 1]
    prediction_class = int(prediction_prob >= 0.5)
    
    # Save prediction
    prediction = Prediction(
        model_id=model.id,
        roi_id=request.roi_id,
        prediction_probability=prediction_prob,
        predicted_class=prediction_class
    )
    db.add(prediction)
    await db.commit()
    await db.refresh(prediction)
    
    return prediction


@router.get("/models/{model_id}/download")
async def download_model(
    model_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    """Download trained model"""
    result = await db.execute(
        select(MLModel).where(MLModel.id == model_id)
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    if model.status != "trained":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model is not trained yet"
        )
    
    model_url = await storage.get_presigned_url(model.model_path)
    scaler_url = await storage.get_presigned_url(model.scaler_path)
    
    return {
        "model_url": model_url,
        "scaler_url": scaler_url
    }


# ==================== Helper functions ====================

async def _get_features_dataframe(extraction_ids: list, db: AsyncSession) -> pd.DataFrame:
    """Get features as pandas DataFrame"""
    all_features = []
    
    for ext_id in extraction_ids:
        result = await db.execute(
            select(FeatureResult).where(FeatureResult.extraction_id == ext_id)
        )
        features = result.scalars().all()
        
        # Pivot features for this extraction
        feature_dict = {"extraction_id": str(ext_id)}
        for f in features:
            feature_dict[f.feature_name] = f.feature_value
        
        all_features.append(feature_dict)
    
    if not all_features:
        return pd.DataFrame()
    
    return pd.DataFrame(all_features)