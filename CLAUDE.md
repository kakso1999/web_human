# Echobot 项目开发规范

> 最后更新: 2026-01-26

## 一、项目概述

Echobot 是一个儿童动画故事平台，支持声音克隆、数字头像生成、视频处理等 AI 功能。

**技术栈:**
- 后端: FastAPI + Python 3.11+ + MongoDB + Redis
- 前端: Vue 3 + TypeScript + Vite
- AI 服务: APIMart (Whisper + Gemini) + 阿里云 (CosyVoice + EMO)

---

## 二、系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              客户端层                                    │
├─────────────────────────────────┬───────────────────────────────────────┤
│        用户端 (Vue 3)            │         管理端 (Vue 3)                │
│    frontend-user :3001          │     frontend-admin :3000              │
└─────────────────────────────────┴───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           API 网关层                                     │
│                    FastAPI :8000 /api/v1                                │
├─────────────────────────────────────────────────────────────────────────┤
│  认证中间件 (JWT) │ 请求日志 │ 错误处理 │ CORS                           │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            业务模块层                                    │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────────────┤
│   auth   │   user   │  story   │  voice   │ digital  │ story_gen       │
│  认证    │   用户   │  故事    │  克隆    │  人头像  │ 视频生成        │
├──────────┴──────────┴──────────┴──────────┴──────────┴─────────────────┤
│                     audiobook (有声书) │ admin (管理)                   │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
┌─────────────────────┐ ┌─────────────┐ ┌─────────────────────────────────┐
│    数据存储层        │ │  缓存层     │ │         外部 AI 服务             │
├─────────────────────┤ ├─────────────┤ ├─────────────────────────────────┤
│  MongoDB            │ │  Redis      │ │ APIMart (Whisper + Gemini)      │
│  - users            │ │  - session  │ │ 阿里云 (CosyVoice + EMO)        │
│  - stories          │ │  - cache    │ │ 本地 (SpeechT5 + FFmpeg)        │
│  - profiles         │ │  - queue    │ │ 图床 (媒体托管)                  │
│  - jobs             │ └─────────────┘ └─────────────────────────────────┘
└─────────────────────┘
```

### 2.2 业务流程图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          管理端: 故事上传流程                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  上传视频 ──► 提取音频 ──► APIMart Whisper ──► 词级字幕                  │
│                               │                                         │
│                               ▼                                         │
│                      APIMart Gemini 分析                                │
│                               │                                         │
│              ┌────────────────┼────────────────┐                        │
│              ▼                ▼                ▼                        │
│         识别说话人       生成标题简介      双人配音方案                   │
│              │                │                │                        │
│              └────────────────┴────────────────┘                        │
│                               │                                         │
│                               ▼                                         │
│                      存储到 MongoDB (stories)                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          用户端: 声音档案创建                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  上传参考音频 (10s) ──► 本地 SpeechT5 克隆 ──► 生成预览音频              │
│        │                                            │                   │
│        │                                            ▼                   │
│        │                                      用户试听确认               │
│        │                                            │                   │
│        ▼                                            ▼                   │
│   上传到图床 ◄──────────────────────────────── 保存声音档案              │
│   (供阿里云使用)                              (voice_profiles)           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          用户端: 故事生成流程                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  选择故事 + 声音档案 + 头像档案 + 配音模式                               │
│                    │                                                    │
│                    ▼                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 按字幕分段 (每段 ≤ 48s)                                          │   │
│  │                                                                  │   │
│  │  段落1  ──► CosyVoice 克隆 ──► EMO 数字人 ──► 画中画合成         │   │
│  │  段落2  ──► CosyVoice 克隆 ──► EMO 数字人 ──► 画中画合成         │   │
│  │  段落N  ──► CosyVoice 克隆 ──► EMO 数字人 ──► 画中画合成         │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                    │                                                    │
│                    ▼                                                    │
│           FFmpeg 拼接所有段落                                           │
│                    │                                                    │
│                    ▼                                                    │
│              最终视频 URL                                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 完整目录结构

```
echobot/
│
├── app/                                # 应用入口
│   ├── __init__.py
│   └── main.py                         # FastAPI 启动入口，注册所有路由
│
├── core/                               # 核心模块 (共享基础设施)
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                 # 环境配置 (Pydantic Settings)
│   │   └── database.py                 # MongoDB 连接配置
│   │
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth.py                     # JWT 认证中间件
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── base.py                     # 基础响应模型 (success_response)
│   │   └── pagination.py               # 分页模型
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   └── mongodb.py                  # MongoDB 客户端单例
│   │
│   ├── exceptions/
│   │   └── handlers.py                 # 全局异常处理
│   │
│   ├── security/
│   │   ├── jwt.py                      # JWT Token 处理
│   │   └── password.py                 # 密码加密 (bcrypt)
│   │
│   └── utils/
│       ├── __init__.py
│       ├── helpers.py                  # 通用工具函数
│       └── apimart_client.py           # APIMart API 客户端
│
├── modules/                            # 业务模块
│   │
│   ├── auth/                           # 认证模块
│   │   ├── __init__.py
│   │   ├── router.py                   # 路由: /api/v1/auth
│   │   ├── schemas.py                  # LoginRequest, AuthResponse
│   │   ├── service.py                  # 登录/注册/OAuth 逻辑
│   │   └── repository.py               # 用户数据访问
│   │
│   ├── user/                           # 用户模块
│   │   ├── __init__.py
│   │   ├── router.py                   # 路由: /api/v1/user
│   │   ├── schemas.py                  # UserProfile, UpdateRequest
│   │   ├── service.py                  # 个人信息管理
│   │   └── repository.py
│   │
│   ├── story/                          # 故事模块
│   │   ├── __init__.py
│   │   ├── router.py                   # 路由: /api/v1/stories
│   │   ├── schemas.py                  # Story, Category
│   │   ├── service.py                  # 故事 CRUD
│   │   ├── repository.py
│   │   ├── analysis_service.py         # APIMart 分析服务
│   │   └── analysis_queue.py           # 分析任务队列
│   │
│   ├── voice_clone/                    # 声音克隆模块
│   │   ├── __init__.py
│   │   ├── router.py                   # 路由: /api/v1/voice_clone
│   │   ├── schemas.py                  # VoiceProfile, TaskStatus
│   │   ├── base.py                     # 抽象基类
│   │   ├── factory.py                  # 服务工厂
│   │   ├── local_service.py            # 本地服务 (SpeechT5)
│   │   ├── cloud_service.py            # 云端服务 (CosyVoice)
│   │   ├── repository.py
│   │   └── preset_stories.py           # 预设朗读故事
│   │
│   ├── digital_human/                  # 数字人模块
│   │   ├── __init__.py
│   │   ├── router.py                   # 路由: /api/v1/digital_human
│   │   ├── schemas.py                  # AvatarProfile, TaskStatus
│   │   ├── base.py                     # 抽象基类
│   │   ├── factory.py                  # 服务工厂
│   │   ├── local_service.py            # 本地服务 (FFmpeg)
│   │   ├── cloud_service.py            # 云端服务 (EMO)
│   │   └── repository.py
│   │
│   ├── story_generation/               # 故事生成模块
│   │   ├── __init__.py
│   │   ├── router.py                   # 路由: /api/v1/story_generation
│   │   ├── schemas.py                  # CreateJobRequest, SpeakerConfig
│   │   ├── service.py                  # 生成流程编排
│   │   └── repository.py
│   │
│   ├── audiobook/                      # 有声书模块
│   │   ├── __init__.py
│   │   ├── router.py                   # 路由: /api/v1/audiobook
│   │   ├── schemas.py                  # AudiobookJob, UserEbook
│   │   ├── service.py                  # TTS 生成有声书
│   │   └── repository.py
│   │
│   └── admin/                          # 管理后台模块
│       ├── __init__.py
│       └── router.py                   # 路由: /api/v1/admin
│
├── frontend-user/                      # 用户端前端 (Vue 3)
│   ├── src/
│   │   ├── api/
│   │   │   ├── http.ts                 # Axios 封装
│   │   │   └── index.ts                # API 定义
│   │   ├── components/                 # 公共组件
│   │   ├── views/                      # 页面视图
│   │   │   ├── Home.vue                # 首页/落地页
│   │   │   ├── Login.vue               # 登录
│   │   │   ├── Register.vue            # 注册
│   │   │   ├── Dashboard.vue           # 故事列表
│   │   │   ├── Studio.vue              # 故事生成工作台
│   │   │   ├── VoiceClone.vue          # 声音克隆
│   │   │   ├── DigitalHuman.vue        # 数字人创建
│   │   │   ├── Account.vue             # 账户设置
│   │   │   ├── VoiceProfiles.vue       # 声音档案管理
│   │   │   ├── AvatarProfiles.vue      # 头像档案管理
│   │   │   └── MyCreations.vue         # 我的作品
│   │   ├── stores/                     # Pinia 状态
│   │   │   └── user.ts                 # 用户状态
│   │   ├── router/                     # Vue Router
│   │   └── styles/                     # 样式文件
│   ├── package.json
│   └── vite.config.ts
│
├── frontend-admin/                     # 管理端前端 (Vue 3)
│   ├── src/
│   │   ├── api/
│   │   ├── views/
│   │   │   ├── Login.vue               # 管理员登录
│   │   │   ├── Dashboard.vue           # 数据概览
│   │   │   ├── Users.vue               # 用户管理
│   │   │   ├── Stories.vue             # 故事管理
│   │   │   ├── StoryEdit.vue           # 故事编辑/上传
│   │   │   └── Categories.vue          # 分类管理
│   │   └── ...
│   └── package.json
│
├── scripts/                            # 运维脚本
│   ├── check_jobs.py                   # 检查任务状态
│   ├── fix_jobs.py                     # 修复失败任务
│   └── ...
│
├── tests/                              # 测试文件
│   └── test_*.py
│
├── uploads/                            # 文件存储 (开发环境)
│   ├── videos/                         # 故事视频
│   ├── voice/                          # 声音文件
│   ├── avatar/                         # 头像文件
│   └── generated/                      # 生成的视频
│
├── pretrained_models/                  # 本地模型
│   └── spkrec-xvect-voxceleb/          # SpeechBrain 说话人模型
│
├── CLAUDE.md                           # 项目规范文档 (本文件)
├── requirements.txt                    # Python 依赖
├── .env                                # 环境变量
└── docker-compose.yml                  # Docker 配置
```

### 2.4 前端页面结构

```
用户端路由 (frontend-user)
├── /                   → Home.vue           # 落地页 (深色背景 + 粒子动画)
├── /login              → Login.vue          # 登录
├── /register           → Register.vue       # 注册
├── /dashboard          → Dashboard.vue      # 故事列表 (需登录)
├── /story/:id          → StoryDetail.vue    # 故事详情/播放
├── /studio             → Studio.vue         # 故事生成工作台
├── /voice-clone        → VoiceClone.vue     # 声音克隆
├── /digital-human      → DigitalHuman.vue   # 数字人创建
├── /account            → Account.vue        # 账户设置
├── /voice-profiles     → VoiceProfiles.vue  # 声音档案管理
├── /avatar-profiles    → AvatarProfiles.vue # 头像档案管理
└── /my-creations       → MyCreations.vue    # 我的作品

