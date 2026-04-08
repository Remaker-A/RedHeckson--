# 帐篷里的存在 - Companion Agent

> 桌面陪伴 Agent 系统 · 深夜施工队

帐篷里住着一个懂你的存在。它不追你，它等你回来。

## 快速启动

### 1. 后端

```bash
cd backend
cp .env.example .env
# 编辑 .env 填入至少一个 LLM API Key

pip install -r requirements.txt
python main.py
```

后端运行在 http://localhost:8000，API 文档在 http://localhost:8000/docs

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:3000（或 3001），自动代理 API 到后端。

### 3. 使用流程

1. 打开前端页面，完成灵魂创建 3 步
2. 进入帐篷房间（手机端体验）或桌面端
3. 使用模拟控制台触发状态切换（人走近/坐下/离开）
4. 观察帐篷内场景变化、说一句话、纸条生成

## 项目结构

```
companion-agent/
├── backend/           # Python FastAPI 后端
│   ├── core/          # 状态机、性格演化、上下文管理
│   ├── intelligence/  # LLM 适配层、Prompt 模板、离线语料
│   ├── mock/          # 硬件模拟层
│   ├── api/           # REST API + WebSocket
│   ├── storage/       # 数据模型 + 文件存储
│   └── data/          # 运行时数据 + 语料库
├── frontend/          # Vue 3 + TypeScript 前端
│   └── src/
│       ├── pages/     # 灵魂创建 / 帐篷房间 / 桌面端
│       ├── components/# 环境音等子组件
│       ├── composables/# API + WebSocket hooks
│       └── stores/    # Pinia 状态管理
└── README.md
```

## 核心 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/soul` | POST/GET/DELETE | 灵魂创建/查询/重置 |
| `/api/status` | GET | 当前状态 |
| `/api/personality` | GET | 性格参数 |
| `/api/room` | GET | 房间场景 |
| `/api/notes` | GET | 纸条列表 |
| `/api/notes/generate` | POST | 生成纸条 |
| `/api/message` | POST | 留言 |
| `/api/focus/start` | POST | 开始专注 |
| `/api/sim/*` | POST | 模拟控制 |
| `/ws/live` | WebSocket | 实时推送 |

## LLM 配置

支持任何 OpenAI 兼容 API。在 `.env` 中配置：

- **硅基流动**: `SILICONFLOW_API_KEY`
- **DeepSeek**: `DEEPSEEK_API_KEY`
- **OpenAI**: `OPENAI_API_KEY`
- 通过 `COMPANION_LLM_PROVIDER` 切换默认 provider

不配置 LLM Key 也能运行，会自动降级为离线语料库。
