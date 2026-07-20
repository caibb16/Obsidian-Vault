# 方向 D：指令即程序 —— VLN 的构成式过程奖励验证框架

> **副标题**：走向语义验证，超越物理度量 —— 当过程奖励不再问"近了吗？"而问"指令执行到哪一步了？"

> **生成日期**：2026-07-20
> **关联文档**：`00_Overview_RL_VLN_Innovation_Directions.md`
> **基础论文**：SeeNav-Agent (Wang 2025) · SACA (Li 2026)

---

## 0. 动机：一个根本性的问题重置

现有 VLN 过程奖励方法（包括 SeeNav-Agent 和 SACA）全部共享一个隐性假设：

> **"好的过程奖励 ≈ 精确地度量物理进展"**

SeeNav-Agent 度量"离目标更近了吗"（距离变化），SACA 度量"能看到当前地标吗"（感知匹配）。两者本质上都是在做 **point-wise 的物理状态度量**。

但导航任务的最终目标是**执行指令**，而非物理接近。

这个区别极其微妙但本质不同：

```
指令："绕过餐桌，向左走向岛台，右转进入厨房，在微波炉前停下"

物理进展视角（现有方法）：    "智能体离微波炉 5m → 3m → 1m ✓"
指令执行视角（本方法）：      "已完成：经餐桌 ✓ → 左转向岛台 ✓ → 入厨房 ✓ → 到微波炉前 ✓"
```

现有方法的奖励信号可以描述为：

| 每步问的问题 | 对应方法 |
|---|---|
| "这步比上步离目标更近了吗？" | SeeNav-Agent VPR |
| "当前能看到指令中提到的地标吗？" | SACA PGSA |

**但从未被问过的问题**：

| 从未被问的问题 | 为什么重要 |
|---|---|
| "这步在指令执行链中处于什么位置？" | 缺少时序上下文，无法区分"提前看到地标"和"按顺序到达" |
| "这步是否跳过了某个关键子任务？" | 无法检测"绕过餐桌直接去厨房"这样的捷径违反 |
| "这步是否在系统性地欺骗奖励函数？" | 无法检测 zigzag / 原地旋转等 reward hacking |
| "如果这是最后一步，目前执行过的指令片段是否完整？" | 奖励与最终目标的语义对齐不足 |

**核心论点**：过程奖励应该从 **"物理进展度量"** 升维到 **"指令执行验证"**。不是问"近了吗？看到了吗？"，而是问"指令执行到哪一步了？当前状态满足约束链吗？"

---

## 1. 问题陈述与研究动机

### 1.1 现有方法的两大盲区

通过对 SeeNav-Agent（2025）和 SACA（2026）的深度对比分析，我们识别出五个共性的深层盲区：

#### 盲区 1：点式度量而非结构验证

| | SeeNav-Agent VPR | SACA PGSA |
|---|---|---|
| 每步计算 | $\mathbb{1}\{dist(p_t, g) < dist(p_{t-1}, g)\}$ | $w_1 \cdot \text{sim}(o_t, l_i) + w_2 \cdot c_{det} + \dots$ |
| 数学本质 | 前后两帧的距离差 | 单帧与文本的相似度 |
| 时序关系 | ❌ 步骤间独立 | ❌ 步骤间独立 |
| 错误示例 | 智能体绕圈靠近目标，每步都"正确" | 智能体提前看到目标但跳过路径，每步都"正确" |

SACA 的硬掩码 $M_t = \mathbb{1}\{S_t > \tau_h\}$ 提供了一个离散的结构信号，但它仍然基于**单帧检测**——如果 $o_t$ 中的地标可见性满足阈值，$M_t=1$，完全丢失了命令执行顺序信息。

#### 盲区 2：依赖模拟器特权信号

| 特权信号 | 用于 | 现实可用？ |
|---|---|---|
| 全局目标位置 $g$（VPR 需要计算 $dist(p_t, g)$） | SeeNav-Agent | ❌ 除非有全局定位系统 |
| Simulator shortest-path teacher action $a^+$（SACA 需要做 Contrastive Correction） | SACA | ❌ 需要预计算最优路径 |
| 完美语义分割（PGSA 依赖 GroundingDINO+SAM 精确度） | SACA | ⚠️ 在真实场景中会衰减 |

这意味着两者的实验验证**被限制在模拟器内**，其结论的适用范围需要谨慎对待。

#### 盲区 3：固定奖励函数无法适应学习阶段

两者都在训练全程使用固定的奖励函数公式。但智能体在不同阶段需要不同的反馈类型：