管理端路由 (frontend-admin)
├── /login              → Login.vue          # 管理员登录
├── /                   → Dashboard.vue      # 数据概览
├── /users              → Users.vue          # 用户管理
├── /stories            → Stories.vue        # 故事列表
├── /stories/create     → StoryEdit.vue      # 创建故事
├── /stories/:id/edit   → StoryEdit.vue      # 编辑故事
└── /categories         → Categories.vue     # 分类管理
```

---

## 三、API 接口文档

> 所有接口前缀: `/api/v1`
> 需要认证的接口在 Header 中传递: `Authorization: Bearer {access_token}`

### 3.1 认证模块 (`/auth`)

| 方法 | 路径 | 功能 | 认证 | 请求参数 |
|------|------|------|------|----------|
| POST | `/auth/login` | 用户登录 | 否 | `{email, password}` |
| POST | `/auth/register` | 用户注册 | 否 | `{email, password, nickname}` |
| POST | `/auth/refresh` | 刷新令牌 | 否 | `{refresh_token}` |
| POST | `/auth/logout` | 退出登录 | 是 | - |
| GET | `/auth/google/url` | 获取 Google OAuth URL | 否 | - |
| POST | `/auth/google` | Google 登录回调 | 否 | `{code}` |
| GET | `/auth/admin/check` | 检查管理员是否存在 | 否 | - |
| POST | `/auth/admin/init` | 初始化管理员 | 否 | - |

**文件位置:** `modules/auth/router.py`

---

### 3.2 用户模块 (`/user`)

| 方法 | 路径 | 功能 | 认证 | 请求参数 |
|------|------|------|------|----------|
| GET | `/user/profile` | 获取用户信息 | 是 | - |
| PUT | `/user/profile` | 更新用户信息 | 是 | `{nickname}` |
| POST | `/user/avatar` | 上传头像 | 是 | FormData: `file` |
| POST | `/user/change-password` | 修改密码 | 是 | `{old_password, new_password}` |

**文件位置:** `modules/user/router.py`

---

### 3.3 故事模块 (`/stories`)

| 方法 | 路径 | 功能 | 认证 | 请求参数 |
|------|------|------|------|----------|
| GET | `/stories/categories` | 获取故事分类 | 否 | - |
| GET | `/stories` | 获取故事列表 | 否 | Query: `page, page_size, category_id, search` |
| GET | `/stories/random` | 获取随机故事 | 否 | Query: `limit` |
| GET | `/stories/{id}` | 获取故事详情 | 否 | - |
| POST | `/stories/{id}/view` | 记录播放 | 否 | - |
| POST | `/stories` | 创建故事 (管理员) | 是 | FormData: `video, thumbnail, title...` |
| PUT | `/stories/{id}` | 更新故事 | 是 | `{title, is_published...}` |
| DELETE | `/stories/{id}` | 删除故事 | 是 | - |

**文件位置:** `modules/story/router.py`

**故事上传自动触发分析流程:**
1. APIMart Whisper-1 提取字幕
2. APIMart Gemini 分析说话人
3. 生成双人配音方案

---

### 3.4 声音克隆模块 (`/voice_clone`)

| 方法 | 路径 | 功能 | 认证 | 请求参数 |
|------|------|------|------|----------|
| GET | `/voice_clone/preset-stories` | 获取预设故事 | 否 | - |
| POST | `/voice_clone/preview` | 创建克隆预览 | 是 | FormData: `audio, story_id` |
| GET | `/voice_clone/preview/{task_id}` | 获取预览状态 | 是 | - |
| GET | `/voice_clone/profiles` | 获取声音档案列表 | 是 | - |
| GET | `/voice_clone/profiles/{id}` | 获取档案详情 | 是 | - |
| POST | `/voice_clone/profiles` | 保存声音档案 | 是 | `{task_id, name}` |
| PUT | `/voice_clone/profiles/{id}` | 更新档案名称 | 是 | `{name}` |
| DELETE | `/voice_clone/profiles/{id}` | 删除档案 | 是 | - |

**文件位置:** `modules/voice_clone/router.py`

**声音克隆流程:**
1. 用户上传参考音频 (10-15秒)
2. 本地 SpeechT5 生成预览 (知识产权保护)
3. 用户确认后保存档案
4. 故事生成时使用阿里云 CosyVoice 克隆

---

### 3.5 数字人模块 (`/digital_human`)

| 方法 | 路径 | 功能 | 认证 | 请求参数 |
|------|------|------|------|----------|
| POST | `/digital_human/preview` | 创建数字人预览 | 是 | FormData: `image, audio?, voice_profile_id?, preview_text?` |
| GET | `/digital_human/preview/{task_id}` | 获取预览状态 | 是 | - |
| GET | `/digital_human/profiles` | 获取头像档案列表 | 是 | - |
| GET | `/digital_human/profiles/{id}` | 获取档案详情 | 是 | - |
| POST | `/digital_human/profiles` | 保存头像档案 | 是 | `{task_id, name}` |
| PUT | `/digital_human/profiles/{id}` | 更新档案名称 | 是 | `{name}` |
| DELETE | `/digital_human/profiles/{id}` | 删除档案 | 是 | - |

**文件位置:** `modules/digital_human/router.py`

**音频来源 (三选一):**
1. 不传音频 → 使用默认音色
2. 传 `audio` 文件 → 使用上传的音频
3. 传 `voice_profile_id + preview_text` → 使用声音档案克隆

---

### 3.6 故事生成模块 (`/story_generation`)

| 方法 | 路径 | 功能 | 认证 | 请求参数 |
|------|------|------|------|----------|
| GET | `/story_generation/speakers/{story_id}` | 获取说话人信息 | 是 | - |
| POST | `/story_generation/analyze/{story_id}` | 触发分析 (已废弃) | 是 | Query: `num_speakers?` |
| POST | `/story_generation/subtitles/{story_id}` | 获取字幕 | 是 | Query: `force?` |
| GET | `/story_generation/subtitles/{story_id}` | 获取字幕 | 是 | Query: `speaker_id?` |
| POST | `/story_generation/jobs` | 创建生成任务 | 是 | `{story_id, speaker_configs?, voice_profile_id?, avatar_profile_id?, full_video?}` |
| GET | `/story_generation/jobs` | 获取任务列表 | 是 | Query: `page, page_size` |
| GET | `/story_generation/jobs/{id}` | 获取任务详情 | 是 | - |
| GET | `/story_generation/jobs/{id}/status` | 获取任务状态 | 是 | - |

**文件位置:** `modules/story_generation/router.py`

**创建任务请求示例:**
```json
{
  "story_id": "xxx",
  "speaker_configs": [
    {"speaker_id": "VOICE_1", "voice_profile_id": "aaa", "avatar_profile_id": "bbb", "enabled": true},
    {"speaker_id": "VOICE_2", "voice_profile_id": "ccc", "avatar_profile_id": "ddd", "enabled": true}
  ],
  "full_video": true
}
```

**任务状态:** `pending` → `processing` → `completed` / `failed`

---

### 3.7 有声书模块 (`/audiobook`)

| 方法 | 路径 | 功能 | 认证 | 请求参数 |
|------|------|------|------|----------|
| GET | `/audiobook/stories` | 获取故事模板 | 是 | Query: `page, page_size, language, category, age_group` |
| GET | `/audiobook/stories/{id}` | 获取模板详情 | 是 | - |
| POST | `/audiobook/jobs` | 创建有声书任务 | 是 | `{story_id, voice_profile_id}` |
| GET | `/audiobook/jobs` | 获取任务列表 | 是 | Query: `page, page_size` |
| GET | `/audiobook/jobs/{id}` | 获取任务详情 | 是 | - |
| DELETE | `/audiobook/jobs/{id}` | 删除任务 | 是 | - |
| POST | `/audiobook/jobs/{id}/favorite` | 收藏/取消收藏 | 是 | - |
| GET | `/audiobook/ebooks` | 获取用户电子书 | 是 | Query: `page, page_size` |
| POST | `/audiobook/ebooks` | 创建电子书 | 是 | `{title, content, language?}` |
| GET | `/audiobook/ebooks/{id}` | 获取电子书详情 | 是 | - |
| PUT | `/audiobook/ebooks/{id}` | 更新电子书 | 是 | `{title?, content?, language?}` |
| DELETE | `/audiobook/ebooks/{id}` | 删除电子书 | 是 | - |
| POST | `/audiobook/ebooks/{id}/jobs` | 从电子书创建任务 | 是 | `{voice_profile_id}` |

**文件位置:** `modules/audiobook/router.py`

---

### 3.8 管理后台模块 (`/admin`)

| 方法 | 路径 | 功能 | 认证 | 请求参数 |
|------|------|------|------|----------|
| GET | `/admin/dashboard` | 获取统计数据 | 是(管理员) | - |
| GET | `/admin/users` | 获取用户列表 | 是(管理员) | Query: `page, page_size, search` |
| PUT | `/admin/users/{id}` | 更新用户 | 是(管理员) | `{role, is_active}` |

**文件位置:** `modules/admin/router.py`

---

## 四、数据模型 (MongoDB)

### 4.1 核心集合

| 集合 | 用途 | 关键字段 |
|------|------|----------|
| `users` | 用户信息 | `email, password_hash, role, subscription` |
| `stories` | 故事 | `title, video_url, is_analyzed, speakers, subtitles, ai_analysis` |
| `voice_profiles` | 声音档案 | `user_id, name, voice_id, reference_audio_url, preview_audio_url` |
| `avatar_profiles` | 头像档案 | `user_id, name, image_url, preview_video_url` |
| `story_generation_jobs` | 生成任务 | `user_id, story_id, speaker_configs, status, final_video_url` |
| `audiobook_jobs` | 有声书任务 | `user_id, story_id, voice_profile_id, status, audio_url` |
| `audiobook_stories` | 有声书模板 | `title, content, language, category` |
| `user_ebooks` | 用户电子书 | `user_id, title, content` |

### 4.2 故事分析字段 (stories 集合)

```javascript
{
  // 基础信息
  title: String,
  video_url: String,
  is_published: Boolean,

  // 分析状态
  is_analyzed: Boolean,
  is_processing: Boolean,
  analysis_error: String,

  // 说话人配置 (VOICE_1, VOICE_2)
  speaker_count: Number,
  speakers: [{
    speaker_id: "VOICE_1",
    label: "Voice 1",
    description: "Narrator, Father",
    duration: 120.5
  }],

  // 字幕 (APIMart Whisper 生成)
  subtitles: [{
    start: 6.8,
    end: 13.2,
    text: "Long long ago...",
    voice: "VOICE_1"
  }],

  // AI 分析结果 (APIMart Gemini 生成)
  ai_analysis: {
    title: "故事标题",
    description: "故事简介",
    original_speakers: [...],
    dual_voice_assignment: {
      VOICE_1: ["NARRATOR", "FATHER"],
      VOICE_2: ["MOTHER", "CHILD"]
    },
    segments: [...]
  }
}
```

---

## 五、AI 服务架构

### 5.1 服务提供商

| 服务 | 提供商 | API/模型 | 用途 |
|------|--------|----------|------|
| 语音转文字 | APIMart | Whisper-1 | 故事字幕提取 |
| 说话人分析 | APIMart | Gemini-3-Flash | 角色识别和分配 |
| 语音克隆 | 阿里云 | CosyVoice | 故事配音生成 |
| 数字人生成 | 阿里云 | EMO | 口型同步视频 |
| 声音预览 | **本地** | SpeechT5 + SpeechBrain | 声音档案预览 |

### 5.2 环境变量

```bash
# APIMart API
APIMART_API_KEY=sk-xxx

