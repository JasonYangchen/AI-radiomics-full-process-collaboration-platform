"""
Pydantic schemas for Feature Extraction
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


class RadiomicsConfig(BaseModel):
    """PyRadiomics configuration"""
    binWidth: int = 25
    interpolator: str = "sitkBSpline"
    resampledPixelSpacing: Optional[List[float]] = None
    textureSampleDistance: Optional[float] = None
    enableCExtensions: bool = True
    additionalInfo: bool = False


class FeatureExtractionCreate(BaseModel):
    """Feature extraction creation schema"""
    study_id: UUID
    roi_id: Optional[UUID] = None
    config: Optional[RadiomicsConfig] = None
    feature_classes: Optional[List[str]] = None  # firstorder, shape, glcm, etc.


class FeatureExtractionResponse(BaseModel):
    """Feature extraction response schema"""
    id: UUID
    study_id: UUID
    roi_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    status: str
    config: Optional[Dict[str, Any]] = None
    progress: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class FeatureResultResponse(BaseModel):
    """Individual feature result"""
    id: UUID
    extraction_id: UUID
    image_id: Optional[UUID] = None
    roi_id: Optional[UUID] = None
    feature_class: str
    feature_name: str
    feature_value: float
    
    class Config:
        from_attributes = True


class FeatureExtractionDetailResponse(FeatureExtractionResponse):
    """Feature extraction with results"""
    results: List[FeatureResultResponse]


class FeatureExtractionListResponse(BaseModel):
    """Paginated feature extraction list"""
    items: List[FeatureExtractionResponse]
    total: int
    page: int
    page_size: int


class FeatureExportResponse(BaseModel):
    """Feature export response"""
    id: UUID
    extraction_id: UUID
    created_by: UUID
    file_path: str
    file_format: str
    download_url: str
    created_at: datetime


class FeatureSummaryResponse(BaseModel):
    """Feature summary for visualization"""
    feature_classes: List[str]
    feature_counts: Dict[str, int]
    value_ranges: Dict[str, Dict[str, float]]