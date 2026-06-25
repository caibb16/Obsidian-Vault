# A+B 组合方案可行性分析

> **生成日期**: 2026-06-21
> **目的**: 验证"方向 A（课程式/分层RL）+ 方向 B（多模态可验证奖励）"组合在 2026 年硕士论文中的可行性与新颖度
> **核心结论**: ✅ **可行且撞车风险低**，但必须明确"VLM-as-Judge"这个差异化卖点
> **目标会议**: NeurIPS 2026 / ICLR 2027
> **工作量**: 8-10 个月

---

## 1. 已有的"部分组合"工作

> 数据来源：03_Literature_Gap_Scan_2026.md 的 4 个并行扫描 agent 结果

| 工作 | 命中 A? | 命中 B? | 性质 |
|---|---|---|---|
| **SACA** (2603.09740) | ❌ | ✅ | 单层 GRPO + step-aware auditor |
| **SeeNav-Agent SRGPO** (2512.02631) | ❌ | ✅ | 单层 + step grouping |
| **SPAct** (2604.27620) | ✅ (curriculum) | ❌ | 空间状态转移，**无 RL 训练** |
| **RAGEN-2** (2604.06268) | ❌ | ❌ | 综述类 |
| **MobileForge** (2606.19930) | ❌ (HFPO) | ❌ | Mobile GUI，非 navigation |
| **Goldilocks RL** (2602.14868) | ✅ (difficulty) | ❌ | 通用 RL，未应用 VLN |

> **关键发现**：**没有任何工作同时占据 A 和 B 两个维度**。
> 现有工作要么 "curriculum-only" 但无 RL，要么 "process reward-only" 但单层。

---

## 2. A+B 组合的 4 种可能形态

### 形态 1：课程化 VLM Judge Reward（推荐 ⭐⭐⭐⭐⭐）

**架构**：
```
Curriculum Scheduler (A) → 按难度采样 prompts
       ↓
Multi-turn GRPO Loop
       ↓
VLM-as-Judge (B - 真正 VLM，非 ground truth) → 评估 sub-goal 完成
       ↓
Dense Process Reward
       ↓
GRPO Update
```

**差异化卖点**：
- SACA 用 perception-grounded（GT）—— "硬奖励"
- SeeNav-Agent 用 step grouping + GT —— 仍是"硬奖励"
- **A+B 差异化**：**VLM (Qwen2-VL) 做 soft semantic judgment**，可处理训练集外 landmark
- 课程化提供 sub-goal 序列（易到难的 landmark 链）

**为何不被撞车**：
- 现有 step-level reward 工作都依赖 ground truth/heuristic
- **零工作**用 VLM-as-judge 端到端接入 GRPO loss
- 这是"RLVR from math to embodied AI"的真正迁移

---

### 形态 2：Hierarchical PRM（分层过程奖励模型）

```
High-level Manager (A)
       ↓ 输出 sub-goal
Low-level Worker
       ↓ 行动
Sub-goal PRM (B)
       ↓ VLM 判 sub-goal 完成度
Step-level + Goal-level Rewards
       ↓
两层 GRPO
```

**差异化卖点**：
- HiMemVLN (2603.14807) 有 hierarchical memory，**但非 RL 分层**
- 三步 Nav (2604.26946) 有 hierarchical planner，**但非 RL 训练**
- A+B 差异化：**HIRO-style Manager-Worker 训练 + PRM 评估 sub-goal 完成**

**风险**：
- 工程量大（两个 actor + PRM）
- 理论复杂度高

---

### 形态 3：Curriculum-of-Difficulty × Process Reward

```
Task Difficulty Measurer (A)
       ↓ 
Self-Paced Curriculum
       ↓ 从简单 landmark chain → 复杂
Step Reward (B, SACA 风格 perception-grounded)
       ↓
GRPO
```

**风险**：与 SACA 太近，扩展可能被原作者在下一篇做掉。

---

### 形态 4：Reverse Curriculum + VLM Judge

```
Reverse Curriculum (A, Florensa 2017 风格)
       ↓ 从目标附近起步
Multi-turn Rollout
       ↓
VLM-as-Judge (B)
       ↓
Process Reward
```

**新颖度极高**，但**实现复杂度也高**。

---

## 3. 强烈推荐：形态 1 = 课程化 VLM Judge Reward

**理由**：
1. **新颖度最高**：VLM-as-judge for VLN sub-goals 完全空白
2. **理论清晰**：经典 "课程学习 + PRM" 组合，理论稳固
3. **工程可行**：基于 ActiveVLN 框架改造，4×A100 够用
4. **不被撞车**：SACA/SRGPO 用 ground truth reward，不是 VLM
5. **可扩展**：加 Manager (A 的分层部分) 即可升级为形态 2

