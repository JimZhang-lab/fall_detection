@echo off
REM Windows 启动脚本

echo.
echo ================================================
echo 跌倒检测系统 Web UI 启动脚本 (Windows)
echo ================================================
echo.

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM 检查 Python
echo 检查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python 未找到。请先安装 Python 3.11 或更高版本
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION%

REM 检查 Node.js
echo 检查 Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Node.js 未找到。请先安装 Node.js 16 或更高版本
    pause
    exit /b 1
)
for /f %%i in ('node --version') do set NODE_VERSION=%%i
echo [OK] Node.js %NODE_VERSION%

echo.
echo 启动 Flask 后端 API...

REM 进入后端目录
cd /d "%PROJECT_ROOT%\fall_detection"

REM 检查 Python 依赖
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo 正在安装 Python 依赖...
    pip install -r requirements.txt
)

REM 启动 Flask API（后台运行）
echo 在后台启动 Flask API (http://127.0.0.1:5000)...
start "Flask Backend" python api.py
timeout /t 2 /nobreak

echo.
echo 启动 React 前端应用...

REM 进入前端目录
cd /d "%SCRIPT_DIR%"

REM 检查 Node 依赖
if not exist "node_modules" (
    echo 正在安装 Node 依赖...
    call npm install --silent
)

echo.
echo ================================================
echo [OK] 启动成功！
echo ================================================
echo.
echo 后端 API:   http://127.0.0.1:5000
echo 前端应用:   http://localhost:3000
echo.
echo 按任意键继续... 浏览器将自动打开应用。
pause

REM 尝试打开浏览器
start http://localhost:3000

REM 启动前端开发服务器
call npm run dev

REM 脚本结束
echo.
echo 应用已关闭
pause