| 训练阶段 | 需要的反馈 | VPR 提供？ | PGSA 提供？ |
|---|---|---|---|
| 早期（探索阶段） | 粗粒度方向引导（"哪个方向大致对"） | ⚠️ 部分 | ⚠️ 部分 |
| 中期（路径选择阶段） | 细粒度路线判别（"左转 vs 右转"） | ❌ 短视 | ✅ |
| 后期（精调阶段） | 精确操作校准（"停在这里，别过冲"） | ❌ | ❌ 过于粗糙 |

#### 盲区 4：过程奖励的对抗性利用 / Reward Hacking

密集的步骤级奖励天然存在被利用的风险。这在 LLM RL 社区已有广泛讨论，但在 VLN 过程中被完全忽视。

**两个具体场景**：

*场景 A（针对 VPR）*：智能体学到绕目标做螺旋运动。每步 $dist(p_t, g)$ 都在减少，但效率极低，且可能在最后一步无法触发 STOP 条件。

```
VPR 视角：每步都在减少距离 → 过程奖励持续为正 ✓
指令视角：没有按照指令执行 → 任务失败 ✗
```

*场景 B（针对 PGSA）*：当指令包含"微波炉"作为地标时，智能体可以先转到能看到微波炉的方向，获得高 PGSA 分数，然后转回来继续做别的。只要地标周期的出现，每步都能获得高相似度。

```
PGSA 视角：多次检测到微波炉 → 过程奖励持续为正 ✓
指令视角："在微波炉前停下"不是"看到微波炉" → 任务失败 ✗
```

**本方向的核心抗击机制**：通过依赖链验证（$\Delta\text{Chain}$），奖励函数检测的是**按顺序的约束满足**，而非独立的检测事件。单帧的高相似度不产生奖励，只有按正确顺序执行才产生奖励。

#### 盲区 5：指令被当作"任务分解"而非"逻辑程序"

SACA 将指令解析为 $\text{Landmarks} = \{l_1, l_2, \dots, l_m\}$，这是一个**列表**。但指令结构远不只是列表：

| 丢失的信息 | 示例 | 为什么重要 |
|---|---|---|
| **时序依赖** | "先走到桌子前，然后左转" | 左转的验证依赖于"已到达桌子前" |
| **空间关系** | "绕过椅子的左侧" | 需要验证相对方位，而非仅检测椅子 |
| **逻辑约束** | "走到微波炉前停下" | "停下"的验证依赖于"已在微波炉前" |
| **否定/避免** | "不要碰到沙发" | 需要负向验证 |
| **选项/条件** | "如果门关着，走侧门" | 条件分支执行 |

### 1.2 核心研究问题

基于上述盲区分析，本方向的核心研究问题是：

> **如何将自然语言导航指令编译为一个可验证的约束程序，使得过程奖励能够从"物理进展度量"升维到"指令执行链验证"，从而同时解决 reward sparsity、reward hacking、可解释性、可迁移性四个问题？**

---

## 2. 方法论设计

### 2.1 总体框架：指令即程序（Instruction as Program）

```
+-----------------------------------------------------------------------+
|  用户指令                                                                |
|  "Walk past the glass doors and turn left towards the island..."        |
+----------------------------------+------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|  Stage 1: 指令编译 (Instruction Compiler)                               |
|  输入：自然语言指令                                                    |
|  输出：时序约束程序 C = {C₁, C₂, ..., Cₘ}                              |
|  方法：VLM 解析 + 约束图构建                                            |
+----------------------------------+------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|  Stage 2: 状态跟踪与约束验证 (Constraint Verification)                  |
|  每步 t：                                                              |
|  ┌─ 2a: 语义状态估计 (VLM as observer)                                |
|  │    - 检测当前视角中的地标                                           |
|  │    - 估计智能体相对位置                                              |
|  │    - 推理已执行的动作                                                |
|  ├─ 2b: 约束满足度计算                                                |
|  │    - 对每个 Cᵢ 计算 satisfy_level ∈ [0, 1]                          |
|  │    - 构建满足度向量 S_t = [s₁, s₂, ..., sₘ]                        |
|  ├─ 2c: 依赖链完整性检查                                              |
|  │    - 验证约束间的时序一致性                                         |
|  │    - 检测跳跃执行 / 顺序违反                                         |
|  └─ 2d: Reward Hacking 检测                                           |
|       - 动作频率异常检测                                                |
|       - 周期性模式检测                                                  |
+----------------------------------+------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|  Stage 3: 构成式过程奖励 (Compositional Process Reward)                |
|  R_t = α·ΔS_t + β·ΔChain - γ·Violation - η·Exploit                    |
|  输出：每步的密集奖励信号                                                |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|  Stage 4: 策略优化 (Policy Optimization by GRPO/SRGPO)                |
|  使用构成式过程奖励替代 / 辅助原始奖励进行 RL 训练                   |
+-----------------------------------------------------------------------+
```

