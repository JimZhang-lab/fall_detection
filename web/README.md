# Fall Detection Web UI

现代化的 Web 前端界面，使用 React + Ant Design + Tailwind CSS 构建。

## 功能特性

- ✨ 现代化的响应式 Web 界面
- 📁 文件拖拽上传（图像和视频）
- 🤖 多模型支持
- 🎯 灵活的检测选项
  - 无人帧筛除
  - 静态帧筛除
  - 自定义帧间隔
- 📊 实时检测日志显示
- 📥 结果文件下载
- 🚀 快速响应和流畅交互

## 快速开始

### 前置要求

- Node.js 16+ 和 npm/yarn
- Python 3.11+ 和 fall_detection 依赖

### 1. 安装后端依赖

```bash
cd fall_detection
pip install -r requirements.txt
```

### 2. 启动 Flask 后端 API

```bash
cd fall_detection
python api.py
```

后端 API 将在 `http://127.0.0.1:5000` 运行

### 3. 安装前端依赖

```bash
cd web
npm install
```

### 4. 启动开发服务器

```bash
npm run dev
```

前端应用将在 `http://localhost:3000` 运行

### 5. 打开浏览器

访问 [http://localhost:3000](http://localhost:3000) 开始使用

## 项目结构

```
web/
├── src/
│   ├── components/
│   │   ├── DetectionPanel.jsx      # 主检测面板组件
│   │   ├── DetectionPanel.css      # 样式文件
│   │   └── LogPanel.jsx            # 日志显示组件
│   ├── App.jsx                     # 主应用组件
│   ├── main.jsx                    # 入口文件
│   └── index.css                   # 全局样式
├── index.html                      # HTML 入口
├── package.json                    # 依赖配置
├── vite.config.js                  # Vite 配置
├── tailwind.config.js              # Tailwind 配置
└── README.md                       # 本文件
```

## 使用说明

### 基本工作流

1. **选择文件**：点击或拖拽上传要检测的图像或视频
2. **选择模型**：从下拉菜单选择要使用的检测模型
3. **配置选项**：
   - 启用/禁用无人帧筛除（去除没有人的帧）
   - 启用/禁用静态帧筛除（去除没有动作的帧）
   - 设置帧检测间隔（推荐设置为 2 以提升性能）
4. **开始检测**：点击"开始检测"按钮执行检测
5. **查看结果**：实时日志显示检测进度，完成后可下载结果文件

### 支持的文件格式

- **图像**：JPG, JPEG, PNG
- **视频**：MP4, AVI, MOV, MKV
- **文件大小限制**：最大 500MB

## API 端点

### 获取可用模型

```
GET /api/models
```

返回所有可用的检测模型列表。

### 上传文件

```
POST /api/upload
```

上传要检测的图像或视频文件。

### 执行检测

```
POST /api/detect
```

执行跌倒检测任务。

**请求体示例：**
```json
{
  "filepath": "/path/to/file",
  "model_name": "GPU-two-100/best.pt",
  "use_filter_person": false,
  "use_filter_static": false,
  "frame_interval": 1
}
```

### 下载结果

```
GET /api/download/<filename>
```

下载检测结果文件。

## 构建生产版本

```bash
npm run build
```

构建的文件将在 `dist/` 目录中，可部署到任何静态文件服务器。

## 技术栈

- **前端框架**：React 18
- **UI 组件库**：Ant Design 5
- **样式方案**：Tailwind CSS + 自定义 CSS
- **构建工具**：Vite
- **HTTP 客户端**：Axios
- **后端**：Flask + Flask-CORS

## 故障排除

### 后端连接错误

如果看到 "连接失败" 错误：
1. 确保 Flask 后端正在运行 (`python api.py`)
2. 检查后端是否在 `http://127.0.0.1:5000` 监听
3. 检查防火墙设置

### 上传文件失败

1. 确认文件大小 < 500MB
2. 确认文件格式正确（图像或视频）
3. 检查磁盘空间是否充足

### 检测超时

1. 尝试增加帧检测间隔（例如从 1 改为 2 或 3）
2. 启用静态帧筛除以减少处理帧数
3. 在 GPU 可用的机器上运行以加快速度

## 开发指南

### 添加新功能

1. 在 `src/components/` 中创建新组件
2. 在 `DetectionPanel.jsx` 中导入并使用
3. 根据需要添加样式到 CSS 文件

### 修改 API 调用

API 调用在 `src/components/DetectionPanel.jsx` 中，使用 Axios。修改时保持与后端 API 端点的同步。

### 样式定制

- 使用 Tailwind CSS 的工具类进行快速样式定制
- 将复杂样式放在 CSS 模块中（`.css` 文件）
- 遵循 Ant Design 的主题系统

## 许可证

本项目遵循与主项目相同的许可证。

## 支持

如有问题或建议，请联系项目维护者。
