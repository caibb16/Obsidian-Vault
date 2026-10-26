# AI Agent 知识体系

> 本文档基于 JavaGuide《AI Agent 核心概念：Agent Loop、Plan-and-Execute、A2A、Agentic Workflows、Tools 注册》整理，按「演进 → 基础 → 循环 → 工具 → 上下文 → 范式 → 工作流」的脉络组织，方便系统复习。

## 目录

- [[#一、AI Agent 的演进]]
- [[#二、AI Agent 基础]]
- [[#三、Agent Loop 与三层能力]]
- [[#四、工具接入]]
- [[#五、上下文工程]]
- [[#六、Agent 核心范式]]
- [[#七、AI 工作流与选型]]
- [[#八、总结]]

---

## 一、AI Agent 的演进

Agent 的能力不是一次性出现的。模型先获得外部调用能力，随后才有编排、长任务和长期在线这些需求。

| 时间 | 关键变化 |
|---|---|
| 2022 | ChatGPT 类产品走红，模型只能依据已有知识回答问题，不能主动调用外部工具，也不能自行完成操作。**Prompt Engineering** 是当时最重要的使用方式 |
| 2023 中 | **Function Calling** 出现，LLM 能调用外部 API；**RAG** 把外部知识库接进回答过程。AutoGPT 等早期尝试随之出现，但经常在多步任务中重复调用甚至陷入无限循环 |
| 2023 底 | 开始重视编排。**ReAct** 广泛被采用，多 Agent 分工进入实践。Coze、Dify 等平台用 **DAG** 约束执行路径，给完全自治加上可观察、可控制的流程边界 |
| 2024 底 | 标准化和多模态变得重要。**MCP** 处理工具接入碎片化，**Computer Use** 把可执行范围扩展到图形界面。Cursor、Claude Code、Codex 把代码库阅读、修改、测试、提交串进同一条链路，"Vibe Coding" 被更多人讨论 |
| 2025 | 往长任务执行方向走。接收任务、运行流程、留下结果，单条 Prompt 无法稳定覆盖。固定流程、上下文、模板、脚本和校验规则被封装为 **Skill** |
| 2026 | 更接近长期在线的数字工作单元。OpenClaw 这类项目把 Skills 和 **Heartbeat** 推到显眼位置：Skills 封装能力，Heartbeat 周期性唤醒 Agent 检查消息或更新状态 |

**注意**：年份只是便于理解的切片，真实产品往往同时具有多个阶段的特征。较明显的分水岭仍是 **2023 年中**——模型从生成文本逐步获得了执行外部操作的能力。

### Harness Engineering

2026 年的关键变化是关注点从模型参数、上下文长度、Prompt 技巧，延伸到了模型之外的工程环境：

```
Agent = Model + Harness
```

- **Model**：负责推理和生成
- **Harness**：提供可执行、可观察、可恢复、可验证的运行环境

需要清醒认识的是：**Heartbeat 是定时唤醒，不是连续意识**；本地数据主权也不代表绝对安全。能安装 Skill、访问文件和执行脚本的 Agent，必须面对权限、沙箱和供应链风险。

### Agent、传统编程和 Workflow 区别？

先看**谁决定执行路径**，就能把三者区分开：

```
传统编程：程序员写代码 → 执行结果
Workflow：产品画流程图 → 执行结果
Agent：用户说意图 → AI 决策 → 动态执行
```

| 类型 | 适用场景 | 理由 |
|---|---|---|
| 传统编程 | 订单扣库存、支付状态流转、消息队列消费 | 逻辑固定且高频，用 Agent 只会额外增加延迟和不确定性 |
| Workflow | 审批、内容发布、线索分配 | 步骤顺序和分支由图控制，问题能落到具体节点排查 |
| Agent | 「排查今天早上服务变慢的原因」 | 查什么看中间证据，难以事先写死每个分支 |

**通俗理解**：长流程中只有少数环节不确定时，用 Plan-and-Execute，在固定框架里留出动态子任务。

### Agent 面临的挑战

1. **失忆与稀释**：长任务跑久了历史信息被截断；上下文变长后推理质量不一定更好，很多模型对中间位置的信息利用效率并不高
2. **幻觉无法根除**：工具调用能降低幻觉，但 LLM 在推理步骤里仍可能生成错误判断，工具返回结果也不一定能把它拉回来
3. **Token 成本**：多轮迭代、工具调用、日志回传、上下文压缩，每一项都在烧 Token，复杂任务跑一轮账单可能真会让人清醒
4. **安全风险**：Agent 能执行代码、调 API、读写文件，必然面对 Prompt Injection 和越权操作。现实做法是权限最小化、沙箱隔离、高危操作人工确认
5. **局部最优**：深度多步推理任务里容易看起来一直在推进，其实已经偏题
6. **可观测性差**：为什么做某个决策、为什么调用某个工具、是哪一步把上下文带偏了，排查起来很头疼

---

## 二、AI Agent 基础

### 什么是 AI Agent？

一个排障 Agent 收到「服务变慢」的请求后，可能先读监控，再根据告警查日志，最后把结论发给负责人。**每一步都取决于前一步得到的证据**。LangChain 等框架把这类过程封装起来，底层通常仍是一个不断读取状态、选择动作、写回结果的循环。

> AI Agent 是能感知环境、决策并执行动作的软件系统。与只生成回复的聊天机器人相比，它会在任务过程中持续观察和调整，直到结束条件满足。

### 四要素：Agent = LLM + Planning + Memory + Tools

| 要素 | 职责 | 常见实现 |
|---|---|---|
| **Reasoning / Planning** | 决定下一步的目标与动作 | LLM 根据当前任务状态拆解目标；**CoT（Chain-of-Thought）** 把推理过程拆成步骤，减少直接给出未经展开的结论 |
| **短期记忆** | 保持对话连续 | 保存在上下文历史中 |
| **长期记忆** | 检索过去积累的信息 | 向量数据库、知识图谱等外部知识库 |
| **Tools** | 查询数据、调 API、读写文件、执行代码 | 见 [[#四、工具接入]] |

**关键点**：工具执行结果**必须追加进上下文，成为下一轮的 Observation（观察）**。否则模型看不到外部操作的反馈，后续动作也就无从判断。

---

## 三、Agent Loop 与三层能力

### 什么是 Agent Loop？

Agent Loop 把反馈链路连续跑起来。每轮先由 LLM 根据上下文选择动作，再执行工具并写回结果；任务完成或命中停止条件时退出。

```
Loop 初始化
  ├─ 载入 System Prompt
  ├─ 载入工具列表
  └─ 载入用户请求
        ↓
  ┌─────────────────────────────────┐
  │ LLM 在「直接回复」和「调用工具」之间选择 │
  └─────────────────────────────────┘
        ↓ (选择调用工具)
     执行工具 → 结果写回上下文
        ↓
  模型是否仍请求工具？——否→退出
        │是
        └────────── 回到循环
```

- **终止条件**：任务完成，或命中最大迭代轮次（通常 **10～20 轮**），也可按 Token 消耗终止。这个边界用来阻止错误判断把任务带进无限循环
- **上下文膨胀**：上下文随每轮结果不断变长，关键信息被稀释后模型更容易跑偏。这正是 [[#五、上下文工程]] 处理的问题
- LangChain、LlamaIndex、Spring AI 提供的封装不同，**底层都绕不开这条 Loop**

### 做一个 Agent 系统最少要搞定哪三层？

| 层 | 负责什么 |
|---|---|
| **LLM Call** | 处理 OpenAI、Anthropic、Hugging Face 等接口差异，以及流式输出、Token 截断和重试 |
| **Tools Call** | 把 Function Calling、MCP、Skills，以及文件读写、网页搜索、代码沙箱和第三方 API 接给模型。外部能力是否可用、返回什么格式，都会影响下一轮决策 |
| **Context Engineering** | 组织传给模型的 Prompt、动态记忆、会话状态和工具描述 |

上下文缺少任务所需信息，或混入太多无关内容时，**即使模型本身能力足够，任务也可能无法推进**。

---

## 四、工具接入

Agent 想准确调用外部工具，绕不开三样东西，各自卡在链路的不同位置：

> **Function Calling 产生命令，MCP 传递命令并连接工具，Agent 决定这条链路何时继续、何时结束。**

### 三者分工

| 组件 | 厂商叫法 | 解决什么 | 产出 |
|---|---|---|---|
| **Function Calling** | OpenAI 叫 Function Calling，Anthropic 叫 **Tool Use** | 模型如何**表达调用意图** | 结构化的「调哪个工具、传什么参数」 |
| **MCP** | Model Context Protocol | 调用意图如何**接到外部系统** | 工具从哪发现、请求怎么传、结果怎么回 |
| **Agent** | —— | **任务的下一步**是什么 | 继续调用 / 结束任务 / 等待人工确认 |

以「读取仓库最新提交」为例，模型先给出结构化的调用意图：

```json
{ "name": "read_file", "arguments": { "path": "/repo/README.md" } }
```

MCP 负责把这个意图接到外部系统。Agent 则关心任务的下一步：它会读取工具结果，继续调用、结束任务，或等待人工确认；规划、记忆和循环也属于这一层。

| 场景 | 更关键的东西 | 原因 |
|---|---|---|
| 让模型判断要不要查天气 | Function Calling | 重点是模型把意图转成结构化参数 |
| 让 Claude Desktop 读取本地文件 | MCP | 重点是宿主和本地文件系统之间有标准接口 |
| 让 AI 自动排查线上故障 | Agent | 重点是多步决策、工具调用和结果反馈 |

> 实际项目里三者通常会一起出现，表格只是用来区分主要责任边界。

### Function Calling

#### 模型输出结构化调用意图

外部工具可以很复杂，但 LLM 推理时只认结构化描述。Function Calling 让模型直接输出「调用哪个函数、参数是什么」，而不是把调用请求写在自然语言里让程序去猜。

#### Function Calling Schema

现在主流的数据格式基本都在向 **OpenAI Function Calling Schema** 靠拢，Anthropic、Google 这些厂商也都支持类似形式。它用 **JSON Schema** 描述工具名称、用途、参数类型、必填字段。模型根据这段描述判断要不要调用工具，以及参数该怎么填。

```json
{
  "type": "function",
  "function": {
    "name": "query_slow_sql",
    "description": "查指定微服务在特定时间段的慢 SQL 日志。服务响应慢、数据库超时、CPU 飙升的时候用这个。如果用户问的是网络或内存问题，别调这个。",
    "parameters": {
      "type": "object",
      "properties": {
        "service_name": { "type": "string", "description": "服务名，比如 user-service、order-service" },
        "time_range":   { "type": "string", "description": "时间范围，格式 HH:MM-HH:MM，比如 09:00-09:30" },
        "threshold_ms": { "type": "integer", "description": "慢 SQL 判定阈值（毫秒），默认 1000" }
      },
      "required": ["service_name", "time_range"]
    }
  }
}
```

**工具描述写得好不好，会直接影响 Agent 的判断**。描述中应同时给出**适用和不适用**条件——慢 SQL 查询工具明确排除网络和内存问题，模型就不会在方向不符时调用它。

**通俗理解**：description 不是注释，是给模型的「使用说明书 + 说明书之外的禁用清单」。MCP 解决接入方式、JSON Schema 解决描述格式，但模型到底调不调、参数怎么填，最后都靠这里几句话。省了力气，后面会双倍还回来。

#### 一轮完整的 Function Calling

**第 1 步**：把工具列表随请求一起发给模型（就是上面的 Schema）。

**第 2 步**：模型返回 `tool_calls`

```json
{
  "role": "assistant",
  "tool_calls": [{
    "id": "call_abc123",
    "type": "function",
    "function": {
      "name": "query_slow_sql",
      "arguments": "{\"service_name\":\"user-service\",\"time_range\":\"09:00-09:30\"}"
    }
  }]
}
```

注意 `arguments` 是**字符串化的 JSON**，需要反序列化后再使用。

**第 3 步**：Host 执行工具并回填结果

```json
{
  "role": "tool",
  "tool_call_id": "call_abc123",
  "content": "共 12 条慢 SQL，最慢 3.2s..."
}
```

**第 4 步**：再次调用模型，模型基于结果继续决策（再调工具 or 直接回答），直到不再请求工具。

> `tool_call_id` 是配对的关键：并行调用多个工具时，靠它把结果对回正确的调用。

#### 与 MCP 的边界

| | Function Calling | MCP |
|---|---|---|
| 层次 | **数据格式** | **通信协议** |
| 回答的问题 | 工具叫什么、参数什么类型 | 工具从哪发现、怎么传、怎么回 |
| 产出 | 模型侧的结构化调用意图 | 跨进程的 JSON-RPC 消息 |
| 谁主导 | OpenAI 定义，各厂商趋同 | Anthropic 定义，跨厂商通用 |

**Function Calling 已经可以让模型表达「调用哪个接口」。MCP 解决的是同一个工具交付给多个 Host 时的重复集成。**

内部工单系统接入一个 Agent 后，换成另一个 Host 往往还要重写连接、参数和结果处理；把能力封装为 MCP Server 后，支持 MCP Client 的应用可以按同一套发现和调用方式接入。

---

### Skills：进阶封装

一次慢查询排查往往需要依次读日志、运行分析脚本，再按团队规范组织建议。若每次都由 Agent 临时规划，步骤和输出都难以稳定复用。Skill 用**可按需加载的指令文件**保存这条执行链的顺序、约束条件和踩坑记录，宿主判断任务匹配后才把相关内容放入上下文。

| 类型 | 组织形式 | LLM 可见性 | 适用场景 |
|---|---|---|---|
| **Toolkits（黑盒）** | 代码中把多个原子工具组合成高阶工具 | 只看到对外的 JSON Schema，看不到内部路径 | 逻辑固定、需要减少推理步骤和 Token 消耗 |
| **Agent Skills（白盒）** | 以 `SKILL.md` 为入口，自然语言表达任务指令 | 看得到完整执行流程 | 需要沉淀团队经验、又保留任务流程弹性 |

Agent Skills 通常是独立文件夹：

```
.claude/skills/code-reviewer/
├── SKILL.md          ← YAML front-matter + 详细指令
├── scripts/xxx.py    ← 可选：配套脚本
└── reference.md      ← 可选：参考资料
```

`SKILL.md` 前面的轻量元数据用于**发现**，说明 Skill 的用途和触发条件；正文记录流程、约束和示例。宿主先读取元数据，模型判断需要后才加载完整正文——**这种延迟加载是 Agent Skills 与传统 Toolkits 的关键差异**。

Claude Code、Cursor 等工具会扫描项目中的 `.claude/skills/` 目录，由模型决定是否激活某个 Skill。

---

### MCP

#### 1. MCP 是什么，不是什么

MCP 全称 **Model Context Protocol**，中文叫「模型上下文协议」。把全称拆开看就很清晰：

| 词 | 含义 |
|---|---|
| **Model** | 面向大模型应用 |
| **Context** | 把外部上下文、工具和数据源带给模型 |
| **Protocol** | 用一套标准协议把交互方式定下来 |

> ⚠️ **不要把 MCP 理解成给模型加插件**。更准确地说，MCP 是 **MCP Client 和 MCP Server 之间的通信协议**，常被叫作 AI 领域的「USB-C 接口」。

**它解决的痛点**：同一个 Git 工具接到 Claude Desktop、Cursor 和自建 Agent 时，往往要各写一层适配。工具参数、鉴权方式或版本一变，接入它的多个客户端都得跟着改。

有了 MCP 之后，Git 相关能力可以封装成一个 MCP Server。Host 里的 MCP Client 连上它，**先发现有哪些工具，再按协议调用工具，最后把结果交给模型继续分析**。协议适配集中在 Server 一侧，Agent 或 AI 应用只需理解用户问题、选择工具并组织结果，两边不必为每个客户端重新约定一套私有接口。

**类比**：这和前后端通过接口契约协作相似——Agent 开发关注任务和交互，工具开发关注能力实现、数据权限和操作边界。

#### 2. 协议版本演进

| Revision | 关键变化 |
|---|---|
| 2024-11-05 | MCP 首次发布 |
| 2025-03-26 | 早期 HTTP+SSE 传输调整为 **Streamable HTTP** |
| 2025-06-18 | 加入 **Elicitation** |
| **2025-11-25** | 当前稳定版；增加实验性的 **Tasks**、**URL 模式 Elicitation** |

> 客户端和 SDK 可能只实现其中一部分。接入前要**同时确认协议 revision、SDK 版本和 Host 能力**。

#### 3. 三个角色：Host / Client / Server

```
┌──────────────────────────────────────────────────┐
│ Host    Claude Desktop / Cursor / VS Code 插件 /  │
│        自建 Agent 平台                           │
│  └─ Client    每个 Server 一个会话                 │
│       └─ Server    开发者编写这一侧                │
│            └─ 数据源  本地文件 / 数据库 / 平台 / API │
└──────────────────────────────────────────────────┘
```

| 角色 | 职责 |
|---|---|
| **Host** | 用户使用的 AI 应用，负责承载用户交互和模型调用 |
| **Client** | 位于 Host 内部，负责与 Server 建立会话和交换协议消息。一个 Host 可连多个 Server，通常每个 Server 对应一个 Client 会话 |
| **Server** | **开发者主要编写这一侧**。文件读取、SQL 查询、GitHub Issue 查询、内部工单查询等能力都由它向 Host 暴露 |
| 数据源 | Server 后面的本地文件、数据库、内部平台、GitHub 或第三方 API。**不属于 MCP 的协议角色**，Host 只通过 Client 调用 Server，查库、请求 API 等底层实现留在 Server 内部 |

#### 4. Server 侧能力：Resources / Tools / Prompts

很多讨论 MCP 时只讲 Tools，但 MCP 里不只有工具。

| 原语 | 用途 | 例子 |
|---|---|---|
| **Resources** | 提供**只读上下文** | 本地文件、日志片段、数据库 Schema、配置记录 |
| **Tools** | **执行动作**，会主动执行逻辑、可能改变外部状态 | 查询数据库、发送消息、创建工单、调用业务接口 |
| **Prompts** | 可复用的提示词模板 | 「按团队规范做代码审查」「把接口文档整理成测试用例」 |

**选择原则**：会主动执行逻辑、可能改变外部状态的能力，应当放在 Tools 中。

**谁来触发**：Tools 通常由**模型**选择并调用；Resources 和 Prompts 的展示、选择方式还可以由 **Host、用户界面或应用逻辑**决定。

**「凉拌黄瓜」类比**——G 友说「我想吃凉拌黄瓜」，LLM 扮演厨师，知道大概怎么做，但还需要外部条件：

| 原语 | 类比 |
|---|---|
| Resources | 食材和菜谱：冰箱里有什么、有没有黄瓜、调料放在哪 |
| Tools | 具体动作：切菜、拌料、开火、下单买菜 |
| Prompts | 家里的固定偏好：少放辣、必须放香菜、不能放蒜 |

如果工具描述写错了，比如把「黄瓜」描述成「西红柿」，模型就可能选错东西。

落到生产环境，工具名、参数描述和返回结构都直接影响 Agent 的选择和后续判断。**Server 能启动只是开始，能力边界还要让模型能准确理解。**

#### 5. Client 侧能力：Roots / Sampling / Elicitation

除了 Server 侧能力，Client 侧也可以提供一些能力给 Server 使用。

| 能力 | 方向 | 用途与注意 |
|---|---|---|
| **Roots** | Host → Server | 告诉 Server 当前会话预期在哪些文件系统根目录内工作。Host 可以只公布当前项目目录，不公布用户主目录。**它是能力协商和范围提示，不会自动形成文件系统沙箱**；Server 仍要做路径规范化、越界检查和 OS 级权限隔离 |
| **Sampling** | Server → Host | 允许 Server 请求 Host 侧的 LLM 做一次生成。比如 Server 读取到一段日志后，希望借助模型做摘要或分类 |
| **Elicitation** | Server → Host | Server 在执行过程中向用户补充询问信息。参数不完整、选项有歧义、执行前需用户确认时，由 Host 侧展示交互 |

大多数 MCP Server 可以先只提供 Tools；需要只读上下文或可复用任务入口时，再考虑 Resources、Prompts。

> **Roots、Sampling、Elicitation 和 Tasks 还取决于对应 Client 是否实现，不能只看 Server SDK 有无接口。**

#### 6. 为什么用 JSON-RPC 2.0

REST 更偏**资源**（`/users/1`、`/orders/100`）；JSON-RPC 更偏**方法调用**（`tools/call`、`resources/read`）。AI 工具调用天然就是「我要执行某个动作」，所以 JSON-RPC 和 MCP 的使用场景比较贴。

```json
// 请求（方法调用，而不是资源路径）
{ "jsonrpc": "2.0", "id": 1, "method": "resources/read",
  "params": { "uri": "file:///repo/README.md" } }

// 成功：只返回 result
{ "jsonrpc": "2.0", "id": 1,
  "result": { "contents": [ { "uri": "file:///repo/README.md", "text": "文件内容..." } ] } }

// 失败：才返回 error
{ "jsonrpc": "2.0", "id": 1,
  "error": { "code": -32602, "message": "Invalid params" } }
```

**语义规则**：成功响应只返回 `result`，失败响应才返回 `error`；**不要在成功响应中再附上 `error: null`**。

**取舍**：JSON-RPC 消息是文本格式，便于记录日志，也不绑定具体传输方式。代价是没有 gRPC 那样的强 IDL 和编译期类型约束。MCP 虽然能用 JSON Schema 描述工具参数，但 Schema 既是运行时校验规则、也是给模型的提示，**Server 仍需对所有参数做严格校验**。

#### 7. 一次完整调用走一遍

以「分析这个仓库的最新提交」为例：模型发现自己缺少 Git 日志后先生成工具调用，Host 把调用交给 MCP Client，Client 通过 JSON-RPC 请求 Server，Server 查询 Git，再把结果沿原路径返回，模型据此组织回答。

**① 初始化握手**

Client 发送 `initialize`，带上自己支持的协议版本和能力列表；Server 返回自己支持的协议版本、能力和基础信息。确认之后 Client 再发 `initialized` 通知，双方才进入可用状态。

```json
// Client → Server
{ "jsonrpc": "2.0", "id": 1, "method": "initialize",
  "params": {
    "protocolVersion": "2025-11-25",
    "capabilities": { "roots": { "listChanged": true }, "sampling": {} },
    "clientInfo": { "name": "my-agent", "version": "0.1.0" }
  } }

// Server → Client
{ "jsonrpc": "2.0", "id": 1,
  "result": {
    "protocolVersion": "2025-11-25",
    "capabilities": { "tools": { "listChanged": true } },
    "serverInfo": { "name": "git-server", "version": "0.1.0" },
    "instructions": "可选的使用说明，会被塞进上下文"
  } }
```

> **这一步的意义**：Client 能知道 Server 支持哪些能力（只有 Tools？还是有 Resources 和 Prompts？），Server 也能知道 Client 的限制。很多「Server 配好了但工具没出现」的问题，排查时都应该**先看初始化阶段有没有失败**。

**② 能力发现**

```json
{ "jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": { "cursor": null } }
```

返回 `tools` 数组，每项含 `name` / `description` / `inputSchema`（JSON Schema）/ `outputSchema` / `annotations`（`readOnlyHint`、`destructiveHint` 等），外加 `nextCursor` 分页游标。`resources/list`、`prompts/list` 同理。

工具集变化时 Server 会推 `notifications/tools/list_changed`，Host 收到后重新 list 并刷新缓存。

**③ 调用意图映射**

Host 把 `tools/list` 结果翻译成模型认识的 Function Calling Schema：

```json
{ "type": "function",
  "function": { "name": "read_file", "description": "...", "parameters": { ... } } }
```

注意这里**只有 name 和 description，没有 serverId** —— 模型选不调、参数填得对不对，全看 description 写没写清适用与不适用条件。

**④ tools/call**

模型返回 tool_calls 后，Host 用本地路由表 `工具名 → (serverId, toolName)` 找到归属，翻译成 JSON-RPC：

```json
// Client → Server
{ "jsonrpc": "2.0", "id": 3, "method": "tools/call",
  "params": { "name": "read_file", "arguments": { "path": "/repo/README.md" } } }

// Server → Client
{ "jsonrpc": "2.0", "id": 3,
  "result": {
    "content": [ { "type": "text", "text": "文件内容..." } ],
    "structuredContent": { },
    "isError": false
  } }
```

- `content` 是数组，可含 `text` / `image` / `audio` / `resource`（内嵌）/ `resource_link`
- **业务错误以 `isError: true` + 文本说明返回**，而不是 JSON-RPC error，好让模型读懂并自我纠正
- **Server 接收到的参数必须视为不可信输入**：文件读取要限制目录，SQL 要参数化，高危操作要审批，返回数据要脱敏

**⑤ 回到 Agent Loop**

Host 把 result 拼成 `role: "tool"` 的消息（带 `tool_call_id`）追加进 messages，回到模型继续推理，直到模型不再请求工具或命中迭代上限（通常 10–20 轮）。

```
用户请求 → LLM → tool_calls → 路由表 → tools/call
 ↑                                      ↓
    └────────── role:"tool" 消息 ←──── Server 执行
```

**⑥ 传输方式选择**

| 场景 | 推荐 | 理由 |
|---|---|---|
| 本地工具、本地文件、个人使用 | `stdio` | Host 将 Server 作为子进程启动，通过 stdin/stdout 交换消息，Claude Desktop 中很多本地 Server 都采用这种方式。没有额外网络部署成本 |
| 团队服务、远程 API、多用户访问 | `Streamable HTTP` | 消息收敛到统一端点后，认证、负载均衡和网关接入可沿用普通 HTTP 服务的运维方式 |

**stdio 的两个坑**：

1. **Server 运行在本机**，文件、Shell 和数据库权限要单独收紧
2. **stdout 是 JSON-RPC 消息通道，不能用于打印调试日志**。一行 `print()` 就可能破坏消息格式，导致 Host 解析失败或 Server 断连。调试日志应写入 **stderr** 或文件；排查「Server 启动失败」时，也要确认 stdout 中没有混入日志

**Streamable HTTP 请求示例**：

```
POST /mcp
Authorization: Bearer xxx
```

响应可能是普通 JSON，也可能是 SSE 流，取决于请求类型。

> 涉及写操作和敏感数据时，不管哪种传输方式，都要额外做鉴权、限流和审计。第三方 Server 最好别直接裸跑——至少先看源码，或用 Docker、cgroups、namespace 这类方式隔离。

#### 8. 写 MCP Server 的注意事项

**别先追求大而全**

一个 Server 常见的错误，是用少量「万能工具」承载所有操作：

```python
execute_sql(sql)                # ❌ 操作范围和权限全交给模型猜
file_operation(op, path, data)  # ❌ 参数越多，误用和越权的空间越大
call_api(url, method, body)     # ❌
```

按业务动作拆分后，Schema、权限和审计规则才能分别落到具体工具上：

```python
get_user_by_id(id)              # ✅
list_active_orders(user_id)     # ✅
read_file(path)                 # ✅
write_report(path, content)     # ✅
```

工具名可以采用**动词加名词**，description 说明适用条件、必填参数和禁用场景。

**大文件和长文本要小心**

日志、Markdown 文档、网页 HTML 和 CSV 文件可能远超模型上下文。资源接口可以先返回文件名、大小、更新时间、摘要和可读取范围，需要内容时再按 chunk 读取。

- 单个 chunk 控制在约 **100KB**
- 资源超过 **10MB** 时只返回说明和可选读取方式，不直接返回全文
- **不要把限制绑定到某个模型的 tokenizer**（不同模型 token 计算不同），用字符数或字节数做粗粒度控制即可；上下文裁剪交给 Host 或上层应用

**安全问题不能靠相信模型解决**

| 风险 | 措施 |
|---|---|
| 路径遍历 | 文件读取在**路径规范化后**检查目录边界，不能让 `../` 越出允许范围 |
| SQL 注入 | 使用参数化语句，不能将模型生成的字符串直接执行 |
| 数据泄露 | 手机号、邮箱、Token、密钥、内部链接等返回数据需要**脱敏** |
| 越权操作 | 删除文件、修改数据库、发送邮件、调用生产接口等写操作默认收紧权限，设置人工确认与审计 |
| 死循环 | 模型可能反复调用同一工具，**限速、超时、熔断和配额要由 Server 自身落实**，不能假设 Host 一定会兜底 |

Server 的 description、Prompt 模板和返回内容同样需要审核——恶意或粗糙的内容可能夹带提示词注入，引导模型读取更多文件或外传信息。

#### 9. 上生产前的检查清单

Demo 中「装一个 Server，问一句话，拿到结果」的链路很短，生产环境要补齐接口约束、审计和运行治理。

> **这些检查项和普通后端服务没有本质区别——MCP 改变了工具接入方式，不会替代鉴权、审计、日志、版本和限流。**

| 维度 | 检查项 |
|---|---|
| **Schema 和版本** | 每个工具是否有明确输入输出 Schema？字段单位、时间格式、枚举值、默认值是否写清楚？工具接口是否有版本号？不兼容变更有没有灰度和回滚方案？ |
| **权限和安全** | Server 能访问哪些文件、目录、数据库和 API？是否区分只读工具和写操作工具？高危操作是否需要人工确认？返回结果是否脱敏？是否防路径遍历、SQL 注入、命令注入？第三方 Server 是否经过源码、依赖和权限审核？ |
| **可观测性** | 每次用户请求是否有 Trace ID？工具调用参数、耗时、结果摘要、错误码是否有结构化日志？是否能还原一次 Agent 回答背后的完整工具调用链？是否有超时、限流、熔断和重试策略？ |
| **成本归因** | 每次调用是否能关联到用户、业务线、工具和会话？Token / API / 云资源成本是否能拆分统计？是否有配额和预算告警？模型循环调用工具时，是否有调用次数上限？ |
| **依赖治理** | MCP SDK、第三方库、第三方 Server 是否有维护者和更新记录？安全漏洞谁负责跟进？Server 升级是否有测试环境和回滚策略？是否避免把核心能力押在无人维护的三方扩展上？ |

**Schema 细节尤其容易翻车**：时间字段是 ISO-8601 还是时间戳、金额单位是元还是分、分页默认值是什么，都要写进 Schema、字段说明和示例。Server 要据此校验参数，并返回**模型能够据以修正请求的错误信息**。

**可观测性容易被忽略**：一条 Agent 回答可能经过多个 Server 和工具。Trace ID、结构化日志和调用链需要记录调用参数、耗时、结果摘要与错误码，才能定位**哪一步影响了最终回答**。

#### 10. 最小示例与本地调试

用官方 Python SDK 写一个天气 Server：

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather-server")

@mcp.tool()
def get_weather(city: str) -> str:
    """获取指定城市的天气信息"""
    return f"{city} 今天晴天，温度 25°C"

@mcp.resource("weather://forecast")
def weather_forecast() -> str:
    """返回未来一周天气预报"""
    return "未来七天天气预报..."

if __name__ == "__main__":
    mcp.run()
```

Claude Desktop 里这样配：

```json
{
  "mcpServers": {
    "weather-server": {
      "command": "uv",
      "args": ["run", "--with", "mcp", "/path/to/weather_server.py"]
    }
  }
}
```

**本地调试直接用 MCP Inspector**，它可以模拟 Host 发请求：Server 初始化有没有问题、工具能不能被发现、参数校验有没有报错，基本都能先在这里看出来。

```bash
# Python Server
npx @modelcontextprotocol/inspector uv run --with mcp /path/to/weather_server.py

# Node Server
npx @modelcontextprotocol/inspector node build/index.js
```

**实现最小 Server 时，先固定协议 revision 和 SDK 版本**，用 Inspector 验证初始化、能力协商、参数校验和错误响应。准备接入远程服务后，再补 OAuth、限流、Trace、版本兼容和回滚；文件与命令工具还要在 Server 侧落实目录校验和沙箱。

> 生产环境别依赖全局 python 里刚好装了 mcp。用虚拟环境解释器，或像上面这样用 `uv run --with mcp ...` 显式声明依赖，会稳一点。如果 Claude Desktop 启动失败，先看 `mcp.log`，别一上来怀疑协议有问题——很多时候只是路径或依赖没配对。

#### 面试表述

> MCP 全称 Model Context Protocol，是 **MCP Client 和 MCP Server 之间的通信协议**，常被叫作 AI 领域的「USB-C」。它不是给模型加插件，而是把「工具名 → 执行函数」的映射从业务代码搬到了协议层。
>
> 它和 Function Calling、Agent 分工不同：**Function Calling 产生结构化调用意图，MCP 把意图接到外部系统，Agent 决定链路何时继续、何时结束**。
>
> 调用流程四步：一是握手，Client 发 `initialize` 协商协议版本并交换能力，Server 返回后 Client 再发 `initialized` 通知；二是发现，Client 调 `tools/list` 拿到工具的 JSON Schema 描述并缓存；三是映射，Host 把这些 Schema 翻译成 Function Calling 格式喂给模型，模型只产出工具名和参数，Server 归属由 Host 的本地路由表决定；四是调用，Host 翻译成 JSON-RPC `tools/call` 发给对应 Server，结果拼成 `role: "tool"` 消息回填上下文，进入下一轮循环。
>
> 传输层本地用 stdio、远程用 Streamable HTTP，全程 JSON-RPC 2.0。业务错误以 `isError` 返回而非 JSON-RPC error，好让模型读懂并重试。MCP 暴露的不只是 Tools，还有 Resources（只读上下文）和 Prompts（提示词模板）；反向还有 Roots、Sampling、Elicitation。
>
> 但**接进来不等于能上生产**：Schema 版本、权限安全、可观测性、成本归因、依赖治理五项检查一个都不能少。写 Server 时也别追求大而全——`execute_sql(sql)` 这种万能工具会把权限交给模型猜，应该拆成 `get_user_by_id`、`list_active_orders` 这类细粒度接口。

---

## 五、上下文工程

上下文混入过多无关信息时，模型即使具备相应能力，任务效果也会下降。

### Prompt Engineering

Prompt 是给大模型的指令与上下文。Prompt Engineering 要处理的是**任务边界、输出格式和约束条件**：缺少这些信息时，模型只能自行猜测；条件明确后，输出才有稳定的依据。

### Context Engineering

做的事情是在有限 Token 窗口里，**把最有用的信息喂给模型，把噪声挡在外面**。管的范围比 Prompt Engineering 更宽：

| 维度 | Prompt Engineering | Context Engineering |
|---|---|---|
| 侧重点 | 提示词**怎么写** | 上下文**装什么、怎么组织** |
| 覆盖范围 | 任务边界、输出格式、约束条件 | 上述全部 + 规则、记忆、工具描述、会话状态、外部观察结果、Token 预算 |

**通俗理解**：Prompt Engineering 管「这一句话怎么说」，Context Engineering 管「这一轮对话的桌上摆哪些纸」。两者容易混，但后者是前者的超集。

---

## 六、Agent 核心范式

### ReAct

**Reasoning + Acting**，由 Shunyu Yao 等人在 2022 年提出。LangChain、LlamaIndex、AgentScope 这类框架的 Agent 模块都能看到它的影子。

思路很直观：模型先推理一步，拿到外部环境反馈，再推理下一步，交替进行。LLM 自己容易缺少实时信息，也容易幻觉，ReAct 就让它「**走一步看一步**」。

**排障示例**——「帮我排查今天早上 user-service 接口变慢的原因，并把结果发给负责人」：

| 步骤 | 动作 | 得到的证据 |
|---|---|---|
| 1 | 查 user-service 早上监控 | 9:00–9:30 CPU 飙到 98%，大量慢 SQL 告警 |
| 2 | 顺着这条线翻日志 | 捞出那条慢 SQL，是没走索引的全表扫描 |
| 3 | 查服务负责人通讯录 | 王建国，wangjianguo@company.com |
| 4 | 组织排查报告并发邮件 | 完成 |

这个过程**不是一开始就写死的**。如果监控显示的是内存 OOM，第二步就应该去查 Heap Dump，而不是继续翻慢 SQL。**ReAct 的价值就在这里：它能根据证据不断修正方向。**

落地组件：

- **历史上下文**：保存推理步骤、执行动作、反馈观察
- **实时环境输入**：系统告警、用户反馈等外部变量
- **LLM 推理模块**：负责逻辑分析和下一步规划
- **工具集与技能库**：包括原子工具和 Skills
- **反馈观察机制**：采集工具响应并追加回上下文

| 优点 | 代价 |
|---|---|
| 每步由外部观察推动，比一次性生成更容易追溯决策依据 | 多轮调用增加响应延迟 |
| 减少脱离环境的判断 | 效果取决于工具和 Skills 是否可靠 |

例如把「查监控、查日志、分析瓶颈」封装为 `diagnose_service_performance` Skill，向 LLM 返回结构化诊断摘要，就无需每次排障都从原子步骤重新组合。

### Plan-and-Execute

LangChain 团队在 2023 年提出：**先由 LLM 生成全局分步计划，再交给执行器逐项完成**。步骤较多、依赖关系明确的长任务用这种方式，更容易保持全局进度。

**边界**：执行过程中若出现未预料的结果，动态调整和容错能力会弱于边做边判断的 ReAct，行为更接近静态工作流。

**两种模式可以嵌套**：用 CoT 给出全局步骤，每个步骤内部运行 ReAct 子循环——**计划提供结构，子循环处理局部的不确定性**。

### Reflection

通过自然语言反馈纠正 Agent 行为，**不需要修改模型权重**。常见实现分别处理不同阶段：

| 方法 | 机制 |
|---|---|
| **Reflexion** | 任务失败后记录反思结论到记忆缓冲区。例如代码调试发现 `count` 在调用前未初始化，下一轮可据此规避 |
| **Self-Refine** | 让模型在完成回答、代码或文案后审查自己的输出，再迭代修改 |
| **CRITIC** | 借助搜索引擎、代码执行器等外部工具验证事实，再按验证结果修正 |

Reflection 通常**叠加**在 ReAct 或 Plan-and-Execute 上：执行过程中加入校验与调整，具体任务仍由原有的执行机制完成。

### Multi-Agent

任务能拆成规划、执行、验收等相对独立的职责时，可以交给多个 Agent 协作。

| 模式 | 结构 | 适用 |
|---|---|---|
| **Orchestrator-Subagent** | 编排 Agent 制定全局计划、分发任务，子 Agent 并行或串行执行，再由编排层汇总 | 任务能按专业角色拆分 |
| **Peer-to-Peer** | 地位对等的 Agent 直接对话和审查 | 需要辩论、评审或相互验证 |

| 优点 | 代价 |
|---|---|
| 可并行执行，单个子任务失败未必阻断整体 | Agent 间通信、协调和调试成本上升 |
| 职责边界清晰 | Token 消耗随之增加 |

落地时还要处理**任务契约、共享状态、并行写冲突、Worker 接管、检查点恢复**。

### A2A 协议

单个 Agent 升级到 Multi-Agent 后，Agent 之间怎么沟通会变成一个工程问题。如果还靠自然语言互相聊天，Token 消耗很高，也容易出现格式解析错误。

**A2A 协议**让 Agent 之间用结构化数据交互（带 Schema 的 JSON、XML，或者状态流转指令），而不是一堆自然语言废话。

**类比**：后端微服务之间不会通过解析 HTML 页面交换数据，而是用 RESTful 或 RPC 接口传结构化对象。A2A 就是给 Agent 之间定义接口契约。

```
产品经理 Agent 不输出：「我写好了，你开发一下」
                ↓ 而是
{ "taskId": "...", "dependencies": [...], "acceptanceCriteria": [...] }
                ↓
开发 Agent 直接反序列化，进入执行流程
```

---

## 七、AI 工作流与选型

### Agentic Workflows

吴恩达（Andrew Ng）重点倡导的概念，强调**用工程编排**把推理、工具、记忆、反思和多实体协作接成可执行流程，而不只等待底层模型能力变化。

常见设计模式：

| 模式 | 含义 |
|---|---|
| Reflection | 让模型检查自己的工作 |
| Tool Use | 给 LLM 配网络搜索、代码执行等工具 |
| Planning | 让模型提出多步计划并执行 |
| Multi-agent Collaboration | 多个 Agent 协作完成任务 |

这些模式在真实项目中**通常组合出现**：例如先用 Planning 拆分任务，在子任务中运行 ReAct、调用 Tools，最后用 Reflection 检查结果。Agentic Workflows 描述的是这种组合方式，而不是某个单独框架。

### 工作流里的 Node、Edge、State

Workflow 运行时三者组成有向图（Graph）：

| 概念 | 职责 | 说明 |
|---|---|---|
| **Node（节点）** | 读取状态、执行逻辑、写回结果 | 节点里可以调 LLM，可以是工具调用，也可以是纯代码逻辑。职责越单一越好排查 |
| **Edge（边）** | 决定执行完跳到哪 | 顺序边按路径走，条件边根据运行时状态分支，循环边让流程回到之前的节点重试 |
| **State（状态）** | 节点之间共享上下文 | 条件边的跳转往往基于 State 里的值来判断 |

**写文章场景**的典型节点：「生成初稿」→「质量审核」→「按反馈修改」。

「审核不通过就回到修改，最多重试 3 次」翻译成图结构：

```
ReviseNode → ReviewNode ──(通过)──→ ExitNode
                  │
            (不通过 且 iteration_count < 3)
                  ↓
              ReviseNode
```

一条从 `ReviewNode` 指向 `ReviseNode` 的**条件边**，加上 `iteration_count >= 3` 时跳到 `ExitNode` 的**安全边界**。State 里的 `iteration_count` 是让这套重试逻辑真正跑起来的关键。

这套图结构比写死的 if-else 链更容易扩展，出了问题也好定位到哪个节点哪条边。**LangGraph（Python）** 和 **Spring AI Alibaba Graph（Java）** 都是基于这套思路实现的。

### AI 工作流和 Agent 到底是什么关系？

| 形态 | 特点 |
|---|---|
| **纯 Agent** | 由 LLM 在运行中决定是否调用工具、调用什么工具、后续路径。适合查什么、怎么查取决于中间证据的任务 |
| **AI 工作流** | 「生成初稿、质量审核、按反馈修改」这类步骤顺序和重试条件可预先写进图结构，LLM 只在某个节点生成或判断 |
| **Agentic Workflows** | **全局 Workflow 固定主流程，只在路径不确定的局部嵌入 Agent 子循环** |

### 什么时候用 Agent，什么时候用 Workflow？

**判断标准一：执行路径能不能提前确定。** 能确定用 Workflow，不能确定用 Agent，两者都有用 Agentic Workflows。

> **常见认知偏差**：很多人觉得任务「路径不确定」，其实是需求没拆清楚。把任务认真拆一遍后，往往会发现大部分场景是「LLM 在固定节点里做生成或判断」，这种用 Workflow 更稳，也更容易排查。

真正适合纯 Agent 的任务，是那种**你提前写不出执行步骤**的场景。比如「帮我排查这个线上故障」，查什么、怎么查、查到什么程度，很难事先规定死。

**判断标准二：容错要求。** Workflow 执行路径固定，出问题好排查；Agent 执行路径动态，调试难度高一个数量级。**To B 商业场景优先考虑 Workflow 或 Agentic Workflows**。

### 各范式怎么选？

| 场景特征 | 推荐方向 | 代价 |
|---|---|---|
| 执行路径可提前确定，节点需要 LLM | AI 工作流（Graph） | 稳定可观测，前期设计成本高 |
| 执行路径不确定，需要动态规划 | ReAct | 灵活，Token 消耗高，调试难 |
| 任务很长，步骤多但结构清晰 | Plan-and-Execute | 不易迷路，动态调整弱 |
| 输出质量要求高，允许多轮迭代 | 叠加 Reflection | 和 ReAct / P&E 配合用，不单独用 |
| 任务天然可拆成多个专业角色 | Multi-Agent | 通信和调试成本翻倍 |
| 长任务 + 部分子任务不可预测 | Agentic Workflows | 全局 Workflow + 局部 ReAct 嵌套 |

**先用最简单的方式跑通，再根据实际失败模式决定升级哪一层。** 上来就搞 Multi-Agent、全靠模型动态推理、上下文不做任何管理，踩进去了再爬出来会很费劲。

---

## 八、总结

大部分 Agent 项目跑起来不稳定，不是模型不够好，而是**基础没搭好**。

`LLM + Planning + Memory + Tools` 四块，缺哪个都有明显短板：

| 缺哪块 | 后果 |
|---|---|
| Tools | Agent 停留在「给建议」阶段 |
| Memory | 稍微长一点的任务就开始失忆 |
| 上下文管理 | 模型随便跑偏 |
| 工具描述 | 该调的不调、参数填不对，排查成本翻倍 |

选型也容易选错：

- **ReAct** 灵活但调试难，Token 烧得也多
- **Workflow** 稳但对需求拆解要求高，前期设计不够充分后面改起来费劲
- **Multi-Agent** 接入后通信和调试成本容易超出预期

上来就搞最复杂的方案，是工程实践里最常见的陷阱。

**Agent 和工作流的选型其实没那么复杂**：先把任务执行路径写出来，能写出来就用 Workflow，写不出来再上 Agent。这个判断先做好，比追框架有用得多。