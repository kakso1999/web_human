# 故事生成功能规划文档

## 一、功能概述

将儿童故事 MP4 视频中的指定播音员声音替换为父母克隆的声音，并在视频右下角添加父母的数字人头像（对口型），生成新的个性化故事视频。

---

## 二、完整业务流程

```
原始故事 MP4 视频
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Step 1: 视频预处理 (IMS)                                 │
│  ├─ 分离视频轨道 (静音视频)                              │
│  ├─ 分离音频轨道 (原始混合音频)                          │
│  └─ 提取字幕/语音识别 (ASR) → SRT 文件                   │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Step 2: 音频分离 (人声分离服务)                          │
│  ├─ 分离背景音乐/环境声 → BGM 轨道                       │
│  └─ 分离人声 → 人声轨道                                  │
│     └─ (可选) 多说话人识别分离                           │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Step 3: 台词解析与角色分配                               │
│  ├─ 解析 SRT 字幕文件 (时间戳 + 文本)                    │
│  ├─ (可选) 识别不同角色的台词                            │
│  └─ 用户选择要扮演的角色/台词                            │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Step 4: 声音克隆 TTS (CosyVoice)                         │
│  ├─ 使用已保存的声音档案                                 │
│  ├─ 为每句台词生成克隆语音                               │
│  └─ 输出: 克隆语音音频文件 (带时间戳)                    │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Step 5: 数字人生成 (EMO)                                 │
│  ├─ 使用已保存的头像档案                                 │
│  ├─ 为克隆语音生成口型同步视频                           │
│  └─ 输出: 数字人视频片段                                 │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Step 6: 音轨合成                                         │
│  ├─ 原始 BGM/环境声 轨道                                 │
│  ├─ 克隆语音轨道 (替换原人声)                            │
│  └─ (可选) 保留其他角色原声                              │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Step 7: 视频合成 (IMS)                                   │
│  ├─ 原始视频 (静音)                                      │
│  ├─ 合成后的音轨                                         │
│  └─ 数字人视频 (画中画, 右下角)                          │
└─────────────────────────────────────────────────────────┘
    │
    ▼
最终成片: 带克隆声音和数字人的故事 MP4
```

---

## 三、技术方案分析

### 3.1 可用的阿里云服务

| 服务 | 功能 | API状态 |
|------|------|---------|
| IMS 智能媒体服务 | 视频分离/合成/剪辑 | 可用 |
| CosyVoice | 声音克隆 + TTS | 可用 (已集成) |
| EMO 悦动人像 | 数字人视频生成 | 可用 (已集成) |
| Paraformer ASR | 语音识别 + 时间戳 | 可用 |
| 智能语音交互 | 说话人识别 | 可用 |

### 3.2 需要外部服务的功能

| 功能 | 推荐方案 | 备选方案 |
|------|----------|----------|
| 人声/背景音分离 | Spleeter (开源) | 阿里云云市场 API |
| 多说话人分离 | pyannote-audio | 阿里云 ASR 角色标注 |

---

## 四、技术难点与解决方案

### 4.1 人声与背景音分离

**难点**: 阿里云没有原生的人声/背景音分离服务

**解决方案**:
1. **方案A: 使用 Spleeter (推荐)**
   - Deezer 开源的音频分离工具
   - 支持 2/4/5 轨道分离 (vocals, drums, bass, piano, other)
   - 可本地部署或使用云服务
   ```python
   # 安装
   pip install spleeter

   # 使用
   from spleeter.separator import Separator
   separator = Separator('spleeter:2stems')  # 2轨: vocals + accompaniment
   separator.separate_to_file('audio.mp3', 'output/')
   ```

2. **方案B: 阿里云云市场 API**
   - 地址: https://market.aliyun.com/detail/cmapi00047539
   - 付费服务，按次计费

### 4.2 多说话人识别与分离

**难点**: 如何识别视频中的不同角色 (旁白、角色A、角色B)

