# RadiomicsHub - AI+Radiomics Full-Process Collaboration Platform

<div align="center">

**AI+Radiomics Full-Process Collaboration Platform**

A multi-user collaborative platform for medical image annotation, feature extraction, and machine learning modeling

[Features](#features) • [Quick Start](#quick-start) • [Project Structure](#project-structure) • [API Documentation](#api-documentation)

</div>

---

## Features

### 🔐 User Permission Management
- Multi-user registration/login system
- Role differentiation: Administrator (Admin), Doctor
- JWT Token authentication
- Comprehensive permission control

### 📁 Image Management
- Supported formats: DICOM (.dcm), NRRD (.nrrd), NIfTI (.nii/.nii.gz)
- Batch upload functionality
- Automatic image metadata parsing
- Image preview (2D slices, 3D rendering)
- Image archiving and classification

### ✏️ Image Annotation
- 3D Slicer-like annotation experience
- Support for multiple annotation tools:
  - Freehand brush
  - Polygon lasso
  - Sphere/Cube
  - Threshold segmentation
- Auto-save ROI
- Annotation version history management
- Multi-doctor collaborative annotation

### 📊 Feature Extraction
- Integrated PyRadiomics library
- Supported feature categories:
  - First-order statistics (19 features)
  - Shape features (17 features)
  - Texture features (GLCM, GLRLM, GLSZM, NGTDM)
- Configurable feature parameters
- Batch feature extraction
- Feature result export (CSV/Excel)

### 🤖 Machine Learning Modeling
- Multiple model support:
  - Logistic Regression
  - Random Forest
  - Support Vector Machine
  - XGBoost
- Dataset splitting and cross-validation
- Model performance evaluation:
  - Accuracy, Sensitivity, Specificity
  - ROC curve, AUC value
  - Confusion matrix
  - Feature importance ranking
- Model download and deployment

### 📈 Visualization Reports
- Model performance visualization charts
- Feature importance ranking
- Prediction result display

---

## Tech Stack

### Backend
- **Python 3.11** - Programming language
- **FastAPI** - Modern high-performance web framework
- **SQLAlchemy 2.0** - Python SQL toolkit and ORM
- **PostgreSQL 15** - Relational database
- **Redis 7** - Cache and message queue
- **Celery** - Distributed task queue
- **MinIO** - S3-compatible object storage
- **PyRadiomics** - Image feature extraction library
- **SimpleITK** - Medical image processing
- **scikit-learn** - Machine learning library
- **XGBoost** - Gradient boosting framework

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling framework
- **Zustand** - State management
- **React Query** - Data fetching
- **Chart.js** - Data visualization

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Container orchestration
- **Nginx** - Reverse proxy

---

## Quick Start

### Prerequisites

- Docker 24.0+
- Docker Compose 2.0+
- 8GB+ available memory
- 20GB+ disk space

### One-Click Launch

**Windows (PowerShell):**

```powershell
# Clone the project
git clone https://github.com/your-username/radiomics-platform.git
cd radiomics-platform

# Start services
docker-compose up -d --build
```

**Linux/macOS:**

```bash
# Clone the project
git clone https://github.com/your-username/radiomics-platform.git
cd radiomics-platform

# Start services
docker-compose up -d --build
```

### Access URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost | React Web Application |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **MinIO Console** | http://localhost:9001 | Object Storage Management |

### Default Accounts

| Role | Username | Password |
|------|----------|----------|
| Administrator | admin | admin123 |
| Doctor | doctor | doctor123 |

---

## Project Structure

```
radiomics-platform/
├── docs/                      # Documentation
│   ├── requirements.md        # Requirements document
│   └── architecture.md        # Architecture document
├── frontend/                  # Frontend project
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Pages
│   │   ├── stores/            # State management
│   │   ├── services/          # API services
│   │   └── types/             # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── backend/                   # Backend project
│   ├── app/
│   │   ├── api/v1/            # API routes
│   │   ├── core/              # Core configuration
│   │   ├── models/            # Data models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   └── db/                # Database configuration
│   ├── scripts/               # Scripts
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml         # Docker orchestration
└── README.md                  # Project documentation
```

---

## User Guide

### 1. Upload Images (Administrator)

1. Log in with administrator account
2. Navigate to "Image Management" page
3. Click "Upload Image" button
4. Select DICOM/NRRD/NIfTI files
5. Wait for system processing to complete

### 2. Annotate ROI (Doctor)

1. Navigate to "Image Management" page
2. Click the annotation button in the image list
3. Use annotation tools to delineate regions of interest
4. Annotation results are saved automatically

### 3. Feature Extraction (Administrator)

1. Navigate to "Feature Extraction" page
2. Click "New Extraction Task"
3. Select the study for feature extraction
4. Configure feature parameters
5. Wait for extraction to complete
6. Export feature results

### 4. Model Training (Administrator)

1. Navigate to "Model Management" page
2. Create a dataset
3. Create a model and select an algorithm
4. Start training
5. View evaluation report

---

## API Documentation

After starting the service, visit http://localhost:8000/docs for complete API documentation.

### Main Endpoints

| Path | Method | Description |
|------|--------|-------------|
| `/api/v1/auth/login` | POST | User login |
| `/api/v1/auth/register` | POST | User registration |
| `/api/v1/users/` | GET | User list |
| `/api/v1/studies/` | GET/POST | Study management |
| `/api/v1/studies/upload` | POST | Image upload |
| `/api/v1/annotations/rois` | GET/POST | Annotation management |
| `/api/v1/features/extract` | POST | Feature extraction |
| `/api/v1/ml/models` | GET/POST | Model management |

---

## Development Guide

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Start development server
uvicorn app.main:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

---

## Environment Variables

Default values are configured in `docker-compose.yml`. For production environments, please modify:

```yaml
# Security configuration
SECRET_KEY: your-secret-key-change-in-production

# Database password
POSTGRES_PASSWORD: your-db-password

# MinIO credentials
MINIO_ROOT_USER: your-minio-user
MINIO_ROOT_PASSWORD: your-minio-password
```

---

## FAQ

### 1. Port Already in Use

Modify the port mapping in `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "8080:80"  # Change to port 8080
```

### 2. Slow Docker Build

In mainland China, you can use mirror accelerators or modify Dockerfile to use domestic mirror sources.

### 3. Insufficient Memory

Increase Docker available memory:
- Windows: Docker Desktop → Settings → Resources → Memory
- Linux: No limit by default

### 4. Database Connection Failed

Wait for PostgreSQL to fully start, typically takes 10-30 seconds. Check logs:

```bash
docker-compose logs postgres
```

### 5. Reinitialize Database

```bash
docker-compose down -v  # Remove volumes
docker-compose up -d --build
```

---

## License

MIT License

---

## Contributing

Issues and Pull Requests are welcome!

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Create a Pull Request

---

<div align="center">

**⭐ If this project helps you, please give it a Star ⭐**

</div>