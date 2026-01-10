# Echobot 项目开发规范

## 一、项目概述

Echobot 是一个儿童动画故事平台，支持声音克隆、数字头像生成、视频处理等 AI 功能。
项目包含用户网站和管理后台两个前端应用，以及统一的后端服务。

---

## 二、技术栈

| 层级 | 技术选型 |
|------|---------|
| 后端框架 | FastAPI (Python 3.11+) |
| 数据库 | MongoDB |
| 缓存 | Redis |
| 前端框架 | Vue 3 + TypeScript |
| UI 组件 | 自定义组件 (Apple Design 风格) |
| 构建工具 | Vite |

---

## 三、项目目录结构

```
echobot/
│
├── CLAUDE.md                       # 项目规范文档 (本文件)
├── statis/                         # 静态资源 (logo等)
│
├── core/                           # [核心模块 - 共享基础设施]
│   ├── __init__.py
│   ├── config/                     # 配置管理
│   │   ├── settings.py             # 环境配置
│   │   └── database.py             # MongoDB 连接配置
│   │
│   ├── security/                   # 安全组件
│   │   ├── jwt.py                  # JWT 令牌处理
│   │   ├── password.py             # 密码加密 (bcrypt)
│   │   ├── encryption.py           # 数据加密 (AES)
│   │   ├── rate_limiter.py         # 请求限流
│   │   └── signature.py            # 请求签名验证
│   │
│   ├── database/                   # 数据库基础
│   │   ├── mongodb.py              # MongoDB 客户端
│   │   └── base_repository.py      # 仓储基类
│   │
│   ├── middleware/                 # 中间件
│   │   ├── auth.py                 # 认证中间件
│   │   ├── logging.py              # 请求日志
│   │   └── security_headers.py     # 安全响应头
│   │
│   ├── schemas/                    # 公共 Schema
│   │   ├── base.py                 # 基础响应模型
│   │   └── pagination.py           # 分页模型
│   │
│   ├── exceptions/                 # 统一异常处理
│   │   └── handlers.py
│   │
│   └── utils/                      # 公共工具
│       ├── validators.py           # 数据验证器
│       └── helpers.py
│
├── modules/                        # [业务模块 - 独立开发]
│   │
│   ├── auth/                       # 认证模块
│   │   ├── __init__.py
│   │   ├── router.py               # 路由定义
│   │   ├── schemas.py              # 请求/响应模型
│   │   ├── service.py              # 业务逻辑
│   │   ├── repository.py           # 数据访问
│   │   └── dependencies.py         # 模块依赖
│   │
│   ├── user/                       # 用户模块
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── models.py               # MongoDB 文档模型
│   │
│   ├── story/                      # 故事模块
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── models.py
│   │
│   ├── order/                      # 订单模块
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── models.py
│   │
│   ├── voice_clone/                # 声音克隆模块
│   │   ├── __init__.py
│   │   ├── router.py               # 声音克隆 API
│   │   ├── schemas.py
│   │   ├── service.py              # CosyVoice TTS 集成
│   │   ├── repository.py
│   │   └── models.py
│   │
│   ├── digital_human/              # 数字人模块
│   │   ├── __init__.py
│   │   ├── router.py               # 数字人 API
│   │   ├── schemas.py
│   │   ├── service.py              # EMO 悦动人像集成
│   │   ├── repository.py
│   │   └── models.py
│   │
│   ├── story_generation/           # 故事生成模块
│   │   ├── __init__.py
│   │   ├── router.py               # 故事生成 API
│   │   ├── schemas.py
│   │   ├── service.py              # 视频处理 + 合成
│   │   ├── repository.py
│   │   └── models.py
│   │
│   ├── audiobook/                  # 有声书模块
│   │   ├── __init__.py
│   │   ├── router.py               # 有声书 API
│   │   ├── schemas.py
│   │   ├── service.py              # TTS 生成有声书
│   │   ├── repository.py
│   │   └── models.py
│   │
│   └── admin/                      # 管理后台模块
│       ├── __init__.py
│       ├── router.py
│       ├── dashboard/              # 数据统计
│       ├── user_manage/            # 用户管理
│       └── story_manage/           # 故事管理
│
├── app/                            # [应用入口]
│   ├── __init__.py
│   └── main.py                     # FastAPI 启动入口
│
├── tests/                          # 测试 (按模块组织)
│   ├── test_auth/
│   ├── test_user/
│   ├── test_story/
│   └── test_order/
│
├── frontend-user/                  # [用户网站前端]
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── views/
│   │   ├── stores/
│   │   ├── router/
│   │   └── styles/
│   └── package.json
│
├── frontend-admin/                 # [管理后台前端]
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── views/
│   │   ├── stores/
│   │   └── router/
│   └── package.json
│
├── docker-compose.yml
└── requirements.txt
```