### 2.2 Stage 1：指令编译器（Instruction Compiler）

将自然语言指令解析为**时序约束程序**。与 SACA 的"地标列表"不同，我们构建的是**约束图**——一个有向无环图，节点是约束条件，边是时序依赖。

#### 指令解析格式

每个约束定义为五元组：

```
Cᵢ = ⟨precondᵢ, verbᵢ, targetᵢ, stateᵢ, postcondᵢ⟩
```

| 字段 | 类型 | 说明 | 示例 |
|---|---|---|---|
| $precond_i$ | 逻辑表达式 | 前置条件（必须满足才能执行此步骤） | $passed(glass\_doors)$ |
| $verb_i$ | 动作类型 | traverse / turn / approach / stop 等 | $turn$ |
| $target_i$ | 实体 | 操作对象 | $left$ |
| $state_i$ | 状态谓词 | 执行成功后的状态 | $facing(island)$ |
| $postcond_i$ | 逻辑表达式 | 此步骤结束后成立的后置条件 | $facing(island)$ |

#### 具体编译示例

指令：*"Walk past the glass doors and turn left towards the island. Turn right and walk into the kitchen. Stop in front of the microwave."*

编译后的约束程序：

```
程序开始

C₁: ⟨∅,                    traverse, [glass_doors], passed(glass_doors),  passed(glass_doors)             ⟩
C₂: ⟨passed(glass_doors),  turn,     [left],        facing(island),      facing(island)                   ⟩
C₃: ⟨facing(island),       traverse, [island],      past(island),        past(island)                     ⟩
C₄: ⟨past(island),         turn,     [right],       in(kitchen),         in(kitchen)                      ⟩
C₅: ⟨in(kitchen),          approach, [microwave],   within(1m, microwave), within(1m, microwave)          ⟩
C₆: ⟨within(1m, microwave), stop,    [],            stopped,             stopped ∧ within(1m, microwave) ⟩

约束图：
C₁ → C₂ → C₃ → C₄ → C₅ → C₆
     (无分支，严格顺序)
```

更复杂的约束图（含分支与并行）：

指令：*"If the door is open, enter the room; otherwise, go around to the window."*

```
C₁: ⟨∅, check, [door_open], checked_door, checked_door⟩
     ├─ C₂ (若 checked_door ∧ door_open): ⟨checked_door, enter, [room], in(room), in(room)⟩
     └─ C₃ (若 checked_door ∧ ¬door_open): ⟨checked_door, traverse, [window], at(window), at(window)⟩
```

#### 解析方法

使用 VLM（如 Qwen2.5-VL-72B 或 GPT-4o）进行指令解析，而非 SACA 的 0.6B 小模型，以保证解析质量。

具体的 prompt 设计：

```
System: You are an instruction compiler. Given a navigation instruction,
parse it into a sequence of constraints. Each constraint must have:
- precondition: logical condition that must hold before this step
- verb: one of [traverse, turn, approach, stop, check, wait]
- target: the object or direction
- state: the post-execution state predicate
- postcondition: logical condition that holds after this step

Output as a JSON list of constraints. Maintain strict temporal ordering.

User: "Walk past the glass doors and turn left towards the island..."
[期望的输出格式]
```

### 2.3 Stage 2：状态跟踪与约束验证器

这是框架的核心创新模块。在每个时间步 $t$，执行三层验证。

#### 2.3a 语义状态估计

使用 VLM（可复用策略模型，或额外的轻量级 verifier）将当前视觉观测 $o_t$ 映射到语义状态：

```
s_t = VLM_observe(o_t, I) → {predicate_i ∈ [0, 1]}
```

其中 $predicate_i$ 包括但不限于：
- $passed(object)$：物体是否已从身边经过
- $facing(direction)$：智能体是否面向某个方向
- $within(d, object)$：与目标的距离是否小于 $d$
- $in(room)$：是否在某房间内
- $visible(object)$：目标是否在当前视野中
- $passed\_count(object, n)$：经过某物体 $n$ 次（检测循环行为）

这里的关键创新：**不是用 GroundingDINO+SAM 做刚性检测，而是用 VLM 做语义推理**。VLM 可以直接回答"目标是否已从右侧经过"这样的关系性问题，而不仅仅是"是否检测到目标实例"。

#### 2.3b 约束满足度计算

对于约束程序 $C = \{C_1, \dots, C_m\}$ 和当前语义状态 $s_t$，计算每个约束的满足度：

