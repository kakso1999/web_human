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

*最后更新: 2024-12-16*
