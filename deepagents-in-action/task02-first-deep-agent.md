# Task02：第一个 Deep Agent、自定义工具与 Trace

> 记录日期：2026-08-20<br>
> 环境：Windows 11 + WSL2（Ubuntu 24.04）<br>
> 实验目录：`/home/charlie/projects/deepagents-course/ch02-quickstart`<br>
> 模型接入：OpenAI 兼容接口，模型 `gpt-5.6-sol`

## 1. 本次目标与完成情况

本次实验结合认知篇第 1、2 章，目标是理解 Deep Agents 在 Agent 技术栈中的位置，并完成一个真正发生自定义工具调用、可通过 Trace 复查的最小 Agent。

| 档位 | 要求 | 完成情况 |
| --- | --- | --- |
| 打卡 | 写 50 字以上 Task 相关内容 | 已完成，本文记录了过程、问题和收获 |
| 本 Task | 跑通第一个 Deep Agent、自定义工具、留下一段 Trace | 已完成 |
| 挑战 | 代码整洁、Trace 清楚、总结完整 | 已完成最小可复现实例和 Trace 分析 |
| 学有余力 | 两个模型对比同一任务 | 尚未完成，不虚构对比结果 |

## 2. 从第 1 章理解 Deep Agents

第 1 章把 Agent 开发分为三个层次：

1. **Runtime（LangGraph）**：负责可靠运行，包括状态、持久化、流式输出和人机协作；
2. **Framework（LangChain）**：提供模型抽象、工具接口和 Agent 循环；
3. **Harness（Deep Agents）**：在前两层之上预置文件系统、任务规划、子 Agent 和长期记忆等能力。

我对 Harness 的理解是：它不是换掉 LangChain 或 LangGraph，而是把复杂 Agent 经常需要的工程能力提前组装好。第 2 章中虽然只显式注册了一个天气函数，但 `create_deep_agent()` 创建出的 Agent 同时具备内置中间件和工具能力，这正是 Harness 与“只调用一次模型”的区别。

第 1 章强调的 Context Engineering 也改变了我的理解：复杂任务不应把全部资料一次性塞进提示词，而应让 Agent 按需读取、搜索和保存中间结果。这样既减轻上下文压力，也更容易观察每一步是怎样发生的。

## 3. 实验准备

我把第 2 章实验与 AgentSeek 模板项目分开，使用独立目录：

```bash
cd /home/charlie/projects/deepagents-course/ch02-quickstart
```

项目使用 Python 3.12 和 uv，核心依赖为：

```bash
uv add deepagents langchain-openai python-dotenv
uv run python -c "import deepagents; import langchain_openai; print('依赖安装成功')"
```

本地 `.env` 保存模型和 LangSmith 配置，但它已被 `.gitignore` 忽略，不进入笔记仓库。代码只读取以下变量名：

```dotenv
OPENAI_API_KEY=<your-api-key>
OPENAI_BASE_URL=<your-openai-compatible-base-url>
MODEL_NAME=<your-tool-calling-model>
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<your-langsmith-key>
LANGSMITH_PROJECT=deepagents-in-action-ch02
```

## 4. 第一个 Deep Agent

实验代码见 [`code/task02/hello_weather.py`](./code/task02/hello_weather.py)。核心结构只有三部分：

1. 用 `ChatOpenAI` 连接 OpenAI 兼容接口；
2. 定义带类型标注和 docstring 的 `get_weather(city: str)`；
3. 把模型、工具和系统提示词传给 `create_deep_agent()`，再调用 `agent.invoke()`。

自定义工具最重要的不是函数有多复杂，而是接口描述是否明确：

- 参数名和类型标注决定模型应生成什么参数；
- docstring 告诉模型工具的用途和调用时机；
- 返回值是 Agent 下一轮判断的观察结果。

本例还在工具内部打印一行标记。这样不能代替 Trace，但能在终端快速确认 Python 函数是否真的执行，避免把模型直接回答误认为工具调用成功。

运行命令：

```bash
cd /home/charlie/projects/deepagents-course/ch02-quickstart
uv run python hello_weather.py
```

实际输出：

```text
[工具被调用] get_weather(city='北京')

最终回答：
北京今天晴朗，气温 24 摄氏度。
```

这说明模型先产生工具调用请求，运行时执行 `get_weather`，再把工具结果交回模型形成最终回答。

## 5. LangSmith Trace

本次成功 Trace 保存在私有项目 `deepagents-in-action-ch02` 中：