---

## 四、模块开发规范

### 4.1 模块独立原则

- 每个业务模块必须完全独立，包含自己的 router/service/repository/schemas
- 模块之间禁止直接 import，必须通过 Core 层或接口约定通信
- 每个模块可由不同开发者独立开发

### 4.2 模块内部结构

```
modules/{module_name}/
├── __init__.py          # 导出 router
├── router.py            # API 路由定义
├── schemas.py           # Pydantic 请求/响应模型
├── service.py           # 业务逻辑层
├── repository.py        # 数据访问层 (操作 MongoDB)
├── models.py            # MongoDB 文档结构定义
└── dependencies.py      # 模块专用依赖注入
```

### 4.3 API 路由规范

- 前缀: `/api/v1/{module}`
- RESTful 风格
- 统一响应格式

---

## 五、安全架构

### 5.1 认证机制

- 双 Token 机制: Access Token (15分钟) + Refresh Token (7天)
- Access Token 存放于请求 Header
- Refresh Token 存放于 HttpOnly Cookie

### 5.2 权限控制 (RBAC)

| 角色 | 说明 |
|------|------|
| user | 普通用户 |
| subscriber | 订阅用户 |
| admin | 管理员 |
| super | 超级管理员 |

### 5.3 数据安全

- 密码: bcrypt 哈希
- 敏感数据: AES-256 加密
- 请求签名: HMAC-SHA256 验证
- 限流: 滑动窗口算法

### 5.4 永远不要信任前端数据

- 所有输入必须经过 Pydantic Schema 验证
- 类型检查、长度限制、正则匹配
- 防 SQL 注入、XSS、路径遍历

---

## 六、MongoDB 集合设计

### 6.1 users 集合

```javascript
{
  _id: ObjectId,
  email: String,           // unique
  password_hash: String,
  nickname: String,
  role: String,            // enum: user, subscriber, admin, super
  subscription: {
    plan: String,          // enum: free, basic, premium
    expires_at: Date
  },
  is_active: Boolean,
  created_at: Date,
  updated_at: Date
}
```

### 6.2 stories 集合

```javascript
{
  _id: ObjectId,
  title: String,
  title_en: String,
  category_id: ObjectId,
  thumbnail_url: String,
  video_url: String,
  duration: Number,
  is_published: Boolean,
  view_count: Number,
  created_at: Date,
  updated_at: Date
}
```

### 6.3 categories 集合

```javascript
{
  _id: ObjectId,
  name: String,
  name_en: String,
  sort_order: Number,
  story_count: Number
}
```

### 6.4 orders 集合

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  plan: String,            // enum: basic, premium
  amount: Number,
  currency: String,
  status: String,          // enum: pending, paid, failed, refunded
  payment_method: String,
  payment_id: String,
  created_at: Date
}
```

### 6.5 audit_logs 集合

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  action: String,
  resource: String,
  resource_id: ObjectId,
  ip_address: String,
  user_agent: String,
  details: Object,
  created_at: Date
}
```

