import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { studiesApi } from '../services/api'
import { useAuthStore } from '../stores'
import { FiUpload, FiFolder, FiTrash2, FiEye, FiSearch } from 'react-icons/fi'
import toast from 'react-hot-toast'
import type { Study } from '../types'

export default function Studies() {
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'admin'
  
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState({
    modality: '',
    status: '',
    patient_id: '',
  })
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [uploadFile, setUploadFile] = useState<File | null>(null)

  // Fetch studies
  const { data, isLoading } = useQuery({
    queryKey: ['studies', 'list', page, filters],
    queryFn: () => studiesApi.list({ page, ...filters }),
  })

  // Delete study mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => studiesApi.delete(id),
    onSuccess: () => {
      toast.success('删除成功')
      queryClient.invalidateQueries({ queryKey: ['studies'] })
    },
    onError: () => {
      toast.error('删除失败')
    },
  })

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => studiesApi.upload(file),
    onSuccess: () => {
      toast.success('上传成功，正在处理...')
      setShowUploadModal(false)
      setUploadFile(null)
      queryClient.invalidateQueries({ queryKey: ['studies'] })
    },
    onError: () => {
      toast.error('上传失败')
    },
  })

  const handleDelete = (study: Study) => {
    if (confirm(`确定要删除研究 "${study.patient_id || study.id}" 吗？`)) {
      deleteMutation.mutate(study.id)
    }
  }

  const handleUpload = () => {
    if (uploadFile) {
      uploadMutation.mutate(uploadFile)
    }
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-700',
      processing: 'bg-blue-100 text-blue-700',
      ready: 'bg-green-100 text-green-700',
      error: 'bg-red-100 text-red-700',
    }
    const labels: Record<string, string> = {
      pending: '待处理',
      processing: '处理中',
      ready: '就绪',
      error: '错误',
    }
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${styles[status] || styles.pending}`}>
        {labels[status] || status}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">影像管理</h1>
          <p className="text-gray-500 mt-1">管理和上传医学影像数据</p>
        </div>
        {isAdmin && (
          <button
            onClick={() => setShowUploadModal(true)}
            className="btn btn-primary flex items-center gap-2"
          >
            <FiUpload className="w-4 h-4" />
            上传影像
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">患者ID</label>
            <div className="relative">
              <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={filters.patient_id}
                onChange={(e) => setFilters({ ...filters, patient_id: e.target.value })}
                className="input pl-10"
                placeholder="搜索患者ID"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">影像类型</label>
            <select
              value={filters.modality}
              onChange={(e) => setFilters({ ...filters, modality: e.target.value })}
              className="input"
            >
              <option value="">全部</option>
              <option value="CT">CT</option>
              <option value="MR">MR</option>
              <option value="X-ray">X-ray</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">状态</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="input"
            >
              <option value="">全部</option>
              <option value="pending">待处理</option>
              <option value="processing">处理中</option>
              <option value="ready">就绪</option>
              <option value="error">错误</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => setFilters({ modality: '', status: '', patient_id: '' })}
              className="btn btn-secondary w-full"
            >
              重置筛选
            </button>
          </div>
        </div>
      </div>

      {/* Studies list */}
      <div className="card">
        {isLoading ? (
          <div className="text-center py-8 text-gray-500">加载中...</div>
        ) : data?.data.items.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FiFolder className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>暂无影像数据</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">患者ID</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">影像类型</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">检查日期</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">状态</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">创建时间</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">操作</th>
                </tr>
              </thead>
              <tbody>
                {data?.data.items.map((study: Study) => (
                  <tr key={study.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 font-medium">{study.patient_id || '-'}</td>
                    <td className="py-3 px-4">{study.modality || '-'}</td>
                    <td className="py-3 px-4">{study.study_date || '-'}</td>
                    <td className="py-3 px-4">{getStatusBadge(study.status)}</td>
                    <td className="py-3 px-4 text-gray-500 text-sm">
                      {new Date(study.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          to={`/studies/${study.id}`}
                          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                          title="查看详情"
                        >
                          <FiEye className="w-4 h-4 text-gray-600" />
                        </Link>
                        <Link
                          to={`/annotation/${study.id}`}
                          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                          title="标注"
                        >
                          <FiFolder className="w-4 h-4 text-primary-600" />
                        </Link>
                        {isAdmin && (
                          <button
                            onClick={() => handleDelete(study)}
                            className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                            title="删除"
                          >
                            <FiTrash2 className="w-4 h-4 text-red-500" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {data && data.data.total > 10 && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-500">
              共 {data.data.total} 条记录
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
                className="btn btn-secondary disabled:opacity-50"
              >
                上一页
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page * 10 >= data.data.total}
                className="btn btn-secondary disabled:opacity-50"
              >
                下一页
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">上传影像</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  选择文件
                </label>
                <input
                  type="file"
                  accept=".dcm,.nrrd,.nii,.nii.gz,.zip"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="input"
                />
                <p className="text-xs text-gray-500 mt-1">
                  支持格式: DICOM (.dcm), NRRD (.nrrd), NIfTI (.nii, .nii.gz), ZIP
                </p>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowUploadModal(false)}
                className="btn btn-secondary"
              >
                取消
              </button>
              <button
                onClick={handleUpload}
                disabled={!uploadFile || uploadMutation.isPending}
                className="btn btn-primary disabled:opacity-50"
              >
                {uploadMutation.isPending ? '上传中...' : '上传'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}