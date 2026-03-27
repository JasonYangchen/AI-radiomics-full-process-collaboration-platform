"""
AI+影像组学全流程协作平台
Backend Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import redis.asyncio as redis

from app.api.v1 import auth, users, studies, annotations, features, ml
from app.core.config import settings
from app.core.celery_app import celery_app
from app.db.session import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize Redis connection
    app.state.redis = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    
    yield
    
    # Shutdown
    await app.state.redis.close()


app = FastAPI(
    title="RadiomicsHub API",
    description="AI+影像组学全流程协作平台后端API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户管理"])
app.include_router(studies.router, prefix="/api/v1/studies", tags=["影像管理"])
app.include_router(annotations.router, prefix="/api/v1/annotations", tags=["标注管理"])
app.include_router(features.router, prefix="/api/v1/features", tags=["特征提取"])
app.include_router(ml.router, prefix="/api/v1/ml", tags=["机器学习"])


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "RadiomicsHub API", "docs": "/api/docs"}