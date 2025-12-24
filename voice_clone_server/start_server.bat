@echo off
chcp 65001 >nul
echo ============================================================
echo 语音克隆服务
echo ============================================================
echo.
echo 服务端口: 3002 (从 .env VOICE_CLONE_PORT 读取)
echo API 文档: http://localhost:3002/docs
echo.

cd /d "%~dp0"

REM 检查 venv 是否存在
if not exist "venv\Scripts\python.exe" (
    echo 错误: 虚拟环境不存在！
    echo 请先运行 install.bat 安装依赖
    pause
    exit /b 1
)

echo 启动服务中...
echo 模型首次加载需要 2-5 分钟，请耐心等待
echo ============================================================
echo.

venv\Scripts\python.exe server.py

pause
