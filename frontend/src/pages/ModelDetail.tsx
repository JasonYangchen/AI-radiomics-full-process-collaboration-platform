import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { mlApi } from '../services/api'
import { FiArrowLeft, FiDownload, FiPlay } from 'react-icons/fi'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  BarElement,
} from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
)

interface RocPoint {
  fpr: number
  tpr: number
}

interface Evaluation {
  id: string
  model_id: string
  accuracy: number | null
  sensitivity: number | null
  specificity: number | null
  precision: number | null
  f1_score: number | null
  auc: number | null
  confusion_matrix: number[][] | null
  roc_data: RocPoint[] | null
  feature_importance: Record<string, number> | null
  created_at: string
}

interface Model {
  id: string
  name: string
  dataset_id: string
  model_type: string
  hyperparameters: Record<string, unknown> | null
  feature_columns: string[] | null
  status: string
  error_message: string | null
  created_by: string | null
  trained_at: string | null
  created_at: string
}

export default function ModelDetail() {
  const { id } = useParams<{ id: string }>()

  const { data: modelData, isLoading: modelLoading } = useQuery({
    queryKey: ['models', id],
    queryFn: () => mlApi.getModel(id!),
    enabled: !!id,
  })

  const { data: evalData } = useQuery({
    queryKey: ['models', id, 'evaluation'],
    queryFn: () => mlApi.getModelEvaluation(id!),
    enabled: !!id && modelData?.data.status === 'trained',
  })

  if (modelLoading) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">加载中...</p>
      </div>
    )
  }

  const model: Model = modelData?.data

  if (!model) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">模型不存在</p>
        <Link to="/models" className="btn btn-primary mt-4 inline-block">
          返回列表
        </Link>
      </div>
    )
  }

  const evaluation: Evaluation | undefined = evalData?.data
  const rocData: RocPoint[] = evaluation?.roc_data || []
  const importanceData: Record<string, number> = evaluation?.feature_importance || {}
  
  const topFeatures = Object.entries(importanceData)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)

  const lineData = {
    labels: rocData.map((p: RocPoint) => p.fpr.toFixed(2)),
    datasets: [
      {
        label: 'ROC曲线',
        data: rocData.map((p: RocPoint) => p.tpr),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
      },
    ],
  }

  const barData = {
    labels: topFeatures.map((f) => f[0]),
    datasets: [
      {
        label: '特征重要性',
        data: topFeatures.map((f) => f[1]),
        backgroundColor: 'rgba(59, 130, 246, 0.7)',
      },
    ],
  }

  const getModelTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      logistic_regression: '逻辑回归',
      random_forest: '随机森林',
      svm: '支持向量机',
      xgboost: 'XGBoost',
    }
    return labels[type] || type
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/models"
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <FiArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-800">{model.name}</h1>
          <p className="text-gray-500 mt-1">
            {getModelTypeLabel(model.model_type)} | 状态: {model.status}
          </p>
        </div>
        {model.status === 'trained' && (
          <button className="btn btn-primary flex items-center gap-2">
            <FiDownload className="w-4 h-4" />
            下载模型
          </button>
        )}
      </div>

      {/* Metrics */}
      {evaluation && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {[
            { label: '准确率', value: evaluation.accuracy },
            { label: '敏感度', value: evaluation.sensitivity },
            { label: '特异度', value: evaluation.specificity },
            { label: '精确率', value: evaluation.precision },
            { label: 'F1分数', value: evaluation.f1_score },
            { label: 'AUC', value: evaluation.auc },
          ].map((metric) => (
            <div key={metric.label} className="card text-center">
              <p className="text-sm text-gray-500">{metric.label}</p>
              <p className="text-2xl font-bold text-gray-800 mt-1">
                {metric.value !== null && metric.value !== undefined 
                  ? (metric.value * 100).toFixed(1) + '%' 
                  : '-'}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Charts */}
      {evaluation && rocData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* ROC Curve */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">ROC曲线</h2>
            <div className="h-64">
              <Line
                data={lineData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    x: { title: { display: true, text: 'False Positive Rate' } },
                    y: { title: { display: true, text: 'True Positive Rate' } },
                  },
                }}
              />
            </div>
          </div>

          {/* Feature Importance */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">特征重要性 Top 10</h2>
            <div className="h-64">
              <Bar
                data={barData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  indexAxis: 'y',
                  scales: {
                    x: { title: { display: true, text: '重要性' } },
                  },
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Confusion Matrix */}
      {evaluation?.confusion_matrix && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">混淆矩阵</h2>
          <div className="flex justify-center">
            <table className="border-collapse">
              <thead>
                <tr>
                  <th className="border p-2"></th>
                  <th className="border p-2 bg-gray-100">预测: 0</th>
                  <th className="border p-2 bg-gray-100">预测: 1</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="border p-2 bg-gray-100">实际: 0</td>
                  <td className="border p-4 text-center text-xl font-bold text-green-600 bg-green-50">
                    {evaluation.confusion_matrix[0]?.[0] ?? 0}
                  </td>
                  <td className="border p-4 text-center text-xl font-bold text-red-600 bg-red-50">
                    {evaluation.confusion_matrix[0]?.[1] ?? 0}
                  </td>
                </tr>
                <tr>
                  <td className="border p-2 bg-gray-100">实际: 1</td>
                  <td className="border p-4 text-center text-xl font-bold text-red-600 bg-red-50">
                    {evaluation.confusion_matrix[1]?.[0] ?? 0}
                  </td>
                  <td className="border p-4 text-center text-xl font-bold text-green-600 bg-green-50">
                    {evaluation.confusion_matrix[1]?.[1] ?? 0}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Not trained message */}
      {model.status !== 'trained' && (
        <div className="card text-center py-8">
          <FiPlay className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-gray-500">
            {model.status === 'training' ? '模型正在训练中...' : '模型尚未训练'}
          </p>
          {model.status === 'pending' && (
            <button className="btn btn-primary mt-4">
              开始训练
            </button>
          )}
        </div>
      )}
    </div>
  )
}