$$s_i^{(t)} = \text{satisfy}(C_i, s_t) \in [0, 1]$$

其中 $satisfy$ 是一个组合函数：

$$s_i^{(t)} = 
\begin{cases} 
\mathbb{1}\{\text{state}_i \subseteq s_t\}, & \text{if } \text{precond}_i \subseteq s_{t-1} \\
0, & \text{otherwise}
\end{cases}$$

即：**只有当该约束的前置条件在上一时间步满足时，此约束才可能被满足。** 这防止了"跳过前置约束直接满足后置约束"的问题。

**满足度向量**：

$$S_t = [s_1^{(t)}, s_2^{(t)}, \dots, s_m^{(t)}]$$

#### 2.3c 依赖链完整性检查

这是本方向的另一个核心创新。定义**约束链完整性**指标：

$$\text{ChainComplete}(S_t) = \sum_{i=1}^{m} \left( s_i^{(t)} \cdot \prod_{j < i} \text{completed}(j, S_t) \right)$$

其中 $\text{completed}(j, S_t) = \max_{k \leq t} s_j^{(k)}$ 表示约束 $C_j$ 是否在某个历史时间步被满足过。

这个公式的直觉是：
- 约束 $C_i$ 的奖励只有在**之前所有约束 $C_{<i}$ 都已被满足过**时才被计入
- 如果智能体跳过了 $C_2$ 直接满足 $C_3$，$\text{ChainComplete}$ 不会计入 $C_3$ 的贡献

**链完整性的变化量**：

$$\Delta\text{Chain}_t = \text{ChainComplete}(S_t) - \text{ChainComplete}(S_{t-1})$$

正向 $\Delta\text{Chain}_t$ 意味着智能体在按正确顺序执行指令。

#### 2.3d Reward Hacking 检测

引入两个检测机制：

**模式检测**：对动作序列 $\{a_{t-w}, \dots, a_{t-1}\}$ 做自相关分析，检测周期性模式（原地转圈、来回移动等）：

$$\text{Periodic}(a_{1:t}) = \max_{\tau > 0} \frac{\sum_{k=0}^{w} \mathbb{1}\{a_{t-k} = a_{t-k-\tau}\}}{w}$$

如果 $\text{Periodic}$ 超过阈值，标记为潜在 reward hacking。

**状态停滞检测**：如果约束满足度 $S_t$ 在连续 $K$ 步内无变化，但动作仍在产生正奖励，检测为 hacking：

$$\text{Stuck}(S_{t-K:t}) = \mathbb{1}\{\|S_t - S_{t-K}\|_1 < \epsilon\}$$

### 2.4 Stage 3：构成式过程奖励

将以上所有信号整合为统一的步骤级奖励：

$$R_t = \alpha \cdot \Delta S_t + \beta \cdot \Delta\text{Chain}_t - \gamma \cdot \text{Violation}_t - \eta \cdot \text{Exploit}_t$$

其中：

| 项 | 公式 | 语义 |
|---|---|---|
| $\Delta S_t$ | $\|S_t\|_1 - \|S_{t-1}\|_1$ | 约束满足度的总体变化 |
| $\Delta\text{Chain}_t$ | 见 2.3c | 依赖链的推进 |
| $\text{Violation}_t$ | $\sum_i s_i^{(t)} \cdot \mathbb{1}\{\text{precond}_i \not\subseteq s_{t-1}\}$ | 违反顺序约束的程度 |
| $\text{Exploit}_t$ | $\text{Periodic} + \text{Stuck}$ | Reward hacking 检测 |

**与现有奖励的关键差异**：

| 维度 | VPR (SeeNav-Agent) | PGSA (SACA) | 本方法 |
|---|---|---|---|
| **信号来源** | 全局距离变化 | 单帧-文本相似度 | 约束程序执行链 |
| **时序依赖** | 仅前后两步 | 无（单帧独立） | 全局约束依赖 |
| **语义粒度** | 距离数值 | 地标存在性 | 关系级 + 约束级 |
| **抗 hacking** | ❌ | ❌ | ✅ 显式检测 |
| **可解释性** | "距离近了/远了" | "地标可见/不可见" | "执行到 C₃ / 跳过 C₂" |
| **可迁移性** | ❌ 需全局位置 | ⚠️ 需精确检测 | ✅ 仅需 VLM + 视觉 |

### 2.5 Stage 4：策略优化

将 $R_t$ 作为过程奖励嵌入现有的 RL 框架中。具体的集成方式有三种选择：

#### 方案 A：替换 SRGPO 的 VPR（在 SeeNav-Agent 框架上）

