# Whisper 服务配置指南

## 概述

项目支持两种 Whisper 语音转文字服务模式：
- **local**: 使用本地 GPU 运行 Whisper large-v3 模型
- **cloud**: 使用 APIMart Whisper-1 API

## 切换方式

### 方法 1: 环境变量 (推荐)

在 `.env` 文件中设置：

```bash
# 使用本地 GPU 模型
WHISPER_SERVICE_MODE=local

# 使用云端 API
WHISPER_SERVICE_MODE=cloud
```

### 方法 2: 代码中指定

```python
from core.services.whisper import get_whisper_service

# 使用默认模式 (从环境变量读取)
service = get_whisper_service()

# 强制使用本地模式
service = get_whisper_service("local")

# 强制使用云端模式
service = get_whisper_service("cloud")

# 使用服务
async with get_whisper_service() as service:
    result = await service.transcribe("audio.mp3", language="en")
    print(result.text)
    print(result.words)  # 词级时间戳
```

## 本地模式要求

1. **GPU**: 需要 NVIDIA 显卡 (推荐 RTX 3080 及以上)
2. **CUDA**: PyTorch CUDA 版本
3. **模型文件**: `E:/local_models/whisper/large-v3.pt` (2.88 GB)

### 安装本地依赖 (仅开发机器)

```bash
# 安装 CUDA 版 PyTorch (不要添加到 requirements.txt)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# 安装 whisper
pip install openai-whisper
```

### 下载模型

使用并行代理池下载：
```bash
python C:/Users/Administrator/.claude/skills/proxy-downloader/scripts/download.py -q download \
  "https://openaipublic.azureedge.net/main/whisper/models/e5b1a55b89c1367dacf97e3e19bfd829a01529dbfdeefa8caeb59b3f1b81dadb/large-v3.pt" \
  -o E:/local_models/whisper/large-v3.pt
```

## 云端模式要求

1. **API Key**: 在 `.env` 中配置 `APIMART_API_KEY`
2. **网络**: 能访问 `api.apimart.ai`

## 服务器部署

**重要**: 服务器部署时必须使用 `cloud` 模式：

```bash
WHISPER_SERVICE_MODE=cloud
```

本地 GPU 相关依赖 (torch+cuda, whisper) 不要添加到 `requirements.txt`。

## 文件结构

```
core/services/whisper/
├── __init__.py        # 模块入口
├── base.py            # 基类定义
├── factory.py         # 工厂函数
├── local_service.py   # 本地 GPU 服务
└── cloud_service.py   # 云端 API 服务
```

## 性能对比

| 模式 | 设备 | 8分钟音频 | 优点 | 缺点 |
|------|------|----------|------|------|
| local | RTX 5090 | ~35秒 | 无 API 费用，无网络依赖 | 需要 GPU |
| cloud | APIMart | ~60秒 | 无需 GPU | 需要网络，有 API 费用 |
