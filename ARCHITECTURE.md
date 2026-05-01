# 剧本评分系统 — 架构文档

## 项目概述

基于 AI 大模型的剧本自动评分平台。用户上传剧本文件（txt/docx/pdf），系统调用配置的 AI 模型从五个维度进行评分分析，通过积分机制控制使用量。

## 技术栈

| 层       | 技术                          |
| -------- | ----------------------------- |
| 后端框架 | FastAPI 0.115 + Uvicorn       |
| ORM      | SQLAlchemy 2.0                |
| 数据库   | SQLite（单文件 `script_scorer.db`） |
| 认证     | JWT (python-jose) + bcrypt    |
| 加密     | Fernet (AES-256, cryptography) |
| 前端框架 | Vue 3.5 + Vite 8             |
| UI 库    | Element Plus 2.13            |
| 状态管理 | Pinia 3.0                    |
| 图表     | Chart.js 4.5 + vue-chartjs   |
| HTTP 客户端 | Axios（前端）/ httpx（后端） |

## 项目结构

```
剧本评分系统/
├── backend/                     # 后端服务
│   ├── main.py                  # FastAPI 应用入口
│   ├── config.py                # 全局配置（JWT密钥、加密密钥、上传路径等）
│   ├── database.py              # 数据库引擎、会话工厂、初始化
│   ├── models.py                # ORM 数据模型
│   ├── schemas.py               # Pydantic 请求/响应模型
│   ├── auth.py                  # JWT 签发/验证、密码哈希、权限依赖
│   ├── init_admin.py            # 初始化默认管理员脚本
│   ├── requirements.txt         # Python 依赖
│   ├── routers/                 # API 路由层
│   │   ├── auth.py              # POST /api/auth/login, GET /api/auth/me
│   │   ├── scripts.py           # 剧本上传/列表/详情/删除
│   │   ├── scoring.py           # AI 评分、可用模型、评分历史
│   │   └── admin.py             # 后台管理：用户CRUD、模型配置、系统设置、统计
│   ├── services/                # 业务逻辑层
│   │   ├── ai_scorer.py         # AI 评分 Prompt 构建、JSON 解析、HTTP 调用
│   │   ├── file_parser.py       # 文件解析器（txt/docx/pdf → 纯文本）
│   │   ├── model_manager.py     # 模型配置 CRUD + API Key 加解密
│   │   ├── points.py            # 积分检查/扣减/发放
│   │   └── system_config.py     # 系统配置键值对读写
│   ├── uploads/                 # 上传文件存储目录
│   └── script_scorer.db         # SQLite 数据库文件
│
├── frontend/                    # 前端应用
│   ├── index.html               # HTML 入口
│   ├── package.json             # 依赖与脚本
│   ├── vite.config.js           # Vite 配置（含 API 代理）
│   ├── public/                  # 静态资源
│   └── src/
│       ├── main.js              # Vue 应用初始化
│       ├── App.vue              # 根组件（导航栏 + 路由出口）
│       ├── api/index.js         # Axios 封装 + 全部 API 方法
│       ├── router/index.js      # 路由配置 + 导航守卫
│       ├── stores/auth.js       # Pinia 认证状态管理
│       ├── assets/global.css    # 全局样式（Apple 风格毛玻璃设计系统）
│       ├── components/
│       │   └── RadarChart.vue   # 雷达图评分组件
│       └── views/
│           ├── LoginView.vue    # 登录页
│           ├── DashboardView.vue # 主面板（上传/列表/评分）
│           ├── ScoreResult.vue  # 评分结果详情（雷达图+维度卡片+AI分析）
│           └── admin/
│               ├── AdminLayout.vue    # 后台布局（侧边栏+内容区）
│               ├── AdminOverview.vue  # 统计概览
│               ├── AdminUsers.vue     # 用户管理
│               ├── AdminModels.vue    # AI 模型配置
│               ├── AdminScores.vue    # 评分记录
│               └── AdminSettings.vue  # 系统设置
│
└── ARCHITECTURE.md              # 本文档
```

## 架构分层

```
┌──────────────────────────────────────────────────────┐
│                    前端 (Vue 3)                       │
│  Views → API (axios) → Stores (pinia) → Components   │
└──────────────────────┬───────────────────────────────┘
                       │ HTTP (JSON)
┌──────────────────────▼───────────────────────────────┐
│               后端路由层 (Routers)                     │
│  auth.router  scripts.router  scoring.router  admin   │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│              服务层 (Services)                        │
│  ai_scorer  file_parser  model_manager  points  cfg  │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│              数据层 (SQLAlchemy ORM)                   │
│  User  PointsLog  Script  Score  ModelConfig  Config  │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│                   SQLite 数据库                        │
└──────────────────────────────────────────────────────┘
```

## 数据模型 ER

```
User (用户)
 ├─ id, username, password_hash, points, is_admin, is_active
 ├─ 1:N → Script (用户上传的剧本)
 ├─ 1:N → Score  (用户的评分记录)
 └─ 1:N → PointsLog (积分变更日志)

Script (剧本)
 ├─ id, user_id, title, content, char_count, filename
 └─ 1:N → Score (剧本的评分结果)

Score (评分记录)
 ├─ id, script_id, user_id, model_config_id, points_cost
 ├─ interestingness, popularity, logic, action_smoothness, plot_smoothness
 ├─ overall (加权平均分), analysis, suggestions
 ├─ progress (评分进度文本，空=未开始/已完成)
 └─ N:1 → ModelConfig (使用的AI模型)

ModelConfig (AI模型配置)
 ├─ id, provider, model_name, api_base, api_key(加密), is_active

SystemConfig (系统设置)
 ├─ key, value (键值对)
   ├─ max_chars: 剧本最大字数限制
   ├─ points_per_10000_chars: 每万字消耗积分
   └─ active_model_id: 当前评分使用的模型ID

PointsLog (积分日志)
 ├─ id, user_id, amount(正=发放/负=消费), reason, balance_after
```

## 评分流程

```
用户 → 上传剧本 → 系统解析文件(txt/docx/pdf)
  → 按字数计算积分消耗: ceil(字数/10000) × 每万字积分
  → 前端发起评分请求 → 后端扣减积分 + 创建占位记录(overall=0)
  → 立即返回占位 ID → 前端每 2 秒轮询 GET /api/scores/{id}/progress
  → 后端异步调用 AI 模型 (OpenAI 兼容 API)
  → Prompt 包含5维度评分标准
  → AI 返回 JSON → 解析 → 校验 → 更新占位记录(overall>0)
  → 前端检测到 overall>0 → 跳转展示结果（综合分 + 雷达图 + 5维度卡片 + 分析 + 建议）
```

## 安全设计

| 项目         | 实现                                        |
| ------------ | ------------------------------------------- |
| 认证         | JWT Bearer Token，7天有效期                 |
| 密码         | bcrypt 哈希存储                             |
| API Key      | Fernet 对称加密（AES-256）存储，脱敏展示    |
| 权限         | 普通用户 / 管理员双角色，路由 + API 双重校验 |
| 文件上传     | 仅允许 txt/docx/pdf，保存后解析             |
| CORS         | 开发环境允许所有来源                         |
