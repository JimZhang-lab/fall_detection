# Web UI 启动脚本

#!/bin/bash

# 后端 API 启动脚本
# 在后台启动 Flask API 服务器

cd "$(dirname "$0")"

echo "启动 Fall Detection Web API..."
echo "后端 API 将在 http://127.0.0.1:5000 运行"

# 检查 Python 依赖
cd fall_detection

if ! python -c "import flask" 2>/dev/null; then
    echo "正在安装 Python 依赖..."
    pip install -r requirements.txt
fi

# 启动 Flask API
python api.py &
BACKEND_PID=$!

echo "后端 PID: $BACKEND_PID"

# 启动前端开发服务器
cd ../web

echo ""
echo "启动 Fall Detection Web 前端..."
echo "前端应用将在 http://localhost:3000 运行"
echo ""

# 检查 Node 依赖
if [ ! -d "node_modules" ]; then
    echo "正在安装 Node 依赖..."
    npm install
fi

# 启动开发服务器
npm run dev

# 清理
kill $BACKEND_PID 2>/dev/null
