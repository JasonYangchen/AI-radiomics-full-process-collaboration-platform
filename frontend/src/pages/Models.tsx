import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { mlApi } from '../services/api'
import { useAuthStore } from '../stores'
import { FiCpu, FiPlus, FiPlay, FiBarChart2 } from 'react-icons/fi'
import type { MLModel } from '../types'

export default function Models() {
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'admin'
  const [page] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['models', 'list', page],
    queryFn: () => mlApi.listModels({ page }),
  })

  const getModelTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      logistic_regression: '逻辑回归',
      random_forest: '随机森林',
      svm: '支持向量机',
      xgboost: 'XGBoost',
    }
    return labels[type] || type
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-700',
      training: 'bg-blue-100 text-blue-700',
      trained: 'bg-green-100 text-green-700',
      error: 'bg-red-100 text-red-700',
    }
    const labels: Record<string, string> = {
      pending: '待训练',
      training: '训练中',
      trained: '已训练',
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
          <h1 className="text-2xl font-bold text-gray-800">模型管理</h1>
          <p className="text-gray-500 mt-1">机器学习模型训练与评估</p>
        </div>
        {isAdmin && (
          <button
            className="btn btn-primary flex items-center gap-2"
          >
            <FiPlus className="w-4 h-4" />
            创建模型
          </button>
        )}
      </div>

      {/* Model types */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { type: 'logistic_regression', name: '逻辑回归', icon: '📈', desc: '线性分类模型' },
          { type: 'random_forest', name: '随机森林', icon: '🌲', desc: '集成学习方法' },
          { type: 'svm', name: '支持向量机', icon: '🎯', desc: '核方法分类' },
          { type: 'xgboost', name: 'XGBoost', icon: '🚀', desc: '梯度提升算法' },
        ].map((model) => (
          <div key={model.type} className="card hover:shadow-lg transition-shadow cursor-pointer">
            <div className="text-3xl mb-2">{model.icon}</div>
            <h3 className="font-semibold text-gray-800">{model.name}</h3>
            <p className="text-sm text-gray-500 mt-1">{model.desc}</p>
          </div>
        ))}
      </div>

      {/* Models list */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">模型列表</h2>
        
        {isLoading ? (
          <div className="text-center py-8 text-gray-500">加载中...</div>
        ) : data?.data.items.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FiCpu className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>暂无模型</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">模型名称</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">类型</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">状态</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">AUC</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">创建时间</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">操作</th>
                </tr>
              </thead>
              <tbody>
                {data?.data.items.map((model: MLModel) => (
                  <tr key={model.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 font-medium">{model.name}</td>
                    <td className="py-3 px-4">{getModelTypeLabel(model.model_type)}</td>
                    <td className="py-3 px-4">{getStatusBadge(model.status)}</td>
                    <td className="py-3 px-4">
                      {model.status === 'trained' ? '0.85' : '-'}
                    </td>
                    <td className="py-3 px-4 text-gray-500 text-sm">
                      {new Date(model.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          to={`/models/${model.id}`}
                          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                          title="查看详情"
                        >
                          <FiBarChart2 className="w-4 h-4 text-gray-600" />
                        </Link>
                        {isAdmin && model.status === 'pending' && (
                          <button
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                            title="开始训练"
                          >
                            <FiPlay className="w-4 h-4 text-primary-600" />
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
      </div>
    </div>
  )
}