### 6.6 voice_profiles 集合 (声音档案)

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  name: String,              // 声音名称，如：爸爸的声音
  voice_id: String,          // CosyVoice 返回的 voice_id
  reference_audio_url: String, // 参考音频 URL
  preview_audio_url: String, // 预览音频 URL
  created_at: Date,
  updated_at: Date
}
```

### 6.7 avatar_profiles 集合 (头像档案)

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  name: String,              // 头像名称，如：爸爸的头像
  image_url: String,         // 原始头像图片 URL
  preview_video_url: String, // 预览视频 URL
  face_bbox: [Number],       // 人脸检测框 [x1, y1, x2, y2]
  ext_bbox: [Number],        // 扩展框
  created_at: Date,
  updated_at: Date
}
```

### 6.8 audiobook_stories 集合 (有声书故事模板)

```javascript
{
  _id: ObjectId,
  title: String,              // 故事标题 (中文)
  title_en: String,           // 英文标题
  content: String,            // 故事全文
  language: String,           // "en" | "zh"
  category: String,           // "fairy_tale" | "fable" | "adventure"
  age_group: String,          // "3-5" | "5-8" | "8-12"
  estimated_duration: Number, // 预估时长(秒)
  thumbnail_url: String,      // 封面图
  background_music_url: String, // 可选背景音乐
  is_published: Boolean,
  sort_order: Number,
  created_at: Date,
  updated_at: Date
}
```

### 6.9 audiobook_jobs 集合 (有声书生成任务)

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  story_id: ObjectId,
  voice_profile_id: ObjectId,
  status: String,             // pending | processing | completed | failed
  progress: Number,           // 0-100
  current_step: String,       // init | tts | mixing | completed
  audio_url: String,          // 最终音频 URL
  duration: Number,           // 实际时长
  story_title: String,        // 缓存标题
  voice_name: String,         // 缓存声音名称
  created_at: Date,
  completed_at: Date,
  error: String
}
```

### 6.10 story_generation_jobs 集合 (故事生成任务)

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  story_id: ObjectId,
  voice_profile_id: ObjectId,
  avatar_profile_id: ObjectId,
  status: String,             // pending | processing | completed | failed
  progress: Number,           // 0-100
  current_step: String,       // extracting | separating | transcribing | cloning | generating | composing
  replace_all_voice: Boolean, // 是否替换全部人声
  full_video: Boolean,        // 是否生成完整视频
  segments: Array,            // 分段信息
  final_video_url: String,    // 最终视频 URL
  created_at: Date,
  completed_at: Date,
  error: String
}
```

---

## 七、API 接口规范

