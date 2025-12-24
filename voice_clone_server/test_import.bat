@echo off
chcp 65001 >nul

set HTTP_PROXY=socks5://192.168.0.221:8800
set HTTPS_PROXY=socks5://192.168.0.221:8800
set ALL_PROXY=socks5://192.168.0.221:8800
set HF_ENDPOINT=https://hf-mirror.com

echo Testing chatterbox import...
python -c "from chatterbox.tts import ChatterboxTTS; print('OK')"
echo Exit code: %ERRORLEVEL%
pause
