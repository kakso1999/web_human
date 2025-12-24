@echo off
chcp 65001 >nul
echo ============================================================
echo 语音克隆服务 - 环境安装
echo ============================================================
echo.

cd /d "%~dp0"

REM 检查 Python 版本
python --version
echo.

REM 检查是否已有 venv
if exist "venv\Scripts\python.exe" (
    echo 虚拟环境已存在，跳过创建
) else (
    echo 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo 创建虚拟环境失败！
        pause
        exit /b 1
    )
)

echo.
echo 激活虚拟环境...
call venv\Scripts\activate.bat

echo.
echo ============================================================
echo 安装依赖 (使用代理: socks5://192.168.0.221:8800)
echo 大型依赖 (torch, transformers) 可能需要较长时间
echo ============================================================
echo.

pip install -r requirements.txt --proxy socks5://192.168.0.221:8800

if errorlevel 1 (
    echo.
    echo 安装失败！请检查网络连接和代理设置
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 安装完成！
echo.
echo 启动服务: start_server.bat
echo 或手动运行: venv\Scripts\python.exe server.py
echo ============================================================
pause
