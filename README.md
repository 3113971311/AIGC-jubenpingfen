# 剧本评分系统

一个简单、干净的 AI 剧本评分 Web 应用。系统支持用户上传或粘贴剧本，调用后台配置的大模型，从有趣度、热门程度、逻辑程度、动作链流畅度、剧情发展流畅度五个维度输出评分、问题分析和修改建议。

## 项目定位

本项目适合用于小团队内部的剧本初筛、短剧内容评估和 AI 辅助审稿。它不是一个复杂平台，而是一个前后端分离的小型应用：后端负责用户、积分、剧本、评分、模型配置和反馈；前端负责登录、工作台、评分结果、积分记录和后台管理。

## 主要功能

- 用户登录：基于 JWT 的登录认证，管理员可创建和禁用用户。
- 剧本导入：支持粘贴文本，也支持上传 `txt`、`docx`、`pdf` 文件。
- 自动识别标题：粘贴剧本时会尝试从剧名、标题、集数、场次中生成标题。
- AI 评分：调用管理员配置的大模型，对剧本进行五维度评分和分析。
- 评分进度：评分任务在后台异步执行，前端轮询进度。
- 积分机制：按剧本文字量扣除积分，评分失败时自动退还。
- 历史记录：用户可查看自己的剧本、评分结果和积分明细。
- 后台管理：管理员可管理用户、积分、模型配置、评分记录和系统参数。
- 反馈邮件：用户可提交反馈，系统可通过 SMTP 发送到指定邮箱。
- 简单部署：提供 `build.sh` 和 `start.sh`，可构建前端并以 FastAPI 托管静态资源。

## 技术栈

| 模块 | 技术 |
| --- | --- |
| 后端框架 | FastAPI + Uvicorn |
| 数据库 | SQLite |
| ORM | SQLAlchemy |
| 认证 | JWT (`python-jose`) + bcrypt |
| 配置 | 环境变量 + `.env` |
| 文件解析 | `python-docx`、`PyPDF2`、纯文本 |
| AI 调用 | `httpx` 请求 OpenAI 兼容接口 |
| 前端框架 | Vue 3 + Vite |
| UI 组件 | Element Plus |
| 状态管理 | Pinia |
| 图表 | Chart.js + vue-chartjs |
| 包管理 | 前端使用 pnpm lockfile |

## 目录结构

```text
AIGC-jubenpingfen/
├── backend/
│   ├── main.py                 # FastAPI 开发入口
│   ├── deploy_app.py           # 生产入口，托管 frontend/dist
│   ├── config.py               # 环境变量与默认配置
│   ├── database.py             # 数据库连接、初始化、兼容迁移
│   ├── models.py               # SQLAlchemy 数据模型
│   ├── schemas.py              # Pydantic 请求和响应结构
│   ├── auth.py                 # 密码哈希、JWT、权限依赖
│   ├── init_admin.py           # 初始化管理员账号
│   ├── routers/                # API 路由
│   ├── services/               # AI 评分、文件解析、积分、配置等业务逻辑
│   ├── uploads/.gitkeep        # 本地上传目录占位文件
│   └── requirements.txt        # Python 依赖
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── vite.config.js
│   ├── public/favicon.svg
│   └── src/
│       ├── api/                # Axios API 封装
│       ├── assets/global.css   # 全局样式
│       ├── components/         # 通用组件
│       ├── router/             # Vue Router
│       ├── stores/             # Pinia store
│       └── views/              # 页面视图
├── build.sh                    # 构建前端静态资源
├── start.sh                    # 生产启动脚本
├── .gitignore
└── README.md
```

## 环境要求

- Python 3.10 或更高版本
- Node.js `>=20.19.0` 或 `>=22.12.0`
- pnpm 9 或更高版本
- 可访问的大模型 API，接口需要兼容 OpenAI Chat Completions 格式

完整依赖和部署安装命令见 [DEPENDENCIES.md](DEPENDENCIES.md)。

## 本地开发

### 1. 准备后端

```bash
cd backend
python -m venv venv

# Windows PowerShell
.\venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python init_admin.py
uvicorn main:app --reload
```

后端默认地址是：

