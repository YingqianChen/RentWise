# RentWise

RentWise 是一个面向香港租房场景的研究型工作台。它帮助租房者整理候选房源、
横向比较、决定下一步该去核实什么——而不是在嘈杂的挂盘信息里瞎猜。

本仓库是**硕士课程作业提交版**，代码冻结在提交当时的状态。后续开发在独立
分叉仓库中继续进行。

**Language**: [English](README.md) • [中文](README_zh.md)

---

## RentWise 做什么

- **候选池**——粘贴或上传一条租房挂盘（文字、截图、图片、PDF）。系统会抽取
  结构化字段（地址、租金、面积、户型、水电、杂费），保留原始资料，并标出
  哪些字段缺失。
- **单房源评估**——对每条候选房，系统跑一组证据检查：SDU 租金基准（这个
  价格在该地段/面积下是否合理）、成本构成（租金+管理费+差饷+估算水电）、
  合同条款级别的标记（按金、提前终止、中介费、维修），以及优先级打分。
- **对比视图**——把用户挑出的 2–5 条候选放到同一张表里并行比较，附带一段
  简短的文字 briefing，指出它们的权衡点。
- **待核实清单**——系统为每条候选生成一小串需要向房东/中介确认的问题
  （"确认中介费分摊方式"、"是否含宽带"、"核对业主身份"），下一条对话
  消息就能直接照着问。

产品哲学是"诚实的助手"：不替用户排名，只把证据和信息缺口摆出来，让用户
自己做有信心的决定。

---

## 仓库结构

```
backend/       FastAPI + SQLAlchemy async + Alembic
  app/
    api/v1/          auth / projects / candidates / comparison / dashboard / investigation
    services/        领域逻辑（基准、抽取、评估……）
    integrations/    LLM 适配层 + prompt
    agent/           LangGraph 研究 agent（实验性）
    db/              SQLAlchemy 模型
    schemas/         Pydantic 入/出参
    data/            SDU 租金基准 JSON
  alembic/           数据库迁移
  tests/             单测 + 集成测试（pytest）

frontend/      Next.js 14 App Router + Tailwind v3 + TypeScript
  app/
    login/                                登录
    projects/                             项目列表
    projects/[id]/                        项目仪表盘
    projects/[id]/import/                 新增候选（粘贴/上传）
    projects/[id]/candidates/[id]/        单房源详情 + 证据
    projects/[id]/compare/                横向对比
  lib/           API 客户端 + auth 工具

docs/          架构 / 数据模型 / API 设计 / AI 使用 / 答辩笔记
```

---

## 后端——模块一览

`backend/app/services/`：

| 服务 | 作用 |
|---|---|
| `extraction_service` | 把原始挂盘文本归一化成候选字段 |
| `ocr_service` | 图片和 PDF 的 OCR |
| `file_storage_service` | 上传源文件的持久化（本地 FS / S3 兼容） |
| `candidate_import_service` + `_background_service` | 解析输入、触发抽取、落库 |
| `candidate_pipeline_service` | 导入后串起一系列评估步骤 |
| `candidate_assessment_service` | 单房源评估入口 |
| `benchmark_service` | 按地段 × 面积匹配 SDU 基准租金，判断"是不是贵了" |
| `cost_assessment_service` | 租金 + 管理费 + 差饷 + 估算水电的合计 |
| `clause_assessment_service` | 按金、提前终止、维修、中介费等条款标记 |
| `priority_service` | 仪表盘用的优先级打分 |
| `investigation_service` | 待核实的开放问题 |
| `comparison_service` + `comparison_briefing_service` | 对比数据 + 自然语言 briefing |
| `dashboard_service` | 项目级汇总数据 |

`backend/app/integrations/`：

- `llm/` —— LLM provider 封装 + 共用 prompt 模板。

---

## 前端——页面一览

| 路由 | 作用 |
|---|---|
| `/` | 落地页 |
| `/login` | 登录 |
| `/projects` | 搜索项目列表（新建/删除） |
| `/projects/[id]` | 项目仪表盘：KPI + 候选栅格 |
| `/projects/[id]/import` | 新增候选（粘贴文字 / 上传文件） |
| `/projects/[id]/candidates/[id]` | 单房源的抽取字段 + 证据 + 待核实清单 |
| `/projects/[id]/compare` | 选中的 2–5 条候选横向对比 |

---

## 本地搭建

### 前置

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+（本地，或用 Neon / Supabase）

