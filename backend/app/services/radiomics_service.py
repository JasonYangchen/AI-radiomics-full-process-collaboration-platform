"""
Radiomics Feature Extraction Service
"""
import io
import os
import tempfile
import asyncio
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime
import SimpleITK as sitk
import numpy as np
from radiomics import featureextractor, firstorder, shape, glcm, glrlm, glszm, ngtdm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.study import Study, Series, Image
from app.models.annotation import ROI
from app.models.feature import FeatureExtraction, FeatureResult
from app.services.storage_service import StorageService
from app.core.config import settings
from app.core.celery_app import celery_app


class RadiomicsService:
    """PyRadiomics feature extraction service"""
    
    def __init__(self):
        self.storage = StorageService()
        self.default_settings = settings.RADIOMICS_CONFIG
    
    def get_extractor(self, config: Optional[Dict] = None) -> featureextractor.RadiomicsFeatureExtractor:
        """Create PyRadiomics extractor with configuration"""
        settings_dict = config or self.default_settings
        
        # Create extractor
        extractor = featureextractor.RadiomicsFeatureExtractor(
            settings=settings_dict,
            voxelBased=False
        )
        
        # Enable all feature classes by default
        extractor.enableAllFeatures()
        
        return extractor
    
    async def run_extraction(
        self,
        extraction_id: UUID,
        db: AsyncSession
    ) -> None:
        """Run feature extraction task"""
        # Get extraction record
        result = await db.execute(
            select(FeatureExtraction)
            .where(FeatureExtraction.id == extraction_id)
            .options(
                selectinload(FeatureExtraction.study).selectinload(Study.series).selectinload(Series.images)
            )
        )
        extraction = result.scalar_one_or_none()
        
        if not extraction:
            raise ValueError(f"Extraction {extraction_id} not found")
        
        try:
            # Update status
            extraction.status = "running"
            extraction.started_at = datetime.utcnow()
            await db.commit()
            
            # Create extractor
            config = extraction.config or self.default_settings
            extractor = self.get_extractor(config)
            
            # Get images
            study = extraction.study
            all_features = []
            
            total_images = sum(len(series.images) for series in study.series)
            processed = 0
            
            for series in study.series:
                for image in series.images:
                    try:
                        # Download image from storage
                        image_bytes = await self.storage.download_file(image.file_path)
                        
                        # Save to temp file
                        with tempfile.NamedTemporaryFile(suffix=self._get_suffix(image.file_format), delete=False) as f:
                            f.write(image_bytes)
                            temp_image_path = f.name
                        
                        # Load image
                        sitk_image = sitk.ReadImage(temp_image_path)
                        
                        # Get mask if ROI specified
                        if extraction.roi_id:
                            mask_sitk = await self._get_roi_mask(extraction.roi_id, image, db)
                        else:
                            # Create whole image mask
                            mask_sitk = self._create_whole_image_mask(sitk_image)
                        
                        # Extract features
                        features = extractor.execute(sitk_image, mask_sitk)
                        
                        # Save features
                        for feature_name, feature_value in features.items():
                            if feature_name.startswith('original_'):
                                # Parse feature class and name
                                parts = feature_name.split('_')
                                if len(parts) >= 3:
                                    feature_class = parts[1]  # e.g., 'firstorder', 'shape', 'glcm'
                                    feature_name_clean = '_'.join(parts[2:])
                                    
                                    result = FeatureResult(
                                        extraction_id=extraction.id,
                                        image_id=image.id,
                                        roi_id=extraction.roi_id,
                                        feature_class=feature_class,
                                        feature_name=feature_name_clean,
                                        feature_value=float(feature_value)
                                    )
                                    db.add(result)
                        
                        # Cleanup temp file
                        os.unlink(temp_image_path)
                        
                        processed += 1
                        extraction.progress = int((processed / total_images) * 100)
                        await db.commit()
                        
                    except Exception as e:
                        print(f"Error processing image {image.id}: {e}")
                        continue
            
            # Update status
            extraction.status = "completed"
            extraction.completed_at = datetime.utcnow()
            extraction.progress = 100
            await db.commit()
            
        except Exception as e:
            extraction.status = "failed"
            extraction.error_message = str(e)
            await db.commit()
            raise
    
    async def _get_roi_mask(
        self,
        roi_id: UUID,
        image: Image,
        db: AsyncSession
    ) -> sitk.Image:
        """Get ROI mask as SimpleITK image"""
        result = await db.execute(select(ROI).where(ROI.id == roi_id))
        roi = result.scalar_one_or_none()
        
        if not roi or not roi.mask_data:
            raise ValueError("ROI not found or has no mask data")
        
        # Decompress mask data
        import zlib
        import base64
        
        mask_bytes = zlib.decompress(roi.mask_data)
        
        # Convert to numpy array and then to SimpleITK image
        # This is simplified - actual implementation would need proper shape/spacing info
        mask_array = np.frombuffer(mask_bytes, dtype=np.uint8)
        
        # Reshape based on image dimensions
        mask_array = mask_array.reshape(image.dimensions)
        
        # Create SimpleITK image
        mask_sitk = sitk.GetImageFromArray(mask_array)
        
        # Set spacing and origin from original image
        if image.spacing:
            mask_sitk.SetSpacing(image.spacing)
        if image.origin:
            mask_sitk.SetOrigin(image.origin)
        
        return mask_sitk
    
    def _create_whole_image_mask(self, image: sitk.Image) -> sitk.Image:
        """Create a mask covering the entire image"""
        array = sitk.GetArrayFromImage(image)
        mask_array = np.ones_like(array, dtype=np.uint8)
        mask = sitk.GetImageFromArray(mask_array)
        mask.CopyInformation(image)
        return mask
    
    def _get_suffix(self, file_format: str) -> str:
        """Get file suffix for format"""
        suffixes = {
            "DICOM": ".dcm",
            "NRRD": ".nrrd",
            "NIfTI": ".nii"
        }
        return suffixes.get(file_format, ".nii")
    
    def extract_features_for_single_image(
        self,
        image_path: str,
        mask_path: Optional[str] = None,
        config: Optional[Dict] = None
    ) -> Dict[str, float]:
        """Extract features from a single image (synchronous)"""
        extractor = self.get_extractor(config)
        
        # Load image
        sitk_image = sitk.ReadImage(image_path)
        
        # Load or create mask
        if mask_path:
            sitk_mask = sitk.ReadImage(mask_path)
        else:
            sitk_mask = self._create_whole_image_mask(sitk_image)
        
        # Extract features
        features = extractor.execute(sitk_image, sitk_mask)
        
        # Filter and format
        result = {}
        for key, value in features.items():
            if key.startswith('original_') and isinstance(value, (int, float)):
                result[key] = float(value)
        
        return result


