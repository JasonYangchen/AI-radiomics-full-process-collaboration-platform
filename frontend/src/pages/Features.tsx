import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { featuresApi, studiesApi } from '../services/api'
import { FiPlay, FiDownload, FiTrash2, FiRefreshCw } from 'react-icons/fi'
import toast from 'react-hot-toast'
import type { FeatureExtraction } from '../types'

export default function Features() {
  const queryClient = useQueryClient()
  const [page] = useState(1)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newExtraction, setNewExtraction] = useState({
    study_id: '',
  })

  // Fetch extractions
  const { data: extractionsData, isLoading } = useQuery({
    queryKey: ['features', 'extractions', page],
    queryFn: () => featuresApi.listExtractions({ page }),
  })

  // Fetch studies for dropdown
  const { data: studiesData } = useQuery({
    queryKey: ['studies', 'list'],
    queryFn: () => studiesApi.list({ page_size: 100 }),
  })

  // Create extraction mutation
  const createMutation = useMutation({
    mutationFn: () => featuresApi.createExtraction({
      study_id: newExtraction.study_id,
    }),
    onSuccess: () => {
      toast.success('特征提取任务已创建')
      setShowCreateModal(false)
      setNewExtraction({ study_id: '' })
      queryClient.invalidateQueries({ queryKey: ['features'] })
    },
    onError: () => {
      toast.error('创建失败')
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => featuresApi.deleteExtraction(id),
    onSuccess: () => {
      toast.success('删除成功')
      queryClient.invalidateQueries({ queryKey: ['features'] })
    },
  })

  // Export mutation
  const exportMutation = useMutation({
    mutationFn: (id: string) => featuresApi.exportResults(id, 'csv'),
    onSuccess: (response) => {
      // Open download URL
      window.open(response.data.download_url, '_blank')
      toast.success('导出成功')
    },
    onError: () => {
      toast.error('导出失败')
    },
  })

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-700',
      running: 'bg-blue-100 text-blue-700',
      completed: 'bg-green-100 text-green-700',
      failed: 'bg-red-100 text-red-700',
    }
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${styles[status] || styles.pending}`}>
        {status}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">特征提取</h1>
          <p className="text-gray-500 mt-1">使用 PyRadiomics 提取影像特征</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <FiPlay className="w-4 h-4" />
          新建提取任务
        </button>
      </div>

      {/* Extractions list */}
      <div className="card">
        {isLoading ? (
          <div className="text-center py-8 text-gray-500">加载中...</div>
        ) : extractionsData?.data.items.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FiPlay className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>暂无特征提取任务</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">任务ID</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">研究ID</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">状态</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">进度</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">创建时间</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">操作</th>
                </tr>
              </thead>
              <tbody>
                {extractionsData?.data.items.map((extraction: FeatureExtraction) => (
                  <tr key={extraction.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 font-mono text-sm">{extraction.id.slice(0, 8)}...</td>
                    <td className="py-3 px-4 font-mono text-sm">{extraction.study_id.slice(0, 8)}...</td>
                    <td className="py-3 px-4">{getStatusBadge(extraction.status)}</td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-primary-600 h-2 rounded-full"
                            style={{ width: `${extraction.progress}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-500">{extraction.progress}%</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-gray-500 text-sm">
                      {new Date(extraction.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-end gap-2">
                        {extraction.status === 'completed' && (
                          <button
                            onClick={() => exportMutation.mutate(extraction.id)}
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                            title="导出结果"
                          >
                            <FiDownload className="w-4 h-4 text-gray-600" />
                          </button>
                        )}
                        {extraction.status === 'pending' && (
                          <button
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                            title="刷新"
                          >
                            <FiRefreshCw className="w-4 h-4 text-gray-600" />
                          </button>
                        )}
                        <button
                          onClick={() => deleteMutation.mutate(extraction.id)}
                          className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                          title="删除"
                        >
                          <FiTrash2 className="w-4 h-4 text-red-500" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Feature classes info */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">PyRadiomics 特征类别</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[
            { name: '一阶统计', count: 19, color: 'bg-blue-100 text-blue-700' },
            { name: '形状特征', count: 17, color: 'bg-green-100 text-green-700' },
            { name: 'GLCM', count: 24, color: 'bg-purple-100 text-purple-700' },
            { name: 'GLRLM', count: 16, color: 'bg-orange-100 text-orange-700' },
            { name: 'GLSZM', count: 16, color: 'bg-pink-100 text-pink-700' },
            { name: 'NGTDM', count: 5, color: 'bg-cyan-100 text-cyan-700' },
          ].map((featureClass) => (
            <div key={featureClass.name} className="bg-gray-50 rounded-lg p-3 text-center">
              <div className={`inline-block px-2 py-1 rounded text-sm ${featureClass.color} mb-2`}>
                {featureClass.name}
              </div>
              <p className="text-sm text-gray-500">{featureClass.count} 个特征</p>
            </div>
          ))}
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">新建特征提取任务</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  选择研究
                </label>
                <select
                  value={newExtraction.study_id}
                  onChange={(e) => setNewExtraction({ ...newExtraction, study_id: e.target.value })}
                  className="input"
                >
                  <option value="">请选择...</option>
                  {studiesData?.data.items.map((study: any) => (
                    <option key={study.id} value={study.id}>
                      {study.patient_id || study.id} ({study.modality || '未知类型'})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="btn btn-secondary"
              >
                取消
              </button>
              <button
                onClick={() => createMutation.mutate()}
                disabled={!newExtraction.study_id || createMutation.isPending}
                className="btn btn-primary disabled:opacity-50"
              >
                {createMutation.isPending ? '创建中...' : '创建'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}