**解决方案**:
1. **方案A: 阿里云 ASR 角色标注**
   - Paraformer 模型支持返回说话人角色标签
   - 但只能区分不同角色，无法识别具体身份
   - 需要用户手动标注角色身份

2. **方案B: pyannote-audio (推荐)**
   - 开源的说话人分离工具
   - 支持说话人分割 (speaker diarization)
   - 可识别"谁在什么时候说话"
   ```python
   from pyannote.audio import Pipeline
   pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
   diarization = pipeline("audio.wav")

   for turn, _, speaker in diarization.itertracks(yield_label=True):
       print(f"{turn.start:.1f}s - {turn.end:.1f}s: {speaker}")
   ```

3. **方案C: 简化处理**
   - 假设视频只有一个主要讲述者
   - 用户选择替换全部人声或保留原声

### 4.3 音频时间对齐

**难点**: 克隆语音与原视频时间轴对齐

**解决方案**:
1. **基于 SRT 字幕时间戳**
   - ASR 识别后生成带时间戳的 SRT 文件
   - 按时间戳逐句生成克隆语音
   - 用静音填充间隔

2. **语速控制 (SSML)**
   - CosyVoice v3 支持 SSML 标记
   - 可控制语速快慢以匹配时长
   ```xml
   <speak>
     <prosody rate="90%">稍慢一点的语速</prosody>
   </speak>
   ```

3. **音频拉伸 (Time Stretching)**
   - 使用 librosa/pyrubberband 调整音频时长
   - 不改变音调的情况下调整语速

### 4.4 数字人视频长度限制

**难点**: EMO 每次生成视频最长 60 秒，长故事需要分段

**解决方案**:
1. **分段生成**
   - 将克隆音频按 60 秒分段
   - 分别生成数字人视频
   - 最后拼接成完整视频

2. **画中画位置保持一致**
   - 所有分段使用相同的头像和 bbox
   - 确保数字人位置不跳动

---

## 五、数据库设计