用 $R_t$ 替换 SRGPO 中的 $R_t^s$（verifiable process reward），保持 SRGPO 的随机分组 + 双层优势估计机制不变。

$$\tilde{R}_t^s = R_t \quad (\text{替换 VPR})$$

**优点**：最小改动，直接对比 VPR vs 构成式奖励。

#### 方案 B：替换 SACA 的 PGSA Soft Score（在 SACA 框架上）

用 $R_t$ 替换 PGSA 的 Soft Score $S_t(o_t, l_i)$，保持 SACA 的 Scenario-Conditioned Group Construction 不变。

**优点**：利用 SACA 的全失败处理机制。

#### 方案 C：独立实现（推荐）

以 GRPO 为基础，构建独立的训练框架。将 $R_t$ 作为步骤级奖励，$\text{TrajectorySuccess}$ 作为片段级奖励，双层优化。

**优点**：完全不受现有框架约束，消融实验最干净。

### 2.6 训练算法伪代码

```
Algorithm: Instruction-as-Program Process Reward Training

Input: 策略模型 π_θ
       指令数据集 D = {I_j}
       环境 E

阶段 1: 预编译指令程序
for each I ∈ D:
    C ← InstructionCompiler(I)   // 解析为约束程序
    D ← D ∪ {(I, C)}             // 缓存

阶段 2: RL 训练
for epoch = 1 to N:
    采样 batch：{(I_1, C_1), ..., (I_K, C_K)} ~ D

    for each (I, C):
        采样 N 条轨迹 {τ_1, ..., τ_N} ~ π_θ(·|I)
        
        for each τ_i = {(a_i1, o_i1), ..., (a_iT, o_iT)}:
            for t = 1 to T:
                s_t ← SemanticStateEstimator(o_t)    // 2.3a
                S_t ← ConstraintSatisfaction(s_t, C)  // 2.3b
                ΔChain_t ← ChainComplete(S_t) - ...   // 2.3c
                Exploit_t ← RewardHackDetect(τ_{1:t}) // 2.3d
                R_it ← α·ΔS_it + β·ΔChain_it - γ·Violation_it - η·Exploit_it

        // 步骤级优势估计（类似 SRGPO 的随机分组或 SACA 的结构分组）
        A_step_it ← StepAdvantage({R_1:T_1, ..., R_N:T_N})
        // 片段级优势估计
        A_ep_i ← EpisodeAdvantage({success_1, ..., success_N})
        // 组合优势
        A_it ← A_ep_i + λ·A_step_it

    // 策略更新（GRPO 风格的 clipped objective）
    J(θ) ← E[ min(ratio·A, clip(ratio, 1-ε, 1+ε)·A) - β·KL(π_θ || π_ref) ]
    更新 θ ← θ + ∇J(θ)
```

---

## 3. 与现有工作的本质差异

### 3.1 与 SeeNav-Agent 的差异

| 对比维度 | SeeNav-Agent VPR | 本方法构成式奖励 |
|---|---|---|
| 奖励来源于 | 目标距离 $dist(p_t, g)$ | 指令约束程序 $C$ |
| 验证方式 | 距离单调性 + 可见性 | 约束满足链完整性 |
| 时序范围 | 前后两步 | 全局约束链 |
| 指令利用 | ❌ 仅作为 prompt | ✅ 编译为可验证程序 |
| 抗 hacking | ❌ 无防御 | ✅ 模式检测 + 停滞检测 |
| 可解释性 | 低（"距离少 0.1m"） | 高（"约束 C₃ 被违反"） |

**核心差异主张**：SeeNav-Agent 做了一个假设——"向目标靠近 = 好的导航"。我们挑战这个假设，认为"按指令执行 = 好的导航"，这是两个不同的目标函数。

### 3.2 与 SACA 的差异

| 对比维度 | SACA PGSA | 本方法构成式奖励 |
|---|---|---|
| 状态评估方式 | GroundingDINO + SAM + CLIP（3 模型级联） | VLM 统一推理 |
| 地标使用方式 | 独立检测，list 结构 | 约束图，DAG 结构 |
| 步骤间关系 | ❌ 独立（仅通过 hard mask 分离有效前缀） | ✅ 显式建模依赖链 |
| 特权信息依赖 | 需要 teacher action $a^+$（shortest-path） | ❌ 不需要 |
| 泛化到新场景 | 依赖检测模型的零样本能力 | 依赖 VLM 的语义推理 |
| 训练计算成本 | 高（每步 3 个模型级联） | 可调节（VLM 统一推理） |

