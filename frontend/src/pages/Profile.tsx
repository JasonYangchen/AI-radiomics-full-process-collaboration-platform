import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { authApi } from '../services/api'
import { useAuthStore } from '../stores'
import { FiUser, FiMail, FiLock, FiSave } from 'react-icons/fi'
import toast from 'react-hot-toast'

export default function Profile() {
  const { user, updateUser } = useAuthStore()
  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
    current_password: '',
    new_password: '',
    confirm_password: '',
  })

  const updateMutation = useMutation({
    mutationFn: (data: any) => authApi.updateMe(data),
    onSuccess: (response) => {
      updateUser(response.data)
      toast.success('资料更新成功')
      setFormData({ ...formData, current_password: '', new_password: '', confirm_password: '' })
    },
    onError: () => {
      toast.error('更新失败')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    const updateData: any = {
      full_name: formData.full_name,
      email: formData.email,
    }
    
    if (formData.new_password) {
      if (formData.new_password !== formData.confirm_password) {
        toast.error('两次输入的密码不一致')
        return
      }
      if (!formData.current_password) {
        toast.error('请输入当前密码')
        return
      }
      updateData.password = formData.new_password
    }
    
    updateMutation.mutate(updateData)
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">个人资料</h1>

      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic info */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-800">基本信息</h2>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                用户名
              </label>
              <div className="relative">
                <FiUser className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={user?.username || ''}
                  disabled
                  className="input pl-10 bg-gray-50"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                姓名
              </label>
              <div className="relative">
                <FiUser className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="input pl-10"
                  placeholder="请输入姓名"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                邮箱
              </label>
              <div className="relative">
                <FiMail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="input pl-10"
                  placeholder="请输入邮箱"
                />
              </div>
            </div>
          </div>

          {/* Password */}
          <div className="space-y-4 pt-6 border-t border-gray-200">
            <h2 className="text-lg font-semibold text-gray-800">修改密码</h2>
            <p className="text-sm text-gray-500">如需修改密码，请填写以下字段</p>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                新密码
              </label>
              <div className="relative">
                <FiLock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="password"
                  value={formData.new_password}
                  onChange={(e) => setFormData({ ...formData, new_password: e.target.value })}
                  className="input pl-10"
                  placeholder="请输入新密码"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                确认新密码
              </label>
              <div className="relative">
                <FiLock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="password"
                  value={formData.confirm_password}
                  onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                  className="input pl-10"
                  placeholder="请再次输入新密码"
                />
              </div>
            </div>
          </div>

          {/* Submit */}
          <div className="flex justify-end pt-4">
            <button
              type="submit"
              disabled={updateMutation.isPending}
              className="btn btn-primary flex items-center gap-2"
            >
              <FiSave className="w-4 h-4" />
              {updateMutation.isPending ? '保存中...' : '保存更改'}
            </button>
          </div>
        </form>
      </div>

      {/* Account info */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">账户信息</h2>
        <dl className="space-y-3">
          <div className="flex justify-between">
            <dt className="text-gray-500">角色</dt>
            <dd className="font-medium">
              {user?.role === 'admin' ? '管理员' : '医生'}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">账户状态</dt>
            <dd className="font-medium text-green-600">活跃</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">注册时间</dt>
            <dd className="font-medium">
              {user?.created_at ? new Date(user.created_at).toLocaleString() : '-'}
            </dd>
          </div>
        </dl>
      </div>
    </div>
  )
}