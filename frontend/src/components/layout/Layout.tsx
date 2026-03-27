import { Link, useLocation, useNavigate, Outlet } from 'react-router-dom'
import { FiHome, FiFolder, FiBarChart2, FiCpu, FiUsers, FiLogOut, FiUser, FiMenu, FiX } from 'react-icons/fi'
import { useAuthStore, useUIStore } from '../../stores'
import { useState } from 'react'

const menuItems = [
  { path: '/dashboard', icon: FiHome, label: '仪表盘', roles: ['admin', 'doctor'] },
  { path: '/studies', icon: FiFolder, label: '影像管理', roles: ['admin', 'doctor'] },
  { path: '/features', icon: FiBarChart2, label: '特征提取', roles: ['admin'] },
  { path: '/models', icon: FiCpu, label: '模型管理', roles: ['admin', 'doctor'] },
  { path: '/users', icon: FiUsers, label: '用户管理', roles: ['admin'] },
]

export default function Layout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const { sidebarOpen, toggleSidebar } = useUIStore()
  const [showUserMenu, setShowUserMenu] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const filteredMenuItems = menuItems.filter(
    (item) => user && item.roles.includes(user.role)
  )

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-40 h-screen pt-4 transition-transform bg-white border-r border-gray-200 ${
          sidebarOpen ? 'w-64' : 'w-20'
        }`}
      >
        {/* Logo */}
        <div className="flex items-center justify-center px-4 mb-8">
          <Link to="/dashboard" className="flex items-center gap-2">
            <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">R</span>
            </div>
            {sidebarOpen && (
              <span className="text-xl font-bold text-gray-800">RadiomicsHub</span>
            )}
          </Link>
        </div>

        {/* Navigation */}
        <nav className="px-3">
          <ul className="space-y-1">
            {filteredMenuItems.map((item) => {
              const isActive = location.pathname === item.path
              const Icon = item.icon
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-primary-50 text-primary-600'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0" />
                    {sidebarOpen && <span>{item.label}</span>}
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>

        {/* User section */}
        <div className="absolute bottom-0 left-0 right-0 p-3 border-t border-gray-200">
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                <FiUser className="w-4 h-4 text-gray-600" />
              </div>
              {sidebarOpen && (
                <div className="flex-1 text-left">
                  <p className="text-sm font-medium text-gray-700 truncate">
                    {user?.full_name || user?.username}
                  </p>
                  <p className="text-xs text-gray-500">
                    {user?.role === 'admin' ? '管理员' : '医生'}
                  </p>
                </div>
              )}
            </button>

            {/* User dropdown */}
            {showUserMenu && (
              <div className="absolute bottom-full left-0 right-0 mb-2 bg-white rounded-lg shadow-lg border border-gray-200 py-1">
                <Link
                  to="/profile"
                  onClick={() => setShowUserMenu(false)}
                  className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  <FiUser className="w-4 h-4" />
                  个人资料
                </Link>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                >
                  <FiLogOut className="w-4 h-4" />
                  退出登录
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className={`transition-all ${sidebarOpen ? 'ml-64' : 'ml-20'}`}>
        {/* Top bar */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            {sidebarOpen ? <FiX className="w-5 h-5" /> : <FiMenu className="w-5 h-5" />}
          </button>
          
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-500">
              AI+影像组学全流程协作平台
            </span>
          </div>
        </header>

        {/* Page content */}
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}