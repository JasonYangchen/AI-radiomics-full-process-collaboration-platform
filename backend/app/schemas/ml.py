"""
Pydantic schemas for Machine Learning
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


class DatasetCreate(BaseModel):
    """Dataset creation schema"""
    name: str
    description: Optional[str] = None
    feature_extraction_ids: List[UUID]
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    test_ratio: float = 0.15


class DatasetUpdate(BaseModel):
    """Dataset update schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    train_ratio: Optional[float] = None
    val_ratio: Optional[float] = None
    test_ratio: Optional[float] = None


class DatasetResponse(BaseModel):
    """Dataset response schema"""
    id: UUID
    name: str
    description: Optional[str] = None
    created_by: Optional[UUID] = None
    feature_extraction_ids: Optional[List[UUID]] = None
    train_ratio: float
    val_ratio: float
    test_ratio: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class ModelCreate(BaseModel):
    """Model creation schema"""
    name: str
    dataset_id: UUID
    model_type: str  # logistic_regression, random_forest, svm, xgboost
    hyperparameters: Optional[Dict[str, Any]] = None
    feature_columns: Optional[List[str]] = None


class ModelUpdate(BaseModel):
    """Model update schema"""
    name: Optional[str] = None
    hyperparameters: Optional[Dict[str, Any]] = None


class ModelResponse(BaseModel):
    """Model response schema"""
    id: UUID
    name: str
    dataset_id: UUID
    model_type: str
    hyperparameters: Optional[Dict[str, Any]] = None
    feature_columns: Optional[List[str]] = None
    status: str
    error_message: Optional[str] = None
    created_by: Optional[UUID] = None
    trained_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ModelListResponse(BaseModel):
    """Paginated model list"""
    items: List[ModelResponse]
    total: int
    page: int
    page_size: int


class EvaluationResponse(BaseModel):
    """Model evaluation response"""
    id: UUID
    model_id: UUID
    accuracy: Optional[float] = None
    sensitivity: Optional[float] = None
    specificity: Optional[float] = None
    precision: Optional[float] = None
    f1_score: Optional[float] = None
    auc: Optional[float] = None
    confusion_matrix: Optional[List[List[int]]] = None
    roc_data: Optional[List[Dict[str, float]]] = None
    calibration_data: Optional[Dict[str, Any]] = None
    feature_importance: Optional[Dict[str, float]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PredictionRequest(BaseModel):
    """Prediction request"""
    roi_id: UUID


class PredictionResponse(BaseModel):
    """Prediction response"""
    id: UUID
    model_id: UUID
    roi_id: UUID
    prediction_probability: float
    predicted_class: int
    actual_class: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TrainModelRequest(BaseModel):
    """Model training request"""
    hyperparameters: Optional[Dict[str, Any]] = None
    feature_columns: Optional[List[str]] = None


class DatasetStats(BaseModel):
    """Dataset statistics"""
    total_samples: int
    train_samples: int
    val_samples: int
    test_samples: int
    feature_count: int
    class_distribution: Dict[str, int]