**核心差异主张**：SACA 的奖励本质上是**物理感知的**——检测地标是否在视野中。我们的是**语义验证的**——验证指令的约束是否按顺序被满足。即使智能体看不到任何地标，约束链完整性也可以提供奖励信号。

### 3.3 与现有 ABC 方向的关系

| 方向 | 核心思路 | 与本方向的关系 |
|---|---|---|
| A. 课程式/分层RL | 课程调度 + 高层规划器 | **可组合**：约束程序 C 自然定义了课程——约束数量递增、依赖图变复杂 |
| B. 多模态可验证奖励 | VLM-grounded 地标奖励 | **可组合**：本方向的约束链可以作为 Direction B 的"可验证性"的具体实现 |
| C. 语言条件化策略 | 指令调节探索熵 | **正交**：本方向聚焦奖励设计，C 聚焦策略表示 |
| **D. 本方向** | 约束程序验证 | **独立**：不依赖其他方向的实现 |

---

## 4. 实验设计

### 4.1 数据集与评估基准

| 基准 | 环境 | 指标 | 与本方向的相关性 |
|---|---|---|---|
| **R2R-CE** | Matterport3D + Habitat | SR, SPL, NE | ✅ 标准连续 VLN 评估 |
| **RxR-CE** | Matterport3D + Habitat | SR, SPL, nDTW | ✅ 更长指令，更依赖子任务执行 |
| **EmbodiedBench-Nav** | AI2-THOR | SR | ✅ 与 SeeNav-Agent 直接对比 |
| **新：指令变体测试** | 同上 + 手动构造 | Constraint Accuracy | 🆕 本方向独有的评估 |

需要新增的评估指标：

- **Constraint Accuracy (CA)**：约束程序中正确完成的约束比例
- **Order Preservation Rate (OPR)**：约束按正确顺序完成的比例
- **Reward Hacking Rate (RHR)**：检测到的 hacking 行为占比

### 4.2 基线方法

| 类别 | 方法 | 对比目的 |
|---|---|---|
| 无过程奖励 | GRPO baseline | 展示过程奖励的必要性 |
| 规则驱动过程奖励 | SeeNav-Agent (VPR+SRGPO) | 对比物理度量 vs 语义验证 |
| 感知驱动过程奖励 | SACA (PGSA+...) | 对比独立检测 vs 约束验证 |
| 本方法 | 构成式过程奖励 + GRPO | 验证核心创新 |

### 4.3 消融实验

| 实验 | 去掉的组件 | 预期效果 |
|---|---|---|
| 去掉依赖链检查 | $\Delta\text{Chain}$ | 约束执行顺序崩坏，OPR 显著下降 |
| 去掉 reward hacking 检测 | $\text{Exploit}$ | 某些种子下 SR 虚高但策略异常 |
| VLM verifier → GroundingDINO | 用检测替换推理 | 关系验证能力下降，CA 降低 |
| 固定权重 vs 自适应权重 | $(\alpha, \beta, \gamma, \eta)$ | 自适应更鲁棒 |

### 4.4 实验假设

1. **H1**：构成式过程奖励在 SR/SPL 上超过 VPR 和 PGSA（在长指令场景中更显著）
2. **H2**：依赖链完整性检查防止了"跳步执行"，OPR 显著高于 SACA 的硬掩码方法
3. **H3**：奖励不依赖特权信息，在模拟器中的 SR 与现有方法可比或更优
4. **H4**：Reward hacking 检测机制使训练曲线的方差降低，极端种子下的失败率降低

### 4.5 预期结果

| 指标 | GRPO | SeeNav-Agent (VPR) | SACA (PGSA) | 本方法 |
|---|---|---|---|---|
| R2R-CE SR | ~52% | ~58% (估计，SeeNav 未在此评估) | 60.3% | **60-63%** |
| RxR-CE SR | ~45% | ~52% (估计) | 60.3% | **58-62%** |
| OPR | - | ~40% (估计) | ~55% | **75-85%** |
| RHR | - | 高（无防御） | 中（间接防御） | **低（显式检测）** |
| 可迁移性评估 | ✅ | ❌（需全局位置） | ⚠️（需检测模型） | ✅（仅需 VLM） |

---

## 5. 论文故事线

### 5.1 标题

**主标题**：《Instruction as Verification: Compositional Process Rewards for Vision-Language Navigation》

**备选标题**：
- 《From Progress to Compliance: Semantic Process Verification for Instruction-Guided Navigation》
- 《Beyond Distance: Constraint-Guided Process Rewards for Language-Conditioned Navigation》

### 5.2 核心叙事

**第一句**：
> "在 VLN 中，过程奖励的本质目标应该是验证指令的执行，而非度量物理进展。"

