"""
Annotation API endpoints
"""
import base64
import zlib
from typing import Optional
from uuid import UUID
import numpy as np
import SimpleITK as sitk
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.user import User
from app.models.study import Image
from app.models.annotation import AnnotationProject, ROI, ROIHistory
from app.schemas.annotation import (
    AnnotationProjectCreate, AnnotationProjectUpdate, AnnotationProjectResponse,
    ROICreate, ROIUpdate, ROIResponse, ROIListResponse, ROIHistoryResponse
)
from app.core.security import get_current_active_user
from app.services.storage_service import StorageService

router = APIRouter()


def compress_mask_data(data: str) -> bytes:
    """Compress base64 mask data"""
    binary_data = base64.b64decode(data)
    return zlib.compress(binary_data)


def decompress_mask_data(data: bytes) -> str:
    """Decompress mask data to base64"""
    decompressed = zlib.decompress(data)
    return base64.b64encode(decompressed).decode('utf-8')


@router.get("/projects", response_model=list[AnnotationProjectResponse])
async def list_projects(
    study_id: Optional[UUID] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List annotation projects"""
    query = select(AnnotationProject).options(selectinload(AnnotationProject.study))
    
    if study_id:
        query = query.where(AnnotationProject.study_id == study_id)
    if status:
        query = query.where(AnnotationProject.status == status)
    
    query = query.order_by(AnnotationProject.created_at.desc())
    
    result = await db.execute(query)
    projects = result.scalars().all()
    
    return [AnnotationProjectResponse.model_validate(p) for p in projects]


@router.post("/projects", response_model=AnnotationProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: AnnotationProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new annotation project"""
    project = AnnotationProject(
        name=project_in.name,
        description=project_in.description,
        study_id=project_in.study_id,
        created_by=current_user.id
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return project


@router.get("/projects/{project_id}", response_model=AnnotationProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get annotation project details"""
    result = await db.execute(
        select(AnnotationProject)
        .where(AnnotationProject.id == project_id)
        .options(
            selectinload(AnnotationProject.study),
            selectinload(AnnotationProject.rois)
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete annotation project"""
    result = await db.execute(
        select(AnnotationProject).where(AnnotationProject.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Only creator can delete
    if project.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project creator can delete it"
        )
    
    await db.delete(project)
    await db.commit()
    
    return {"message": "Project deleted"}


@router.get("/rois", response_model=ROIListResponse)
async def list_rois(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    image_id: Optional[UUID] = None,
    project_id: Optional[UUID] = None,
    created_by: Optional[UUID] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List ROI annotations"""
    query = select(ROI).where(ROI.is_latest == True)
    count_query = select(func.count(ROI.id)).where(ROI.is_latest == True)
    
    if image_id:
        query = query.where(ROI.image_id == image_id)
        count_query = count_query.where(ROI.image_id == image_id)
    if project_id:
        query = query.where(ROI.project_id == project_id)
        count_query = count_query.where(ROI.project_id == project_id)
    if created_by:
        query = query.where(ROI.created_by == created_by)
        count_query = count_query.where(ROI.created_by == created_by)
    
    # Get total count
    total = (await db.execute(count_query)).scalar()
    
    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(ROI.created_at.desc())
    
    result = await db.execute(query)
    rois = result.scalars().all()
    
    return ROIListResponse(
        items=[ROIResponse.model_validate(r) for r in rois],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/rois/{roi_id}", response_model=ROIResponse)
async def get_roi(
    roi_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get ROI details"""
    result = await db.execute(
        select(ROI)
        .where(ROI.id == roi_id)
        .options(selectinload(ROI.image))
    )
    roi = result.scalar_one_or_none()
    
    if not roi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ROI not found"
        )
    
    return roi


@router.post("/rois", response_model=ROIResponse, status_code=status.HTTP_201_CREATED)
async def create_roi(
    roi_in: ROICreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new ROI annotation"""
    # Verify image exists
    result = await db.execute(select(Image).where(Image.id == roi_in.image_id))
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Compress and store mask data
    mask_data = compress_mask_data(roi_in.mask_data)
    
    # Calculate basic statistics
    # In production, this would use SimpleITK to calculate volume, centroid, etc.
    statistics = {}
    volume_mm3 = None
    centroid = None
    
    # Create ROI
    roi = ROI(
        image_id=roi_in.image_id,
        project_id=roi_in.project_id,
        created_by=current_user.id,
        roi_name=roi_in.roi_name,
        roi_type=roi_in.roi_type,
        label_color=roi_in.label_color,
        mask_data=mask_data,
        volume_mm3=volume_mm3,
        centroid=centroid,
        statistics=statistics
    )
    db.add(roi)
    
    # Create history record
    history = ROIHistory(
        roi=roi,
        changed_by=current_user.id,
        change_type="create"
    )
    db.add(history)
    
    await db.commit()
    await db.refresh(roi)
    
    return roi


@router.put("/rois/{roi_id}", response_model=ROIResponse)
async def update_roi(
    roi_id: UUID,
    roi_update: ROIUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update ROI annotation"""
    result = await db.execute(select(ROI).where(ROI.id == roi_id))
    roi = result.scalar_one_or_none()
    
    if not roi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ROI not found"
        )
    
    # Only creator can update
    if roi.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator can update this ROI"
        )
    
    # Store previous state for history
    previous_data = {
        "roi_name": roi.roi_name,
        "label_color": roi.label_color
    }
    
    # Update fields
    if roi_update.roi_name is not None:
        roi.roi_name = roi_update.roi_name
    if roi_update.label_color is not None:
        roi.label_color = roi_update.label_color
    if roi_update.mask_data is not None:
        roi.mask_data = compress_mask_data(roi_update.mask_data)
        roi.version += 1
    
    # Create history record
    history = ROIHistory(
        roi_id=roi.id,
        changed_by=current_user.id,
        change_type="update",
        previous_data=previous_data
    )
    db.add(history)
    
    await db.commit()
    await db.refresh(roi)
    
    return roi


@router.delete("/rois/{roi_id}")
async def delete_roi(
    roi_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete ROI annotation"""
    result = await db.execute(select(ROI).where(ROI.id == roi_id))
    roi = result.scalar_one_or_none()
    
    if not roi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ROI not found"
        )
    
    # Only creator can delete
    if roi.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator can delete this ROI"
        )
    
    # Create history record before deletion
    history = ROIHistory(
        roi_id=roi.id,
        changed_by=current_user.id,
        change_type="delete",
        previous_data={"roi_name": roi.roi_name, "roi_type": roi.roi_type}
    )
    db.add(history)
    
    await db.delete(roi)
    await db.commit()
    
    return {"message": "ROI deleted"}


@router.get("/rois/{roi_id}/download")
async def download_roi(
    roi_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Download ROI mask data"""
    result = await db.execute(select(ROI).where(ROI.id == roi_id))
    roi = result.scalar_one_or_none()
    
    if not roi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ROI not found"
        )
    
    # Decompress mask data
    mask_data = decompress_mask_data(roi.mask_data)
    
    return {
        "roi_id": str(roi_id),
        "roi_name": roi.roi_name,
        "roi_type": roi.roi_type,
        "mask_data": mask_data,
        "format": roi.mask_format
    }


@router.get("/rois/{roi_id}/history", response_model=list[ROIHistoryResponse])
async def get_roi_history(
    roi_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get ROI change history"""
    result = await db.execute(
        select(ROIHistory)
        .where(ROIHistory.roi_id == roi_id)
        .order_by(ROIHistory.created_at.desc())
    )
    history = result.scalars().all()
    
    return [ROIHistoryResponse.model_validate(h) for h in history]