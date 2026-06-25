#!/bin/bash
# Windows 用户请在 PowerShell 中运行，或使用 WSL

set -e  # 错误时退出

echo "================================================"
echo "跌倒检测系统 Web UI 启动脚本"
echo "================================================"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 颜色定义（用于输出）
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Python
echo "${YELLOW}检查 Python...${NC}"
if ! command -v python &> /dev/null; then
    echo "${RED}❌ Python 未找到。请先安装 Python 3.11 或更高版本${NC}"
    exit 1
fi
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "${GREEN}✓ Python $PYTHON_VERSION${NC}"

# 检查 Node.js
echo "${YELLOW}检查 Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo "${RED}❌ Node.js 未找到。请先安装 Node.js 16 或更高版本${NC}"
    exit 1
fi
NODE_VERSION=$(node --version)
echo "${GREEN}✓ Node.js $NODE_VERSION${NC}"

echo ""
echo "${YELLOW}启动 Flask 后端 API...${NC}"

# 进入后端目录
cd "$PROJECT_ROOT/fall_detection"

# 检查 Python 依赖
if ! python -c "import flask" 2>/dev/null; then
    echo "${YELLOW}正在安装 Python 依赖...${NC}"
    pip install -r requirements.txt
fi

# 启动 Flask API（后台运行）
echo "${YELLOW}在后台启动 Flask API (http://127.0.0.1:5000)...${NC}"
python api.py > "$SCRIPT_DIR/../api.log" 2>&1 &
BACKEND_PID=$!
echo "${GREEN}✓ 后端 PID: $BACKEND_PID${NC}"

# 等待后端启动
sleep 2

# 检查后端是否成功启动
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "${RED}❌ 后端启动失败。检查 api.log：${NC}"
    cat "$SCRIPT_DIR/../api.log"
    exit 1
fi

echo ""
echo "${YELLOW}启动 React 前端应用...${NC}"

# 进入前端目录
cd "$SCRIPT_DIR"

# 检查 Node 依赖
if [ ! -d "node_modules" ]; then
    echo "${YELLOW}正在安装 Node 依赖...${NC}"
    npm install --silent
fi

echo ""
echo "${GREEN}================================================${NC}"
echo "${GREEN}✓ 启动成功！${NC}"
echo "${GREEN}================================================${NC}"
echo ""
echo "后端 API:   http://127.0.0.1:5000"
echo "前端应用:   http://localhost:3000"
echo ""
echo "按 Enter 在默认浏览器中打开应用..."
read

# 尝试打开浏览器
if command -v open &> /dev/null; then
    open http://localhost:3000
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
elif command -v start &> /dev/null; then
    start http://localhost:3000
fi

# 启动前端开发服务器
npm run dev

# 清理
echo ""
echo "${YELLOW}清理资源...${NC}"
kill $BACKEND_PID 2>/dev/null || true
echo "${GREEN}✓ 已关闭${NC}"
