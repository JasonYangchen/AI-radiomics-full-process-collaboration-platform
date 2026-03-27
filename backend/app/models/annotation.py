"""
Annotation models
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Integer, Float, ARRAY, JSON, LargeBinary, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.session import Base


class AnnotationProject(Base):
    """Annotation project"""
    __tablename__ = "annotation_projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    study_id = Column(UUID(as_uuid=True), ForeignKey("studies.id", ondelete="CASCADE"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    status = Column(String(20), default="active")  # active, completed, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    study = relationship("Study", back_populates="annotations")
    creator = relationship("User")
    rois = relationship("ROI", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AnnotationProject {self.name}>"


class ROI(Base):
    """Region of Interest annotation"""
    __tablename__ = "rois"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_id = Column(UUID(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("annotation_projects.id", ondelete="CASCADE"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    roi_name = Column(String(100))
    roi_type = Column(String(50))  # freehand, polygon, sphere, cube, threshold
    label_color = Column(String(20), default="#FF0000")
    mask_data = Column(LargeBinary)  # compressed binary mask data
    mask_format = Column(String(20), default="nrrd")
    volume_mm3 = Column(Float)  # volume in cubic mm
    centroid = Column(ARRAY(Float))  # center point coordinates [x, y, z]
    statistics = Column(JSON)  # basic statistics
    version = Column(Integer, default=1)
    is_latest = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    image = relationship("Image", back_populates="rois")
    project = relationship("AnnotationProject", back_populates="rois")
    creator = relationship("User", back_populates="rois")
    history = relationship("ROIHistory", back_populates="roi", cascade="all, delete-orphan")
    feature_results = relationship("FeatureResult", back_populates="roi")
    
    def __repr__(self):
        return f"<ROI {self.roi_name or self.id}>"


class ROIHistory(Base):
    """ROI change history"""
    __tablename__ = "roi_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roi_id = Column(UUID(as_uuid=True), ForeignKey("rois.id", ondelete="CASCADE"), nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    change_type = Column(String(20))  # create, update, delete
    previous_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    roi = relationship("ROI", back_populates="history")
    user = relationship("User")
    
    def __repr__(self):
        return f"<ROIHistory {self.change_type}>"