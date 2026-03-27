"""
Medical imaging study API endpoints
"""
import os
import tempfile
import aiofiles
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.user import User
from app.models.study import Study, Series, Image
from app.schemas.study import (
    StudyCreate, StudyUpdate, StudyResponse, StudyListResponse,
    SeriesResponse, ImageResponse, StudyDetailResponse, UploadProgress
)
from app.core.security import get_current_active_user, get_admin_user
from app.services.storage_service import StorageService
from app.services.image_processing import ImageProcessor

router = APIRouter()


def get_storage_service() -> StorageService:
    return StorageService()


@router.get("/", response_model=StudyListResponse)
async def list_studies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    modality: Optional[str] = None,
    status: Optional[str] = None,
    patient_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all studies"""
    query = select(Study).options(selectinload(Study.series))
    count_query = select(func.count(Study.id))
    
    if modality:
        query = query.where(Study.modality == modality)
        count_query = count_query.where(Study.modality == modality)
    
    if status:
        query = query.where(Study.status == status)
        count_query = count_query.where(Study.status == status)
    
    if patient_id:
        query = query.where(Study.patient_id.ilike(f"%{patient_id}%"))
        count_query = count_query.where(Study.patient_id.ilike(f"%{patient_id}%"))
    
    # Get total count
    total = (await db.execute(count_query)).scalar()
    
    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Study.created_at.desc())
    
    result = await db.execute(query)
    studies = result.scalars().all()
    
    return StudyListResponse(
        items=[StudyResponse.model_validate(s) for s in studies],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{study_id}", response_model=StudyDetailResponse)
async def get_study(
    study_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get study details"""
    result = await db.execute(
        select(Study)
        .where(Study.id == study_id)
        .options(
            selectinload(Study.series).selectinload(Series.images)
        )
    )
    study = result.scalar_one_or_none()
    
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Build response with series
    series_list = []
    for series in study.series:
        series_data = SeriesResponse.model_validate(series)
        series_list.append(series_data)
    
    response = StudyDetailResponse(
        **StudyResponse.model_validate(study).model_dump(),
        series=series_list
    )
    
    return response


@router.post("/", response_model=StudyResponse, status_code=status.HTTP_201_CREATED)
async def create_study(
    study_in: StudyCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new study (admin only)"""
    study = Study(
        patient_id=study_in.patient_id,
        study_description=study_in.study_description,
        uploaded_by=current_user.id
    )
    db.add(study)
    await db.commit()
    await db.refresh(study)
    
    return study


@router.post("/upload", response_model=StudyResponse, status_code=status.HTTP_201_CREATED)
async def upload_study(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    patient_id: Optional[str] = None,
    study_description: Optional[str] = None,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    """Upload medical imaging study (DICOM, NRRD, NIfTI) - admin only"""
    # Validate file extension
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in [".dcm", ".nrrd", ".nii", ".nii.gz", ".zip"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Supported: DICOM (.dcm), NRRD (.nrrd), NIfTI (.nii, .nii.gz), ZIP"
        )
    
    # Create study record
    study = Study(
        patient_id=patient_id,
        study_description=study_description,
        uploaded_by=current_user.id,
        status="processing"
    )
    db.add(study)
    await db.commit()
    await db.refresh(study)
    
    # Save uploaded file temporarily
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename)
    
    async with aiofiles.open(temp_file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Process in background
    async def process_uploaded_file():
        try:
            processor = ImageProcessor()
            
            # Determine file format and process
            if filename.endswith('.zip'):
                # Extract ZIP and process
                import zipfile
                with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                # Find DICOM/NRRD files
                for root, dirs, files in os.walk(temp_dir):
                    for f in files:
                        if f.endswith(('.dcm', '.nrrd', '.nii', '.nii.gz')):
                            await processor.process_file(
                                os.path.join(root, f), study.id, db, storage
                            )
            else:
                await processor.process_file(temp_file_path, study.id, db, storage)
            
            study.status = "ready"
            
        except Exception as e:
            study.status = "error"
            study.error_message = str(e)
        
        finally:
            await db.commit()
            # Cleanup temp files
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    background_tasks.add_task(process_uploaded_file)
    
    return study


@router.put("/{study_id}", response_model=StudyResponse)
async def update_study(
    study_id: UUID,
    study_update: StudyUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update study (admin only)"""
    result = await db.execute(select(Study).where(Study.id == study_id))
    study = result.scalar_one_or_none()
    
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    if study_update.patient_id is not None:
        study.patient_id = study_update.patient_id
    if study_update.study_description is not None:
        study.study_description = study_update.study_description
    
    await db.commit()
    await db.refresh(study)
    
    return study


@router.delete("/{study_id}")
async def delete_study(
    study_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    """Delete study and all associated data (admin only)"""
    result = await db.execute(
        select(Study)
        .where(Study.id == study_id)
        .options(selectinload(Study.series).selectinload(Series.images))
    )
    study = result.scalar_one_or_none()
    
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Delete files from storage
    for series in study.series:
        for image in series.images:
            try:
                await storage.delete_file(image.file_path)
            except Exception:
                pass  # Ignore storage errors during deletion
    
    # Delete database records (cascade)
    await db.delete(study)
    await db.commit()
    
    return {"message": "Study deleted successfully"}


@router.get("/{study_id}/series")
async def list_series(
    study_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all series in a study"""
    result = await db.execute(
        select(Series)
        .where(Series.study_id == study_id)
        .options(selectinload(Series.images))
    )
    series_list = result.scalars().all()
    
    return [
        {
            **SeriesResponse.model_validate(s).model_dump(),
            "images": [ImageResponse.model_validate(i) for i in s.images]
        }
        for s in series_list
    ]


@router.get("/{study_id}/images")
async def list_images(
    study_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all images in a study"""
    result = await db.execute(
        select(Image)
        .join(Series)
        .where(Series.study_id == study_id)
    )
    images = result.scalars().all()
    
    return [ImageResponse.model_validate(i) for i in images]


@router.get("/{study_id}/download")
async def download_study(
    study_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    """Get download URL for study files"""
    result = await db.execute(
        select(Study)
        .where(Study.id == study_id)
        .options(selectinload(Study.series).selectinload(Series.images))
    )
    study = result.scalar_one_or_none()
    
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Generate presigned URLs for all images
    download_urls = []
    for series in study.series:
        for image in series.images:
            url = await storage.get_presigned_url(image.file_path)
            download_urls.append({
                "image_id": str(image.id),
                "file_path": image.file_path,
                "download_url": url
            })
    
    return {"study_id": str(study_id), "files": download_urls}