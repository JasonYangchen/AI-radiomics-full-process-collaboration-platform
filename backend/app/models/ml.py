"""
Machine learning models
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Integer, Float, ARRAY, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.session import Base


class Dataset(Base):
    """Dataset for model training"""
    __tablename__ = "datasets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    feature_extraction_ids = Column(ARRAY(UUID))  # linked extraction tasks
    train_ratio = Column(Float, default=0.7)
    val_ratio = Column(Float, default=0.15)
    test_ratio = Column(Float, default=0.15)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = relationship("User")
    models = relationship("MLModel", back_populates="dataset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Dataset {self.name}>"


class MLModel(Base):
    """Machine learning model"""
    __tablename__ = "models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"))
    model_type = Column(String(50))  # logistic_regression, random_forest, svm, xgboost
    hyperparameters = Column(JSON)
    feature_columns = Column(ARRAY(Text))
    model_path = Column(String(500))  # MinIO path
    scaler_path = Column(String(500))  # scaler file path
    status = Column(String(20), default="pending")  # pending, training, trained, error
    error_message = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    trained_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    dataset = relationship("Dataset", back_populates="models")
    creator = relationship("User")
    evaluations = relationship("ModelEvaluation", back_populates="model", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="model", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MLModel {self.name}>"


class ModelEvaluation(Base):
    """Model evaluation results"""
    __tablename__ = "model_evaluations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    accuracy = Column(Float)
    sensitivity = Column(Float)
    specificity = Column(Float)
    precision = Column(Float)
    f1_score = Column(Float)
    auc = Column(Float)
    confusion_matrix = Column(JSON)  # [[tn, fp], [fn, tp]]
    roc_data = Column(JSON)  # [{fpr, tpr}, ...]
    calibration_data = Column(JSON)
    feature_importance = Column(JSON)  # {feature_name: importance}
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    model = relationship("MLModel", back_populates="evaluations")
    
    def __repr__(self):
        return f"<ModelEvaluation for {self.model_id}>"


class Prediction(Base):
    """Prediction record"""
    __tablename__ = "predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    roi_id = Column(UUID(as_uuid=True), ForeignKey("rois.id", ondelete="SET NULL"))
    prediction_probability = Column(Float)
    predicted_class = Column(Integer)
    actual_class = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    model = relationship("MLModel", back_populates="predictions")
    roi = relationship("ROI")
    
    def __repr__(self):
        return f"<Prediction {self.id}>"