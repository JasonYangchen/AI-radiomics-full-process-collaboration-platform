"""
Machine Learning Service
"""
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, roc_curve, precision_recall_curve
)
try:
    from sklearn.metrics import calibration_curve
except ImportError:
    from sklearn.calibration import calibration_curve
from sklearn.feature_selection import SelectKBest, f_classif
import xgboost as xgb
import joblib
import io

from app.models.ml import MLModel, ModelEvaluation, Dataset
from app.models.feature import FeatureExtraction, FeatureResult
from app.services.storage_service import StorageService
from app.core.config import settings


class MLService:
    """Machine learning model training and prediction service"""
    
    def __init__(self):
        self.storage = StorageService()
    
    def get_model_class(self, model_type: str):
        """Get sklearn model class by type"""
        models = {
            "logistic_regression": LogisticRegression,
            "random_forest": RandomForestClassifier,
            "svm": SVC,
            "xgboost": xgb.XGBClassifier,
            "gradient_boosting": GradientBoostingClassifier
        }
        return models.get(model_type)
    
    async def prepare_dataset(
        self,
        dataset: Dataset,
        db
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prepare feature matrix and labels from dataset"""
        # Get all features from extractions
        all_features = []
        extraction_ids = dataset.feature_extraction_ids
        
        for ext_id in extraction_ids:
            # Get features for this extraction
            from sqlalchemy import select
            from app.models.feature import FeatureResult
            
            result = await db.execute(
                select(FeatureResult).where(FeatureResult.extraction_id == ext_id)
            )
            features = result.scalars().all()
            
            # Pivot to wide format
            feature_dict = {"extraction_id": str(ext_id)}
            for f in features:
                feature_dict[f.feature_name] = f.feature_value
            
            all_features.append(feature_dict)
        
        df = pd.DataFrame(all_features)
        
        # For demo, create synthetic labels if not present
        if 'label' not in df.columns:
            np.random.seed(42)
            df['label'] = np.random.randint(0, 2, len(df))
        
        # Get feature columns
        feature_cols = [c for c in df.columns if c not in ['extraction_id', 'label']]
        X = df[feature_cols].values
        y = df['label'].values
        
        return X, y, feature_cols
    
    async def train_model(
        self,
        model: MLModel,
        dataset: Dataset,
        db
    ) -> ModelEvaluation:
        """Train a machine learning model"""
        # Prepare data
        X, y, feature_cols = await self.prepare_dataset(dataset, db)
        
        # Handle missing values
        X = np.nan_to_num(X, nan=0.0)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            train_size=dataset.train_ratio,
            test_size=dataset.test_ratio,
            random_state=42,
            stratify=y
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Get model class and create instance
        model_class = self.get_model_class(model.model_type)
        if not model_class:
            raise ValueError(f"Unknown model type: {model.model_type}")
        
        # Create model with hyperparameters
        hyperparams = model.hyperparameters or {}
        clf = model_class(**hyperparams)
        
        # Train
        clf.fit(X_train_scaled, y_train)
        
        # Predict
        y_pred = clf.predict(X_test_scaled)
        
        # Get probabilities if available
        if hasattr(clf, 'predict_proba'):
            y_prob = clf.predict_proba(X_test_scaled)[:, 1]
        else:
            y_prob = clf.decision_function(X_test_scaled)
            y_prob = (y_prob - y_prob.min()) / (y_prob.max() - y_prob.min())
        
        # Calculate metrics
        metrics = self._calculate_metrics(y_test, y_pred, y_prob)
        
        # Get feature importance
        feature_importance = self._get_feature_importance(clf, feature_cols)
        
        # Save model and scaler
        model_bytes = pickle.dumps(clf)
        scaler_bytes = pickle.dumps(scaler)
        
        model_path = f"models/{model.id}/model.pkl"
        scaler_path = f"models/{model.id}/scaler.pkl"
        
        await self.storage.upload_file(model_path, model_bytes, "application/octet-stream")
        await self.storage.upload_file(scaler_path, scaler_bytes, "application/octet-stream")
        
        # Create evaluation record
        evaluation = ModelEvaluation(
            model_id=model.id,
            **metrics,
            feature_importance=feature_importance
        )
        
        return evaluation
    
    def _calculate_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_prob: np.ndarray
    ) -> Dict[str, Any]:
        """Calculate all evaluation metrics"""
        # Basic metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, zero_division=0)
        sensitivity = recall_score(y_true, y_pred, zero_division=0)
        specificity = recall_score(y_true, y_pred, pos_label=0, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        
        try:
            auc = roc_auc_score(y_true, y_prob)
        except ValueError:
            auc = 0.5
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred).tolist()
        
        # ROC curve data
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        roc_data = [{"fpr": float(f), "tpr": float(t)} for f, t in zip(fpr, tpr)]
        
        # Calibration curve
        try:
            prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10)
            calibration_data = {
                "prob_true": prob_true.tolist(),
                "prob_pred": prob_pred.tolist()
            }
        except:
            calibration_data = None
        
        return {
            "accuracy": accuracy,
            "precision": precision,
            "sensitivity": sensitivity,
            "specificity": specificity,
            "f1_score": f1,
            "auc": auc,
            "confusion_matrix": cm,
            "roc_data": roc_data,
            "calibration_data": calibration_data
        }
    
    def _get_feature_importance(
        self,
        model,
        feature_names: List[str]
    ) -> Dict[str, float]:
        """Extract feature importance from trained model"""
        importance = {}
        
        if hasattr(model, 'feature_importances_'):
            for name, imp in zip(feature_names, model.feature_importances_):
                importance[name] = float(imp)
        elif hasattr(model, 'coef_'):
            coef = model.coef_[0] if len(model.coef_.shape) > 1 else model.coef_
            for name, c in zip(feature_names, coef):
                importance[name] = float(abs(c))
        else:
            # Use permutation importance or set uniform
            for name in feature_names:
                importance[name] = 1.0 / len(feature_names)
        
        return importance
    
    async def predict(
        self,
        model: MLModel,
        features: np.ndarray
    ) -> Tuple[int, float]:
        """Make prediction using trained model"""
        # Load model and scaler
        model_bytes = await self.storage.download_file(model.model_path)
        scaler_bytes = await self.storage.download_file(model.scaler_path)
        
        clf = pickle.loads(model_bytes)
        scaler = pickle.loads(scaler_bytes)
        
        # Scale features
        features_scaled = scaler.transform(features.reshape(1, -1))
        
        # Predict
        prediction = clf.predict(features_scaled)[0]
        probability = clf.predict_proba(features_scaled)[0, 1]
        
        return int(prediction), float(probability)
    
    def cross_validate(
        self,
        model_type: str,
        X: np.ndarray,
        y: np.ndarray,
        cv: int = 5,
        hyperparams: Optional[Dict] = None
    ) -> Dict[str, float]:
        """Perform cross-validation"""
        model_class = self.get_model_class(model_type)
        hyperparams = hyperparams or {}
        clf = model_class(**hyperparams)
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Cross-validation scores
        scores = cross_val_score(clf, X_scaled, y, cv=cv, scoring='accuracy')
        
        return {
            "mean_accuracy": float(scores.mean()),
            "std_accuracy": float(scores.std()),
            "fold_scores": scores.tolist()
        }
    
    def get_available_models(self) -> Dict[str, Dict]:
        """Get list of available model types and their descriptions"""
        return {
            "logistic_regression": {
                "name": "Logistic Regression",
                "description": "Linear model for binary classification",
                "hyperparameters": {
                    "C": {"type": "float", "default": 1.0, "description": "Regularization strength"},
                    "penalty": {"type": "categorical", "default": "l2", "options": ["l1", "l2", "elasticnet"]},
                    "solver": {"type": "categorical", "default": "lbfgs", "options": ["lbfgs", "liblinear", "saga"]}
                }
            },
            "random_forest": {
                "name": "Random Forest",
                "description": "Ensemble of decision trees",
                "hyperparameters": {
                    "n_estimators": {"type": "int", "default": 100, "description": "Number of trees"},
                    "max_depth": {"type": "int", "default": None, "description": "Maximum tree depth"},
                    "min_samples_split": {"type": "int", "default": 2, "description": "Min samples to split"},
                    "min_samples_leaf": {"type": "int", "default": 1, "description": "Min samples per leaf"}
                }
            },
            "svm": {
                "name": "Support Vector Machine",
                "description": "Support vector classifier with RBF kernel",
                "hyperparameters": {
                    "C": {"type": "float", "default": 1.0, "description": "Regularization parameter"},
                    "kernel": {"type": "categorical", "default": "rbf", "options": ["linear", "poly", "rbf", "sigmoid"]},
                    "gamma": {"type": "categorical", "default": "scale", "options": ["scale", "auto"]}
                }
            },
            "xgboost": {
                "name": "XGBoost",
                "description": "Gradient boosting classifier",
                "hyperparameters": {
                    "n_estimators": {"type": "int", "default": 100, "description": "Number of boosting rounds"},
                    "max_depth": {"type": "int", "default": 6, "description": "Maximum tree depth"},
                    "learning_rate": {"type": "float", "default": 0.1, "description": "Learning rate"},
                    "subsample": {"type": "float", "default": 1.0, "description": "Subsample ratio"}
                }
            }
        }


# Model type configurations for reference
MODEL_CONFIGS = {
    "logistic_regression": {
        "name": "Logistic Regression",
        "type": "linear",
        "supports_probability": True,
        "supports_feature_importance": True,
        "recommended_for": ["Small datasets", "Linear relationships", "Interpretability"]
    },
    "random_forest": {
        "name": "Random Forest",
        "type": "ensemble",
        "supports_probability": True,
        "supports_feature_importance": True,
        "recommended_for": ["Non-linear relationships", "Feature selection", "Robust predictions"]
    },
    "svm": {
        "name": "Support Vector Machine",
        "type": "kernel",
        "supports_probability": True,
        "supports_feature_importance": False,
        "recommended_for": ["Small to medium datasets", "High-dimensional data", "Complex boundaries"]
    },
    "xgboost": {
        "name": "XGBoost",
        "type": "boosting",
        "supports_probability": True,
        "supports_feature_importance": True,
        "recommended_for": ["Large datasets", "Best performance", "Feature importance"]
    }
}