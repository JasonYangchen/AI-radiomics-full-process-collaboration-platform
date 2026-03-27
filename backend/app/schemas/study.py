"""
Pydantic schemas for Study and Image
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
from uuid import UUID


class StudyBase(BaseModel):
    """Base study schema"""
    patient_id: Optional[str] = None
    study_description: Optional[str] = None


class StudyCreate(StudyBase):
    """Study creation schema"""
    pass


class StudyUpdate(BaseModel):
    """Study update schema"""
    patient_id: Optional[str] = None
    study_description: Optional[str] = None


class StudyResponse(StudyBase):
    """Study response schema"""
    id: UUID
    study_uid: Optional[str] = None
    study_date: Optional[date] = None
    modality: Optional[str] = None
    uploaded_by: Optional[UUID] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StudyListResponse(BaseModel):
    """Paginated study list"""
    items: List[StudyResponse]
    total: int
    page: int
    page_size: int


class SeriesResponse(BaseModel):
    """Series response schema"""
    id: UUID
    study_id: UUID
    series_uid: Optional[str] = None
    series_description: Optional[str] = None
    series_number: Optional[int] = None
    modality: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ImageResponse(BaseModel):
    """Image response schema"""
    id: UUID
    series_id: UUID
    file_path: str
    file_format: str
    file_size: Optional[int] = None
    dimensions: Optional[List[int]] = None
    spacing: Optional[List[float]] = None
    origin: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="image_metadata")
    created_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True


class StudyDetailResponse(StudyResponse):
    """Study detail with series and images"""
    series: List[SeriesResponse]


class UploadProgress(BaseModel):
    """Upload progress response"""
    study_id: UUID
    status: str
    progress: int
    message: str