### 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# 编辑 .env —— 见下文"环境变量"

alembic upgrade head
uvicorn app.main:app --reload
# http://127.0.0.1:8000  （swagger 文档：/docs）
```

### 前端

```bash
cd frontend
npm install
cp .env.local.example .env.local
# 如果后端不在 :8000，改 NEXT_PUBLIC_API_BASE_URL
npm run dev
# http://localhost:3000
```

### 环境变量

**后端** (`backend/.env`)：

必填：
- `DATABASE_URL` —— 例如 `postgresql+asyncpg://user:pass@host:5432/rentwise`
- `SECRET_KEY` —— JWT 签名密钥（`openssl rand -hex 32` 生成）
- `OPENAI_API_KEY` **或** `ANTHROPIC_API_KEY` —— 选一家 LLM 供应商

可选：
- `LLM_PROVIDER` —— `openai` 或 `anthropic`（默认 `openai`）
- `LLM_MODEL` —— 覆盖默认模型
- `ALLOWED_ORIGINS` —— CORS 白名单，逗号分隔
- `STORAGE_BACKEND` —— `local`（默认）或 `s3`
- `S3_BUCKET` / `S3_REGION` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` —— `STORAGE_BACKEND=s3` 时必填

**前端** (`frontend/.env.local`)：

- `NEXT_PUBLIC_API_BASE_URL` —— 例如 `http://localhost:8000`

---

## 测试

```bash
# 后端
cd backend
pytest                    # 单测 + 集成
pytest tests/unit/        # 只跑单测（更快）

# 前端
cd frontend
npm run lint
npx next build            # 类型检查 + 生产构建
```

集成测试需要 `DATABASE_URL` 指向一个真实的 PostgreSQL 实例。单测不依赖数据库。

---

## 数据安全

- 密码：bcrypt。
- JWT：HS256，用 `SECRET_KEY` 签名。
- 候选源文件：按 user + project 命名空间存储，访问需携带用户 JWT。
- 不接任何第三方追踪。LLM 请求由后端直接发给 OpenAI/Anthropic，不经中间
  数据转卖层。

---

## 证据层

| 层 | 状态 | 说明 |
|---|---|---|
| SDU 租金基准 | 已上线 | 基于内嵌 JSON 的地段 × 面积租金区间（源自 HK SDU 调查数据） |
| 成本构成 | 已上线 | 租金 + 管理费 + 差饷 + 估算水电 |
| 条款标记 | 已上线 | 按金、提前终止、中介费、维修、宠物 |
| 待核实清单 | 已上线 | 单房源的开放问题 |
| 通勤证据 | **设计完成，尚未实现** | 设计文档见 `docs/superpowers/specs/2026-04-05-single-destination-commute-design.md` |
| 租务条例 RAG | Roadmap | 基于 HK《业主与租客（综合）条例》的检索问答 |

---

## 阶段状态

- **Phase 1**——候选池、抽取、导入、仪表盘。已完成。
- **Phase 2**——单房源评估（基准、成本、条款、优先级）、对比视图 + briefing、
  待核实清单。已完成。
- **Phase 2.5**——Agent 细节优化、脏数据抽取改进、对比 briefing 打磨。
  即本次提交所处的活跃阶段。
- **Phase 3**——通勤证据、UI 视觉重做、租务条例 RAG。已规划，详见 `docs/`
  下的设计文档。

---

## 部署（参考）

项目可直接部署于：

- **前端**：Vercel（Next.js App Router）。
- **后端**：Render / Railway / Fly.io（uvicorn + 启动时 alembic migrate）。
- **数据库**：Neon 或 Supabase（PostgreSQL，支持 async 连接串）。

后端需配置 `ALLOWED_ORIGINS` 指向前端部署 URL，前端需配置
`NEXT_PUBLIC_API_BASE_URL` 指向后端部署 URL。

---

## 文档

- `docs/overview.md` —— 产品概述
- `docs/architecture.md` —— 高层架构
- `docs/data-model.md` —— 数据模型
- `docs/api-design.md` —— REST API 约定
- `docs/ai-features.md` —— 各服务中 LLM 的使用方式
- `docs/presentation-notes.md` —— 答辩/展示笔记
- `docs/refactor/implementation-spec-v2.md` —— 内部重构 spec
- `docs/superpowers/specs/2026-04-05-single-destination-commute-design.md` —— 通勤功能设计（本次提交版本尚未实现）

---

## License

课程作业提交版。版权归作者所有。
