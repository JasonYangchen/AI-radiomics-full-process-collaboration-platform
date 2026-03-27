# AI+影像组学全流程协作平台 - 技术架构文档

## 1. 系统架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐     │
│  │  影像查看器  │   标注工具   │  特征分析   │  模型管理   │     │
│  │  (VTK.js)   │  (Canvas 3D)│ (Charts.js) │ (ML Panel)  │     │
│  └─────────────┴─────────────┴─────────────┴─────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────────┐
│                     API Gateway (Nginx)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    Backend Services (FastAPI)                   │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐     │
│  │  Auth Svc   │  Image Svc  │  Label Svc   │  ML Svc     │     │
│  │  (JWT)      │  (DICOM)    │  (ROI)       │ (PyRadiomics)│   │
│  └─────────────┴─────────────┴─────────────┴─────────────┘     │
└─────────────────────────────────────────────────────────────────┘
        │                    │                    │
┌───────┴───────┐   ┌────────┴────────┐   ┌─────┴──────┐
│  PostgreSQL   │   │     MinIO       │   │   Redis    │
│   (元数据)    │   │  (影像存储)     │   │  (缓存/队列)│
└───────────────┘   └─────────────────┘   └────────────┘
```

## 2. 技术栈详解

### 2.1 前端技术栈
| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.x | UI框架 |
| TypeScript | 5.x | 类型安全 |
| Vite | 5.x | 构建工具 |
| TailwindCSS | 3.x | 样式框架 |
| Zustand | 4.x | 状态管理 |
| React Router | 6.x | 路由管理 |
| VTK.js | 28.x | 3D医学影像渲染 |
| ITK.js | 14.x | 影像处理 |
| Chart.js | 4.x | 数据可视化 |
| Axios | 1.x | HTTP客户端 |
| React Query | 5.x | 数据获取/缓存 |
| Socket.io-client | 4.x | 实时通信 |

### 2.2 后端技术栈
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.11 | 运行时环境 |
| FastAPI | 0.109.x | Web框架 |
| SQLAlchemy | 2.x | ORM |
| Alembic | 1.x | 数据库迁移 |
| Pydantic | 2.x | 数据验证 |
| PyJWT | 2.x | JWT认证 |
| PyRadiomics | 3.x | 影像特征提取 |
| SimpleITK | 2.x | 医学影像处理 |
| scikit-learn | 1.x | 机器学习 |
| XGBoost | 2.x | 梯度提升 |
| Celery | 5.x | 任务队列 |
| Redis | 7.x | 缓存/消息队列 |
| MinIO | Python SDK | 对象存储 |
| Uvicorn | 0.27.x | ASGI服务器 |

### 2.3 基础设施
| 服务 | 版本 | 用途 |
|------|------|------|
| PostgreSQL | 15.x | 主数据库 |
| Redis | 7.x | 缓存/任务队列 |
| MinIO | RELEASE.2024-x | 对象存储 |
| Nginx | 1.25.x | 反向代理 |
| Docker | 24.x | 容器化 |
| Docker Compose | 2.x | 容器编排 |

## 3. 数据模型设计

### 3.1 用户模块
```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'doctor', -- admin, doctor
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户会话表
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 影像模块
```sql
-- 影像研究表 (对应一个完整的影像检查)
CREATE TABLE studies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id VARCHAR(100),
    study_uid VARCHAR(255) UNIQUE, -- DICOM StudyInstanceUID
    study_date DATE,
    study_description TEXT,
    modality VARCHAR(20), -- CT, MR, X-ray
    uploaded_by UUID REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, ready, error
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 影像序列表
CREATE TABLE series (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    study_id UUID REFERENCES studies(id) ON DELETE CASCADE,
    series_uid VARCHAR(255), -- DICOM SeriesInstanceUID
    series_description TEXT,
    series_number INTEGER,
    modality VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 影像文件表
CREATE TABLE images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    series_id UUID REFERENCES series(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL, -- MinIO path
    file_format VARCHAR(20) NOT NULL, -- DICOM, NRRD, NIfTI
    file_size BIGINT,
    dimensions INTEGER[], -- [x, y, z] or [x, y]
    spacing FLOAT[], -- voxel spacing
    origin FLOAT[], -- image origin
    metadata JSONB, -- 完整元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.3 标注模块
```sql
-- 标注项目表
CREATE TABLE annotation_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    study_id UUID REFERENCES studies(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ROI标注表
CREATE TABLE rois (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_id UUID REFERENCES images(id) ON DELETE CASCADE,
    project_id UUID REFERENCES annotation_projects(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id),
    roi_name VARCHAR(100),
    roi_type VARCHAR(50), -- freehand, polygon, sphere, cube, threshold
    label_color VARCHAR(20),
    mask_data BYTEA, -- 压缩的二进制mask数据
    mask_format VARCHAR(20) DEFAULT 'nrrd',
    volume_mm3 FLOAT, -- 体积(立方毫米)
    centroid FLOAT[], -- 中心点坐标
    statistics JSONB, -- 基础统计信息
    version INTEGER DEFAULT 1,
    is_latest BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 标注历史表
CREATE TABLE roi_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    roi_id UUID REFERENCES rois(id) ON DELETE CASCADE,
    changed_by UUID REFERENCES users(id),
    change_type VARCHAR(20), -- create, update, delete
    previous_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.4 特征提取模块
```sql
-- 特征提取任务表
CREATE TABLE feature_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    study_id UUID REFERENCES studies(id) ON DELETE CASCADE,
    roi_id UUID REFERENCES rois(id) ON DELETE SET NULL,
    created_by UUID REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending', -- pending, running, completed, failed
    config JSONB, -- PyRadiomics配置
    progress INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 特征结果表
CREATE TABLE feature_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extraction_id UUID REFERENCES feature_extractions(id) ON DELETE CASCADE,
    image_id UUID REFERENCES images(id) ON DELETE CASCADE,
    roi_id UUID REFERENCES rois(id) ON DELETE SET NULL,
    feature_class VARCHAR(50), -- firstorder, shape, glcm, etc.
    feature_name VARCHAR(100),
    feature_value FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 特征导出表
CREATE TABLE feature_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extraction_id UUID REFERENCES feature_extractions(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id),
    file_path VARCHAR(500), -- MinIO path
    file_format VARCHAR(20), -- CSV, Excel
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.5 机器学习模块
```sql
-- 数据集表
CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id),
    feature_extraction_ids UUID[], -- 关联的特征提取任务
    train_ratio FLOAT DEFAULT 0.7,
    val_ratio FLOAT DEFAULT 0.15,
    test_ratio FLOAT DEFAULT 0.15,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 模型表
CREATE TABLE models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    model_type VARCHAR(50), -- logistic_regression, random_forest, svm, xgboost
    hyperparameters JSONB,
    feature_columns TEXT[],
    model_path VARCHAR(500), -- MinIO path
    scaler_path VARCHAR(500), -- 标准化器路径
    status VARCHAR(20) DEFAULT 'pending', -- pending, training, trained, error
    created_by UUID REFERENCES users(id),
    trained_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 模型评估结果表
CREATE TABLE model_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES models(id) ON DELETE CASCADE,
    accuracy FLOAT,
    sensitivity FLOAT,
    specificity FLOAT,
    precision FLOAT,
    f1_score FLOAT,
    auc FLOAT,
    confusion_matrix INTEGER[][],
    roc_data JSONB, -- [{fpr, tpr}, ...]
    calibration_data JSONB,
    feature_importance JSONB, -- {feature_name: importance}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 预测表
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES models(id) ON DELETE CASCADE,
    roi_id UUID REFERENCES rois(id) ON DELETE SET NULL,
    prediction_probability FLOAT,
    predicted_class INTEGER,
    actual_class INTEGER, -- 如果有标签
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 4. API 设计

### 4.1 认证接口 `/api/v1/auth`
| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | /register | 用户注册 | 公开 |
| POST | /login | 用户登录 | 公开 |
| POST | /logout | 用户登出 | 已登录 |
| GET | /me | 获取当前用户 | 已登录 |
| PUT | /me | 更新用户信息 | 已登录 |
| PUT | /me/password | 修改密码 | 已登录 |

### 4.2 用户管理接口 `/api/v1/users` (管理员)
| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | / | 用户列表 | admin |
| GET | /{id} | 用户详情 | admin |
| PUT | /{id} | 更新用户 | admin |
| DELETE | /{id} | 删除用户 | admin |
| PUT | /{id}/role | 修改角色 | admin |

### 4.3 影像接口 `/api/v1/studies`
| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | / | 研究列表 | 全部 |
| GET | /{id} | 研究详情 | 全部 |
| POST | / | 上传影像 | admin |
| PUT | /{id} | 更新研究 | admin |
| DELETE | /{id} | 删除研究 | admin |
| GET | /{id}/series | 序列列表 | 全部 |
| GET | /{id}/images | 影像列表 | 全部 |
| GET | /{id}/download | 下载研究 | 全部 |

### 4.4 标注接口 `/api/v1/annotations`
| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | /projects | 标注项目列表 | 全部 |
| POST | /projects | 创建项目 | 全部 |
| GET | /projects/{id} | 项目详情 | 全部 |
| DELETE | /projects/{id} | 删除项目 | 创建者 |
| GET | /rois | ROI列表 | 全部 |
| GET | /rois/{id} | ROI详情 | 全部 |
| POST | /rois | 创建ROI | 全部 |
| PUT | /rois/{id} | 更新ROI | 创建者 |
| DELETE | /rois/{id} | 删除ROI | 创建者 |
| GET | /rois/{id}/download | 下载ROI | 全部 |

### 4.5 特征提取接口 `/api/v1/features` (管理员)
| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | /extract | 创建提取任务 | admin |
| GET | /extractions | 任务列表 | admin |
| GET | /extractions/{id} | 任务详情 | admin |
| DELETE | /extractions/{id} | 删除任务 | admin |
| GET | /extractions/{id}/results | 查看结果 | admin |
| GET | /extractions/{id}/export | 导出结果 | admin |
| POST | /extractions/{id}/cancel | 取消任务 | admin |

### 4.6 建模接口 `/api/v1/ml`
| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | /datasets | 创建数据集 | admin |
| GET | /datasets | 数据集列表 | admin |
| GET | /datasets/{id} | 数据集详情 | admin |
| DELETE | /datasets/{id} | 删除数据集 | admin |
| POST | /models | 创建模型 | admin |
| GET | /models | 模型列表 | 全部 |
| GET | /models/{id} | 模型详情 | 全部 |
| POST | /models/{id}/train | 训练模型 | admin |
| GET | /models/{id}/evaluation | 评估结果 | 全部 |
| POST | /models/{id}/predict | 预测 | admin |
| GET | /models/{id}/download | 下载模型 | admin |

## 5. 项目目录结构

```
radiomics-platform/
├── docs/
│   ├── requirements.md          # 需求文档
│   └── architecture.md          # 架构文档
├── frontend/
│   ├── public/
│   │   └── favicon.ico
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/          # 通用组件
│   │   │   ├── layout/          # 布局组件
│   │   │   ├── viewer/          # 影像查看器
│   │   │   ├── annotation/      # 标注工具
│   │   │   ├── features/        # 特征提取
│   │   │   └── ml/              # 机器学习
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Studies.tsx
│   │   │   ├── Viewer.tsx
│   │   │   ├── Annotation.tsx
│   │   │   ├── Features.tsx
│   │   │   ├── Models.tsx
│   │   │   └── Users.tsx
│   │   ├── stores/              # Zustand状态管理
│   │   ├── hooks/               # 自定义Hooks
│   │   ├── utils/               # 工具函数
│   │   ├── types/               # TypeScript类型
│   │   ├── services/            # API服务
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── users.py
│   │   │   │   ├── studies.py
│   │   │   │   ├── annotations.py
│   │   │   │   ├── features.py
│   │   │   │   └── ml.py
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── celery_app.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── study.py
│   │   │   ├── annotation.py
│   │   │   ├── feature.py
│   │   │   └── ml.py
│   │   ├── schemas/
│   │   │   ├── user.py
│   │   │   ├── study.py
│   │   │   ├── annotation.py
│   │   │   ├── feature.py
│   │   │   └── ml.py
│   │   ├── services/
│   │   │   ├── image_processing.py
│   │   │   ├── radiomics_service.py
│   │   │   ├── ml_service.py
│   │   │   └── storage_service.py
│   │   ├── utils/
│   │   │   ├── dicom_utils.py
│   │   │   └── nrrd_utils.py
│   │   └── main.py
│   ├── tests/
│   │   ├── test_auth.py
│   │   ├── test_studies.py
│   │   └── test_features.py
│   ├── alembic/
│   │   └── versions/
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── .env.example
├── start.sh
└── README.md
```

## 6. 安全设计

### 6.1 认证与授权
- JWT Token 认证，过期时间 24 小时
- 密码使用 bcrypt 加密存储
- 基于角色的访问控制 (RBAC)
- API 请求限流

### 6.2 数据安全
- HTTPS 强制加密传输
- 敏感数据（密码）加密存储
- 数据库连接加密
- 定期备份机制

### 6.3 文件安全
- 上传文件类型白名单验证
- 文件大小限制
- 文件名随机化
- 隔离存储

## 7. 性能优化

### 7.1 前端优化
- 代码分割 (Code Splitting)
- 懒加载
- 虚拟滚动
- Web Worker 处理大文件

### 7.2 后端优化
- 数据库索引优化
- Redis 缓存热点数据
- Celery 异步处理耗时任务
- 分页查询

### 7.3 存储优化
- MinIO 分片存储
- 冷热数据分离
- 定期清理临时文件

## 8. 部署架构

```yaml
# Docker Compose 服务架构
services:
  frontend:      # React前端
  backend:       # FastAPI后端
  celery-worker: # Celery任务处理
  postgres:      # PostgreSQL数据库
  redis:         # Redis缓存/队列
  minio:         # MinIO对象存储
  nginx:         # Nginx反向代理
```

## 9. 监控与日志

- 应用日志：结构化JSON日志
- 访问日志：Nginx访问记录
- 错误追踪：异常堆栈记录
- 性能监控：API响应时间统计