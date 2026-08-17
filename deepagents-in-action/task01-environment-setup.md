# Task01：Deep Agents 环境准备与自检记录

> 记录日期：2026-08-18  
> 环境：Windows + WSL2（Ubuntu 24.04）  
> 项目：AgentSeek `deepagents/research` 模板

## 1. 本次目标

完成运行 Deep Agent 所需的基础环境，包括 Python、uv、Node.js、npm、Git、模型 API、Tavily、LangSmith，以及 AgentSeek 项目依赖；最后使用 `agentseek doctor` 完成自检，并实际跑通一次带网络搜索和 LangSmith Trace 的 research 任务。

## 2. 最终环境

| 项目 | 版本或配置 | 验证结果 |
| --- | --- | --- |
| Python | 3.12.3 | 通过 |
| uv | 0.12.5 | 通过 |
| Node.js | 24.19.0 LTS | 通过 |
| npm | 11.17.0 | 通过 |
| Git | 2.43.0 | 通过 |
| AgentSeek | 0.1.2 | 通过 |
| LangSmith CLI | 0.2.48 | 通过 |
| 模型接口 | OpenAI 兼容接口 | 通过 |
| 模型 | `gpt-5.6-sol` | 通过实际调用验证 |
| 搜索 | Tavily | 通过实际工具调用验证 |
| LangSmith | `deepagents-course` 项目 | 成功记录完整 Trace |

项目级开发技能也已经安装：

- `langchain-dev-guide`
- `langsmith-trace`

## 3. 可复现步骤

### 3.1 检查基础工具

```bash
python3 --version
uv --version
node --version
npm --version
git --version
agentseek version
langsmith --version
```

Windows 用户如果选择 WSL2，应始终在 WSL 中使用 Python、uv、Node.js、npm 和 Git，不要把 Windows 与 WSL 的运行环境混在同一个项目中。

### 3.2 安装 Node.js

本机最初的自检结果是 `node` 和 `npm` 缺失。我使用 nvm 管理 WSL 内的 Node.js，并安装 Node 24 LTS：

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.6/install.sh | bash

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

nvm install 24
nvm alias default 24
```

安装后重新打开 WSL 终端，再检查：

```bash
node --version
npm --version
```

### 3.3 配置项目

安装后端和前端依赖：

```bash
agentseek task sync
agentseek task frontend
```

`.env` 中只填写真实密钥，文档和 Git 仓库只保留占位符：

```dotenv
AGENTSEEK_MODEL_PROVIDER=openai
AGENTSEEK_MODEL=gpt-5.6-sol
OPENAI_API_BASE=https://dasuapi.com/v1
OPENAI_API_KEY=<your-api-key>

TAVILY_API_KEY=<your-tavily-key>

LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<your-langsmith-key>
LANGSMITH_PROJECT=deepagents-course
```

`.gitignore` 已忽略 `.env`、`.venv/`、`node_modules/` 和本地 LangGraph 状态目录，避免把密钥、依赖和运行状态提交到仓库。

### 3.4 安装开发技能

```bash
npx skills add ob-labs/agentseek \
  --skill langchain-dev-guide \
  --skill langsmith-trace

npx skills list
```

### 3.5 执行环境自检

```bash
agentseek doctor
```

最终检查项全部通过，包括：

- uv、Node.js、npm 可用；
- `pyproject.toml`、`langgraph.json` 和前端配置存在；
- Python 与前端依赖已安装；
- 模型、Tavily 和 LangSmith 所需环境变量已配置；
- 后端和前端工作目录有效。

还可以在不启动服务的情况下预览运行计划：

```bash
agentseek dev --dry-run
```

得到的服务地址为：

- LangGraph 后端：`http://127.0.0.1:2024`
- Vite 前端：`http://127.0.0.1:5174`

## 4. 实际运行验证

启动应用：

```bash
agentseek dev
```

在前端提交研究任务后，系统成功完成了以下流程：

1. 根 `research` 流程接收问题；
2. 主 Agent 通过 `task` 委派给 `research-agent`；
3. `research-agent` 多次调用 `gpt-5.6-sol`；
4. Agent 调用 `tavily_search` 获取资料；
5. 最终生成带来源的研究报告；
6. LangSmith 在 `deepagents-course` 中保存了完整 Trace。

一次成功 Trace 的总耗时约 334.65 秒，共记录 18 次实际模型调用和 6 次 Tavily 搜索。最慢的叶子模型调用约 89.06 秒，输入约 4.19 万 tokens、输出约 4718 tokens；最慢的实际 Tavily 调用约 6.97 秒。由此可以判断，当前主要性能瓶颈是搜索结果导致的长上下文和长回答，而不是单次搜索工具。

## 5. 踩坑与解决办法

### 问题一：Windows 已安装 Node，但 WSL 自检仍失败

原因是 Windows 和 WSL 是两套运行环境。Windows 中的 `node.exe` 不能代替 WSL 项目所需的 Linux Node.js。

解决办法是在 WSL 中通过 nvm 单独安装 Node LTS，并重新打开终端加载 nvm。

### 问题二：模型能聊天，不代表适合 Agent

OpenAI 兼容接口可能在 Tool Call、流式输出、空 `tools` 数组或 `reasoning_content` 上存在差异。因此不能只测试普通问答，还要实际验证工具调用、网络搜索和多轮 Agent 流程。

本次通过完整 research Trace 证明了当前模型配置能够完成 Tool Call 和研究任务。对于 `reasoning_content` 的保留仍应视为兼容性边界，不把“界面没有展示思考过程”直接当作调用失败。

### 问题三：提示词中的搜索次数限制不一定严格执行

研究提示词规定最多搜索 5 次，但实际 Trace 中出现了 6 次 Tavily 搜索。这说明生产环境中重要的预算限制应通过代码或 Middleware 强制执行，而不能只依赖提示词。

## 6. 收获

这次准备过程让我认识到，“环境装好了”和“Agent 真能运行”是两个不同层次。版本命令和 `agentseek doctor` 只能证明静态条件基本齐全；真正的验收还需要一次端到端任务，确认模型调用、Tool Call、搜索服务、前后端和 LangSmith Trace 能共同工作。LangSmith 也不只是记录日志，它能把根流程、子 Agent、模型叶子调用和实际工具调用区分开，为性能优化提供证据。

## 7. 安全检查清单

- 不提交 `.env`；
- 不在文档、截图或命令中展示 API Key；
- 发布前运行 `git status` 检查待提交文件；
- 只发布 `.env.example` 中的占位符；
- Trace 可能包含提示词、搜索参数和模型输出，公开分享前先检查敏感信息。

## 8. 参考资料

- [Deep Agents 实战教程](https://datawhalechina.github.io/deepagents-in-action/)
- [nvm 官方仓库](https://github.com/nvm-sh/nvm)
- [Node.js 发布周期](https://nodejs.org/en/about/previous-releases)
- [LangSmith CLI 官方文档](https://docs.langchain.com/langsmith/langsmith-cli)