### 7.1 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": { }
}
```

### 7.2 分页响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

### 7.3 错误响应格式

```json
{
  "code": 40001,
  "message": "参数验证失败",
  "data": null
}
```

---

## 八、前端设计规范

### 8.1 设计风格

- **风格**: Apple Design 风格，丝滑圆润
- **圆角**: 大圆角设计 (12px - 24px)
- **阴影**: 柔和阴影，营造层次感
- **动画**: 流畅过渡动画 (0.2s - 0.3s ease)
- **间距**: 充足留白，呼吸感

### 8.2 禁止事项

- **禁止使用 Emoji**
- 禁止使用过于鲜艳的颜色
- 禁止使用尖锐的边角

### 8.3 主色调 (基于 Logo)

```css
:root {
  /* 主色 - 深青色 (Logo 背景色) */
  --color-primary: #2D6B6B;
  --color-primary-light: #3D7B7B;
  --color-primary-dark: #1D5B5B;

  /* 辅助色 - 米色 (Logo 文字色) */
  --color-secondary: #E8E4D4;
  --color-secondary-light: #F5F2E8;
  --color-secondary-dark: #D8D4C4;

  /* 中性色 */
  --color-text-primary: #1A1A1A;
  --color-text-secondary: #666666;
  --color-text-muted: #999999;

  /* 背景色 */
  --color-bg-primary: #FFFFFF;
  --color-bg-secondary: #F8F8F8;
  --color-bg-tertiary: #F0F0F0;

  /* 边框色 */
  --color-border: #E5E5E5;
  --color-border-light: #F0F0F0;

  /* 状态色 */
  --color-success: #34C759;
  --color-warning: #FF9500;
  --color-error: #FF3B30;
  --color-info: #007AFF;
}
```

### 8.4 字体规范

```css
:root {
  /* 字体家族 */
  --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                 'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei',
                 sans-serif;

  /* 字号 */
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-base: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 20px;
  --font-size-2xl: 24px;
  --font-size-3xl: 30px;

  /* 字重 */
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
}
```

### 8.5 间距规范

```css
:root {
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-2xl: 48px;
  --spacing-3xl: 64px;
}
```

### 8.6 圆角规范

```css
:root {
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --radius-full: 9999px;
}
```

### 8.7 阴影规范

```css
:root {
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.15);
}
```

---

## 九、页面设计规范

### 9.1 用户端页面结构

```
用户端 (frontend-user)
│
├── Landing Page (首页/落地页)         # 路由: /
│   ├── 深色背景 + 粒子/星空动画特效
│   ├── Logo + 标语 "AI驱动的数字人动画平台"
│   ├── "点击进入" 按钮 (圆角胶囊形)
│   └── 底部 3D 故事轮播图 (立体旋转木马效果)
│
├── 登录页面                           # 路由: /login
│   ├── 邮箱 + 密码登录表单
│   ├── Google 账号登录按钮
│   ├── 注册链接
│   └── 忘记密码链接
│
├── 注册页面                           # 路由: /register
│   ├── 邮箱输入
│   ├── 密码输入 (含强度提示)
│   ├── 确认密码
│   └── 邮箱验证码
│
├── 主界面 (登录后)                    # 路由: /dashboard
│   ├── 左侧边栏 (固定宽度 200px)
│   │   ├── Logo
│   │   ├── 故事库管理
│   │   ├── 上传照片
│   │   ├── 上传音频
│   │   └── 生成动画
│   │
│   ├── 顶部栏
│   │   └── 右侧: 用户头像 + 用户名 (点击展开下拉菜单)
│   │
│   └── 主内容区
│       └── 故事卡片网格 (响应式布局)
│           ├── 缩略图 (16:9)
│           ├── 视频时长标签 (右下角)
│           └── 故事标题
│
├── 个人信息页面                       # 路由: /profile
│   ├── 头像上传/修改
│   ├── 用户名修改
│   ├── 邮箱 (只读)
│   ├── 密码修改
│   └── 订阅状态显示
│
└── 故事详情/播放页面                  # 路由: /story/:id
    ├── 视频播放器
    ├── 故事信息
    └── 相关故事推荐
```

### 9.2 管理后台页面结构

```
管理后台 (frontend-admin)
│
├── 登录页面                           # 路由: /login
│   └── 管理员账号密码登录 (无第三方登录)
│
├── 主界面                             # 路由: /
│   ├── 左侧边栏
│   │   ├── Logo
│   │   ├── 数据概览 (Dashboard)
│   │   ├── 用户管理
│   │   ├── 故事库管理
│   │   ├── 分类管理
│   │   ├── 订单管理
│   │   └── 系统设置
│   │
│   └── 顶部栏
│       └── 管理员信息 + 退出登录
│
├── 数据概览                           # 路由: /dashboard
│   ├── 今日新增用户数
│   ├── 总用户数
│   ├── 今日播放次数
│   ├── 故事总数
│   └── 订阅收入统计图表
│
├── 用户管理                           # 路由: /users
│   ├── 用户列表 (表格形式)
│   │   ├── ID / 邮箱 / 昵称 / 角色 / 订阅状态 / 注册时间
│   │   └── 操作: 查看 / 编辑 / 禁用
│   ├── 搜索过滤
│   └── 分页
│
├── 故事库管理                         # 路由: /stories
│   ├── 故事列表 (卡片/表格视图切换)
│   │   ├── 缩略图 / 标题 / 分类 / 时长 / 状态 / 创建时间
│   │   └── 操作: 编辑 / 上架下架 / 删除
│   ├── 添加故事按钮
│   ├── 批量操作
│   └── 分页
│
├── 添加/编辑故事                      # 路由: /stories/create, /stories/:id/edit
│   ├── 标题 (中/英文)
│   ├── 分类选择
│   ├── 缩略图上传
│   ├── 视频文件上传
│   ├── 视频URL (或选择已上传)
│   └── 发布状态
│
├── 分类管理                           # 路由: /categories
│   ├── 分类列表
│   ├── 添加/编辑/删除分类
│   └── 排序调整
│
└── 订单管理                           # 路由: /orders
    ├── 订单列表
    └── 订单详情
