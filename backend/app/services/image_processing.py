"""
Image Processing Service
"""
import os
import tempfile
import shutil
from typing import Optional, Dict, Any
from uuid import UUID
import SimpleITK as sitk
import pydicom
import nibabel as nib
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.study import Study, Series, Image
from app.services.storage_service import StorageService


class ImageProcessor:
    """Process medical imaging files"""
    
    def __init__(self):
        self.storage = StorageService()
    
    async def process_file(
        self,
        file_path: str,
        study_id: UUID,
        db: AsyncSession,
        storage: StorageService
    ) -> None:
        """Process uploaded medical image file"""
        file_ext = self._get_file_extension(file_path)
        
        if file_ext == ".dcm":
            await self._process_dicom(file_path, study_id, db, storage)
        elif file_ext == ".nrrd":
            await self._process_nrrd(file_path, study_id, db, storage)
        elif file_ext in [".nii", ".nii.gz"]:
            await self._process_nifti(file_path, study_id, db, storage)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def _get_file_extension(self, file_path: str) -> str:
        """Get file extension"""
        file_path_lower = file_path.lower()
        if file_path_lower.endswith(".nii.gz"):
            return ".nii.gz"
        return os.path.splitext(file_path_lower)[1]
    
    async def _process_dicom(
        self,
        file_path: str,
        study_id: UUID,
        db: AsyncSession,
        storage: StorageService
    ) -> None:
        """Process DICOM file(s)"""
        # Read DICOM
        ds = pydicom.dcmread(file_path)
        
        # Get study info
        result = await db.execute(select(Study).where(Study.id == study_id))
        study = result.scalar_one()
        
        # Update study with DICOM metadata
        if hasattr(ds, 'StudyInstanceUID'):
            study.study_uid = ds.StudyInstanceUID
        if hasattr(ds, 'StudyDate'):
            from datetime import datetime
            try:
                study.study_date = datetime.strptime(ds.StudyDate, "%Y%m%d").date()
            except:
                pass
        if hasattr(ds, 'StudyDescription'):
            study.study_description = ds.StudyDescription
        if hasattr(ds, 'Modality'):
            study.modality = ds.Modality
        if hasattr(ds, 'PatientID'):
            study.patient_id = ds.PatientID
        
        # Create or get series
        series_uid = getattr(ds, 'SeriesInstanceUID', None)
        series_description = getattr(ds, 'SeriesDescription', None)
        series_number = getattr(ds, 'SeriesNumber', None)
        modality = getattr(ds, 'Modality', None)
        
        series = Series(
            study_id=study_id,
            series_uid=series_uid,
            series_description=series_description,
            series_number=series_number,
            modality=modality
        )
        db.add(series)
        await db.flush()
        
        # Read image data
        image_array = ds.pixel_array
        dimensions = list(image_array.shape)
        
        # Get spacing and origin
        spacing = None
        origin = None
        if hasattr(ds, 'PixelSpacing'):
            spacing = [float(ds.PixelSpacing[0]), float(ds.PixelSpacing[1])]
            if hasattr(ds, 'SliceThickness'):
                spacing.append(float(ds.SliceThickness))
        
        if hasattr(ds, 'ImagePositionPatient'):
            origin = [float(x) for x in ds.ImagePositionPatient]
        
        # Upload to storage
        storage_path = f"studies/{study_id}/series/{series.id}/image.dcm"
        with open(file_path, 'rb') as f:
            await storage.upload_file(storage_path, f.read(), "application/dicom")
        
        # Create image record
        image = Image(
            series_id=series.id,
            file_path=storage_path,
            file_format="DICOM",
            file_size=os.path.getsize(file_path),
            dimensions=dimensions,
            spacing=spacing,
            origin=origin,
            image_metadata=self._extract_dicom_metadata(ds)
        )
        db.add(image)
        await db.commit()
    
    async def _process_nrrd(
        self,
        file_path: str,
        study_id: UUID,
        db: AsyncSession,
        storage: StorageService
    ) -> None:
        """Process NRRD file"""
        import pynrrd
        
        # Read NRRD
        image_data, header = pynrrd.read(file_path)
        
        # Get study
        result = await db.execute(select(Study).where(Study.id == study_id))
        study = result.scalar_one()
        
        # Update study
        study.modality = self._guess_modality_from_header(header)
        
        # Create series
        series = Series(
            study_id=study_id,
            series_description="NRRD Import"
        )
        db.add(series)
        await db.flush()
        
        # Get metadata
        dimensions = list(image_data.shape)
        spacing = header.get('space directions')
        if spacing is not None:
            spacing = [float(s) for s in np.diag(spacing) if s != 0]
        origin = header.get('space origin')
        if origin is not None:
            origin = [float(o) for o in origin]
        
        # Upload to storage
        storage_path = f"studies/{study_id}/series/{series.id}/image.nrrd"
        with open(file_path, 'rb') as f:
            await storage.upload_file(storage_path, f.read(), "application/octet-stream")
        
        # Create image record
        image = Image(
            series_id=series.id,
            file_path=storage_path,
            file_format="NRRD",
            file_size=os.path.getsize(file_path),
            dimensions=dimensions,
            spacing=spacing,
            origin=origin,
            image_metadata=header
        )
        db.add(image)
        await db.commit()
    
    async def _process_nifti(
        self,
        file_path: str,
        study_id: UUID,
        db: AsyncSession,
        storage: StorageService
    ) -> None:
        """Process NIfTI file"""
        # Read NIfTI
        img = nib.load(file_path)
        image_data = img.get_fdata()
        affine = img.affine
        
        # Get study
        result = await db.execute(select(Study).where(Study.id == study_id))
        study = result.scalar_one()
        
        # Create series
        series = Series(
            study_id=study_id,
            series_description="NIfTI Import"
        )
        db.add(series)
        await db.flush()
        
        # Get metadata
        dimensions = list(image_data.shape)
        # Calculate voxel spacing from affine
        spacing = [float(img.header.get_zooms()[i]) for i in range(min(3, len(img.header.get_zooms())))]
        origin = [float(affine[i, 3]) for i in range(3)]
        
        # Upload to storage
        ext = ".nii.gz" if file_path.endswith(".nii.gz") else ".nii"
        storage_path = f"studies/{study_id}/series/{series.id}/image{ext}"
        with open(file_path, 'rb') as f:
            await storage.upload_file(storage_path, f.read(), "application/octet-stream")
        
        # Create image record
        image = Image(
            series_id=series.id,
            file_path=storage_path,
            file_format="NIfTI",
            file_size=os.path.getsize(file_path),
            dimensions=dimensions,
            spacing=spacing,
            origin=origin,
            image_metadata={"affine": affine.tolist()}
        )
        db.add(image)
        await db.commit()
    
    def _extract_dicom_metadata(self, ds) -> Dict[str, Any]:
        """Extract relevant DICOM metadata"""
        metadata = {}
        
        # Patient info
        if hasattr(ds, 'PatientName'):
            metadata['patient_name'] = str(ds.PatientName)
        if hasattr(ds, 'PatientID'):
            metadata['patient_id'] = ds.PatientID
        if hasattr(ds, 'PatientBirthDate'):
            metadata['patient_birth_date'] = ds.PatientBirthDate
        if hasattr(ds, 'PatientSex'):
            metadata['patient_sex'] = ds.PatientSex
        
        # Study info
        if hasattr(ds, 'StudyInstanceUID'):
            metadata['study_instance_uid'] = ds.StudyInstanceUID
        if hasattr(ds, 'StudyDate'):
            metadata['study_date'] = ds.StudyDate
        if hasattr(ds, 'StudyTime'):
            metadata['study_time'] = ds.StudyTime
        if hasattr(ds, 'StudyDescription'):
            metadata['study_description'] = ds.StudyDescription
        
        # Series info
        if hasattr(ds, 'SeriesInstanceUID'):
            metadata['series_instance_uid'] = ds.SeriesInstanceUID
        if hasattr(ds, 'SeriesNumber'):
            metadata['series_number'] = ds.SeriesNumber
        if hasattr(ds, 'SeriesDescription'):
            metadata['series_description'] = ds.SeriesDescription
        
        # Image info
        if hasattr(ds, 'Modality'):
            metadata['modality'] = ds.Modality
        if hasattr(ds, 'Manufacturer'):
            metadata['manufacturer'] = ds.Manufacturer
        if hasattr(ds, 'Rows'):
            metadata['rows'] = ds.Rows
        if hasattr(ds, 'Columns'):
            metadata['columns'] = ds.Columns
        if hasattr(ds, 'BitsStored'):
            metadata['bits_stored'] = ds.BitsStored
        if hasattr(ds, 'WindowCenter'):
            metadata['window_center'] = ds.WindowCenter
        if hasattr(ds, 'WindowWidth'):
            metadata['window_width'] = ds.WindowWidth
        
        return metadata
    
    def _guess_modality_from_header(self, header: dict) -> str:
        """Guess modality from NRRD header"""
        # Try to find modality hints in the header
        description = str(header.get('description', '')).lower()
        
        if 'ct' in description:
            return 'CT'
        elif 'mr' in description or 'mri' in description:
            return 'MR'
        elif 'pet' in description:
            return 'PT'
        else:
            return 'OT'  # Other
    
    def load_image(self, file_path: str, file_format: str) -> sitk.Image:
        """Load image using SimpleITK"""
        if file_format == "DICOM":
            # For DICOM series, we need the directory
            return sitk.ReadImage(file_path)
        else:
            return sitk.ReadImage(file_path)
    
    def get_image_array(self, image: sitk.Image) -> np.ndarray:
        """Convert SimpleITK image to numpy array"""
        return sitk.GetArrayFromImage(image)