```text
http://127.0.0.1:8000
```

健康检查：

```text
GET http://127.0.0.1:8000/api/health
```

默认管理员账号：

```text
用户名：admin
密码：admin123
```

首次部署后请尽快在后台创建正式管理员或修改初始化脚本中的默认密码。

### 2. 准备前端

```bash
cd frontend
pnpm install
pnpm dev
```

前端默认地址是：

```text
http://localhost:5173
```

`frontend/vite.config.js` 已将 `/api` 代理到 `http://127.0.0.1:8000`，本地开发时前后端可以分开启动。

## 环境变量

项目会读取根目录 `.env` 文件，也可以直接使用系统环境变量。

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `JWT_SECRET_KEY` | `change-me-to-a-random-string-in-production` | JWT 签名密钥，生产环境必须修改 |
| `ENCRYPTION_KEY` | `change-me-32-bytes-key-here!!` | 模型 API Key 加密密钥，生产环境必须修改 |
| `DATABASE_URL` | 本地 `sqlite:///./script_scorer.db` | SQLAlchemy 数据库地址 |
| `UPLOAD_DIR` | 本地 `uploads` | 上传文件目录 |
| `SMTP_HOST` | `smtp.qq.com` | 反馈邮件 SMTP 地址 |
| `SMTP_PORT` | `587` | SMTP 端口 |
| `SMTP_USERNAME` | 空 | SMTP 用户名 |
| `SMTP_PASSWORD` | 空 | SMTP 密码或授权码 |
| `SMTP_USE_TLS` | `true` | 是否使用 STARTTLS |
| `FEEDBACK_RECIPIENT` | `3113971311@qq.com` | 反馈收件人 |
建议新建 `.env`：

```env
JWT_SECRET_KEY=please-change-this-to-a-long-random-secret
ENCRYPTION_KEY=please-change-this-32-byte-secret
DATABASE_URL=sqlite:///./script_scorer.db
UPLOAD_DIR=uploads
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true
FEEDBACK_RECIPIENT=
```

## 模型配置

管理员登录后进入「系统设置」，添加模型配置：

| 字段 | 说明 |
| --- | --- |
| 厂商 | 展示用名称，例如 OpenAI、DeepSeek、Qwen |
| 模型名 | 实际模型名称，例如 `gpt-4o`、`deepseek-chat` |
| API 地址 | OpenAI 兼容接口地址 |
| API Key | 模型服务密钥，保存时会加密 |
| 是否启用 | 用户端只会显示启用模型 |

系统支持三种评分模式：

- 标准评分：优先使用 `active_model_id`。
- 深度评分：优先使用 `deep_model_id`。
- 快速评分：优先使用 `fast_model_id`。

这些 ID 可以在后台系统设置中配置。如果对应模式没有配置模型，系统会回退到用户选择的模型。

## 评分规则

AI 评分固定评估五个维度：

| 维度 | 关注点 |
| --- | --- |
| 有趣度 | 概念新颖度、钩子、悬念、情绪共鸣 |
| 热门程度 | 题材热度、爆款潜力、受众规模、当下情绪需求 |
| 逻辑程度 | 人物动机、情节因果、空间时间逻辑、世界观自洽 |
| 动作链流畅度 | 场景和事件之间的衔接、动作链是否断裂 |
| 剧情发展流畅度 | 起承转合、节奏、高低潮分布、主支线关系 |

每个维度为 `1-100` 分，综合评分为五个维度的平均值。AI 需要返回结构化 JSON，后端会解析为评分结果并保存。

## 主要 API

所有业务 API 都以 `/api` 开头。

### 认证

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/auth/login` | 用户登录 |
| `GET` | `/api/auth/me` | 获取当前用户 |

### 剧本

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/scripts/text` | 通过文本创建剧本 |
| `POST` | `/api/scripts/upload` | 上传剧本文件 |
| `GET` | `/api/scripts` | 获取当前用户剧本列表 |
| `GET` | `/api/scripts/{id}` | 获取剧本详情 |
| `DELETE` | `/api/scripts/{id}` | 删除剧本 |