```

### 9.3 用户端配色方案 (深色主题)

```css
/* 用户端采用深色主题 */
:root {
  /* 背景色 */
  --color-bg-dark: #0D0D0D;           /* 主背景 - 近乎纯黑 */
  --color-bg-dark-secondary: #1A1A1A;  /* 次级背景 - 侧边栏 */
  --color-bg-dark-tertiary: #262626;   /* 卡片背景 */
  --color-bg-dark-hover: #333333;      /* 悬停背景 */

  /* 文字色 */
  --color-text-dark-primary: #FFFFFF;   /* 主文字 - 白色 */
  --color-text-dark-secondary: #B3B3B3; /* 次级文字 - 灰白 */
  --color-text-dark-muted: #666666;     /* 弱化文字 */

  /* 边框色 */
  --color-border-dark: #333333;
  --color-border-dark-light: #404040;

  /* 强调色 - 使用 Logo 主色 */
  --color-accent: #2D6B6B;
  --color-accent-light: #3D7B7B;
}
```

### 9.4 管理后台配色方案 (深色主题)

```css
/* 管理后台同样采用深色主题，保持一致性 */
:root {
  /* 与用户端相同的深色配色 */
  --color-bg-dark: #0D0D0D;
  --color-bg-dark-secondary: #1A1A1A;
  --color-bg-dark-tertiary: #262626;

  /* 管理后台可以有少量亮色点缀 */
  --color-admin-accent: #2D6B6B;
}
```

### 9.5 组件设计规范

#### 按钮

```
主按钮 (Primary):
- 背景: 透明或半透明
- 边框: 1px solid rgba(255,255,255,0.3)
- 圆角: 24px (胶囊形)
- 悬停: 背景变亮，边框变亮
- 示例: "点击进入" 按钮

次级按钮 (Secondary):
- 背景: 透明
- 边框: 1px solid rgba(255,255,255,0.2)
- 圆角: 12px
```

#### 卡片 (故事卡片)

```
- 背景: var(--color-bg-dark-tertiary)
- 圆角: 12px
- 阴影: 无或极轻微
- 悬停: 轻微上浮 + 边框高亮
- 缩略图: 16:9 比例，圆角 8px
- 时长标签: 右下角，半透明黑色背景
```

#### 侧边栏

```
- 宽度: 200px (固定)
- 背景: var(--color-bg-dark-secondary)
- 菜单项:
  - 图标 + 文字
  - 悬停: 背景变亮
  - 选中: 左侧边框高亮 或 背景色变化
```

#### 输入框

```
- 背景: var(--color-bg-dark-tertiary)
- 边框: 1px solid var(--color-border-dark)
- 圆角: 8px
- 聚焦: 边框变为强调色
- placeholder: var(--color-text-dark-muted)
```

### 9.6 动画规范

```css
/* 轮播图 - 3D 旋转木马效果 */
.carousel-3d {
  perspective: 1000px;
  transform-style: preserve-3d;
}

/* 背景粒子动画 */
.particle-bg {
  /* 使用 Canvas 或 CSS 实现星空/粒子效果 */
}

