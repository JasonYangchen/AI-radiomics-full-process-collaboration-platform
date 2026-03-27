"""
DICOM utilities
"""
import os
import tempfile
from typing import Dict, List, Optional, Any, Tuple
import pydicom
from pydicom.dataset import Dataset
import SimpleITK as sitk
import numpy as np


class DICOMUtils:
    """DICOM file utilities"""
    
    @staticmethod
    def read_dicom_file(file_path: str) -> Dataset:
        """Read a single DICOM file"""
        return pydicom.dcmread(file_path)
    
    @staticmethod
    def read_dicom_series(directory: str) -> sitk.Image:
        """Read DICOM series from directory"""
        reader = sitk.ImageSeriesReader()
        dicom_names = reader.GetGDCMSeriesFileNames(directory)
        
        if not dicom_names:
            raise ValueError(f"No DICOM series found in {directory}")
        
        reader.SetFileNames(dicom_names)
        return reader.Execute()
    
    @staticmethod
    def get_series_uids(directory: str) -> List[str]:
        """Get all Series Instance UIDs in a directory"""
        reader = sitk.ImageSeriesReader()
        series_ids = reader.GetGDCMSeriesIDs(directory)
        return list(series_ids)
    
    @staticmethod
    def extract_metadata(ds: Dataset) -> Dict[str, Any]:
        """Extract relevant metadata from DICOM dataset"""
        metadata = {}
        
        # Patient metadata
        patient_fields = [
            ('PatientID', 'patient_id'),
            ('PatientName', 'patient_name'),
            ('PatientBirthDate', 'patient_birth_date'),
            ('PatientSex', 'patient_sex'),
            ('PatientAge', 'patient_age'),
            ('PatientWeight', 'patient_weight'),
        ]
        
        for tag, key in patient_fields:
            if hasattr(ds, tag):
                metadata[key] = getattr(ds, tag)
        
        # Study metadata
        study_fields = [
            ('StudyInstanceUID', 'study_instance_uid'),
            ('StudyID', 'study_id'),
            ('StudyDate', 'study_date'),
            ('StudyTime', 'study_time'),
            ('StudyDescription', 'study_description'),
            ('AccessionNumber', 'accession_number'),
        ]
        
        for tag, key in study_fields:
            if hasattr(ds, tag):
                metadata[key] = getattr(ds, tag)
        
        # Series metadata
        series_fields = [
            ('SeriesInstanceUID', 'series_instance_uid'),
            ('SeriesNumber', 'series_number'),
            ('SeriesDescription', 'series_description'),
            ('Modality', 'modality'),
            ('SeriesDate', 'series_date'),
        ]
        
        for tag, key in series_fields:
            if hasattr(ds, tag):
                metadata[key] = getattr(ds, tag)
        
        # Image metadata
        image_fields = [
            ('Rows', 'rows'),
            ('Columns', 'columns'),
            ('NumberOfFrames', 'number_of_frames'),
            ('BitsAllocated', 'bits_allocated'),
            ('BitsStored', 'bits_stored'),
            ('PixelRepresentation', 'pixel_representation'),
            ('PhotometricInterpretation', 'photometric_interpretation'),
            ('SamplesPerPixel', 'samples_per_pixel'),
            ('PixelSpacing', 'pixel_spacing'),
            ('SliceThickness', 'slice_thickness'),
            ('ImageOrientationPatient', 'image_orientation_patient'),
            ('ImagePositionPatient', 'image_position_patient'),
            ('SliceLocation', 'slice_location'),
            ('WindowCenter', 'window_center'),
            ('WindowWidth', 'window_width'),
            ('RescaleIntercept', 'rescale_intercept'),
            ('RescaleSlope', 'rescale_slope'),
        ]
        
        for tag, key in image_fields:
            if hasattr(ds, tag):
                value = getattr(ds, tag)
                # Convert to serializable format
                if isinstance(value, pydicom.multival.MultiValue):
                    metadata[key] = list(value)
                elif hasattr(value, 'value'):
                    metadata[key] = value.value
                else:
                    metadata[key] = value
        
        # Acquisition metadata
        acquisition_fields = [
            ('Manufacturer', 'manufacturer'),
            ('ManufacturerModelName', 'manufacturer_model_name'),
            ('InstitutionName', 'institution_name'),
            ('StationName', 'station_name'),
            ('ProtocolName', 'protocol_name'),
            ('KVP', 'kvp'),
            ('ExposureTime', 'exposure_time'),
            ('XRayTubeCurrent', 'xray_tube_current'),
            ('Exposure', 'exposure'),
        ]
        
        for tag, key in acquisition_fields:
            if hasattr(ds, tag):
                metadata[key] = getattr(ds, tag)
        
        return metadata
    
    @staticmethod
    def get_pixel_array(ds: Dataset, apply_modality_lut: bool = True) -> np.ndarray:
        """Get pixel array from DICOM dataset"""
        if apply_modality_lut:
            return pydicom.pixel_data_handlers.util.apply_modality_lut(
                ds.pixel_array, ds
            )
        return ds.pixel_array
    
    @staticmethod
    def apply_windowing(
        pixel_array: np.ndarray,
        window_center: float,
        window_width: float,
        output_range: Tuple[float, float] = (0, 255)
    ) -> np.ndarray:
        """Apply windowing to pixel array"""
        min_value = window_center - window_width // 2
        max_value = window_center + window_width // 2
        
        # Clip values
        windowed = np.clip(pixel_array, min_value, max_value)
        
        # Normalize to output range
        windowed = (windowed - min_value) / (max_value - min_value)
        windowed = windowed * (output_range[1] - output_range[0]) + output_range[0]
        
        return windowed.astype(np.uint8)
    
    @staticmethod
    def create_dicom_from_array(
        pixel_array: np.ndarray,
        metadata: Dict[str, Any],
        output_path: str
    ) -> None:
        """Create DICOM file from numpy array and metadata"""
        file_meta = pydicom.dataset.FileMetaDataset()
        
        # Create dataset
        ds = Dataset()
        ds.file_meta = file_meta
        
        # Set required DICOM tags
        ds.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'  # CT Image Storage
        ds.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
        ds.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
        
        # Set patient/study/series info from metadata
        for key, value in metadata.items():
            if hasattr(pydicom.tag, key.upper()):
                setattr(ds, key, value)
        
        # Set image data
        ds.Rows, ds.Columns = pixel_array.shape
        ds.PixelData = pixel_array.tobytes()
        ds.BitsAllocated = 16
        ds.BitsStored = 16
        ds.HighBit = 15
        ds.PixelRepresentation = 1
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        
        # Save
        ds.save_as(output_path)
    
    @staticmethod
    def anonymize_dicom(
        input_path: str,
        output_path: str,
        keep_tags: Optional[List[str]] = None
    ) -> None:
        """Anonymize DICOM file"""
        ds = pydicom.dcmread(input_path)
        
        # Tags to remove/anonymize
        anonymize_tags = [
            'PatientName', 'PatientID', 'PatientBirthDate', 'PatientAddress',
            'PatientPhoneNumbers', 'PatientInsurancePlanCodeSequence',
            'InstitutionName', 'InstitutionAddress', 'InstitutionCodeSequence',
            'ReferringPhysicianName', 'ReferringPhysicianAddress',
            'ReferringPhysicianPhoneNumbers', 'PhysiciansOfRecord',
            'PerformingPhysicianName', 'NameOfPhysiciansReadingStudy',
            'OperatorsName', 'StationName'
        ]
        
        keep_tags = keep_tags or []
        
        for tag in anonymize_tags:
            if tag not in keep_tags and hasattr(ds, tag):
                if tag in ['PatientID', 'PatientName']:
                    setattr(ds, tag, 'ANONYMOUS')
                elif tag == 'PatientBirthDate':
                    setattr(ds, tag, '19000101')
                else:
                    delattr(ds, tag)
        
        ds.save_as(output_path)