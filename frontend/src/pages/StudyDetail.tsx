import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { studiesApi } from '../services/api'
import { FiArrowLeft, FiFolder, FiEdit } from 'react-icons/fi'
import type { Study } from '../types'

export default function StudyDetail() {
  const { id } = useParams<{ id: string }>()

  const { data, isLoading } = useQuery({
    queryKey: ['studies', id],
    queryFn: () => studiesApi.get(id!),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">加载中...</p>
      </div>
    )
  }

  if (!data?.data) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">研究不存在</p>
        <Link to="/studies" className="btn btn-primary mt-4">
          返回列表
        </Link>
      </div>
    )
  }

  const study = data.data as Study & { series: any[] }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/studies"
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <FiArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-800">
            {study.patient_id || '未命名研究'}
          </h1>
          <p className="text-gray-500 mt-1">
            {study.modality} | {study.study_description || '无描述'}
          </p>
        </div>
        <Link
          to={`/annotation/${study.id}`}
          className="btn btn-primary flex items-center gap-2"
        >
          <FiEdit className="w-4 h-4" />
          开始标注
        </Link>
      </div>

      {/* Study info */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">研究信息</h2>
            <dl className="grid grid-cols-2 gap-4">
              <div>
                <dt className="text-sm text-gray-500">患者ID</dt>
                <dd className="font-medium">{study.patient_id || '-'}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">影像类型</dt>
                <dd className="font-medium">{study.modality || '-'}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">检查日期</dt>
                <dd className="font-medium">{study.study_date || '-'}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">状态</dt>
                <dd className="font-medium">{study.status}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">研究UID</dt>
                <dd className="font-medium text-sm">{study.study_uid || '-'}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">创建时间</dt>
                <dd className="font-medium">
                  {new Date(study.created_at).toLocaleString()}
                </dd>
              </div>
            </dl>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">统计</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-500">序列数</span>
              <span className="font-medium">{study.series?.length || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-500">图像数</span>
              <span className="font-medium">
                {study.series?.reduce((acc, s) => acc + (s.images?.length || 0), 0) || 0}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Series list */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">序列列表</h2>
        
        {study.series?.length === 0 ? (
          <p className="text-gray-500 text-center py-4">暂无序列数据</p>
        ) : (
          <div className="space-y-4">
            {study.series?.map((series, index) => (
              <div key={series.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                      <FiFolder className="w-5 h-5 text-gray-400" />
                    </div>
                    <div>
                      <p className="font-medium">
                        {series.series_description || `序列 ${index + 1}`}
                      </p>
                      <p className="text-sm text-gray-500">
                        {series.images?.length || 0} 张图像
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-500">{series.modality}</p>
                    <p className="text-xs text-gray-400">{series.series_number}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}