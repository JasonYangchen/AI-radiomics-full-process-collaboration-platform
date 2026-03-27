"""
Feature extraction models
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Integer, Float, ARRAY, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.session import Base


class FeatureExtraction(Base):
    """Feature extraction task"""
    __tablename__ = "feature_extractions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id = Column(UUID(as_uuid=True), ForeignKey("studies.id", ondelete="CASCADE"))
    roi_id = Column(UUID(as_uuid=True), ForeignKey("rois.id", ondelete="SET NULL"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    config = Column(JSON)  # PyRadiomics configuration
    progress = Column(Integer, default=0)  # 0-100
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    study = relationship("Study")
    roi = relationship("ROI")
    creator = relationship("User")
    results = relationship("FeatureResult", back_populates="extraction", cascade="all, delete-orphan")
    exports = relationship("FeatureExport", back_populates="extraction", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FeatureExtraction {self.id}>"


class FeatureResult(Base):
    """Individual feature result"""
    __tablename__ = "feature_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    extraction_id = Column(UUID(as_uuid=True), ForeignKey("feature_extractions.id", ondelete="CASCADE"), nullable=False)
    image_id = Column(UUID(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"))
    roi_id = Column(UUID(as_uuid=True), ForeignKey("rois.id", ondelete="SET NULL"))
    feature_class = Column(String(50))  # firstorder, shape, glcm, etc.
    feature_name = Column(String(100))
    feature_value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    extraction = relationship("FeatureExtraction", back_populates="results")
    image = relationship("Image")
    roi = relationship("ROI", back_populates="feature_results")
    
    def __repr__(self):
        return f"<FeatureResult {self.feature_name}: {self.feature_value}>"


class FeatureExport(Base):
    """Feature export file"""
    __tablename__ = "feature_exports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    extraction_id = Column(UUID(as_uuid=True), ForeignKey("feature_extractions.id", ondelete="CASCADE"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    file_path = Column(String(500))  # MinIO path
    file_format = Column(String(20))  # CSV, Excel
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    extraction = relationship("FeatureExtraction", back_populates="exports")
    creator = relationship("User")
    
    def __repr__(self):
        return f"<FeatureExport {self.file_path}>"