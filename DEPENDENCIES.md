# 依赖与部署安装清单

本文档用于在新机器或服务器上快速安装本项目依赖。项目的真实依赖来源仍以以下文件为准：

- 后端：`backend/requirements.txt`
- 前端：`frontend/package.json`
- 前端锁定版本：`frontend/pnpm-lock.yaml`

部署时请一起复制这些文件，尤其是 `pnpm-lock.yaml`，这样前端依赖版本会更稳定。

## 基础环境

| 环境 | 建议版本 | 说明 |
| --- | --- | --- |
| Python | 3.10 或更高 | 当前项目在 Python 3.10 下验证通过 |
| Node.js | `>=20.19.0` 或 `>=22.12.0` | Vite 8 的版本要求 |
| pnpm | 10.x | 当前本地使用 pnpm 10.33.2 |
| Git | 任意较新版本 | 方便拉取代码，可选 |

检查命令：

```bash
python --version
node --version
pnpm --version
```

如果机器上没有 pnpm，可以安装：

```bash
npm install -g pnpm
```

## 后端依赖

后端依赖文件：

```text
backend/requirements.txt
```

当前后端依赖列表：

| 包 | 版本 | 用途 |
| --- | --- | --- |
| `fastapi` | `0.115.6` | 后端 Web 框架 |
| `uvicorn` | `0.34.0` | ASGI 服务 |
| `sqlalchemy` | `2.0.36` | ORM 和数据库访问 |
| `python-jose[cryptography]` | `3.3.0` | JWT 生成与验证 |
| `bcrypt` | `4.2.1` | 密码哈希 |
| `python-multipart` | `0.0.18` | 文件上传表单解析 |
| `pydantic` | `2.10.3` | 请求和响应数据模型 |
| `httpx` | `0.28.1` | 调用 AI 模型接口 |
| `python-docx` | `1.1.2` | 解析 `.docx` 剧本文件 |
| `PyPDF2` | `3.0.1` | 解析 `.pdf` 剧本文件 |
| `cryptography` | `44.0.0` | API Key 加密 |
| `python-dotenv` | `1.0.1` | 读取 `.env` 配置 |

### 后端安装

从项目根目录执行：

```bash
cd backend
python -m venv venv
```

Windows PowerShell：

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Linux / macOS：

```bash
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

初始化默认管理员：

```bash
python init_admin.py
```

启动后端：

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

默认管理员：

```text
用户名：admin
密码：admin123
```

## 前端依赖

前端依赖文件：

```text
frontend/package.json
frontend/pnpm-lock.yaml
```

当前前端运行依赖：

| 包 | package.json 版本 | 用途 |
| --- | --- | --- |
| `@element-plus/icons-vue` | `^2.3.2` | Element Plus 图标 |
| `axios` | `^1.15.2` | HTTP 请求 |
| `chart.js` | `^4.5.1` | 图表渲染 |
| `element-plus` | `^2.13.7` | UI 组件库 |
| `pinia` | `^3.0.4` | 前端状态管理 |
| `vue` | `^3.5.32` | 前端框架 |
| `vue-chartjs` | `^5.3.3` | Vue 图表封装 |
| `vue-router` | `^4.6.4` | 前端路由 |

当前前端开发依赖：

| 包 | package.json 版本 | 用途 |
| --- | --- | --- |
| `@vitejs/plugin-vue` | `^6.0.6` | Vite Vue 插件 |
| `vite` | `^8.0.10` | 前端开发服务器和构建工具 |

### 前端安装

从项目根目录执行：

```bash
cd frontend
pnpm install --frozen-lockfile
```

本地开发启动：

```bash
pnpm dev --host 0.0.0.0 --port 5173
```

生产构建：

```bash
pnpm build
```

预览构建产物：

```bash
pnpm preview
```

## 一键脚本

项目根目录提供两个脚本：

```bash
bash build.sh
bash start.sh
```

`build.sh` 会安装并构建前端资源。后端 Python 依赖仍建议在目标机器上先按本文档安装到虚拟环境中。

`start.sh` 会进入 `backend`，初始化默认管理员，然后启动：

```bash
python3 -m uvicorn deploy_app:app --host 0.0.0.0 --port 5000 --log-level info
```

如果使用 Windows PowerShell，建议直接按上文的后端和前端命令分别启动。

## 环境变量

项目会从根目录 `.env` 读取配置。没有 `.env` 时会使用开发默认值。

建议生产部署至少配置：

```env
JWT_SECRET_KEY=please-change-this-to-a-long-random-secret
ENCRYPTION_KEY=please-change-this-32-byte-secret
DATABASE_URL=sqlite:///./script_scorer.db
UPLOAD_DIR=uploads
```

反馈邮件可选配置：

```env
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true
FEEDBACK_RECIPIENT=
```

## 运行产物

以下内容是安装或运行后生成的本地文件，不需要提交：

- `backend/venv/`
- `frontend/node_modules/`
- `frontend/dist/`
- `backend/script_scorer.db`
- `backend/uploads/` 中的用户上传文件
- `*.log`
- `__pycache__/`

## 新机器部署顺序

推荐顺序：

1. 安装 Python、Node.js、pnpm。
2. 克隆或复制项目代码。
3. 配置 `.env`。
4. 安装后端依赖：`pip install -r backend/requirements.txt`。
5. 安装前端依赖：`cd frontend && pnpm install --frozen-lockfile`。
6. 构建前端：`pnpm build`。
7. 初始化管理员：`cd backend && python init_admin.py`。
8. 启动服务：`python -m uvicorn deploy_app:app --host 0.0.0.0 --port 5000`。

启动后访问：

```text
http://服务器地址:5000
```
