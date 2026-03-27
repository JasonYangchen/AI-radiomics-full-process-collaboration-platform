import { useParams } from 'react-router-dom'
import { useState } from 'react'

export default function Annotation() {
  const { studyId } = useParams<{ studyId: string }>()
  const [tool, setTool] = useState<'freehand' | 'polygon' | 'sphere'>('freehand')
  const [color, setColor] = useState('#FF0000')

  return (
    <div className="h-[calc(100vh-120px)] flex gap-4">
      {/* Toolbar */}
      <div className="w-16 bg-white rounded-xl shadow-lg p-2 flex flex-col gap-2">
        <button
          onClick={() => setTool('freehand')}
          className={`p-3 rounded-lg transition-colors ${tool === 'freehand' ? 'bg-primary-100 text-primary-600' : 'hover:bg-gray-100'}`}
          title="自由画笔"
        >
          ✏️
        </button>
        <button
          onClick={() => setTool('polygon')}
          className={`p-3 rounded-lg transition-colors ${tool === 'polygon' ? 'bg-primary-100 text-primary-600' : 'hover:bg-gray-100'}`}
          title="多边形"
        >
          🔷
        </button>
        <button
          onClick={() => setTool('sphere')}
          className={`p-3 rounded-lg transition-colors ${tool === 'sphere' ? 'bg-primary-100 text-primary-600' : 'hover:bg-gray-100'}`}
          title="球体"
        >
          ⚪
        </button>
        <hr className="my-2" />
        <div className="p-2">
          <input
            type="color"
            value={color}
            onChange={(e) => setColor(e.target.value)}
            className="w-full h-8 cursor-pointer"
            title="选择颜色"
          />
        </div>
      </div>

      {/* Viewer */}
      <div className="flex-1 bg-gray-900 rounded-xl flex items-center justify-center">
        <div className="text-center text-gray-400">
          <div className="text-6xl mb-4">🩺</div>
          <p className="text-lg">影像标注工具</p>
          <p className="text-sm mt-2">类似于 3D Slicer 的标注体验</p>
          <p className="text-xs mt-4 text-gray-500">
            注：完整实现需要集成 VTK.js 或 Cornerstone.js 库
          </p>
        </div>
      </div>

      {/* ROI Panel */}
      <div className="w-64 bg-white rounded-xl shadow-lg p-4">
        <h3 className="font-semibold text-gray-800 mb-4">标注列表</h3>
        <div className="space-y-2 text-sm text-gray-500">
          <p>标注功能说明：</p>
          <ul className="list-disc list-inside space-y-1">
            <li>支持自由画笔标注</li>
            <li>支持多边形套索</li>
            <li>支持球体/立方体</li>
            <li>支持阈值分割</li>
            <li>自动保存 ROI</li>
          </ul>
          <p className="mt-4 text-xs">
            研究ID: {studyId}
          </p>
        </div>
      </div>
    </div>
  )
}