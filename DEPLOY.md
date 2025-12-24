# Echobot 部署指南

## 一、系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Ubuntu 20.04+ / Windows Server 2019+ | Ubuntu 22.04 LTS |
| CPU | 4 核 | 8 核+ |
| 内存 | 8GB | 16GB+ (语音克隆需要) |
| 显卡 | - | NVIDIA GPU 8GB+ (语音克隆加速) |
| 硬盘 | 50GB | 100GB+ SSD |
| Python | 3.11+ | 3.11 |
| Node.js | 18+ | 20 LTS |
| MongoDB | 6.0+ | 7.0 |
| Redis | 7.0+ | 7.0 |

## 二、端口规划

| 服务 | 端口 | 说明 |
|------|------|------|
| 后端 API | 8000 | FastAPI 服务 |
| 管理员前端 | 3000 | Vue 3 管理后台 |
| 用户前端 | 3001 | Vue 3 用户网站 |
| 语音克隆服务 | 3002 | 独立 TTS 服务 |
| MongoDB | 27017 | 数据库 |
| Redis | 6379 | 缓存 |

## 三、快速部署步骤

### 3.1 克隆代码

```bash
git clone https://github.com/kakso1999/web_human.git echobot
cd echobot
```

### 3.2 配置环境变量

```bash
# 复制配置文件
cp .env.example .env
cp frontend-admin/.env.example frontend-admin/.env
cp frontend-user/.env.example frontend-user/.env

# 编辑主配置文件
nano .env
```

**必须修改的配置项:**
```bash
# 安全密钥 (生产环境必须更换)
SECRET_KEY=随机生成的64位字符串
AES_KEY=随机生成的32位字符串

# 数据库配置 (如果不是本地)
MONGODB_URL=mongodb://用户名:密码@服务器地址:27017
REDIS_URL=redis://:密码@服务器地址:6379

# CORS (根据实际域名修改)
CORS_ORIGINS=["https://your-domain.com","https://admin.your-domain.com"]
```

### 3.3 安装后端依赖

```bash
# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate  # Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3.4 安装前端依赖

```bash
# 管理员前端
cd frontend-admin
npm install
npm run build

# 用户前端
cd ../frontend-user
npm install
npm run build
```

### 3.5 启动服务

```bash
# 启动后端 (在项目根目录)
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 启动前端 (生产环境使用 nginx 托管 dist 目录)
```

## 四、语音克隆服务部署 (可选)

语音克隆服务需要单独部署，因为模型文件较大 (~9GB)。

### 4.1 安装依赖

```bash
cd voice_clone_server

# 创建虚拟环境 (必须使用 Python 3.11)
python3.11 -m venv venv
source venv/bin/activate

# 安装依赖 (需要代理或国内镜像)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4.2 下载模型

模型会在首次启动时自动下载，或手动下载:

```bash
# 创建模型目录
mkdir -p ../models/ResembleAI/chatterbox

# 从 HuggingFace 下载 (需要代理)
# 模型地址: https://huggingface.co/ResembleAI/chatterbox
```

### 4.3 启动语音克隆服务

```bash
cd voice_clone_server
source venv/bin/activate
python server.py
```

## 五、使用 Nginx 反向代理 (推荐)

### 5.1 安装 Nginx

```bash
sudo apt update
sudo apt install nginx
```

### 5.2 配置文件

创建 `/etc/nginx/sites-available/echobot`:

```nginx
# 后端 API
upstream backend {
    server 127.0.0.1:8000;
}

# 用户网站
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/echobot/frontend-user/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 上传文件
    location /uploads {
        proxy_pass http://backend;
    }
}

# 管理后台
server {
    listen 80;
    server_name admin.your-domain.com;

    location / {
        root /path/to/echobot/frontend-admin/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /uploads {
        proxy_pass http://backend;
    }
}
```

### 5.3 启用配置

```bash
sudo ln -s /etc/nginx/sites-available/echobot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 六、使用 Systemd 管理服务

### 6.1 后端服务

创建 `/etc/systemd/system/echobot-backend.service`:

```ini
[Unit]
Description=Echobot Backend API
After=network.target mongodb.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/echobot
Environment="PATH=/path/to/echobot/venv/bin"
ExecStart=/path/to/echobot/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 6.2 语音克隆服务

创建 `/etc/systemd/system/echobot-voice.service`:

```ini
[Unit]
Description=Echobot Voice Clone Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/echobot/voice_clone_server
Environment="PATH=/path/to/echobot/voice_clone_server/venv/bin"
ExecStart=/path/to/echobot/voice_clone_server/venv/bin/python server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 6.3 启动服务

```bash
sudo systemctl daemon-reload
sudo systemctl enable echobot-backend echobot-voice
sudo systemctl start echobot-backend echobot-voice

# 查看状态
sudo systemctl status echobot-backend
sudo systemctl status echobot-voice
```

## 七、Docker 部署 (可选)

### 7.1 docker-compose.yml

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:7
    restart: always
    volumes:
      - mongo_data:/data/db
    ports:
      - "27017:27017"

  redis:
    image: redis:7-alpine
    restart: always
    ports:
      - "6379:6379"

  backend:
    build: .
    restart: always
    ports:
      - "8000:8000"
    depends_on:
      - mongodb
      - redis
    env_file:
      - .env
    volumes:
      - ./uploads:/app/uploads

  frontend-user:
    build: ./frontend-user
    restart: always
    ports:
      - "3001:80"

  frontend-admin:
    build: ./frontend-admin
    restart: always
    ports:
      - "3000:80"

volumes:
  mongo_data:
```

### 7.2 启动

```bash
docker-compose up -d
```

## 八、常见问题

### Q1: 语音克隆服务启动慢
首次启动需要下载模型 (~9GB)，需要 5-10 分钟。建议提前下载模型到 `models/ResembleAI/chatterbox` 目录。

### Q2: 前端打包失败
确保 Node.js 版本 >= 18，并清除缓存重试:
```bash
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Q3: MongoDB 连接失败
检查 MongoDB 是否启动，以及 `.env` 中的连接字符串是否正确:
```bash
mongosh --eval "db.adminCommand('ping')"
```

### Q4: 上传文件失败
确保 `uploads` 目录存在且有写权限:
```bash
mkdir -p uploads
chmod 755 uploads
```

## 九、监控和日志

### 9.1 查看日志

```bash
# 后端日志
journalctl -u echobot-backend -f

# 语音克隆日志
journalctl -u echobot-voice -f

# Nginx 日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### 9.2 健康检查

```bash
# 后端健康检查
curl http://localhost:8000/health

# 语音克隆服务健康检查
curl http://localhost:3002/health
```

## 十、备份

### 10.1 数据库备份

```bash
# MongoDB 备份
mongodump --db echobot --out /backup/mongo/$(date +%Y%m%d)

# 恢复
mongorestore --db echobot /backup/mongo/20241224/echobot
```

### 10.2 上传文件备份

```bash
# 备份上传文件
tar -czf /backup/uploads_$(date +%Y%m%d).tar.gz uploads/
```

---

*最后更新: 2024-12-24*