- Trace ID：`01a01fc0-5341-7793-ad87-a80e7f0a5773`
- 根运行：`LangGraph (chain)`
- 总耗时：10.52 秒
- 总 tokens：6044
- 模型调用：2 次 `ChatOpenAI`，分别约 5.33 秒和 5.17 秒
- 自定义工具调用：1 次 `get_weather`，工具本身耗时低于 1 毫秒

Trace 展示的关键顺序是：

```text
LangGraph
├── model → ChatOpenAI          # 第一次模型调用，决定调用工具
├── tools → get_weather         # 执行自定义工具
└── model → ChatOpenAI          # 第二次模型调用，结合工具结果回答
```

这个顺序比终端中的“最终回答”更有证明力。最终文字看起来正确，并不能证明工具被调用；Trace 同时保留模型节点、工具节点、参数、返回值、耗时和 token，才能确认完整 Agent 循环确实发生。

可在配置好 LangSmith 环境变量后复查：

```bash
langsmith trace get 01a01fc0-5341-7793-ad87-a80e7f0a5773 \
  --project deepagents-in-action-ch02 \
  --include-metadata
```

Trace 可能包含提示词、工具参数和模型输出，因此本文只记录私有 Trace ID 和脱敏摘要，不公开完整 I/O。

## 6. 踩坑记录

### 6.1 Agent 成功不等于 Trace 成功

第一次运行时，天气工具和最终回答都成功了，但 LangSmith 上传返回 `401 Unauthorized`。检查后发现第 2 章 `.env` 中启用了 `LANGSMITH_TRACING`，却没有提供 `LANGSMITH_API_KEY`。

补齐有效的 LangSmith 凭据并重新运行后，Trace 才真正出现在 `deepagents-in-action-ch02` 项目中。由此可见，验收要分成两部分：

- 应用层：模型是否回答、工具是否执行；
- 可观测性层：Trace 是否成功上传并能查询。

### 6.2 中转接口能聊天，不代表工具调用一定可用

本实验使用 OpenAI 兼容接口。普通对话成功只能证明基本请求格式可用，不能证明 Tool Calling、多轮回传和流式行为都兼容。本次天气实验用“终端工具标记 + LangSmith 工具节点”双重证据验证了自动工具调用，但更复杂的强制工具选择、结构化输出等能力仍应分别测试。

### 6.3 工具的业务结果与调用机制要分开看

`get_weather` 返回的是固定演示数据，并不是真实天气。因此本次实验验证的是“模型选择工具—运行时执行—模型读取结果”的机制，而不是天气数据的真实性。真实项目需要把函数内部替换为可靠天气 API，并处理超时、错误和数据来源。

## 7. 实验心得

这次实验让我把第 1 章的三层概念和第 2 章的代码对应了起来：`ChatOpenAI` 是模型适配，工具函数是可执行能力，`create_deep_agent()` 把模型、工具和 Harness 中间件组装成 LangGraph 上的运行循环。最直观的收获是，Agent 并不是“模型一次回答”，而是模型提出动作、受控代码执行动作、结果回到上下文、模型继续判断的循环。

我也认识到 Trace 不是锦上添花。只看最终回答，很容易误判模型是否真正使用了工具；只有把两次模型调用和中间的工具节点串起来，才能解释 Agent 为什么得到这个答案。以后调试更复杂的研究助手时，我会同时检查终端结果、工具调用次数、Trace 层级、耗时和 token，而不是只看最后一段文字。

## 8. 后续计划：双模型对比

学有余力部分尚未执行。后续会保持提示词、工具、输入和参数完全相同，只修改 `MODEL_NAME`，每个模型重复运行至少 5 次，并记录：

- 是否调用正确工具；
- 工具参数是否正确；
- 是否出现跳过工具或重复调用；
- 完成耗时和 token；
- 最终回答是否忠实于工具返回值。

只有单次成功不足以说明哪个模型“更稳”，重复实验后的成功率和错误类型才有比较意义。

## 9. 原始资料

- [第 1 章：从 Agent Framework 到 Agent Harness](https://datawhalechina.github.io/deepagents-in-action/chapters/ch01-agent-harness/)
- [第 2 章：快速上手——5 分钟构建第一个 Deep Agent](https://datawhalechina.github.io/deepagents-in-action/chapters/ch02-quickstart/)
- [Deep Agents 官方文档](https://docs.langchain.com/oss/python/deepagents/overview)
- [LangSmith 官方文档](https://docs.langchain.com/langsmith/home)