# 阿里云 DashScope
DASHSCOPE_API_KEY=sk-xxx

# 图床服务 (供阿里云访问媒体文件)
MEDIA_BED_URL=http://47.251.179.50
```

### 5.3 API 限制

| 服务 | 限制 |
|------|------|
| CosyVoice | 单次最大 2000 字符 |
| EMO | 单次最大 48 秒音频 |
| 全局 | 最大 5 并发 |

---

## 六、前端 API 调用

前端 API 定义位置: `frontend-user/src/api/index.ts`

```typescript
// 认证
authApi.login(data)
authApi.register(data)

// 用户
userApi.getProfile()
userApi.updateProfile(data)
userApi.uploadAvatar(file)
userApi.changePassword(old, new)

// 故事
storyApi.getCategories()
storyApi.getStories(params)
storyApi.getStory(id)

// 声音克隆
voiceCloneApi.getPresetStories()
voiceCloneApi.createPreview(audio, storyId)
voiceCloneApi.getPreviewStatus(taskId)
voiceCloneApi.getProfiles()
voiceCloneApi.saveProfile(taskId, name)
voiceCloneApi.updateProfile(id, name)
voiceCloneApi.deleteProfile(id)

// 数字人
digitalHumanApi.createPreview(image, options)
digitalHumanApi.getPreviewStatus(taskId)
digitalHumanApi.getProfiles()
digitalHumanApi.saveProfile(taskId, name)
digitalHumanApi.updateProfile(id, name)
digitalHumanApi.deleteProfile(id)

