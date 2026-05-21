# 社区志愿服务管理系统（Django + Vue）

一个前后端分离的社区志愿服务管理平台，支持志愿者报名、活动管理、公告发布、审核流转、签到工时与操作日志审计等核心场景。

## 技术栈

- 后端：Django、Django REST Framework、Simple JWT、CORS Headers
- 前端：Vue 3、TypeScript、Vite、Pinia、Vue Router、Element Plus
- 数据库：SQLite（默认，文件位于 `backend/db.sqlite3`）

## 主要功能

- 多角色用户体系：志愿者 / 社区管理员 / 系统管理员
- 活动全流程：创建、审核、报名、审核、签到签退、工时确认
- 社区管理：社区信息维护、志愿者社区变更申请
- 内容互动：公告、活动评价、活动评论（含回复）
- 审计能力：系统管理员操作日志

## 项目结构

```text
fast_try/
├─ backend/                 # Django 后端
│  ├─ api/                  # 业务模型、序列化、接口
│  ├─ volunteer_system/     # Django 配置
│  ├─ manage.py
│  └─ db.sqlite3
├─ frontend/                # Vue 前端
│  ├─ src/
│  ├─ package.json
│  └─ vite.config.ts
├─ scripts/                 # 辅助脚本
├─ run_all.bat              # 一键启动前后端（Windows）
└─ stop_all.bat             # 一键停止服务（Windows）
```

## 快速启动（Windows）

### 方式一：一键启动（推荐）

在项目根目录运行：

```bat
run_all.bat
```

脚本会自动执行：

1. 后端迁移：`python manage.py migrate`
2. 前端依赖安装（若 `node_modules` 不存在）
3. 启动后端（`0.0.0.0:8000`）与前端（`0.0.0.0:5173`）

访问地址：

- 前端：http://127.0.0.1:5173
- 后端：http://127.0.0.1:8000

停止服务：

```bat
stop_all.bat
```

### 方式二：手动启动

后端：

```powershell
cd backend
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

前端（新终端）：

```powershell
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

## 环境建议

- Python 3.11+
- Node.js 20+
- npm 10+

## 说明

- 当前默认是开发配置（`DEBUG=True`，`ALLOWED_HOSTS=*`），仅用于本地开发测试。
- 生产部署前请务必更换 `SECRET_KEY`、关闭 `DEBUG`、收紧跨域与主机白名单，并替换为生产数据库。