**三段式**：
1. **问题**：现有过程奖励（SeeNav-Agent 的 VPR、SACA 的 PGSA）都做"物理状态的点式度量"，忽略指令的结构性和时序性，导致三类系统性问题——reward sparsity 未真正解决、reward hacking 无防御、模拟器特权不可迁移。
2. **方案**：提出**指令即程序**范式，将指令编译为时序约束程序，用约束链完整性作为过程奖励信号。这是一个问题定义的升维——从"度量进展"到"验证执行"。
3. **验证**：在 R2R-CE/RxR-CE/EmbodiedBench 上验证有效性，并提出新的评估维度（CA, OPR, RHR）来测量指令执行质量。

### 5.3 论文结构

```
Chapter 1: 绪论
  1.1 VLN 任务与研究意义
  1.2 现有方法的共同局限（基于 SeeNav-Agent + SACA 的深度分析）
      1.2.1 物理度量 vs 指令验证：一个根本性的错配
      1.2.2 五个系统性盲区（点式度量、特权依赖、固定奖励、hacking、弱指令利用）
  1.3 本文研究内容与贡献

Chapter 2: 相关工作
  2.1 Vision-and-Language Navigation
  2.2 过程奖励模型（PRM）在 LLM 推理与 VLN 中的应用
  2.3 指令理解与语义解析
  2.4 Reward Design 与 Reward Hacking

Chapter 3: 指令即程序：构成式过程奖励
  3.1 问题形式化
  3.2 指令编译器（Instruction Compiler）
      3.2.1 约束程序定义
      3.2.2 VLM-based 编译方法
      3.2.3 约束图构建
  3.3 语义状态跟踪器
  3.4 构成式奖励计算
      3.4.1 约束满足度
      3.4.2 依赖链完整性
      3.4.3 Reward Hacking 检测
      3.4.4 奖励融合
  3.5 策略优化（GRPO/SRGPO 集成）

Chapter 4: 实验
  4.1 实验设置
  4.2 主实验结果（对比 SOTA）
  4.3 消融研究
      4.3.1 奖励组件消融
      4.3.2 依赖链 vs 独立满足
      4.3.3 Hacking 检测效果
  4.4 新指标：CA, OPR, RHR 分析
  4.5 可解释性与失败分析
  4.6 可迁移性验证（零模拟器特权设置）

Chapter 5: 讨论
  5.1 为什么本方法优于物理度量方法
  5.2 失败模式与边界
  5.3 与 SeeNav-Agent / SACA 的本质差异

Chapter 6: 结论与展望
```

---

## 6. 可行性分析

### 6.1 关键技术风险

| 风险 | 等级 | 缓解策略 |
|---|---|---|
| VLM 指令解析不稳定 | 中 | 多轮解析 + 人工校正 seed set；使用强模型（70B+） |
| VLM 状态推理延迟 | 中-高 | 轻量级 verifier 蒸馏（Offline 生成训练数据 -> 训练小模型） |
| 约束图过于复杂 | 低 | 从线性约束开始，逐步增加分支/并行 |
| 与 GRPO 集成后收敛困难 | 中 | 先做 reward 热加载（warmup），逐步增加权重 |
| 计算资源：需要 VLM 推理 | 中 | 可复用策略模型做 verifier，或使用小模型（8B 级别） |

### 6.2 时间线（假设 2 年制硕士，12 个月有效研究时间）

| 阶段 | 时间 | 工作 |
|---|---|---|
| 0-1 月 | 2026.07-08 | 复现 SeeNav-Agent + SACA baseline（利用开源代码） |
| 1-2 月 | 2026.09-10 | 实现指令编译器模块（VLM 解析 + 约束图） |
| 2-4 月 | 2026.11-2027.01 | 实现状态跟踪器 + 构成式奖励计算 |
| 4-5 月 | 2027.02-03 | 与 GRPO 集成，在 R2R-CE 上跑通 pipeline |
| 5-7 月 | 2027.04-06 | 主实验 + 消融 + 新指标 |
| 7-8 月 | 2027.07-08 | 论文撰写 + 投稿 |

### 6.3 资源需求

| 资源 | 最低需求 | 推荐配置 |
|---|---|---|
| GPU | 4× RTX 3090 (24GB) | 4× A6000 (48GB) |
| 存储 | 200GB | 500GB |
| 主要依赖 | PyTorch + Habitat + Transformers | + LLaMA-Factory for RL |

### 6.4 备选方案

如果某模块遇到不可解决的困难，可切换的备选方案：