// 故事生成
storyGenerationApi.getSpeakers(storyId)
storyGenerationApi.createJob(data)
storyGenerationApi.getJobs(params)
storyGenerationApi.getJob(id)

// 有声书
audiobookApi.getStories(params)
audiobookApi.createJob(storyId, voiceProfileId)
audiobookApi.getJobs(params)
audiobookApi.getJob(id)
```

---

## 七、开发规范

### 7.1 API 响应格式

```json
// 成功
{"code": 0, "message": "success", "data": {...}}

// 分页
{"code": 0, "message": "success", "data": {"items": [], "total": 100, "page": 1, "page_size": 20}}

// 错误
{"code": 40001, "message": "参数错误", "data": null}
```

### 7.2 路由命名规范

- 使用下划线: `/voice_clone`, `/digital_human`, `/story_generation`
- RESTful 风格
- 列表: `GET /items`
- 详情: `GET /items/{id}`
- 创建: `POST /items`
- 更新: `PUT /items/{id}`
- 删除: `DELETE /items/{id}`

### 7.3 模块结构

```
modules/{module}/
├── __init__.py
├── router.py      # API 路由
├── schemas.py     # Pydantic 模型
├── service.py     # 业务逻辑
├── repository.py  # 数据访问
└── models.py      # MongoDB 模型
```

### 7.4 前端设计规范

- 风格: Apple Design
- 主题: 深色
- 主色: `#2D6B6B`
- 圆角: 12-24px
- 禁止使用 Emoji

