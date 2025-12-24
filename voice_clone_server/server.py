#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的语音克隆服务
使用 Chatterbox TTS 进行零样本语音克隆
运行在独立端口，不影响主程序
"""

import os
import sys
import uuid
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

# 设置代理（必须在导入其他模块之前）
PROXY = "socks5://192.168.0.221:8800"
os.environ['HTTP_PROXY'] = PROXY
os.environ['HTTPS_PROXY'] = PROXY
os.environ['ALL_PROXY'] = PROXY
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# 加载环境变量
from dotenv import load_dotenv
# 先尝试加载主项目的 .env
main_env_path = Path(__file__).parent.parent / ".env"
if main_env_path.exists():
    load_dotenv(main_env_path)
# 再加载本地 .env (如果有的话，会覆盖)
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# 服务配置 - 从环境变量读取
SERVICE_PORT = int(os.getenv("VOICE_CLONE_PORT", "3002"))
MODEL_PATH = Path(__file__).parent.parent / "models" / "ResembleAI" / "chatterbox"
UPLOAD_DIR = Path(__file__).parent / "uploads"
OUTPUT_DIR = Path(__file__).parent / "outputs"

# 确保目录存在
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 线程池
executor = ThreadPoolExecutor(max_workers=2)

# 全局模型实例
_model = None
_model_loading = False


class CloneRequest(BaseModel):
    """语音克隆请求"""
    text: str
    exaggeration: float = 0.5
    cfg_weight: float = 0.5


class CloneResponse(BaseModel):
    """语音克隆响应"""
    success: bool
    message: str
    audio_url: Optional[str] = None
    task_id: Optional[str] = None


class TaskStatus(BaseModel):
    """任务状态"""
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int = 0
    audio_url: Optional[str] = None
    error: Optional[str] = None


# 任务存储
tasks: dict = {}


def load_model():
    """加载模型（同步方法）"""
    global _model, _model_loading

    if _model is not None:
        return _model

    if _model_loading:
        import time
        while _model_loading:
            time.sleep(0.5)
        return _model

    _model_loading = True

    try:
        print("=" * 50)
        print("正在加载 Chatterbox TTS 模型...")
        print(f"模型路径: {MODEL_PATH}")
        print("=" * 50)

        import torch
        from chatterbox.tts import ChatterboxTTS

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"使用设备: {device}")

        if MODEL_PATH.exists():
            print("从本地加载模型...")
            _model = ChatterboxTTS.from_local(str(MODEL_PATH), device=device)
        else:
            print("本地模型不存在，从 HuggingFace 下载...")
            _model = ChatterboxTTS.from_pretrained(device=device)

        print("=" * 50)
        print("模型加载完成!")
        print("=" * 50)
        return _model

    except Exception as e:
        print(f"模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        _model_loading = False


def generate_audio_sync(
    reference_audio_path: str,
    text: str,
    output_path: str,
    exaggeration: float = 0.5,
    cfg_weight: float = 0.5
) -> str:
    """同步生成音频"""
    import torchaudio

    model = load_model()

    print(f"开始生成语音...")
    print(f"参考音频: {reference_audio_path}")
    print(f"文本: {text[:100]}...")
    print(f"exaggeration: {exaggeration}, cfg_weight: {cfg_weight}")

    wav = model.generate(
        text=text,
        audio_prompt_path=reference_audio_path,
        exaggeration=exaggeration,
        cfg_weight=cfg_weight
    )

    sample_rate = model.sr
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torchaudio.save(str(output_path), wav, sample_rate)

    print(f"语音生成成功: {output_path}")
    return str(output_path)


# 创建 FastAPI 应用
app = FastAPI(
    title="Voice Clone Service",
    description="独立的语音克隆服务 - Chatterbox TTS",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """启动时预加载模型"""
    print("\n" + "=" * 50)
    print("语音克隆服务启动中...")
    print(f"服务端口: {SERVICE_PORT}")
    print(f"模型路径: {MODEL_PATH}")
    print(f"模型存在: {MODEL_PATH.exists()}")
    print("=" * 50 + "\n")

    # 在后台线程中加载模型
    loop = asyncio.get_event_loop()
    asyncio.create_task(preload_model())


async def preload_model():
    """异步预加载模型"""
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(executor, load_model)
        print("\n模型预加载完成，服务就绪!\n")
    except Exception as e:
        print(f"\n模型预加载失败: {e}\n")


@app.get("/")
async def root():
    """服务信息"""
    return {
        "service": "Voice Clone Service",
        "version": "1.0.0",
        "model": "Chatterbox TTS",
        "model_loaded": _model is not None,
        "model_path": str(MODEL_PATH),
        "endpoints": {
            "health": "/health",
            "clone_sync": "POST /clone",
            "clone_async": "POST /clone/async",
            "task_status": "GET /task/{task_id}",
            "download": "GET /download/{filename}"
        }
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "model_loaded": _model is not None,
        "model_loading": _model_loading
    }


@app.post("/clone", response_model=CloneResponse)
async def clone_voice(
    audio: UploadFile = File(..., description="参考音频文件 (10-15秒)"),
    text: str = Form(..., description="要生成的文本"),
    exaggeration: float = Form(0.5, description="情感夸张度 0.25-2.0"),
    cfg_weight: float = Form(0.5, description="CFG权重 0.0-1.0")
):
    """
    同步语音克隆（等待完成后返回）

    - audio: 参考音频文件 (WAV/MP3, 10-15秒清晰语音)
    - text: 要生成的文本内容
    - exaggeration: 情感夸张度 (默认 0.5)
    - cfg_weight: CFG权重 (默认 0.5)
    """
    try:
        # 保存上传的音频
        audio_id = uuid.uuid4().hex[:8]
        audio_ext = Path(audio.filename or "audio.wav").suffix or ".wav"
        audio_path = UPLOAD_DIR / f"{audio_id}{audio_ext}"

        content = await audio.read()
        with open(audio_path, "wb") as f:
            f.write(content)

        print(f"收到克隆请求: audio={audio_path}, text={text[:50]}...")

        # 生成输出路径
        output_id = uuid.uuid4().hex[:8]
        output_path = OUTPUT_DIR / f"{output_id}.wav"

        # 在线程池中执行
        loop = asyncio.get_event_loop()
        result_path = await loop.run_in_executor(
            executor,
            generate_audio_sync,
            str(audio_path),
            text,
            str(output_path),
            exaggeration,
            cfg_weight
        )

        return CloneResponse(
            success=True,
            message="语音生成成功",
            audio_url=f"/download/{output_path.name}"
        )

    except Exception as e:
        print(f"克隆失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clone/async", response_model=CloneResponse)
async def clone_voice_async(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(..., description="参考音频文件"),
    text: str = Form(..., description="要生成的文本"),
    exaggeration: float = Form(0.5),
    cfg_weight: float = Form(0.5)
):
    """
    异步语音克隆（立即返回任务ID，后台处理）

    使用 GET /task/{task_id} 查询状态
    """
    try:
        # 保存上传的音频
        audio_id = uuid.uuid4().hex[:8]
        audio_ext = Path(audio.filename or "audio.wav").suffix or ".wav"
        audio_path = UPLOAD_DIR / f"{audio_id}{audio_ext}"

        content = await audio.read()
        with open(audio_path, "wb") as f:
            f.write(content)

        # 创建任务
        task_id = uuid.uuid4().hex[:12]
        output_path = OUTPUT_DIR / f"{task_id}.wav"

        tasks[task_id] = {
            "status": "pending",
            "progress": 0,
            "audio_url": None,
            "error": None,
            "created_at": datetime.utcnow()
        }

        # 后台处理
        background_tasks.add_task(
            process_clone_task,
            task_id,
            str(audio_path),
            text,
            str(output_path),
            exaggeration,
            cfg_weight
        )

        return CloneResponse(
            success=True,
            message="任务已创建，请轮询获取状态",
            task_id=task_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def process_clone_task(
    task_id: str,
    audio_path: str,
    text: str,
    output_path: str,
    exaggeration: float,
    cfg_weight: float
):
    """后台处理克隆任务"""
    try:
        tasks[task_id]["status"] = "processing"
        tasks[task_id]["progress"] = 10

        loop = asyncio.get_event_loop()

        tasks[task_id]["progress"] = 30

        await loop.run_in_executor(
            executor,
            generate_audio_sync,
            audio_path,
            text,
            output_path,
            exaggeration,
            cfg_weight
        )

        tasks[task_id]["status"] = "completed"
        tasks[task_id]["progress"] = 100
        tasks[task_id]["audio_url"] = f"/download/{Path(output_path).name}"

    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        print(f"任务 {task_id} 失败: {e}")


@app.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks[task_id]
    return TaskStatus(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        audio_url=task.get("audio_url"),
        error=task.get("error")
    )


@app.get("/download/{filename}")
async def download_audio(filename: str):
    """下载生成的音频"""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=str(file_path),
        media_type="audio/wav",
        filename=filename
    )


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("启动独立语音克隆服务")
    print("=" * 60)
    print(f"端口: {SERVICE_PORT}")
    print(f"API 文档: http://localhost:{SERVICE_PORT}/docs")
    print("=" * 60 + "\n")

    uvicorn.run(
        app,  # 直接传递 app 对象
        host="0.0.0.0",
        port=SERVICE_PORT,
        log_level="info"
    )