| 原始方案 | 备选方案 | 代价 |
|---|---|---|
| VLM 端到端推理 | GroundingDINO + CLIP 替代（类似 PGSA） | 语义推理能力下降，但保留了约束链结构 |
| 全约束图 | 线性约束链（无分支/并行） | 丢失条件执行能力，但核心验证框架不变 |
| 独立框架 | 在 SACA 框架上替换 PGSA 为构成式奖励 | 受限于 SACA 框架，但减少了实现量 |
| VLM verifier 蒸馏 | 使用开源 VLM（LLaVA-Video-8B）直接推理 | 推理速度慢，但可用 |

---

## 7. 潜在风险与备选方案

### 7.1 审稿人可能提出的质疑

| 质疑 | 回应准备 |
|---|---|
| "这不过是把 SACA 的 landmark list 换成了 constraint graph" | 核心创新不在"约束图"本身，而在**验证方式**：SACA 做独立检测，我们做依赖链完整性检查。两者的奖励信号性质完全不同——一个是"检测到 X"，一个是"按顺序完成了 C₁, C₂, ..., Cₙ"。即使两者都解析指令，验证方式不同导致行为不同 |
| "VLM 做 verifier 太慢了，不实用" | 可蒸馏为轻量级模型（方向 5 的变体），论文中我们聚焦于概念验证，实际部署和蒸馏作为 future work |
| "约束程序太严格，无法覆盖所有指令" | 从严格的线性约束开始，这是最常见的指令类型，后续扩展到条件分支 |
| "你提出的新指标 CA/OPR 没有广泛认可" | 我们不以此作为主指标推翻现有指标（SR/SPL），而是作为额外的分析维度。主结果仍用 SR/SPL 与 SOTA 对比，CA/OPR 用于解释为什么本方法有效 |

### 7.2 不可行时的退路

如果在研究过程中发现核心假设不成立（如 VLM 约束解析的噪声太大，导致奖励信号比 VPR 更差），退路如下：

- **退路 1**：将约束链从"全自动 VLM 解析"改为"半自动 + 人工模板"，缩小范围但保留核心验证框架
- **退路 2**：将约束验证与现有的 VPR / PGSA 进行信号融合（而非替换），作为附加奖励项，仍可观察 ΔChain 和 Exploit 的增益
- **退路 3**：转做"Reward Hacking 检测在 VLN 中的首次系统研究"——聚焦一个更窄但更深入的问题

---

## 8. 参考文献

[1] Wang et al. SeeNav-Agent: Enhancing Vision-Language Navigation with Visual Prompt and Step-Level Policy Optimization. arXiv:2512.02631, 2025.

[2] Li et al. Let's Reward Step-by-Step: Step-Aware Contrastive Alignment for Vision-Language Navigation in Continuous Environments. arXiv:2603.09740, 2026.

[3] Shao et al. DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models. arXiv:2402.03300, 2024. (GRPO)

[4] Qi et al. VLN-R1: Vision-Language Navigation via Reinforcement Fine-Tuning. arXiv:2506.17221, 2025.

[5] Lightman et al. Let's Verify Step by Step. (Process Reward Model)

[6] Anderson et al. Vision-and-Language Navigation: Interpreting Visually-Grounded Navigation Instructions in Real Environments. CVPR 2018. (R2R)

[7] Ku et al. Room-Across-Room: Multilingual Vision-and-Language Navigation with Dense Spatiotemporal Grounding. EMNLP 2020. (RxR)

[8] Feng et al. Group-in-Group Policy Optimization for LLM Agent Training. arXiv:2505.10978, 2025. (GiGPO)

[9] Shao et al. DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models. arXiv:2402.03300, 2024.

[10] Yang et al. EmbodiedBench: Comprehensive Benchmarking Multi-modal Large Language Models for Vision-Driven Embodied Agents. arXiv:2502.09560, 2025.

[11] Kolve et al. AI2-THOR: An Interactive 3D Environment for Visual AI. arXiv:1712.05474, 2017.

[12] Liu et al. Grounding DINO: Marrying DINO with Grounded Pre-Training for Open-Set Object Detection. ECCV 2024.

[13] Radford et al. Learning Transferable Visual Models from Natural Language Supervision. ICML 2021. (CLIP)

[14] Schulman et al. Proximal Policy Optimization Algorithms. arXiv:1707.06347, 2017.

[15] Rafailov et al. Direct Preference Optimization: Your Language Model is Secretly a Reward Model. NeurIPS 2023. (DPO)

[16] Wei et al. StreamVLN: Streaming Vision-and-Language Navigation via Slow-Fast Context Modeling. ICRA 2026.

[17] Zhang et al. ActiveVLN: Towards Active Exploration via Multi-Turn RL in Vision-and-Language Navigation. 2025.
