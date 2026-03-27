"""
Feature extraction API endpoints (Admin only)
"""
import io
import pandas as pd
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.user import User
from app.models.study import Study
from app.models.annotation import ROI
from app.models.feature import FeatureExtraction, FeatureResult, FeatureExport
from app.schemas.feature import (
    FeatureExtractionCreate, FeatureExtractionResponse,
    FeatureExtractionDetailResponse, FeatureExtractionListResponse,
    FeatureResultResponse, FeatureExportResponse
)
from app.core.security import get_admin_user
from app.services.storage_service import StorageService
from app.services.radiomics_service import RadiomicsService

router = APIRouter()


def get_storage_service() -> StorageService:
    return StorageService()


@router.post("/extract", response_model=FeatureExtractionResponse, status_code=status.HTTP_201_CREATED)
async def create_extraction(
    extraction_in: FeatureExtractionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new feature extraction task"""
    # Verify study exists
    result = await db.execute(select(Study).where(Study.id == extraction_in.study_id))
    study = result.scalar_one_or_none()
    
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Create extraction task
    extraction = FeatureExtraction(
        study_id=extraction_in.study_id,
        roi_id=extraction_in.roi_id,
        created_by=current_user.id,
        config=extraction_in.config.model_dump() if extraction_in.config else None,
        status="pending"
    )
    db.add(extraction)
    await db.commit()
    await db.refresh(extraction)
    
    # Run extraction in background
    async def run_extraction():
        radiomics_service = RadiomicsService()
        await radiomics_service.run_extraction(extraction.id, db)
    
    background_tasks.add_task(run_extraction)
    
    return extraction


@router.get("/extractions", response_model=FeatureExtractionListResponse)
async def list_extractions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    study_id: Optional[UUID] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List feature extraction tasks"""
    query = select(FeatureExtraction)
    count_query = select(func.count(FeatureExtraction.id))
    
    if study_id:
        query = query.where(FeatureExtraction.study_id == study_id)
        count_query = count_query.where(FeatureExtraction.study_id == study_id)
    
    if status_filter:
        query = query.where(FeatureExtraction.status == status_filter)
        count_query = count_query.where(FeatureExtraction.status == status_filter)
    
    # Get total count
    total = (await db.execute(count_query)).scalar()
    
    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(FeatureExtraction.created_at.desc())
    
    result = await db.execute(query)
    extractions = result.scalars().all()
    
    return FeatureExtractionListResponse(
        items=[FeatureExtractionResponse.model_validate(e) for e in extractions],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/extractions/{extraction_id}", response_model=FeatureExtractionDetailResponse)
async def get_extraction(
    extraction_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get feature extraction details with results"""
    result = await db.execute(
        select(FeatureExtraction)
        .where(FeatureExtraction.id == extraction_id)
        .options(selectinload(FeatureExtraction.results))
    )
    extraction = result.scalar_one_or_none()
    
    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )
    
    return FeatureExtractionDetailResponse(
        **FeatureExtractionResponse.model_validate(extraction).model_dump(),
        results=[FeatureResultResponse.model_validate(r) for r in extraction.results]
    )


@router.delete("/extractions/{extraction_id}")
async def delete_extraction(
    extraction_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete feature extraction task and results"""
    result = await db.execute(
        select(FeatureExtraction).where(FeatureExtraction.id == extraction_id)
    )
    extraction = result.scalar_one_or_none()
    
    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )
    
    await db.delete(extraction)
    await db.commit()
    
    return {"message": "Extraction deleted"}


@router.post("/extractions/{extraction_id}/cancel")
async def cancel_extraction(
    extraction_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel running extraction task"""
    result = await db.execute(
        select(FeatureExtraction).where(FeatureExtraction.id == extraction_id)
    )
    extraction = result.scalar_one_or_none()
    
    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )
    
    if extraction.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel extraction with status: {extraction.status}"
        )
    
    # In production, would cancel Celery task
    extraction.status = "cancelled"
    extraction.error_message = "Cancelled by user"
    await db.commit()
    
    return {"message": "Extraction cancelled"}


@router.get("/extractions/{extraction_id}/results")
async def get_extraction_results(
    extraction_id: UUID,
    feature_class: Optional[str] = None,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get feature extraction results"""
    query = select(FeatureResult).where(FeatureResult.extraction_id == extraction_id)
    
    if feature_class:
        query = query.where(FeatureResult.feature_class == feature_class)
    
    result = await db.execute(query)
    results = result.scalars().all()
    
    # Group by feature class
    grouped = {}
    for r in results:
        if r.feature_class not in grouped:
            grouped[r.feature_class] = []
        grouped[r.feature_class].append({
            "name": r.feature_name,
            "value": r.feature_value
        })
    
    return grouped


@router.get("/extractions/{extraction_id}/export", response_model=FeatureExportResponse)
async def export_results(
    extraction_id: UUID,
    format: str = Query("csv", regex="^(csv|excel)$"),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    """Export feature extraction results to CSV or Excel"""
    result = await db.execute(
        select(FeatureExtraction)
        .where(FeatureExtraction.id == extraction_id)
        .options(selectinload(FeatureExtraction.results))
    )
    extraction = result.scalar_one_or_none()
    
    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )
    
    if extraction.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extraction not completed"
        )
    
    # Prepare data
    data = []
    for r in extraction.results:
        data.append({
            "feature_class": r.feature_class,
            "feature_name": r.feature_name,
            "feature_value": r.feature_value
        })
    
    df = pd.DataFrame(data)
    
    # Generate file
    if format == "csv":
        output = io.StringIO()
        df.to_csv(output, index=False)
        file_content = output.getvalue().encode('utf-8')
        file_name = f"features_{extraction_id}.csv"
        content_type = "text/csv"
    else:  # excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Features')
        file_content = output.getvalue()
        file_name = f"features_{extraction_id}.xlsx"
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    # Upload to storage
    file_path = f"exports/{file_name}"
    await storage.upload_file(file_path, file_content, content_type)
    
    # Create export record
    export = FeatureExport(
        extraction_id=extraction_id,
        created_by=current_user.id,
        file_path=file_path,
        file_format=format
    )
    db.add(export)
    await db.commit()
    await db.refresh(export)
    
    # Generate download URL
    download_url = await storage.get_presigned_url(file_path)
    
    return FeatureExportResponse(
        **export.model_dump(),
        download_url=download_url
    )