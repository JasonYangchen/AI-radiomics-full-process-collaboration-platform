import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// ==================== Auth API ====================
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  
  register: (data: { username: string; email: string; password: string; full_name?: string; role?: string }) =>
    api.post('/auth/register', data),
  
  getMe: () => api.get('/auth/me'),
  
  updateMe: (data: Partial<{ email: string; full_name: string; password: string }>) =>
    api.put('/auth/me', data),
  
  logout: () => api.post('/auth/logout'),
}

// ==================== Users API ====================
export const usersApi = {
  list: (params?: { page?: number; page_size?: number; role?: string }) =>
    api.get('/users/', { params }),
  
  get: (id: string) => api.get(`/users/${id}`),
  
  update: (id: string, data: Partial<{ email: string; full_name: string; password: string }>) =>
    api.put(`/users/${id}`, data),
  
  delete: (id: string) => api.delete(`/users/${id}`),
  
  updateRole: (id: string, role: string) =>
    api.put(`/users/${id}/role`, null, { params: { role } }),
  
  toggleActive: (id: string, is_active: boolean) =>
    api.put(`/users/${id}/activate`, null, { params: { is_active } }),
}

// ==================== Studies API ====================
export const studiesApi = {
  list: (params?: { page?: number; page_size?: number; modality?: string; status?: string; patient_id?: string }) =>
    api.get('/studies/', { params }),
  
  get: (id: string) => api.get(`/studies/${id}`),
  
  create: (data: { patient_id?: string; study_description?: string }) =>
    api.post('/studies/', data),
  
  update: (id: string, data: Partial<{ patient_id: string; study_description: string }>) =>
    api.put(`/studies/${id}`, data),
  
  delete: (id: string) => api.delete(`/studies/${id}`),
  
  upload: (file: File, patientId?: string, studyDescription?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    if (patientId) formData.append('patient_id', patientId)
    if (studyDescription) formData.append('study_description', studyDescription)
    return api.post('/studies/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  
  getSeries: (studyId: string) => api.get(`/studies/${studyId}/series`),
  getImages: (studyId: string) => api.get(`/studies/${studyId}/images`),
  download: (studyId: string) => api.get(`/studies/${studyId}/download`),
}

// ==================== Annotations API ====================
export const annotationsApi = {
  listProjects: (params?: { study_id?: string; status?: string }) =>
    api.get('/annotations/projects', { params }),
  
  createProject: (data: { name: string; description?: string; study_id: string }) =>
    api.post('/annotations/projects', data),
  
  getProject: (id: string) => api.get(`/annotations/projects/${id}`),
  
  deleteProject: (id: string) => api.delete(`/annotations/projects/${id}`),
  
  listRois: (params?: { page?: number; page_size?: number; image_id?: string; project_id?: string }) =>
    api.get('/annotations/rois', { params }),
  
  getRoi: (id: string) => api.get(`/annotations/rois/${id}`),
  
  createRoi: (data: { image_id: string; project_id?: string; roi_name?: string; roi_type: string; label_color?: string; mask_data: string }) =>
    api.post('/annotations/rois', data),
  
  updateRoi: (id: string, data: Partial<{ roi_name: string; label_color: string; mask_data: string }>) =>
    api.put(`/annotations/rois/${id}`, data),
  
  deleteRoi: (id: string) => api.delete(`/annotations/rois/${id}`),
  
  downloadRoi: (id: string) => api.get(`/annotations/rois/${id}/download`),
  
  getRoiHistory: (id: string) => api.get(`/annotations/rois/${id}/history`),
}

// ==================== Features API ====================
export const featuresApi = {
  createExtraction: (data: { study_id: string; roi_id?: string; config?: Record<string, unknown>; feature_classes?: string[] }) =>
    api.post('/features/extract', data),
  
  listExtractions: (params?: { page?: number; page_size?: number; study_id?: string; status?: string }) =>
    api.get('/features/extractions', { params }),
  
  getExtraction: (id: string) => api.get(`/features/extractions/${id}`),
  
  deleteExtraction: (id: string) => api.delete(`/features/extractions/${id}`),
  
  cancelExtraction: (id: string) => api.post(`/features/extractions/${id}/cancel`),
  
  getExtractionResults: (extractionId: string, featureClass?: string) =>
    api.get(`/features/extractions/${extractionId}/results`, { params: { feature_class: featureClass } }),
  
  exportResults: (extractionId: string, format: 'csv' | 'excel' = 'csv') =>
    api.get(`/features/extractions/${extractionId}/export`, { params: { format } }),
}

// ==================== ML API ====================
export const mlApi = {
  createDataset: (data: { name: string; description?: string; feature_extraction_ids: string[]; train_ratio?: number; val_ratio?: number; test_ratio?: number }) =>
    api.post('/ml/datasets', data),
  
  listDatasets: () => api.get('/ml/datasets'),
  
  getDataset: (id: string) => api.get(`/ml/datasets/${id}`),
  
  getDatasetStats: (id: string) => api.get(`/ml/datasets/${id}/stats`),
  
  deleteDataset: (id: string) => api.delete(`/ml/datasets/${id}`),
  
  createModel: (data: { name: string; dataset_id: string; model_type: string; hyperparameters?: Record<string, unknown>; feature_columns?: string[] }) =>
    api.post('/ml/models', data),
  
  listModels: (params?: { page?: number; page_size?: number }) =>
    api.get('/ml/models', { params }),
  
  getModel: (id: string) => api.get(`/ml/models/${id}`),
  
  trainModel: (id: string, data?: { hyperparameters?: Record<string, unknown>; feature_columns?: string[] }) =>
    api.post(`/ml/models/${id}/train`, data || {}),
  
  getModelEvaluation: (id: string) => api.get(`/ml/models/${id}/evaluation`),
  
  predict: (modelId: string, roiId: string) =>
    api.post(`/ml/models/${modelId}/predict`, { roi_id: roiId }),
  
  downloadModel: (id: string) => api.get(`/ml/models/${id}/download`),
}