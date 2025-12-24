# 独立语音克隆服务

这是一个独立的语音克隆服务，使用 Chatterbox TTS 模型，与主程序分离运行。

## 目录结构

```
voice_clone_server/
├── server.py          # 主服务文件 (FastAPI)
├── start_server.bat   # Windows 启动脚本
├── start_daemon.py    # 后台启动脚本
├── test_clone.py      # HTTP API 测试脚本
├── test_direct.py     # 直接模型测试脚本
├── test_import.bat    # 导入测试批处理
├── uploads/           # 上传的参考音频
└── outputs/           # 生成的音频输出
```

## 快速开始

### 1. 启动服务

打开命令提示符或 PowerShell，运行：

```bash
cd E:\工作代码\73_web_human\voice_clone_server
python server.py
```

或者双击 `start_server.bat`

### 2. 等待模型加载

首次启动会加载 9GB 的模型，需要 2-5 分钟。看到以下信息表示就绪：

```
模型加载完成!
INFO:     Uvicorn running on http://0.0.0.0:8003
```

### 3. 测试服务

打开浏览器访问：http://localhost:8003/docs

或使用 curl 测试：

```bash
# 健康检查
curl http://localhost:8003/health

# 查看服务信息
curl http://localhost:8003/
```

### 4. 语音克隆

使用 curl 或 Postman：

```bash
curl -X POST http://localhost:8003/clone \
  -F "audio=@参考音频.wav" \
  -F "text=Hello, this is a voice cloning test." \
  -F "exaggeration=0.5" \
  -F "cfg_weight=0.5"
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /health | GET | 健康检查 |
| /clone | POST | 同步语音克隆（等待完成返回） |
| /clone/async | POST | 异步语音克隆（返回任务ID） |
| /task/{task_id} | GET | 查询异步任务状态 |
| /download/{filename} | GET | 下载生成的音频 |

## 参数说明

- **audio**: 参考音频文件 (WAV/MP3，10-15秒清晰语音)
- **text**: 要生成的文本内容
- **exaggeration**: 情感夸张度 (0.25-2.0，默认 0.5)
- **cfg_weight**: CFG权重 (0.0-1.0，默认 0.5)

## 与主程序对接

主程序可以通过 HTTP 调用此服务：

```python
import requests

def clone_voice(audio_path: str, text: str) -> str:
    """调用语音克隆服务"""
    with open(audio_path, "rb") as f:
        resp = requests.post(
            "http://localhost:8003/clone",
            files={"audio": f},
            data={"text": text}
        )
    result = resp.json()
    return result.get("audio_url")
```

## 注意事项

1. 模型使用 CPU 运行，首次生成可能需要 1-2 分钟
2. 参考音频需要 10-15 秒清晰的单人语音
3. 服务端口为 8003，确保端口未被占用
4. 需要设置代理才能正常运行（已在代码中配置）