---

## 4. 形态 1 实施细节

### 4.1 整体架构

```
┌────────────────────────────────────────────────────┐
│         Curriculum × VLM-Judge RL                  │
├────────────────────────────────────────────────────┤
│                                                    │
│  ┌────────────────┐                                │
│  │ Difficulty      │   L(I) + len(τ*) + topo        │
│  │ Measurer        │                                │
│  └────────┬───────┘                                │
│           ↓                                        │
│  ┌────────────────┐                                │
│  │ Self-Paced      │   P(i) ∝ 1{success(i)>τ}       │
│  │ Scheduler       │                                │
│  └────────┬───────┘                                │
│           ↓ batch of prompts                       │
│  ┌────────────────┐                                │
│  │ Sub-goal         │   LLM 解析指令为              │
│  │ Extractor       │   [g1, g2, ..., gK]            │
│  └────────┬───────┘                                │
│           ↓                                        │
│  ┌────────────────┐                                │
│  │ Multi-turn      │   ActiveVLN 风格               │
│  │ Rollout         │   Qwen2.5-VL Worker            │
│  └────────┬───────┘                                │
│           ↓ trajectory with obs                    │
│  ┌────────────────┐                                │
│  │ VLM-as-Judge    │   Qwen2-VL 判 "是否经过"      │
│  │ (B)             │   "brown couch"/"door"        │
│  └────────┬───────┘                                │
│           ↓ dense per-step reward                  │
│  ┌────────────────┐                                │
│  │ GRPO            │   group-wise normalization     │
│  │ Update          │   A = R - mean / std            │
│  └────────────────┘                                │
│                                                    │
└────────────────────────────────────────────────────┘
```

### 4.2 关键公式

**Reward 组成**：
$$R(\tau) = w_1 \cdot R_{\text{success}} + w_2 \cdot R_{\text{subgoal}} + w_3 \cdot R_{\text{format}}$$

其中：
- $R_{\text{success}} = 15 \cdot \mathbb{I}(\text{success}) \cdot d_{\text{goal}}/3$
- $R_{\text{subgoal}} = \sum_{k=1}^{K} \gamma^k \cdot \mathbb{I}(\text{VLM-judge}(\tau, g_k))$
- $R_{\text{format}} = -0.1 \cdot \mathbb{I}(\text{format error})$

### 4.3 VLM-as-Judge Prompt（关键）

```python
vlm_judge_prompt = """
You are a navigation evaluator. Given:
- Instruction: {I}
- Sub-goal: {g_k} (e.g., "turn left at brown couch")
- Trajectory: Sequence of observations from agent's perspective

Question: Has the agent completed the sub-goal "{g_k}"?

Answer with one of:
- YES (1.0): the agent clearly passed or interacted with "{g_k}"
- PARTIAL (0.5): the agent is near but didn't clearly complete
- NO (0.0): the agent did not engage with "{g_k}"

Provide your confidence (0-1) and reasoning.
"""
```

### 4.4 训练数据准备

**Sub-goal 提取**（LLM 离线生成）：
```python
def extract_subgoals(instruction):
    # 例: "Walk past the kitchen counter, turn left at the brown couch, 
    #      then go through the door to the living room"
    # → ["reach kitchen counter", "turn left at brown couch", "enter living room"]
    return llm_parse(instruction)
```

### 4.5 训练循环伪代码

```python
def train_curriculum_vlm_judge():
    # 阶段 1: 复用 ActiveVLN 的 IL bootstrap
    worker = il_pretrain(expert_trajectories)
    
    # 阶段 2: LLM 离线生成 sub-goals
    sub_goals = {I_i: extract_subgoals(I_i) for I_i in train_set}
    
    # 阶段 3: Curriculum × GRPO with VLM Judge
    curriculum = SelfPacedCurriculum(train_set, difficulty_metric)
    vlm_judge = Qwen2VL()  # 冻结
    
    for step in range(total_steps):
        # 4.1 课程采样
        batch = curriculum.sample(K_prompts)
        
        # 4.2 Multi-turn rollout
        rollouts = []
        for I in batch:
            traj = rollout_worker(worker, I, sub_goals[I])
            rollouts.append(traj)
        
        # 4.3 VLM Judge 评估 sub-goal 完成
        rewards = []
        for traj, I in zip(rollouts, batch):
            r_success = compute_success_reward(traj)
            r_subgoal = 0
            for g_k in sub_goals[I]:
                r_judge = vlm_judge(I, g_k, traj.observations)
                r_subgoal += 0.5 * gamma**k * r_judge
            rewards.append(r_success + r_subgoal)
        
        # 4.4 GRPO 更新
        advantages = group_wise_normalize(rewards)
        worker.update(grpo_loss(rollouts, advantages))
        
        # 4.5 课程更新
        curriculum.update(batch, rewards)
```

