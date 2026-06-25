# API 启动优化 - 模型预加载

## 概述

已优化 Flask API 启动过程，实现在应用启动时自动预加载至少一个检测模型，大幅提升第一次检测的响应速度。

## 改进内容

### 后端 (`fall_detection/api.py`)

#### 1. 模型缓存系统
```python
MODEL_CACHE = {}  # 存储已加载的模型
PRELOAD_STATUS = {"status": "idle", "model": None, "message": ""}
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
```

#### 2. 新增函数

**`load_model(model_path_str)`**
- 将模型加载到内存缓存中
- 同一个模型只加载一次
- 支持 CUDA/CPU 自动选择

**`preload_model_background()`**
- 在后台线程中预加载第一个可用模型
- 不阻塞 API 启动
- 实时更新预加载状态

**`get_available_models()`**
- 返回所有可用模型列表

#### 3. 新增 API 端点

**`GET /api/preload-status`**
- 返回模型预加载状态
- 返回缓存的模型数量
- 用于前端显示预加载进度

#### 4. 增强的现有端点

**`GET /api/health`**
- 增加设备信息 (CUDA/CPU)
- 增加预加载状态

**`GET /api/models`**
- 返回每个模型的缓存状态
- 已缓存的模型标记 `"cached": true`

**`POST /api/detect`**
- 自动使用缓存模型（如果可用）
- 首次使用的模型自动缓存
- 日志显示模型加载状态

### 前端 (`web/src/components/DetectionPanel.jsx`)

#### 1. 预加载状态监听
```javascript
useEffect(() => {
  loadPreloadStatus();
  // 每 2 秒轮询一次状态
  const interval = setInterval(loadPreloadStatus, 2000);
  return () => clearInterval(interval);
}, []);
```

#### 2. 预加载状态显示
- 在控制面板顶部显示预加载进度
- 状态类型：`loading` (蓝色), `ready` (绿色), `error` (红色)
- 实时显示预加载消息

#### 3. 模型缓存指示
- 在模型选择下拉框中显示 `[已缓存]` 标签
- 快速识别已加载的模型

## 性能提升

### 预加载前
- 首次检测：模型加载 + 检测 = ~10-30 秒（取决于模型大小）
- 第二次检测（同模型）：仅检测 = ~2-5 秒

### 预加载后
- API 启动：后台预加载模型（不阻塞）
- 首次检测：几乎无延迟 = ~2-5 秒（模型已预加载）
- 第二次检测：相同速度 = ~2-5 秒

### 用户体验提升
✅ 应用启动不被阻塞
✅ 用户可以立即看到 UI
✅ 模型预加载进度可见
✅ 首次检测响应时间大幅降低

## 启动流程

```
API 启动
  ↓
Flask 应用初始化
  ↓
后台线程启动预加载任务
  ↓
API 立即就绪 (可接收请求)
  ↓
后台线程加载模型 (并发进行)
  ↓
预加载完成 (通过 /api/preload-status 反映)
```

## 使用示例

### 检查预加载状态

```bash
# 查看当前预加载状态
curl http://127.0.0.1:5000/api/preload-status

# 响应示例
{
  "status": "ready",
  "model": "GPU-two-100",
  "message": "Model preloaded: GPU-two-100",
  "cached_models_count": 1
}
```

### 查看模型缓存信息

```bash
# 获取模型列表（包含缓存状态）
curl http://127.0.0.1:5000/api/models

# 响应示例
{
  "models": [
    {
      "name": "GPU-two-100",
      "path": "GPU-two-100/best.pt",
      "cached": true        # ← 已预加载
    },
    {
      "name": "mixdata-two-70-augment",
      "path": "mixdata-two-70-augment/best.pt",
      "cached": false       # ← 未加载
    }
  ],
  "preload": {
    "status": "ready",
    "model": "GPU-two-100",
    "message": "Model preloaded: GPU-two-100"
  }
}
```

## 配置选项

### 环境变量

**`FLASK_DEBUG`** (可选)
- 设置为 `1`, `true`, 或 `yes` 启用调试模式
- 默认：`false`

**`FALL_DETECTION_CORS_ORIGINS`** (可选)
- 逗号分隔的允许源列表
- 默认：`http://localhost:3000,http://127.0.0.1:3000`

### 示例启动命令

```bash
# 标准启动
python api.py

# 调试模式启动
FLASK_DEBUG=1 python api.py

# 自定义 CORS 源
FALL_DETECTION_CORS_ORIGINS=http://localhost:3000,http://192.168.1.100:3000 python api.py
```

## 技术细节

### 线程安全
- 使用 `PRELOAD_LOCK` 保证对预加载状态的线程安全访问
- 模型缓存字典 `MODEL_CACHE` 在预加载完成后为只读

### 内存管理
- 预加载的模型保留在内存中供后续请求使用
- 可以通过加载其他模型来扩展缓存
- 建议在部署环境中监控内存使用

### 错误处理
- 预加载失败不会导致 API 启动失败
- 错误信息显示在预加载状态中
- 用户仍然可以通过 API 手动加载模型

## 监控指标

### 日志输出

API 启动时的典型日志：
```
WARNING: This is a development server. Do not use it in production directly.
* Running on http://127.0.0.1:5000
* Preloader thread started...
* Model loading: GPU-two-100
✓ Model loaded and cached
* Preload completed successfully
```

### 性能监控建议

1. **预加载时间**：从 API 启动到预加载完成的时间
2. **缓存命中率**：检测请求中使用缓存模型的比例
3. **内存占用**：监控预加载前后的内存变化

## 最佳实践

### 生产部署

1. **使用 Gunicorn/uWSGI**：
   ```bash
   gunicorn --workers 1 --threads 4 api:app
   ```

2. **监控预加载状态**：
   ```bash
   curl -s http://127.0.0.1:5000/api/preload-status | jq .
   ```

3. **设置合适的超时时间**：
   预加载通常需要 10-60 秒，确保负载均衡器超时时间充足

### 多模型场景

对于需要多个模型的部署：
1. 预加载最常用的模型
2. 其他模型在首次使用时加载并缓存
3. 监控内存使用，必要时实现 LRU 缓存策略

## 故障排除

### 预加载失败

症状：预加载状态显示 `error`

解决方案：
1. 检查模型文件是否存在：`ls fall_detection/assets/*/best.pt`
2. 查看后端日志获取详细错误
3. 确认 PyTorch 和 ultralytics 已正确安装

### 模型缓存未生效

症状：每次检测都加载模型

解决方案：
1. 检查模型路径是否一致
2. 查看 API 日志中的 "Using cached model" 消息
3. 确认 MODEL_CACHE 不为空：`curl http://127.0.0.1:5000/api/models`

### 内存占用过高

症状：API 进程内存不断增加

解决方案：
1. 减少并发请求数
2. 清理不使用的模型缓存
3. 考虑实现模型卸载机制

## 后续优化建议

- [ ] 实现 LRU 模型缓存淘汰策略
- [ ] 添加模型预热（多个样本预运行）
- [ ] 实现模型卸载 API 端点
- [ ] 支持多个模型的预加载
- [ ] 添加预加载进度 WebSocket 推送
- [ ] 实现模型版本管理

## 更新日志

### v1.1.0 (2026-06-25)

✨ **新增功能**
- 模型预加载系统
- 模型缓存机制
- 预加载状态 API
- 前端预加载状态显示

🔧 **改进**
- 更快的首次检测响应时间
- 更好的 API 启动流程
- 增强的模型管理功能

## 许可证

遵循项目主许可证。
