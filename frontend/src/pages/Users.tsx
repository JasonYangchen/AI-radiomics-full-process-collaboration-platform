import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { usersApi } from '../services/api'
import { FiUser, FiTrash2 } from 'react-icons/fi'
import toast from 'react-hot-toast'
import type { User } from '../types'

export default function Users() {
  const queryClient = useQueryClient()
  const [page] = useState(1)
  const [roleFilter, setRoleFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['users', page, roleFilter],
    queryFn: () => usersApi.list({ page, role: roleFilter || undefined }),
  })

  const updateRoleMutation = useMutation({
    mutationFn: ({ id, role }: { id: string; role: string }) =>
      usersApi.updateRole(id, role),
    onSuccess: () => {
      toast.success('角色更新成功')
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
    onError: () => {
      toast.error('更新失败')
    },
  })

  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      usersApi.toggleActive(id, is_active),
    onSuccess: () => {
      toast.success('状态更新成功')
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => usersApi.delete(id),
    onSuccess: () => {
      toast.success('删除成功')
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })

  const handleDelete = (user: User) => {
    if (confirm(`确定要删除用户 "${user.username}" 吗？`)) {
      deleteMutation.mutate(user.id)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">用户管理</h1>
          <p className="text-gray-500 mt-1">管理平台用户和权限</p>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex items-center gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">角色</label>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="input w-40"
            >
              <option value="">全部</option>
              <option value="admin">管理员</option>
              <option value="doctor">医生</option>
            </select>
          </div>
        </div>
      </div>

      {/* Users list */}
      <div className="card">
        {isLoading ? (
          <div className="text-center py-8 text-gray-500">加载中...</div>
        ) : data?.data.items.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FiUser className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>暂无用户</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">用户</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">邮箱</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">角色</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">状态</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">创建时间</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">操作</th>
                </tr>
              </thead>
              <tbody>
                {data?.data.items.map((user: User) => (
                  <tr key={user.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                          <FiUser className="w-5 h-5 text-gray-500" />
                        </div>
                        <div>
                          <p className="font-medium">{user.username}</p>
                          <p className="text-sm text-gray-500">{user.full_name || '-'}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-gray-600">{user.email}</td>
                    <td className="py-3 px-4">
                      <select
                        value={user.role}
                        onChange={(e) => updateRoleMutation.mutate({ id: user.id, role: e.target.value })}
                        className="text-sm border border-gray-200 rounded px-2 py-1"
                      >
                        <option value="admin">管理员</option>
                        <option value="doctor">医生</option>
                      </select>
                    </td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => toggleActiveMutation.mutate({ id: user.id, is_active: !user.is_active })}
                        className={`px-2 py-1 text-xs rounded-full ${
                          user.is_active
                            ? 'bg-green-100 text-green-700'
                            : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {user.is_active ? '活跃' : '禁用'}
                      </button>
                    </td>
                    <td className="py-3 px-4 text-gray-500 text-sm">
                      {new Date(user.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleDelete(user)}
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
    </div>
  )
}