/* 页面切换过渡 */
.page-transition {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

/* 卡片悬停效果 */
.card:hover {
  transform: translateY(-4px);
  transition: transform 0.2s ease;
}

/* 按钮悬停效果 */
.btn:hover {
  background: rgba(255,255,255,0.1);
  transition: background 0.2s ease;
}
```

---

## 十、文件存储规范

### 10.1 存储结构

```
存储服务 (本地开发用 uploads/, 生产用 OSS/S3)
│
├── avatars/                    # 用户头像
│   └── {user_id}/
│       └── avatar.jpg
│
├── stories/                    # 故事资源
│   └── {story_id}/
│       ├── thumbnail.jpg       # 缩略图
│       └── video.mp4           # 视频文件
│
└── temp/                       # 临时文件
    └── {upload_id}/
```

### 10.2 文件命名规范

- 用户头像: `avatars/{user_id}/avatar_{timestamp}.{ext}`
- 故事缩略图: `stories/{story_id}/thumbnail.{ext}`
- 故事视频: `stories/{story_id}/video.{ext}`

### 10.3 MongoDB 存储路径字段

```javascript
// users 集合
{
  avatar_url: "/avatars/user123/avatar_1702700000.jpg"
}

// stories 集合
{
  thumbnail_url: "/stories/story456/thumbnail.jpg",
  video_url: "/stories/story456/video.mp4"
}
```

---

## 十一、Logo 资源

Logo 文件位于 `statis/` 目录:

- `statis/logo1.jpg` - 深青色背景版本 (用于浅色页面)
- `statis/logo2.jpg` - 灰色背景版本 (用于深色页面)
- `statis/logo3.jpg` - 备用版本

---

## 十二、开发协作规范

### 12.1 分工原则

1. **Core 模块优先**: 必须先完成 Core 模块，其他模块依赖于此
2. **模块独立开发**: 各业务模块可并行开发
3. **接口先行**: 开发前先定义 API 接口文档

### 12.2 Git 分支规范

```
main                    # 生产分支
├── develop             # 开发分支
│   ├── feature/auth    # 认证模块
│   ├── feature/user    # 用户模块
│   ├── feature/story   # 故事模块
│   └── feature/order   # 订单模块
```

### 12.3 提交信息规范

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式 (不影响功能)
refactor: 重构
test: 测试
chore: 构建/工具
```

---

## 十三、环境配置

### 13.1 开发环境

```bash
# Python 虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 启动后端
uvicorn app.main:app --reload --port 8000

# 启动前端
cd frontend-user && npm run dev
cd frontend-admin && npm run dev
```

### 13.2 环境变量 (.env)

```
# 应用配置
APP_NAME=Echobot
DEBUG=true
API_V1_PREFIX=/api/v1

# 安全配置
SECRET_KEY=your-secret-key-here
AES_KEY=your-aes-key-here

# 数据库
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=echobot

# Redis
REDIS_URL=redis://localhost:6379

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

---

## 十四、代理配置

### 14.1 代理工具位置

```
E:\工作代码\Tools\01_python依赖下载器\proxy_downloader.py
```

### 14.2 代理池 (SOCKS5)

```
socks5://192.168.0.221:8800
socks5://192.168.0.222:8800
socks5://192.168.0.223:8800
socks5://192.168.0.224:8800
socks5://192.168.0.225:8800
socks5://192.168.0.226:8800
socks5://192.168.0.227:8800
socks5://192.168.0.228:8800
socks5://192.168.0.229:8800
```

### 14.3 使用方法

```bash
# 使用代理安装 Python 包
pip install package_name --proxy socks5://192.168.0.221:8800

# 使用代理下载器（自动轮换）
python E:\工作代码\Tools\01_python依赖下载器\proxy_downloader.py install package_name

# 测试代理可用性
python E:\工作代码\Tools\01_python依赖下载器\proxy_downloader.py test
```

### 14.4 适用场景

- 下载 PyPI 包（pip install）
- 下载 npm 包
- 下载 HuggingFace 模型
- 其他需要访问外网的场景

---

## 十五、阿里云 AI 服务配置

### 15.1 服务概览

项目使用阿里云百炼平台提供的 AI 服务实现核心功能：

| 服务 | 用途 | 模型 |
|------|------|------|
| CosyVoice | 声音克隆 + TTS | cosyvoice-v1, cosyvoice-clone-v1 |
| EMO (悦动人像) | 数字人视频生成 | emo-v1, emo-detect-v1 |
| IMS (智能媒体服务) | 视频分离/合成 | - |

### 15.2 业务流程

```
原始儿童故事 MP4
       ↓
┌──────────────────┐
│  IMS 视频分离     │  → 提取音轨、字幕
└──────────────────┘
       ↓
┌──────────────────┐
│  CosyVoice 克隆   │  → 家长音色克隆 + TTS 生成新音频
└──────────────────┘
       ↓
┌──────────────────┐
│  EMO 数字人生成   │  → 家长照片 + 新音频 → 口型同步视频
└──────────────────┘
       ↓
┌──────────────────┐
│  IMS 视频合成     │  → 原视频 + 数字人画中画 + 新音频
└──────────────────┘
       ↓
最终个性化故事视频
```

### 15.3 环境变量配置

```bash
# .env 文件
# 阿里云百炼 API 密钥 (DashScope)
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# IMS 智能媒体服务 (如需使用)
ALIYUN_ACCESS_KEY_ID=your-access-key-id
ALIYUN_ACCESS_KEY_SECRET=your-access-key-secret
ALIYUN_IMS_REGION=cn-shanghai
```

### 15.4 Python SDK 依赖

```bash
# 安装 DashScope SDK (CosyVoice + EMO)
pip install dashscope

# 安装阿里云 SDK (IMS)
pip install alibabacloud-ice20201109
```

### 15.5 API 调用示例

```python
# CosyVoice TTS
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
synthesizer = SpeechSynthesizer(model='cosyvoice-v1', voice='longxiaochun')
audio = synthesizer.call("要转换的文本")

# EMO 数字人
import requests
headers = {"Authorization": f"Bearer {API_KEY}"}
payload = {
    "model": "emo-v1",
    "input": {"image_url": "照片URL", "audio_url": "音频URL"}
}
response = requests.post(
    "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis",
    headers=headers, json=payload
)
task_id = response.json()["output"]["task_id"]
```

### 15.6 相关文档

- **详细 API 文档**: `阿里云.md` (项目根目录)
- **API 测试脚本**: `test_aliyun_api.py`
- **官方文档**:
  - CosyVoice: https://help.aliyun.com/zh/model-studio/cosyvoice-python-sdk
  - EMO: https://help.aliyun.com/zh/model-studio/developer-reference/emo-quick-start
  - IMS: https://help.aliyun.com/zh/ims/developer-reference/

---

## 十六、语音分离模块 (voice_separation)

### 16.1 模块概述

语音分离模块用于分析故事视频中的音频，识别不同说话人并生成独立音轨。

**核心技术栈:**
- **Demucs (htdemucs)**: 分离人声和背景音乐
- **Pyannote speaker-diarization-3.1**: 说话人识别和分割
- **Faster-Whisper**: 词级时间戳字幕生成

### 16.2 模块结构

```
modules/voice_separation/
├── __init__.py
├── service.py          # 核心服务 (VoiceSeparationService)
├── repository.py       # 数据访问
└── models.py           # 数据模型
```

### 16.3 核心功能

```python
class VoiceSeparationService:
    async def analyze_story_audio(self, story_id, video_path, num_speakers=None):
        """
        分析故事音频，识别说话人

        流程：
        1. 从视频提取音频 (FFmpeg)
        2. 使用 Demucs 分离人声/背景
        3. 使用 Pyannote 进行说话人分割 (限制最多2人)
        4. 提取各说话人独立音轨
        5. 为每个说话人生成词级字幕 (Whisper)

        Returns:
            {
                "speaker_count": 2,
                "speakers": [
                    {"speaker_id": "SPEAKER_00", "duration": 120.5, ...},
                    {"speaker_id": "SPEAKER_01", "duration": 85.3, ...}
                ],
                "background_audio_url": "...",
                "segments": [...]
            }
        """
```

### 16.4 说话人限制

为简化用户体验，系统强制限制为最多 **2个说话人**（男声/女声）：

```python
# voice_separation/service.py
max_speakers = 2
effective_speakers = min(num_speakers, max_speakers) if num_speakers else max_speakers
diarization = pipeline(audio_input, num_speakers=effective_speakers)
```

### 16.5 环境配置

```bash
# .env 新增
HF_TOKEN=hf_xxxxx  # HuggingFace Token (用于 Pyannote 模型下载)
```

### 16.6 依赖

```bash
pip install demucs pyannote.audio faster-whisper soundfile torch torchaudio
```

---

## 十七、最新功能更新记录

### 17.1 多说话人声音克隆 (2026-01)

#### 功能说明
- 故事上传后自动进行说话人分析
- 支持为每个说话人单独配置声音档案和头像档案
- 支持"单声音模式"：用一个声音克隆所有说话人
- 支持"单头像模式"：用一个头像应用到所有说话人

#### 相关文件
- `modules/voice_separation/service.py` - 语音分离服务
- `modules/story_generation/service.py` - 故事生成服务
- `modules/story_generation/schemas.py` - SpeakerConfig 模型
- `frontend-user/src/views/Studio.vue` - 用户端生成界面

#### 数据模型变更

```javascript
// stories 集合新增字段
{
  speaker_count: Number,          // 说话人数量
  speakers: [                     // 说话人列表
    {
      speaker_id: String,         // "SPEAKER_00", "SPEAKER_01"
      label: String,              // "说话人 1", "说话人 2"
      gender: String,             // "male" | "female" | "unknown"
      audio_url: String,          // 独立音轨 URL
      duration: Number            // 发言时长
    }
  ],
  background_audio_url: String,   // 背景音 URL
  is_analyzed: Boolean,           // 是否已分析
  analysis_error: String          // 分析错误信息
}

// story_generation_jobs 集合新增字段
{
  speaker_configs: [              // 多说话人配置
    {
      speaker_id: String,
      voice_profile_id: String,   // 可为 null (保持原声)
      avatar_profile_id: String,  // 可为 null (无数字人)
      enabled: Boolean
    }
  ]
}
```

### 17.2 个人资料管理增强 (2026-01)

#### Account.vue 账户设置页面
- 头像上传功能（支持实时预览和上传状态）
- 昵称编辑
- 密码修改
- 订阅状态显示
- 快捷入口到声音档案、头像档案、我的作品

#### VoiceProfiles.vue 声音档案管理
- 声音档案列表展示
- 档案名称编辑（弹窗模式）
- 档案删除
- 音频预览播放

#### AvatarProfiles.vue 头像档案管理
- 头像档案网格展示
- 档案名称编辑（弹窗模式）
- 档案删除
- 预览视频播放（弹窗模式）

#### MyCreations.vue 我的作品
- 分标签显示：故事视频 / 有声书
- 状态过滤：全部/完成/处理中/等待/失败
- 分页加载更多
- 刷新功能
- 错误信息显示
- 当前处理步骤显示

### 17.3 登录状态持久化修复 (2026-01)

**问题**: 用户登录后刷新页面，导航栏仍显示 "Login" 按钮

**解决方案**: 在 `App.vue` 的 `onMounted` 中调用 `userStore.init()` 从 localStorage 恢复登录状态

```vue
// App.vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

onMounted(() => {
  userStore.init()  // 恢复登录状态
})
</script>
```

### 17.4 前端 API 更新

```typescript
// api/index.ts 新增/更新

// 故事生成 API
storyGenerationApi.getSpeakers(storyId)      // 获取说话人信息
storyGenerationApi.analyzeStory(storyId)     // 触发说话人分析
storyGenerationApi.createJob(data)           // 支持 speaker_configs

// 用户 API
userApi.uploadAvatar(file)                   // 上传头像
userApi.changePassword(old, new)             // 修改密码

// 声音档案 API
voiceCloneApi.updateProfile(id, name)        // 更新档案名称

// 头像档案 API
digitalHumanApi.updateProfile(id, name)      // 更新档案名称
```

### 17.5 类型定义更新

```typescript
// types/index.ts

interface Speaker {
  speaker_id: string
  label: string
  gender: 'male' | 'female' | 'unknown'
  audio_url: string
  duration: number
}

interface SpeakerConfig {
  speaker_id: string
  voice_profile_id: string | null
  avatar_profile_id: string | null
  enabled: boolean
}

interface CreateStoryJobRequest {
  story_id: string
  speaker_configs?: SpeakerConfig[]  // 多说话人模式
  voice_profile_id?: string          // 单说话人模式 (向后兼容)
  avatar_profile_id?: string
  full_video?: boolean
}
```

---

*最后更新: 2026-01-09*
