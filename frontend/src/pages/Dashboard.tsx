import { useQuery } from '@tanstack/react-query'
import { studiesApi, featuresApi, mlApi } from '../services/api'
import { useAuthStore } from '../stores'
import { FiFolder, FiBarChart2, FiCpu } from 'react-icons/fi'

export default function Dashboard() {
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'admin'

  // Fetch statistics
  const { data: studiesData } = useQuery({
    queryKey: ['studies', 'list'],
    queryFn: () => studiesApi.list({ page_size: 1 }),
  })

  const { data: extractionsData } = useQuery({
    queryKey: ['features', 'extractions'],
    queryFn: () => featuresApi.listExtractions({ page_size: 1 }),
    enabled: isAdmin,
  })

  const { data: modelsData } = useQuery({
    queryKey: ['models', 'list'],
    queryFn: () => mlApi.listModels({ page_size: 1 }),
  })

  const stats = [
    {
      label: '影像研究',
      value: studiesData?.data.total || 0,
      icon: FiFolder,
      color: 'bg-blue-500',
    },
    {
      label: '特征提取任务',
      value: extractionsData?.data.total || 0,
      icon: FiBarChart2,
      color: 'bg-green-500',
      adminOnly: true,
    },
    {
      label: '训练模型',
      value: modelsData?.data.total || 0,
      icon: FiCpu,
      color: 'bg-purple-500',
    },
  ]

  const filteredStats = stats.filter((s) => !s.adminOnly || isAdmin)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-800">仪表盘</h1>
        <p className="text-gray-500 mt-1">欢迎回来，{user?.full_name || user?.username}</p>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredStats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <div key={index} className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">{stat.label}</p>
                  <p className="text-3xl font-bold text-gray-800 mt-1">{stat.value}</p>
                </div>
                <div className={`w-12 h-12 ${stat.color} rounded-lg flex items-center justify-center`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent studies */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">最近影像研究</h2>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                    <FiFolder className="w-5 h-5 text-gray-400" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-700">研究 #{i}</p>
                    <p className="text-sm text-gray-500">2024-01-{10 + i}</p>
                  </div>
                </div>
                <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                  已完成
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent models */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">最近训练模型</h2>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                    <FiCpu className="w-5 h-5 text-gray-400" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-700">模型 #{i}</p>
                    <p className="text-sm text-gray-500">Random Forest</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-700">AUC: 0.8{i}</p>
                  <p className="text-xs text-gray-500">准确率: 85%</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* System info */}
      {isAdmin && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">系统信息</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500">数据库状态</p>
              <p className="font-medium text-green-600">正常</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500">存储使用</p>
              <p className="font-medium text-gray-700">2.5 GB / 100 GB</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500">任务队列</p>
              <p className="font-medium text-gray-700">3 运行中</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500">在线用户</p>
              <p className="font-medium text-gray-700">5 人</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}