### 5.1 故事处理任务表 (story_jobs)

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  story_id: ObjectId,              // 原始故事 ID
  voice_profile_id: ObjectId,      // 声音档案 ID
  avatar_profile_id: ObjectId,     // 头像档案 ID

  // 状态
  status: String,                  // pending, processing, completed, failed
  progress: Number,                // 0-100
  current_step: String,            // 当前步骤名称

  // 输入
  original_video_url: String,
  selected_role: String,           // 用户选择的角色 (如有多角色)

  // 中间产物
  muted_video_url: String,         // 静音视频
  original_audio_url: String,      // 原始音频
  bgm_audio_url: String,           // 背景音乐
  vocals_audio_url: String,        // 人声音轨
  subtitle_srt_url: String,        // SRT 字幕文件
  cloned_audio_url: String,        // 克隆语音
  digital_human_video_url: String, // 数字人视频

  // 输出
  final_video_url: String,         // 最终成片

  // 时间
  created_at: Date,
  updated_at: Date,
  completed_at: Date,

  // 错误信息
  error: String
}
```

### 5.2 字幕解析结果 (subtitles)

```javascript
{
  _id: ObjectId,
  job_id: ObjectId,
  index: Number,                   // 字幕序号
  start_time: Number,              // 开始时间 (ms)
  end_time: Number,                // 结束时间 (ms)
  text: String,                    // 字幕文本
  speaker: String,                 // 说话人标签 (如有)
  is_replaced: Boolean             // 是否需要替换
}
```

---

## 六、API 设计

### 6.1 创建故事生成任务

```
POST /api/v1/story-generation/jobs
```

**请求体**:
```json
{
  "story_id": "string",           // 故事 ID
  "voice_profile_id": "string",   // 声音档案 ID
  "avatar_profile_id": "string",  // 头像档案 ID
  "replace_all_voice": true       // 是否替换全部人声
}
```

**响应**:
```json
{
  "code": 0,
  "data": {
    "job_id": "string",
    "status": "pending"
  }
}
```

### 6.2 查询任务状态

```
GET /api/v1/story-generation/jobs/{job_id}
```

**响应**:
```json
{
  "code": 0,
  "data": {
    "job_id": "string",
    "status": "processing",
    "progress": 45,
    "current_step": "generating_cloned_audio",
    "final_video_url": null
  }
}
```

### 6.3 获取字幕预览 (用于角色选择)

```
GET /api/v1/story-generation/jobs/{job_id}/subtitles
```

**响应**:
```json
{
  "code": 0,
  "data": {
    "subtitles": [
      {
        "index": 1,
        "start_time": 0,
        "end_time": 3500,
        "text": "很久很久以前...",
        "speaker": "narrator"
      },
      {
        "index": 2,
        "start_time": 4000,
        "end_time": 6500,
        "text": "小红帽，你好！",
        "speaker": "character_a"
      }
    ]
  }
}
```

---

## 七、实现优先级

### Phase 1: MVP (最小可行产品)

**简化假设**:
- 视频只有单一讲述者
- 替换全部人声
- 不做人声/BGM 分离 (直接用克隆语音覆盖)

**实现步骤**:
1. ASR 语音识别生成 SRT 字幕
2. CosyVoice 按字幕生成克隆语音
3. EMO 生成数字人视频 (分段)
4. IMS 合成最终视频

### Phase 2: 增强版

**新增功能**:
- 人声/BGM 分离
- 克隆语音 + 原 BGM 混合

### Phase 3: 完整版

**新增功能**:
- 多说话人识别
- 角色选择
- 保留其他角色原声

---

## 八、成本估算

| 服务 | 单价 | 预估用量/10分钟视频 | 成本 |
|------|------|---------------------|------|
| ASR Paraformer | ~0.2元/分钟 | 10分钟 | 2元 |
| CosyVoice TTS | 2元/万字符 | ~5000字符 | 1元 |
| EMO 视频生成 | 0.08元/秒 | 600秒 | 48元 |
| IMS 视频合成 | ~0.1元/分钟 | 10分钟 | 1元 |
| **总计** | | | **~52元** |

注: EMO 成本最高，可考虑:
- 只在关键台词时显示数字人
- 降低数字人视频长度

---

## 九、依赖安装

```bash
# 阿里云 SDK
pip install dashscope                    # CosyVoice + EMO
pip install aliyun-python-sdk-ice        # IMS
pip install oss2                         # OSS 文件存储

# 音频处理
pip install spleeter                     # 人声分离
pip install pydub                        # 音频处理
pip install librosa                      # 音频分析

# 说话人分离 (可选)
pip install pyannote.audio               # 说话人分割
pip install torch torchaudio             # PyTorch 依赖
```

---

## 十、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| EMO 并发限制 (1个任务) | 长时间排队 | 分时段处理，显示排队进度 |
| CosyVoice 语速不匹配 | 音画不同步 | SSML 语速调节 + 时间拉伸 |
| 人声分离效果不佳 | BGM 残留 | 使用多模型对比选最佳 |
| 长视频处理超时 | 任务失败 | 分段处理 + 断点续传 |

---

## 十一、参考资源

- [阿里云 IMS 文档](https://help.aliyun.com/zh/ims/)
- [CosyVoice API](https://help.aliyun.com/zh/model-studio/cosyvoice-clone-api)
- [EMO API](https://help.aliyun.com/zh/model-studio/emo-quick-start)
- [Paraformer ASR](https://help.aliyun.com/zh/model-studio/paraformer-speech-recognition/)
- [Spleeter GitHub](https://github.com/deezer/spleeter)
- [pyannote-audio](https://github.com/pyannote/pyannote-audio)

---

**文档版本**: v1.0
**创建日期**: 2025-12-27
**作者**: Claude Code
