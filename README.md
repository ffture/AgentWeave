# AgentWeave

AgentWeave 面向软件原型开发、研发任务自动化与智能体工作流构建等场景。针对传统开发流程中需求理解、任务拆解、跨角色协同和质量迭代依赖大量人工协调的问题，项目基于大语言模型构建自组织的多智能体开发系统。系统通过自然语言需求分析、动态角色编排、任务依赖调度、软件产物生成、反馈驱动重构与知识沉淀，形成从需求到持续改进的协作闭环，为软件研发提供可追溯、可扩展的智能化支撑。

系统把模型的认知决策与运行内核的确定性约束结合起来：DeepSeek 负责理解、规划、实现和评审；运行内核管理任务图、生命周期、文件边界与验证结果。每轮任务都有独立工作区和可追溯的运行记录。

## 系统架构

```text
自然语言目标
    │
    ▼
需求契约 ──► 动态组队 ──► 任务依赖图
                            │
                            ▼
                      多角色协作执行
                            │
                            ▼
                       产物与质量评审
                            │
               ┌────────────┴────────────┐
               │                         │
          触发自主重构                进入经验提炼
               │                         ▲
               └──► 修改产物并再次验证 ───┘
                                         │
                                         ▼
                                  长期组织记忆
```

### Multi-Agent：按任务形成研发组织

多智能体协作不是预设的一组固定职位。需求契约智能体先提取功能、约束、质量属性与验收标准；组织拓扑智能体结合本次需求和已积累的经验，生成角色、职责与技能组合。任务编译智能体随后生成带依赖关系的研发任务图，`TaskGraph` 负责校验并按拓扑顺序调度。

执行时，每个任务以对应角色的身份调用模型，并接收当前需求、已有文件及前序任务结果。这样，需求分析、设计、实现、测试与评审可以在同一目标下共享上下文，又保留各自的职责。角色是由模型驱动的逻辑智能体，团队规模和任务顺序由本轮需求决定。

### 自进化：从反馈到自主重构

执行阶段结束后，`VerificationSuite` 检查生成的 Python 与 JSON 文件；质量雷达智能体依据需求契约和产物给出评分、问题与重构机会。`FeedbackEvolutionPolicy` 综合验证结果、质量阈值和重构建议作出决策。需要改进时，系统无需等待新的用户指令，就会创建演化任务，由演化修复智能体修改产物，并再次验证。

这条“生成 → 评估 → 改进 → 再验证”的路径会写入 `run_report.json`，包括触发原因、演化前后的验证结果以及文件变更来源。后续任务还可通过组织记忆检索此前提炼的经验。

### 运行内核与知识沉淀

`AgentWeaveRuntime` 串联研发阶段；`RunLedger` 以状态机记录阶段迁移、执行角色和事件时间；`ArtifactVault` 把每轮文件隔离在独立工作区，校验写入路径并记录修改来源。研发完成后，组织学习智能体将经验和标签保存到 `knowledge/memory.json`。系统也支持从本地文本或网页提炼外部工程知识，供后续任务召回。

## 快速开始

建议使用 Python 3.11。在项目目录中安装：

```bash
cd AgentWeave
uv venv --python 3.11
uv pip install --python .venv/bin/python -e ".[dev]"
```

项目根目录的 `.env` 用于配置 DeepSeek。没有该文件时，可先执行 `cp .env.example .env`，再填写：

```dotenv
DEEPSEEK_API_KEY=你的_API_Key
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

启动交互模式：

```bash
.venv/bin/python -m agentweave --chat --output demo_output_v2
```

安装后也可以使用 `.venv/bin/agentweave --chat --output demo_output_v2` 启动。

可以直接聊天，也可以描述开发任务。完成一轮研发后，继续提出修改要求，下一轮会继承当前项目文件：

```text
你> 开发一个待办事项命令行程序，支持本地保存和单元测试
助手> 正在处理，完成后会给你产物位置…
助手> 已生成项目（… 个文件）：…/workspace
你> 给刚才的程序增加按优先级筛选
助手> 已更新项目（… 个文件）：…/workspace
```

交互命令：`/status` 查看当前项目，`/new` 开始新项目，`/help` 查看帮助，`/exit` 退出。`/new` 不会删除此前生成的产物。

单次提交需求也可以直接运行：

```bash
.venv/bin/python -m agentweave --output demo_output_v2 \
  "开发一个 Python 命令行计算器，支持加减乘除，并提供单元测试"
```

## 知识学习与运行记录

导入本地文本或网页：

```bash
.venv/bin/python -m agentweave --output demo_output_v2 --learn ./engineering-notes.txt
.venv/bin/python -m agentweave --output demo_output_v2 --learn https://example.com/guide
```

每轮研发的主要输出如下：

```text
demo_output_v2/
├── knowledge/memory.json
└── runs/<运行时间>/
    ├── run_report.json
    └── workspace/
```

`workspace/` 保存软件文件；`run_report.json` 保存需求契约、团队配置、任务执行顺序、文件变更、质量评审、演化决策、事件时间线与运行指标。

仓库中的[温度转换 CLI 运行记录](demo_output_v2/runs/20260930-214318-944603/run_report.json)来自一次真实的 DeepSeek 任务：系统形成 3 个角色与 5 个研发任务，记录 13 次文件修订，并在质量评审后自主发起重构。对最终产物独立运行的 21 项单元测试和 6 项验收测试均通过。

## 测试

运行研发内核测试：

```bash
.venv/bin/python -m pytest tests/src/native_dev -q
```

使用 `--offline` 可通过确定性模拟响应检查完整研发流程，不会调用模型 API：

```bash
.venv/bin/python -m agentweave --offline --output demo_output_v2 \
  "开发一个问候程序"
```

正常开发任务使用默认的 DeepSeek 模式。

## 代码结构

```text
agentweave/
├── native_dev/   # 对话入口、研发运行时、任务调度、演化策略与知识库
├── agents/       # 智能体基础组件
├── workflow/     # 工作流组件
├── models/       # 模型适配
├── tools/        # 工具能力
├── memory/       # 记忆组件
├── rag/          # 检索增强组件
├── storages/     # 数据与索引存储
├── optimizers/   # 工作流优化组件
├── evaluators/   # 评估组件
├── benchmark/    # 基准任务与指标
└── hitl/         # 人类在环组件
```

## 其他组件

除交互式研发流程外，代码库还提供可组合的组件，用于构建专门的智能体工作流：

- **RAG 与存储**：`rag/` 包含文档读取、切分、嵌入、索引、检索和结果重排；`storages/` 提供向量、图及关系型存储接口。可以按数据类型和检索策略组合知识处理链路。
- **工作流优化**：`optimizers/` 包含 SEW、AFlow、TextGrad、MIPRO、MAP-Elites 等优化器，支持围绕评估结果调整工作流结构或提示词。
- **评估与基准**：`evaluators/` 负责执行工作流评估，`benchmark/` 提供代码、数学、问答等基准任务与指标，用于比较不同配置的表现。
- **工具集成**：`tools/` 提供文件、命令、搜索、浏览器、数据库和 MCP 等工具接口，让智能体可以在工作流中访问外部资源或执行操作。
- **人类在环**：`hitl/` 提供审批、输入收集与工作流拦截组件，可在需要人工判断的节点接入交互。
- **模型与记忆**：`models/` 包含多种模型适配器；`memory/` 提供上下文管理和长期记忆基础能力，便于在不同工作流中复用。