@celery_app.task(bind=True)
def extract_features_task(self, extraction_id: str, study_id: str, roi_id: str = None, config: dict = None):
    """Celery task for feature extraction"""
    import asyncio
    
    async def run():
        from app.db.session import async_session_maker
        
        async with async_session_maker() as db:
            service = RadiomicsService()
            await service.run_extraction(UUID(extraction_id), db)
    
    asyncio.run(run())


# Feature class descriptions for reference
FEATURE_CLASSES = {
    "firstorder": {
        "name": "First Order Statistics",
        "description": "Statistics describing the distribution of voxel intensities",
        "features": [
            "Energy", "TotalEnergy", "Entropy", "Minimum", "10Percentile",
            "90Percentile", "Maximum", "Mean", "Median", "InterquartileRange",
            "Range", "MeanAbsoluteDeviation", "RobustMeanAbsoluteDeviation",
            "RootMeanSquared", "StandardDeviation", "Skewness", "Kurtosis",
            "Variance", "Uniformity"
        ]
    },
    "shape": {
        "name": "Shape-based (3D)",
        "description": "3D shape descriptors",
        "features": [
            "MeshVolume", "VoxelVolume", "SurfaceArea", "SurfaceVolumeRatio",
            "Compactness1", "Compactness2", "Sphericity", "SphericalDisproportion",
            "Maximum3DDiameter", "Maximum2DDiameterSlice", "Maximum2DDiameterColumn",
            "Maximum2DDiameterRow", "MajorAxisLength", "MinorAxisLength",
            "LeastAxisLength", "Elongation", "Flatness"
        ]
    },
    "glcm": {
        "name": "Gray Level Co-occurrence Matrix (GLCM)",
        "description": "Texture features from the GLCM",
        "features": [
            "Autocorrelation", "JointAverage", "ClusterProminence",
            "ClusterShade", "ClusterTendency", "Contrast", "Correlation",
            "DifferenceAverage", "DifferenceEntropy", "DifferenceVariance",
            "JointEnergy", "JointEntropy", "Imc1", "Imc2", "Idm", "Idmn",
            "Id", "Idn", "InverseVariance", "MaximumProbability", "SumAverage",
            "SumEntropy", "SumSquares"
        ]
    },
    "glrlm": {
        "name": "Gray Level Run Length Matrix (GLRLM)",
        "description": "Texture features from the GLRLM",
        "features": [
            "ShortRunEmphasis", "LongRunEmphasis", "GrayLevelNonUniformity",
            "GrayLevelNonUniformityNormalized", "RunLengthNonUniformity",
            "RunLengthNonUniformityNormalized", "RunPercentage",
            "GrayLevelVariance", "RunVariance", "RunEntropy",
            "LowGrayLevelRunEmphasis", "HighGrayLevelRunEmphasis",
            "ShortRunLowGrayLevelEmphasis", "ShortRunHighGrayLevelEmphasis",
            "LongRunLowGrayLevelEmphasis", "LongRunHighGrayLevelEmphasis"
        ]
    },
    "glszm": {
        "name": "Gray Level Size Zone Matrix (GLSZM)",
        "description": "Texture features from the GLSZM",
        "features": [
            "SmallAreaEmphasis", "LargeAreaEmphasis", "GrayLevelNonUniformity",
            "GrayLevelNonUniformityNormalized", "SizeZoneNonUniformity",
            "SizeZoneNonUniformityNormalized", "ZonePercentage", "GrayLevelVariance",
            "ZoneVariance", "ZoneEntropy", "LowGrayLevelZoneEmphasis",
            "HighGrayLevelZoneEmphasis", "SmallAreaLowGrayLevelEmphasis",
            "SmallAreaHighGrayLevelEmphasis", "LargeAreaLowGrayLevelEmphasis",
            "LargeAreaHighGrayLevelEmphasis"
        ]
    },
    "ngtdm": {
        "name": "Neighbouring Gray Tone Difference Matrix (NGTDM)",
        "description": "Texture features from the NGTDM",
        "features": [
            "Coarseness", "Contrast", "Busyness", "Complexity", "Strength"
        ]
    }
}