"""
Create sample test data for the platform
"""
import asyncio
import sys
import os
import random
import numpy as np
from datetime import datetime, timedelta
from uuid import UUID

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.user import User
from app.models.study import Study, Series, Image
from app.models.annotation import AnnotationProject, ROI
from app.models.feature import FeatureExtraction, FeatureResult
from app.models.ml import Dataset, MLModel, ModelEvaluation, Prediction
from app.core.security import get_password_hash


async def create_test_data():
    """Create comprehensive test data"""
    async with async_session_maker() as session:
        print("Creating test data...")
        
        # Get admin user
        result = await session.execute(select(User).where(User.username == "admin"))
        admin = result.scalar_one_or_none()
        
        result = await session.execute(select(User).where(User.username == "doctor"))
        doctor = result.scalar_one_or_none()
        
        if not admin or not doctor:
            print("Please run init_db.py first")
            return
        
        # Create sample studies
        studies_data = []
        for i in range(5):
            study = Study(
                patient_id=f"P{1000 + i}",
                study_uid=f"1.2.840.113619.2.55.3.{i}",
                study_date=datetime.now() - timedelta(days=random.randint(1, 30)),
                study_description=f"CT Chest Abdomen {i+1}",
                modality=random.choice(["CT", "MR"]),
                uploaded_by=admin.id,
                status="ready"
            )
            session.add(study)
            studies_data.append(study)
        
        await session.flush()
        print(f"✓ Created {len(studies_data)} studies")
        
        # Create series and images for each study
        images_data = []
        for study in studies_data:
            for j in range(2):  # 2 series per study
                series = Series(
                    study_id=study.id,
                    series_uid=f"1.2.840.113619.2.55.3.{study.id}.{j}",
                    series_description=f"Series {j+1}",
                    series_number=j+1,
                    modality=study.modality
                )
                session.add(series)
                await session.flush()
                
                # Create images
                for k in range(3):  # 3 images per series
                    image = Image(
                        series_id=series.id,
                        file_path=f"studies/{study.id}/series/{series.id}/image_{k}.nrrd",
                        file_format="NRRD",
                        file_size=random.randint(1000000, 5000000),
                        dimensions=[512, 512, random.randint(50, 200)],
                        spacing=[0.5, 0.5, 1.0],
                        origin=[0.0, 0.0, 0.0],
                        metadata={"window_center": 40, "window_width": 400}
                    )
                    session.add(image)
                    images_data.append(image)
        
        await session.flush()
        print(f"✓ Created series and {len(images_data)} images")
        
        # Create annotation projects
        projects_data = []
        for study in studies_data[:3]:
            project = AnnotationProject(
                name=f"标注项目 - {study.patient_id}",
                description="示例标注项目",
                study_id=study.id,
                created_by=doctor.id,
                status="active"
            )
            session.add(project)
            projects_data.append(project)
        
        await session.flush()
        print(f"✓ Created {len(projects_data)} annotation projects")
        
        # Create ROIs
        rois_data = []
        for i, image in enumerate(images_data[:10]):
            roi = ROI(
                image_id=image.id,
                project_id=projects_data[i % len(projects_data)].id if projects_data else None,
                created_by=doctor.id,
                roi_name=f"ROI_{i+1}",
                roi_type=random.choice(["freehand", "polygon", "sphere"]),
                label_color=random.choice(["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]),
                mask_data=b"sample_mask_data",
                volume_mm3=random.uniform(1000, 50000),
                centroid=[random.uniform(-100, 100) for _ in range(3)],
                statistics={"mean": random.uniform(100, 200), "std": random.uniform(10, 30)}
            )
            session.add(roi)
            rois_data.append(roi)
        
        await session.flush()
        print(f"✓ Created {len(rois_data)} ROIs")
        
        # Create feature extractions
        extractions_data = []
        for study in studies_data[:3]:
            extraction = FeatureExtraction(
                study_id=study.id,
                created_by=admin.id,
                status="completed",
                progress=100,
                config={"binWidth": 25},
                completed_at=datetime.now()
            )
            session.add(extraction)
            extractions_data.append(extraction)
        
        await session.flush()
        print(f"✓ Created {len(extractions_data)} feature extractions")
        
        # Create feature results
        feature_classes = ["firstorder", "shape", "glcm", "glrlm"]
        feature_names = {
            "firstorder": ["Mean", "Median", "StandardDeviation", "Skewness", "Kurtosis"],
            "shape": ["Volume", "SurfaceArea", "Sphericity", "Compactness"],
            "glcm": ["Contrast", "Correlation", "Energy", "Entropy"],
            "glrlm": ["ShortRunEmphasis", "LongRunEmphasis", "GrayLevelNonUniformity"]
        }
        
        for extraction in extractions_data:
            for fclass in feature_classes:
                for fname in feature_names[fclass]:
                    result = FeatureResult(
                        extraction_id=extraction.id,
                        feature_class=fclass,
                        feature_name=fname,
                        feature_value=random.uniform(0, 100)
                    )
                    session.add(result)
        
        await session.flush()
        print("✓ Created feature results")
        
        # Create dataset
        dataset = Dataset(
            name="示例数据集",
            description="包含多个特征提取任务的数据集",
            created_by=admin.id,
            feature_extraction_ids=[str(e.id) for e in extractions_data],
            train_ratio=0.7,
            val_ratio=0.15,
            test_ratio=0.15
        )
        session.add(dataset)
        await session.flush()
        print("✓ Created dataset")
        
        # Create ML models
        models_data = []
        model_types = ["logistic_regression", "random_forest", "svm", "xgboost"]
        for mtype in model_types:
            model = MLModel(
                name=f"{mtype.replace('_', ' ').title()} Model",
                dataset_id=dataset.id,
                model_type=mtype,
                status="trained",
                created_by=admin.id,
                trained_at=datetime.now()
            )
            session.add(model)
            models_data.append(model)
        
        await session.flush()
        print(f"✓ Created {len(models_data)} ML models")
        
        # Create model evaluations
        for model in models_data:
            evaluation = ModelEvaluation(
                model_id=model.id,
                accuracy=random.uniform(0.75, 0.95),
                sensitivity=random.uniform(0.70, 0.90),
                specificity=random.uniform(0.75, 0.95),
                precision=random.uniform(0.72, 0.92),
                f1_score=random.uniform(0.74, 0.91),
                auc=random.uniform(0.80, 0.95),
                confusion_matrix=[[random.randint(40, 60), random.randint(5, 15)],
                                  [random.randint(5, 15), random.randint(40, 60)]],
                roc_data=[{"fpr": i/100, "tpr": min(1.0, i/100 + random.uniform(0.1, 0.3))} 
                          for i in range(0, 101, 5)],
                feature_importance={f"feature_{i}": random.uniform(0, 1) for i in range(20)}
            )
            session.add(model)
        
        await session.commit()
        print("\n✅ Test data creation complete!")
        print("\n📊 Summary:")
        print(f"  - Studies: {len(studies_data)}")
        print(f"  - Images: {len(images_data)}")
        print(f"  - Annotation Projects: {len(projects_data)}")
        print(f"  - ROIs: {len(rois_data)}")
        print(f"  - Feature Extractions: {len(extractions_data)}")
        print(f"  - ML Models: {len(models_data)}")


if __name__ == "__main__":
    asyncio.run(create_test_data())