---

## 八、部署配置

### 8.1 端口

| 服务 | 端口 |
|------|------|
| 后端 API | 8000 |
| 管理端前端 | 3000 |
| 用户端前端 | 3001 |

### 8.2 启动命令

```bash
# 后端
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend-user && npm run dev
cd frontend-admin && npm run dev
```

### 8.3 初始化管理员

```bash
curl -X POST http://localhost:8000/api/v1/auth/admin/init
# 默认账号: admin@echobot.local / admin123
```

---

## 九、变更记录

### 2026-01-26 重构

**删除:**
- `modules/voice_separation/` - 已被 APIMart API 替代
- `modules/voice_clone/local_tts_service.py` - 未使用
- `modules/voice_clone/worker.py` - 未使用

**移动:**
- 调试脚本从 `tests/` 移动到 `scripts/`

**修改:**
- API 路由从连字符改为下划线 (`/voice-clone` → `/voice_clone`)
- `story_generation` 分析功能重定向到新的分析队列
- 更新 `requirements.txt`: 移除 demucs/pyannote, 添加 transformers/speechbrain

### 当前架构

```
故事上传 → APIMart (Whisper + Gemini) 分析
    ↓
用户选择声音/头像档案
    ↓
故事生成 → 阿里云 (CosyVoice + EMO) + FFmpeg 合成
    ↓
最终视频
```