---

## 5. 与已有工作的具体差异

| 维度 | SACA | SeeNav-Agent | A+B (本文) |
|---|---|---|---|
| **奖励类型** | Perception-grounded (GT) | Step grouping (GT) | **VLM-as-Judge (semantic)** |
| **课程化** | ❌ | ❌ | **✅ Self-Paced** |
| **Sub-goal 提取** | 自动 (perception) | 无显式 sub-goal | **LLM 解析** |
| **Open-vocab** | ❌ (依赖 GT) | ❌ | **✅ (VLM 见过即可)** |
| **单层/分层** | 单层 | 单层 | 单层 (可升级) |
| **新颖度** | 已发表 | 已发表 | **空白** |

---

## 6. 实验设计

### 6.1 主实验对比

| 方法 | 期望 SR | 关键差异点 |
|---|---|---|
| ActiveVLN-3B RL (baseline) | 50.1 | 主对比 |
| SACA-style (复现) | ~52 | 验证 perception-grounded 路线 |
| SeeNav-style (复现) | ~51 | 验证 step grouping 路线 |
| **A+B (本文)** | **~55** | Curriculum + VLM Judge |
| A+B w/o Curriculum | ~53 | 消融课程 |
| A+B w/o VLM Judge (用 GT) | ~52 | 消融 judge 类型 |

### 6.2 关键消融

1. **Reward Type Ablation**: GT vs VLM-Judge vs Hybrid
2. **Curriculum Ablation**: Self-Paced vs Linear vs Reverse vs Random
3. **Sub-goal Extraction**: LLM vs Heuristic vs Learned
4. **VLM Judge Model**: Qwen2-VL-2B vs Qwen2-VL-7B vs GPT-4V
5. **Difficulty Metric**: Length vs Path vs Topology vs Combined

### 6.3 新增指标

- **Sub-goal Completion Rate (SCR)**: 每个 sub-goal 被 VLM Judge 判为 YES 的比例
- **Judge Reliability**: VLM Judge 与 ground-truth landmark 距离的相关性
- **Sample Efficiency Curve**: SR vs rollout 数

---

## 7. 关键风险与缓解

| 风险 | 概率 | 缓解 |
|---|---|---|
| VLM Judge 不准确 | 中 | GT 距离 + VLM Judge 联合；多 judge ensemble |
| 课程化不稳定 | 中 | curriculum ratio 监控；保留 random baseline |
| Sub-goal 提取错误 | 中 | 多 LLM 投票；ground-truth path 反推 |
| 与 SACA 作者撞车 | **低**（VLM 路线正交） | 强调 "soft semantic judgment" 卖点 |
| 计算资源 | 低（4×A100 够用） | VLM Judge 推理与 worker rollout 并行 |

---

## 8. 时间线（8-10 个月）

| 月份 | 工作 |
|---|---|
| 1-2 | 复现 ActiveVLN + 阅读 SACA/SeeNav 全文 |
| 3-4 | 实现 VLM-as-Judge pipeline + 评估可靠性 |
| 5-6 | 实现 Self-Paced Curriculum Scheduler |
| 7-8 | 联合训练 + 完整消融 |
| 9-10 | 论文撰写 + 投递 NeurIPS 2026 / ICLR 2027 |

---

## 9. 最终判断

> **走 A+B 组合完全可行，且撞车风险低。**
> 
> 关键：
> 1. **强调 "VLM-as-Judge"（非 GT reward）**这个差异化点
> 2. **课程化要用 Self-Paced + 动态难度**（非简单线性）
> 3. **Sub-goal 提取**用 LLM 离线生成，避免额外训练成本
> 4. **目标会议**：NeurIPS 2026 / ICLR 2027

### 论文标题候选

- "Curriculum-Guided Verifiable Rewards for Vision-Language Navigation"
- "From Sparse to Dense: VLM-Judged Process Rewards with Curriculum Learning for VLN"
- "Curriculum × VLM-Judge RL for Embodied Vision-Language Navigation"

### 备选：升级为 A+B+Manager（形态 2）

如果时间充裕，可加 Manager 模块升级为完整 HRL+PRM 方案，对应文献中的更大 gap（**零工作**做 Manager-Worker RL × PRM × MLLM-VLN），目标顶会潜力更高。
