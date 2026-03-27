"""
NRRD utilities
"""
import os
import tempfile
from typing import Dict, Optional, Tuple, Any
import numpy as np
import SimpleITK as sitk
import pynrrd


class NRRDUtils:
    """NRRD file utilities"""
    
    @staticmethod
    def read_nrrd(file_path: str) -> Tuple[np.ndarray, Dict]:
        """Read NRRD file and return data and header"""
        return pynrrd.read(file_path)
    
    @staticmethod
    def write_nrrd(
        file_path: str,
        data: np.ndarray,
        header: Optional[Dict] = None
    ) -> None:
        """Write numpy array to NRRD file"""
        if header is None:
            header = {}
        
        # Ensure required header fields
        if 'encoding' not in header:
            header['encoding'] = 'gzip'
        if 'space' not in header:
            header['space'] = 'left-posterior-superior'
        
        pynrrd.write(file_path, data, header)
    
    @staticmethod
    def read_as_sitk(file_path: str) -> sitk.Image:
        """Read NRRD file as SimpleITK image"""
        return sitk.ReadImage(file_path)
    
    @staticmethod
    def from_sitk(image: sitk.Image) -> Tuple[np.ndarray, Dict]:
        """Convert SimpleITK image to numpy array and NRRD header"""
        array = sitk.GetArrayFromImage(image)
        
        # Build header
        header = {
            'type': NRRDUtils._get_nrrd_type(array.dtype),
            'dimension': len(array.shape),
            'sizes': list(array.shape),
            'space': 'left-posterior-superior',
            'space directions': list(image.GetDirection()),
            'space origin': list(image.GetOrigin()),
            'encoding': 'gzip'
        }
        
        spacing = image.GetSpacing()
        if len(spacing) == 3:
            header['space directions'] = [
                [spacing[0], 0, 0],
                [0, spacing[1], 0],
                [0, 0, spacing[2]]
            ]
        
        return array, header
    
    @staticmethod
    def _get_nrrd_type(dtype: np.dtype) -> str:
        """Get NRRD type string from numpy dtype"""
        type_map = {
            'int8': 'int8',
            'int16': 'int16',
            'int32': 'int32',
            'int64': 'int64',
            'uint8': 'uint8',
            'uint16': 'uint16',
            'uint32': 'uint32',
            'uint64': 'uint64',
            'float32': 'float',
            'float64': 'double',
        }
        return type_map.get(str(dtype), 'float')
    
    @staticmethod
    def create_mask_nrrd(
        mask_array: np.ndarray,
        reference_header: Dict,
        output_path: str
    ) -> None:
        """Create NRRD mask file with reference header"""
        header = {
            'type': 'uint8',
            'dimension': len(mask_array.shape),
            'sizes': list(mask_array.shape),
            'space': reference_header.get('space', 'left-posterior-superior'),
            'encoding': 'gzip'
        }
        
        # Copy spatial information from reference
        if 'space directions' in reference_header:
            header['space directions'] = reference_header['space directions']
        if 'space origin' in reference_header:
            header['space origin'] = reference_header['space origin']
        
        pynrrd.write(output_path, mask_array.astype(np.uint8), header)
    
    @staticmethod
    def extract_header_info(header: Dict) -> Dict[str, Any]:
        """Extract useful information from NRRD header"""
        info = {
            'dimension': header.get('dimension'),
            'sizes': header.get('sizes'),
            'type': header.get('type'),
            'encoding': header.get('encoding'),
            'space': header.get('space'),
            'space_origin': header.get('space origin'),
            'space_directions': header.get('space directions'),
        }
        
        # Calculate spacing from space directions
        if 'space directions' in header:
            directions = header['space directions']
            if isinstance(directions, list):
                spacing = []
                for d in directions:
                    if isinstance(d, list) and len(d) == 3:
                        # Extract diagonal elements
                        for i, val in enumerate(d):
                            if val != 0:
                                spacing.append(abs(val))
                                break
                info['spacing'] = spacing
        
        return info
    
    @staticmethod
    def merge_masks(mask_files: list, output_path: str) -> None:
        """Merge multiple mask files into one"""
        combined_mask = None
        
        for i, mask_file in enumerate(mask_files):
            mask_data, header = pynrrd.read(mask_file)
            
            if combined_mask is None:
                combined_mask = np.zeros_like(mask_data, dtype=np.uint8)
            
            # Add this mask with label value (i+1)
            combined_mask[mask_data > 0] = i + 1
        
        # Save combined mask
        NRRDUtils.write_nrrd(output_path, combined_mask, header)
    
    @staticmethod
    def resample_mask(
        mask_file: str,
        reference_file: str,
        output_path: str,
        interpolator=sitk.sitkNearestNeighbor
    ) -> None:
        """Resample mask to match reference image"""
        mask_image = sitk.ReadImage(mask_file)
        ref_image = sitk.ReadImage(reference_file)
        
        # Resample
        resampled = sitk.Resample(
            mask_image,
            ref_image,
            sitk.Transform(),
            interpolator,
            0.0,
            mask_image.GetPixelID()
        )
        
        # Save
        sitk.WriteImage(resampled, output_path)