### 评分

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/models/active` | 获取用户可用模型 |
| `POST` | `/api/scripts/{id}/score` | 发起评分 |
| `GET` | `/api/scores/{id}` | 获取评分结果 |
| `GET` | `/api/scores/{id}/progress` | 获取评分进度 |
| `GET` | `/api/scores/history` | 获取评分历史 |
| `GET` | `/api/points/log` | 获取积分记录 |

### 后台

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/admin/users` | 用户列表 |
| `POST` | `/api/admin/users` | 创建用户 |
| `PUT` | `/api/admin/users/{id}` | 更新用户 |
| `DELETE` | `/api/admin/users/{id}` | 删除用户 |
| `POST` | `/api/admin/users/{id}/recharge` | 用户充值积分 |
| `GET` | `/api/admin/models` | 模型配置列表 |
| `POST` | `/api/admin/models` | 创建模型配置 |
| `PUT` | `/api/admin/models/{id}` | 更新模型配置 |
| `DELETE` | `/api/admin/models/{id}` | 删除模型配置 |
| `POST` | `/api/admin/models/{id}/test` | 测试模型连接 |
| `GET` | `/api/admin/scores` | 查看所有评分记录 |
| `GET` | `/api/admin/stats` | 查看统计数据 |
| `GET` | `/api/admin/settings` | 读取系统设置 |
| `PUT` | `/api/admin/settings` | 更新系统设置 |

## 数据说明

SQLite 默认会在后端工作目录生成 `script_scorer.db`。该文件是运行数据，不应该提交到 Git。

核心表：

| 表 | 说明 |
| --- | --- |
| `users` | 用户、积分、管理员标记、账号状态 |
| `scripts` | 用户上传或粘贴的剧本内容 |
| `scores` | 五维评分、分析、建议、进度、耗时 |
| `points_log` | 积分发放、消费、退款流水 |
| `model_configs` | 模型厂商、模型名、API 地址、加密后的 Key |
| `system_configs` | 系统参数，例如默认模型、扣费规则、超时时间 |

## 构建和部署

### 手动构建前端

```bash
cd frontend
pnpm install
pnpm build
```

构建产物会生成到 `frontend/dist`。

### 使用项目脚本构建

```bash
bash build.sh
```

该脚本会安装前端依赖并构建前端静态资源。后端依赖请在运行环境中通过 `pip install -r backend/requirements.txt` 安装。

### 启动生产服务

```bash
bash start.sh
```

生产入口会使用 `backend/deploy_app.py`：

- `/api/*` 请求由 FastAPI 路由处理。
- 前端静态资源由 FastAPI 从 `frontend/dist` 托管。

## 常用维护命令

初始化或重置默认管理员：

```bash
cd backend
python init_admin.py
```

只检查后端语法：

```bash
python -m compileall backend
```

构建前端：

```bash
cd frontend
pnpm build
```

清理本地运行产物：

```bash
rm -rf backend/venv frontend/node_modules frontend/dist
rm -rf backend/__pycache__ backend/routers/__pycache__ backend/services/__pycache__
rm -f backend/*.log frontend/*.log backend/script_scorer.db
```

Windows PowerShell 可使用：

```powershell
Remove-Item -Recurse -Force backend\venv, frontend\node_modules, frontend\dist -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force backend\__pycache__, backend\routers\__pycache__, backend\services\__pycache__ -ErrorAction SilentlyContinue
Remove-Item -Force backend\*.log, frontend\*.log, backend\script_scorer.db -ErrorAction SilentlyContinue
```

## 提交规范建议

建议只提交源码、配置模板、锁文件和文档，不提交以下内容：

- `backend/venv/`
- `frontend/node_modules/`
- `frontend/dist/`
- `backend/script_scorer.db`
- `backend/uploads/` 中的用户文件
- `*.log`
- `__pycache__/`

当前仓库已经在 `.gitignore` 中排除了这些运行产物。

## 清理记录

本次整理将分散文档合并为根目录 `README.md`，移除了 Vite 模板 README、重复 npm lockfile、未引用的模板图片、本地 IDE 推荐配置和平台部署残留。项目现在保留一份前端锁文件 `pnpm-lock.yaml`，并把本地依赖、数据库、日志、缓存、上传内容都视为运行产物。
