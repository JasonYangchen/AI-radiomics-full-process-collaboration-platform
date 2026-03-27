"""
Schemas package
"""
from app.schemas.user import (
    UserBase, UserCreate, UserUpdate, UserResponse, UserListResponse,
    Token, TokenData
)
from app.schemas.study import (
    StudyBase, StudyCreate, StudyUpdate, StudyResponse, StudyListResponse,
    SeriesResponse, ImageResponse, StudyDetailResponse, UploadProgress
)
from app.schemas.annotation import (
    AnnotationProjectBase, AnnotationProjectCreate, AnnotationProjectUpdate,
    AnnotationProjectResponse, ROIBase, ROICreate, ROIUpdate, ROIResponse,
    ROIListResponse, ROIHistoryResponse
)
from app.schemas.feature import (
    RadiomicsConfig, FeatureExtractionCreate, FeatureExtractionResponse,
    FeatureResultResponse, FeatureExtractionDetailResponse,
    FeatureExtractionListResponse, FeatureExportResponse, FeatureSummaryResponse
)
from app.schemas.ml import (
    DatasetCreate, DatasetUpdate, DatasetResponse,
    ModelCreate, ModelUpdate, ModelResponse, ModelListResponse,
    EvaluationResponse, PredictionRequest, PredictionResponse,
    TrainModelRequest, DatasetStats
)

__all__ = [
    # User schemas
    "UserBase", "UserCreate", "UserUpdate", "UserResponse", "UserListResponse",
    "Token", "TokenData",
    # Study schemas
    "StudyBase", "StudyCreate", "StudyUpdate", "StudyResponse", "StudyListResponse",
    "SeriesResponse", "ImageResponse", "StudyDetailResponse", "UploadProgress",
    # Annotation schemas
    "AnnotationProjectBase", "AnnotationProjectCreate", "AnnotationProjectUpdate",
    "AnnotationProjectResponse", "ROIBase", "ROICreate", "ROIUpdate", "ROIResponse",
    "ROIListResponse", "ROIHistoryResponse",
    # Feature schemas
    "RadiomicsConfig", "FeatureExtractionCreate", "FeatureExtractionResponse",
    "FeatureResultResponse", "FeatureExtractionDetailResponse",
    "FeatureExtractionListResponse", "FeatureExportResponse", "FeatureSummaryResponse",
    # ML schemas
    "DatasetCreate", "DatasetUpdate", "DatasetResponse",
    "ModelCreate", "ModelUpdate", "ModelResponse", "ModelListResponse",
    "EvaluationResponse", "PredictionRequest", "PredictionResponse",
    "TrainModelRequest", "DatasetStats"
]