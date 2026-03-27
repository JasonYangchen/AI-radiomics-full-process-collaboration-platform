"""
Study and Image models
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Integer, Float, ARRAY, JSON, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.session import Base


class Study(Base):
    """Medical imaging study"""
    __tablename__ = "studies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(String(100), index=True)
    study_uid = Column(String(255), unique=True, index=True)  # DICOM StudyInstanceUID
    study_date = Column(Date)
    study_description = Column(Text)
    modality = Column(String(20))  # CT, MR, X-ray
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    status = Column(String(20), default="pending")  # pending, processing, ready, error
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    uploader = relationship("User", back_populates="studies")
    series = relationship("Series", back_populates="study", cascade="all, delete-orphan")
    annotations = relationship("AnnotationProject", back_populates="study", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Study {self.study_uid or self.id}>"


class Series(Base):
    """Medical imaging series"""
    __tablename__ = "series"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id = Column(UUID(as_uuid=True), ForeignKey("studies.id", ondelete="CASCADE"), nullable=False)
    series_uid = Column(String(255), index=True)  # DICOM SeriesInstanceUID
    series_description = Column(Text)
    series_number = Column(Integer)
    modality = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    study = relationship("Study", back_populates="series")
    images = relationship("Image", back_populates="series", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Series {self.series_uid or self.id}>"


class Image(Base):
    """Medical image file"""
    __tablename__ = "images"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    series_id = Column(UUID(as_uuid=True), ForeignKey("series.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(500), nullable=False)  # MinIO path
    file_format = Column(String(20), nullable=False)  # DICOM, NRRD, NIfTI
    file_size = Column(Integer)  # bytes
    dimensions = Column(ARRAY(Integer))  # [x, y, z] or [x, y]
    spacing = Column(ARRAY(Float))  # voxel spacing
    origin = Column(ARRAY(Float))  # image origin
    image_metadata = Column(JSON)  # full metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    series = relationship("Series", back_populates="images")
    rois = relationship("ROI", back_populates="image", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Image {self.file_path}>"