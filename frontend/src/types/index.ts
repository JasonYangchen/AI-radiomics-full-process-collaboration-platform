// API Types
export interface User {
  id: string
  username: string
  email: string
  full_name: string | null
  role: 'admin' | 'doctor'
  is_active: boolean
  created_at: string
}

export interface Study {
  id: string
  patient_id: string | null
  study_uid: string | null
  study_date: string | null
  study_description: string | null
  modality: string | null
  uploaded_by: string | null
  status: 'pending' | 'processing' | 'ready' | 'error'
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface Series {
  id: string
  study_id: string
  series_uid: string | null
  series_description: string | null
  series_number: number | null
  modality: string | null
  created_at: string
}

export interface Image {
  id: string
  series_id: string
  file_path: string
  file_format: string
  file_size: number | null
  dimensions: number[] | null
  spacing: number[] | null
  origin: number[] | null
  metadata: Record<string, unknown> | null
  created_at: string
}

export interface AnnotationProject {
  id: string
  name: string
  description: string | null
  study_id: string
  created_by: string | null
  status: string
  created_at: string
}

export interface ROI {
  id: string
  image_id: string
  project_id: string | null
  created_by: string | null
  roi_name: string | null
  roi_type: string
  label_color: string
  volume_mm3: number | null
  centroid: number[] | null
  statistics: Record<string, unknown> | null
  version: number
  is_latest: boolean
  created_at: string
  updated_at: string
}

export interface FeatureExtraction {
  id: string
  study_id: string
  roi_id: string | null
  created_by: string | null
  status: 'pending' | 'running' | 'completed' | 'failed'
  config: Record<string, unknown> | null
  progress: number
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface FeatureResult {
  id: string
  extraction_id: string
  image_id: string | null
  roi_id: string | null
  feature_class: string
  feature_name: string
  feature_value: number
}

export interface Dataset {
  id: string
  name: string
  description: string | null
  created_by: string | null
  feature_extraction_ids: string[] | null
  train_ratio: number
  val_ratio: number
  test_ratio: number
  created_at: string
}

export interface MLModel {
  id: string
  name: string
  dataset_id: string
  model_type: string
  hyperparameters: Record<string, unknown> | null
  feature_columns: string[] | null
  status: 'pending' | 'training' | 'trained' | 'error'
  error_message: string | null
  created_by: string | null
  trained_at: string | null
  created_at: string
}

export interface ModelEvaluation {
  id: string
  model_id: string
  accuracy: number | null
  sensitivity: number | null
  specificity: number | null
  precision: number | null
  f1_score: number | null
  auc: number | null
  confusion_matrix: number[][] | null
  roc_data: Array<{ fpr: number; tpr: number }> | null
  calibration_data: Record<string, unknown> | null
  feature_importance: Record<string, number> | null
  created_at: string
}

export interface Prediction {
  id: string
  model_id: string
  roi_id: string
  prediction_probability: number
  predicted_class: number
  actual_class: number | null
  created_at: string
}

// Paginated response
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// API Response types
export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface UploadProgress {
  study_id: string
  status: string
  progress: number
  message: string
}