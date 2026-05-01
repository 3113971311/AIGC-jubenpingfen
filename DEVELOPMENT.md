# 剧本评分系统 — 开发文档

## 环境准备

- **Python** 3.10+
- **Node.js** 18+
- （可选）虚拟环境工具

## 快速启动

### 1. 后端

```bash
cd backend

# 创建虚拟环境（可选）
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 初始化管理员账号
python init_admin.py
# 默认账户: admin / admin123

# 启动后端服务（默认 http://127.0.0.1:8000）
uvicorn main:app --reload
```

### 2. 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器（默认 http://localhost:5173）
npm run dev
```

前端开发服务器自动将 `/api` 请求代理到后端 `http://127.0.0.1:8000`。

### 3. 构建部署

```bash
# 构建前端
cd frontend && npm run build

# dist/ 目录即为静态文件，可直接部署到 Nginx 或由 FastAPI 托管
```

## API 接口一览

### 认证

| 方法   | 路径             | 说明     | 权限   |
| ------ | ---------------- | -------- | ------ |
| POST   | `/api/auth/login` | 登录     | 无     |
| GET    | `/api/auth/me`    | 当前用户 | 登录   |

### 剧本

| 方法   | 路径                  | 说明       | 权限 |
| ------ | --------------------- | ---------- | ---- |
| POST   | `/api/scripts/upload`  | 上传剧本   | 登录 |
| GET    | `/api/scripts`         | 我的剧本列表 | 登录 |
| GET    | `/api/scripts/{id}`    | 剧本详情   | 所有者/管理员 |
| DELETE | `/api/scripts/{id}`    | 删除剧本   | 所有者/管理员 |

### 评分

| 方法 | 路径                        | 说明            | 权限 |
| ---- | --------------------------- | --------------- | ---- |
| GET  | `/api/models/active`         | 可用模型列表    | 登录 |
| POST | `/api/scripts/{id}/score`   | 发起AI评分（异步，立即返回占位记录） | 剧本所有者 |
| GET  | `/api/scores/{id}/progress`  | 查询评分进度    | 所有者/管理员 |
| GET  | `/api/scores/history`        | 我的评分历史    | 登录 |
| GET  | `/api/scores/{id}`           | 评分详情        | 所有者/管理员 |

### 后台管理（管理员）

| 方法   | 路径                            | 说明       |
| ------ | ------------------------------- | ---------- |
| GET    | `/api/admin/stats`              | 统计概览   |
| GET    | `/api/admin/users`              | 用户列表   |
| POST   | `/api/admin/users`              | 创建用户   |
| PUT    | `/api/admin/users/{id}`         | 编辑用户   |
| DELETE | `/api/admin/users/{id}`         | 删除用户   |
| PUT    | `/api/admin/users/{id}/toggle`  | 启用/禁用  |
| POST   | `/api/admin/users/{id}/recharge`| 用户充值   |
| GET    | `/api/admin/models`             | 模型列表   |
| POST   | `/api/admin/models`             | 添加模型   |
| PUT    | `/api/admin/models/{id}`        | 编辑模型   |
| DELETE | `/api/admin/models/{id}`        | 删除模型   |
| PUT    | `/api/admin/models/{id}/toggle` | 启用/禁用  |
| POST   | `/api/admin/models/{id}/test`   | 测试模型连接 |
| GET    | `/api/admin/scores`             | 评分记录   |
| GET    | `/api/admin/settings`           | 系统设置   |
| PUT    | `/api/admin/settings`           | 更新设置   |
| GET    | `/api/health`                   | 健康检查   |

## 配置说明

所有敏感配置通过环境变量覆盖：

| 环境变量            | 默认值                        | 说明              |
| ------------------- | ----------------------------- | ----------------- |
| `JWT_SECRET_KEY`    | `change-me-to-a-random-...`   | JWT 签名密钥      |
| `DATABASE_URL`      | `sqlite:///./script_scorer.db`| 数据库连接地址    |
| `ENCRYPTION_KEY`    | `change-me-32-bytes-key-here!!`| API Key 加密密钥  |

系统运行配置（存储在数据库 SystemConfig 表中，通过后台管理界面修改）：

| 配置项                | 默认值  | 说明                       |
| --------------------- | ------- | -------------------------- |
| `max_chars`           | 100000  | 剧本最大字数限制（0=不限） |
| `points_per_10000_chars` | 1    | 每万字消耗积分             |
| `active_model_id`     | 空      | 当前生效的评分模型ID       |

## 添加新的 AI 评分模型

系统支持任何兼容 OpenAI API 格式的服务：

1. 登录管理员账号，进入「模型配置」
2. 点击「添加模型」填写：
   - **厂商名称**：如 OpenAI / DeepSeek / 硅基流动
   - **模型名**：如 gpt-4o / deepseek-chat
   - **API 地址**：如 https://api.openai.com/v1
   - **API Key**：服务商提供的密钥
3. 点击「测试」验证连接
4. 进入「系统设置」，在「评分模型」下拉中选择该模型
5. 保存

API Key 使用 Fernet 对称加密存储于数据库，界面仅展示脱敏后的前4后4字符。

## 评分计算规则

- **积分消耗** = ceil(剧本字数 / 10000) × `points_per_10000_chars`（最低 1 积分）
- **综合得分**：AI 根据5个维度按加权计算并返回（保留1位小数）
- **5个维度**：有趣度、热门度、逻辑程度、动作链流畅程度、剧情发展流畅程度，每题1-100分

## 开发注意事项

- 后端 `.db` 文件包含在项目中，生产环境应更换 `DATABASE_URL` 指向独立数据库
- 生产环境需修改 `config.py` 中的默认密钥，并设置环境变量
- 前端 API 超时设置为 180 秒，因为 AI 评分可能耗时较长
- 去除了前端 `DashboardView.vue` 中使用但未导入的 `ElMessageBox`，如需删除功能请添加 `import { ElMessageBox } from 'element-plus'`
- `backend/auth.py` 中 `get_current_user` 依赖 `HTTPBearer`，所有受保护接口需在 Header 中携带 `Authorization: Bearer <token>`
