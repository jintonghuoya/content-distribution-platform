# CDP - 热点话题感知-过滤-内容生成-分发平台

自动实时采集热点话题 → 内容安全过滤 → AI 生成文章/语音/视频 → 分发到国内主流平台 → 流量变现。

## 架构概览

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Collector │───▶│  Filter  │───▶│Generator │───▶│Distributor│───▶│ Revenue  │
│  热点采集  │    │  内容过滤 │    │ AI内容生成│    │  多平台分发│    │  收益追踪 │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     ▲                                                              │
     │              Celery Workflow Pipeline                         │
     └──────────────────────────────────────────────────────────────┘
                              FastAPI 管理面板
```

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| 任务队列 | Celery + Redis |
| 数据库 | PostgreSQL + SQLAlchemy (async) |
| 数据迁移 | Alembic |
| 内容生成 | Claude API (Anthropic) |
| 部署 | Docker Compose |

## 快速开始

```bash
# 1. 复制环境变量
cp .env.example .env

# 2. 启动所有服务
docker compose up -d

# 3. 数据库迁移
docker compose exec api alembic upgrade head

# 4. 访问 API 文档
open http://localhost:8000/docs
```

## 模块说明

### 1. 热点采集 (Collector) — 已实现

自动从多个国内平台抓取热点话题，统一格式后存入数据库。

**已支持平台**: 微博热搜、百度热搜、知乎热榜
**待接入**: 抖音热点、B站热门、今日头条

**核心设计**:
- `BaseCollector` 抽象基类 — 所有平台采集器继承它
- `CollectorRegistry` 注册中心 — 自动发现采集器，按 `config/sources.yaml` 控制启用/禁用
- Celery Beat 定时调度 — 按配置频率自动采集

**API**:
- `GET /api/v1/topics` — 查看热点列表（支持按来源、状态过滤、分页）
- `GET /api/v1/topics/{id}` — 查看单条热点详情
- `POST /api/v1/topics/collect` — 手动触发采集
- `GET /api/v1/sources` — 查看所有采集源状态

### 2. 内容过滤 (Filter) — 已实现

多层管道过滤引擎：
- 关键词黑名单过滤（匹配即 reject）
- 热度阈值过滤（低于阈值 reject，高于阈值计算优先级）
- AI 内容审核（LLM 批量评估话题质量、受众相关性、生成潜力）

**API**:
- `GET /api/v1/filters/rules` — 查看过滤规则
- `POST /api/v1/filters/rules` — 创建过滤规则
- `POST /api/v1/filters/trigger` — 手动触发全量过滤
- `POST /api/v1/filters/trigger/{topic_id}` — 手动触发单条过滤

### 3. 内容生成 (Generator) — 已实现

基于过滤后的热点自动生成多形态内容：
- **文章**: LLM 驱动，800-1500 字深度解读
- **社交媒体文案**: 100-300 字短文，适合微博/微信发布
- **待接入**: TTS 语音合成、视频生成

**API**:
- `GET /api/v1/generators/` — 查看所有生成器
- `POST /api/v1/generators/trigger` — 手动触发全量生成
- `POST /api/v1/generators/trigger/{topic_id}` — 为单条 topic 生成内容
- `GET /api/v1/generators/content` — 分页查询已生成内容
- `PUT /api/v1/generators/content/{id}/publish` — 发布生成内容

### 4. 内容分发 (Distributor) — 已实现

适配器模式，每个平台一个分发器，统一接口 `publish()` 和 `check_status()`：
- 微信公众号（官方 API — 需配置凭证）
- 今日头条（头条号 API — 需配置凭证）
- 小红书（Playwright 自动化 — 需配置登录态）
- B站（创作者 API — 需配置凭证）
- 抖音（开放平台 API — 需配置凭证）

**API**:
- `GET /api/v1/distributors/` — 查看所有分发器
- `POST /api/v1/distributors/trigger` — 手动触发全量分发
- `POST /api/v1/distributors/trigger/{content_id}` — 分发单条内容
- `GET /api/v1/distributors/records` — 分页查询分发记录

### 5. 收益追踪 (Revenue) — 已实现

采集各平台阅读量、播放量、收益数据，按平台维度汇总生成报表。

**API**:
- `GET /api/v1/revenue/records` — 分页查询收益记录
- `GET /api/v1/revenue/summary` — 获取收益汇总（支持按平台、天数筛选）
- `POST /api/v1/revenue/collect` — 手动触发收益采集

## 目录结构

```
rig/
├── app/
│   ├── api/              # REST API 路由
│   ├── collector/        # 热点采集模块
│   │   ├── base.py       # 采集器基类
│   │   ├── registry.py   # 注册中心
│   │   ├── scheduler.py  # 调度器
│   │   └── sources/      # 各平台采集器实现
│   ├── filter/           # 内容过滤模块
│   ├── generator/        # AI内容生成模块
│   ├── distributor/      # 多平台分发模块
│   ├── revenue/          # 收益追踪模块
│   ├── models/           # SQLAlchemy ORM 模型
│   ├── schemas/          # Pydantic 序列化模型
│   ├── workers/          # Celery Worker 定义
│   ├── database.py       # 数据库连接
│   └── main.py           # FastAPI 入口
├── config/
│   ├── settings.py       # 全局配置（环境变量）
│   └── sources.yaml      # 采集源配置
├── alembic/              # 数据库迁移
├── docker-compose.yml    # 服务编排
├── Dockerfile            # 应用镜像
├── pyproject.toml        # Python 项目配置
└── .env.example          # 环境变量模板
```

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| API | 8000 | FastAPI 应用 |
| PostgreSQL | 5432 | 主数据库 |
| Redis | 6379 | 缓存 + 消息队列 |
| Flower | 5555 | Celery 监控面板 |
