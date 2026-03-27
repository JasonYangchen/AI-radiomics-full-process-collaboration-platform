"""
Pydantic schemas for Annotation
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


class AnnotationProjectBase(BaseModel):
    """Base annotation project schema"""
    name: str
    description: Optional[str] = None


class AnnotationProjectCreate(AnnotationProjectBase):
    """Annotation project creation schema"""
    study_id: UUID


class AnnotationProjectUpdate(BaseModel):
    """Annotation project update schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class AnnotationProjectResponse(AnnotationProjectBase):
    """Annotation project response schema"""
    id: UUID
    study_id: UUID
    created_by: Optional[UUID] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ROIBase(BaseModel):
    """Base ROI schema"""
    roi_name: Optional[str] = None
    roi_type: str  # freehand, polygon, sphere, cube, threshold
    label_color: str = "#FF0000"


class ROICreate(ROIBase):
    """ROI creation schema"""
    image_id: UUID
    project_id: Optional[UUID] = None
    mask_data: str  # base64 encoded mask data


class ROIUpdate(BaseModel):
    """ROI update schema"""
    roi_name: Optional[str] = None
    label_color: Optional[str] = None
    mask_data: Optional[str] = None  # base64 encoded


class ROIResponse(ROIBase):
    """ROI response schema"""
    id: UUID
    image_id: UUID
    project_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    volume_mm3: Optional[float] = None
    centroid: Optional[List[float]] = None
    statistics: Optional[Dict[str, Any]] = None
    version: int
    is_latest: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ROIListResponse(BaseModel):
    """Paginated ROI list"""
    items: List[ROIResponse]
    total: int
    page: int
    page_size: int


class ROIHistoryResponse(BaseModel):
    """ROI history response"""
    id: UUID
    roi_id: UUID
    changed_by: Optional[UUID] = None
    change_type: str
    previous_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True