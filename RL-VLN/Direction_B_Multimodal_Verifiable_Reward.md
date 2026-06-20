# 方向 B: 多模态可验证奖励机制 (Multimodal Verifiable Reward) for VLN

> **方向代号**: B
> **目标空白**: G2 (奖励稀疏) + G3 (范式融合)
> **预期贡献**: 首次将 R1-style verifiable reward 扩展到多模态 VLN，提出 VLM-grounded 奖励框架
> **技术栈**: ActiveVLN multi-turn GRPO + VLM-as-Judge + Landmark Grounding
> **目标会议**: NeurIPS 2026 / ICLR 2027 / IROS 2026
> **工作量**: 10-12 个月 (含 VLM 评估管线开发)
> **理论意义**: 把 RLVR 从"语言-逻辑可验证"推广到"视觉-语言-空间可验证"

---

## 1. 问题陈述

### 1.1 当前奖励设计的局限

两篇 SOTA 论文的奖励信号**都极稀疏**：

| 方法 | 奖励形式 | 稀疏度 |
|---|---|---|
| **ActiveVLN** | $R = 15 \cdot \mathbb{I}(\text{success}) \cdot \frac{d_{\text{goal}}}{3}$ | 99% 时间步 r=0 |
| **VLN-R1 (TDR)** | $R = \sum_k \gamma^k \cdot \mathbb{I}(\alpha_{t+k}=\alpha^*_{t+k})$ | 单步 r ∈ {0, 1} |
| **VLN-R1 (Hard)** | $R = 1 \cdot \mathbb{I}(\text{success})$ | 极端稀疏 |

**后果**：
1. **信用分配 (Credit Assignment) 困难**：长 episode (10-30 步) 中，关键动作被淹没
2. **样本效率低**：大量 rollout 得不到有效信号
3. **局部最优**：agent 学会"避开失败"而非"主动成功"

### 1.2 学术问题（可写入论文）

> "在视觉-语言导航任务中，我们能否将 **R1 风格的'可验证奖励' (Verifiable Reward)** 从纯文本/数学领域，扩展为**多模态可验证奖励** (Multimodal Verifiable Reward)？具体地，我们能否用 VLM 来自动验证 agent 是否经过指令中提到的关键地标？"

### 1.3 核心洞察

**RLVR (RL with Verifiable Reward) 的成功**：DeepSeek-R1 证明，当任务有**可验证的正确性**时，RL 可以远超 SFT。

**VLN 任务的特殊性**：
- 指令中包含**可验证的子目标** ("turn left at the brown couch")
- 视觉流提供**可验证的 ground truth** (agent 实际经过的物体)
- 这两者的**对齐**本身可被 VLM 验证！

**关键 idea**：
$$\text{如果 VLM 能验证 "agent 是否经过了 'brown couch'"，} \Rightarrow \text{它就能提供中间奖励}$$

---

## 2. 理论基础

### 2.1 RL with Verifiable Reward (RLVR)

**定义** (Shao et al., 2024 [GRPO]; Lambert et al., 2024 [RLVR-Survey])：
> 奖励函数 $R(q, o)$ **不依赖** human preferences，而是基于**可验证的客观标准**。

**代表工作**：
- **DeepSeek-R1** (Guo et al., 2025): 数学题答案对错可验证
- **DeepSeekMath-GRPO** (Shao et al., 2024): 同样
- **Code R1** (OpenCodeInterpreter 等): 代码能否通过测试可验证
- **Vision-R1** (Huang et al., 2025): 视觉问答答案可验证

**为什么 RLVR 在 LLM 上成功**：
1. **无 reward hacking**：硬约束让模型不能"刷分"
2. **清晰信号**：正确/错误一目了然
3. **可扩展**：自动 verifier 比人工标注便宜

### 2.2 Reward Shaping 理论

**经典框架** (Ng et al., 1999 [RewardShaping-1999])：
> 如果新奖励 $R'(s,a,s') = R(s,a,s') + \gamma \Phi(s') - \Phi(s)$，且 $\Phi$ 是 potential function，则最优策略不变。

**潜在风险** (后续工作)：
- 如果 $\Phi$ 设计不当，会**误导** agent
- 称为 "**reward hacking**"：agent 学会最大化 shaped reward 而非真实目标

**对我们的启示**：
- 多模态奖励必须**真与最终目标一致**
- 不能让 agent "刷 landmark 数量" 而不抵达目标

### 2.3 Process Reward Model (PRM)

**vs Outcome Reward Model (ORM)**：
- **ORM**: $R(\tau) \to \{0, 1\}$，仅看最终结果
- **PRM**: $R(s_t, a_t) \to \mathbb{R}$，每步都给信号

**代表工作**：
- **Math-Shepherd** (Wang et al., 2024): 数学推理 PRM
- **Let's Verify Step by Step** (Lightman et al., 2023 [PRM-Lightman]): o1-style PRM
- **CriticGPT**: 用 LLM 做 PRM

**对 VLN 的应用**：
- 每个 landmark 完成 = 一个 PRM 信号
- 序列完成 = cumulative PRM

### 2.4 VLM-as-a-Judge

**核心理念**：用 VLM (Qwen2-VL, GPT-4V, LLaVA) 评估视觉-语言对齐质量。

**应用形式**：
1. **Pairwise Comparison**: 给定两段轨迹，VLM 选更好的
2. **Pointwise Scoring**: 给定一段轨迹，VLM 打分
3. **Fact Verification**: 给定 (query, response, evidence)，验证 response 正确性
4. **Sub-goal Verification**: **我们的新应用** —— 验证 sub-goal 完成

**理论问题**：
- VLM 判断的**可靠性** (Reliability)
- VLM 的 **reward hacking 风险** (VLM 可能被 fool)
- **Bootstrap 问题**: 训练一个 VLM 评估另一个 VLM

### 2.5 任务分解理论 (Task Decomposition)

**Horizon Reduction**:
- 长 horizon: SR(成功 | horizon=H) 低
- 短 horizon: SR(成功 | horizon=h) 高 (h ≪ H)
- 期望: $P(\text{long}) = \prod_i P(\text{short}_i)$

**Sub-goal Decomposition**:
- 把任务分解为 K 个 sub-goals
- 每个 sub-goal 独立 RL 子问题
- 联合 reward = sum of sub-rewards + final bonus

---

## 3. 相关文献综述

### 3.1 RL with Verifiable Reward

1. **[RLVR-Survey-2024]** Lambert, N., et al. **"RewardBench: Evaluating Reward Models"**. arXiv:2403.13787.
   - 系统综述 reward model 评估

2. **[GRPO-2024]** Shao, Z., et al. **"DeepSeekMath"**. arXiv:2402.03300.
   - GRPO 算法
   - 数学推理上验证

3. **[R1-2025]** Guo, D., et al. **"DeepSeek-R1"**. arXiv:2501.12948.
   - 首次大规模 R1 训练
   - 纯 RL 不需 SFT 也能涌现推理

4. **[Vision-R1-2025]** Huang, Z., et al. **"Vision-R1: Incentivizing Reasoning Capability in MLLMs via RL"**. arXiv:2503.06749.
   - **多模态 R1 早期工作**
   - 视觉推理任务

5. **[R1-V-2025]** Zhang, J., et al. **"R1-V"**. (referenced in many surveys)
   - 视觉计数/几何任务

6. **[MM-Eureka-2025]** Meng, F., et al. **"MM-Eureka"**. arXiv:2503.07365.
   - 多模态 RL on text-rich images

7. **[Visual-CoT-2024]** Shao, H., et al. **"Visual CoT"**. arXiv:2409.12186 (related).
   - 视觉 reasoning + RL

8. **[Seg-Zero-2025]** Du, H., et al. **"Seg-Zero"**. arXiv:2503.06520.
   - 视觉分割 RL

9. **[LMM-R1-2025]** (assumed) "LMM-R1" (recent MLLM-RL)

### 3.2 Reward Shaping & Potential-Based Methods

1. **[RewardShaping-1999]** Ng, A. Y., et al. **"Policy Invariance Under Reward Transformations"**. ICML 1999.
   - Potential-based reward shaping 奠基
   - 证明不改变最优策略

2. **[GridShaping-2004]** Devlin, S., & Grzes, M. **"An Empirical Study of Potential-Based Reward Shaping"**. 2014 (extended analysis).

3. **[AutoShaping-2023]** Küttler, H., et al. (related work on automatic shaping)

4. **[Dense-Rewards-2022]** Hu, Y., et al. **"Density-based Reward Shaping"**.

### 3.3 Process Reward Models (PRM)

1. **[PRM-Lightman-2023]** Lightman, H., et al. **"Let's Verify Step by Step"**. arXiv:2305.20050.
   - o1-style PRM
   - 在 MATH 任务上大幅超越 ORM

2. **[Math-Shepherd-2024]** Wang, P., et al. **"Math-Shepherd"**. arXiv:2312.08935.
   - 自动构建 PRM 训练数据

3. **[CriticGPT-2024]** (related, OpenAI)
   - 用 LLM 评估 LLM 推理

4. **[PRM-Process-2024]** (Survey by OpenAI, 2024)

### 3.4 VLM-as-a-Judge / Reward Modeling

1. **[LLaVA-Reward-2024]** Yu, T., et al. **"LLaVA-Critic"**. arXiv:2410.02712 (related).
2. **[Vision-Feedback-2024]** (assumed) "VLM-as-Reward"
3. **[Multimodal-RM-2024]** Li, X., et al. (related)
4. **[CLIP-Reward-2024]** (assumed) using CLIP similarity as reward

### 3.5 Visual Grounding in Navigation

1. **[Visual-Grounding-2018]** Mao, J., et al. **"Generation and Comprehension of Unambiguous Object Descriptions"**. CVPR 2016 (foundational).
2. **[CLIP-2021]** Radford, A., et al. **"Learning Transferable Visual Models From Natural Language Supervision"**. ICML 2021.
   - CLIP 是 VLM-grounding 的核心技术
3. **[CLIP-Nav-2022]** Gadre, S., et al. **"CLIP on Wheels"**. CoRL 2022.
   - **首批**将 CLIP 用于 zero-shot 导航
4. **[VLFM-2024]** Yokoyama, N., et al. **"Vision-Language Frontier Maps"**. ICRA 2024.
   - VLM 探索未知环境
5. **[VLM-Map-2023]** Huang, C., et al. **"Visual Language Maps"**. ICRA 2023.

### 3.6 VLN 子目标/中间奖励

1. **[Sub-Instr-2020]** Hong, Y., et al. (related)
2. **[LAW-2021]** Raychaudhuri, S., et al. **"Language-Aligned Waypoint Supervision"**. EMNLP 2021.
   - **最相关工作！** 用语言对齐的 waypoint 作为中间监督
3. **[ETPnav-2024]** An, D., et al. **"Evolving Topological Planning"**. TPAMI 2024.
4. **[Subgoal-VLN-2022]** (assumed) "Subgoal-based Navigation"

### 3.7 Reward Hacking & Safe RL

1. **[Reward-Hacking-2017]** Amodei, D., et al. **"Concrete Problems in AI Safety"**. 2016.
2. **[Specification-Gaming-2020]** Krakovna, V., et al. **"Specification Gaming"**. 2020.
3. **[Goodhart-2014]** (related)

### 3.8 MLLM + GRPO 系列

1. **[GRPO-2024]** Shao, Z., et al. (引)
2. **[DAPO-2025]** Yu, Q., et al. **"DAPO"**. arXiv:2503.14476.
   - 改进 GRPO
3. **[RAGEN-2025]** Wang, Z., et al. (引)
4. **[ActiveVLN-2025]** Zhang, Z., et al. (引)
5. **[VLN-R1-2025]** Qi, Z., et al. (引)
6. **[DeepEyes-2025]** Zheng, Z., et al. (引)

---

## 4. 方法学设计

### 4.1 整体框架

```
┌──────────────────────────────────────────────────────────────┐
│         Multimodal Verifiable Reward (MVR) for VLN           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Input: Instruction I = "go past the brown couch, then       │
│                          turn left at the door"              │
│                                                              │
│  Step 1: Sub-goal Extraction (LLM)                           │
│    ↓ {sg_1: "pass brown couch", sg_2: "turn left at door"}    │
│                                                              │
│  Step 2: VLM Verifier (Qwen2-VL)                             │
│    ↓ For each step: v_t ↔ sub-goal_i                          │
│    ↓ Returns: sub_goal_completed_t ∈ {0, 1}                  │
│                                                              │
│  Step 3: Multimodal Verifiable Reward                        │
│    R = R_success + Σ_i R_subgoal_i + R_progress              │
│                                                              │
│  Step 4: GRPO Optimization (复用 AVLN)                        │
│    ↓ Update policy with shaped reward                        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Sub-goal 提取 (Sub-goal Extraction)

**输入**: 自然语言指令 $I$
**输出**: Sub-goal 序列 $\{g_1, g_2, ..., g_K\}$

**方法 A**: 规则解析
- 用 spaCy / NLTK 提取动词 + 宾语
- 复杂指令容易出错

**方法 B** (推荐): LLM 解析
```python
prompt = f"""Extract sub-goals from the navigation instruction:
"{instruction}"

Output a JSON list of sub-goals in execution order.
Each sub-goal should describe ONE atomic navigation step.
Example: ["turn left", "go past brown couch", "stop at door"]

Sub-goals:"""

sub_goals = llm(prompt)  # 用 Qwen2-7B 或 GPT-4
```

**方法 C**: 利用 RxR 的 path description
- RxR 数据集自带"sub-instruction"
- 可作为 ground truth 训练 sub-goal extractor

### 4.3 VLM Verifier (核心创新)

**任务**: 给定 $(v_t, g_i)$，判断 sub-goal $g_i$ 是否在当前观测中**已完成**

**实现**:
```python
def vlm_verify(v_t: Image, g_i: str) -> bool:
    """使用 Qwen2-VL 验证 sub-goal"""
    prompt = f"""You are a navigation verifier.
    Current observation: <image>
    Sub-goal: {g_i}
    
    Question: Has the agent just completed this sub-goal?
    - If yes, return: COMPLETED
    - If no, return: NOT_COMPLETED
    
    Answer:"""
    
    response = qwen2_vl(prompt, v_t)
    return "COMPLETED" in response.upper()
```

**复杂度分析**:
- VLM 推理: ~100ms/次
- Episode 30 步: 30 × 100ms = 3s verification
- 与 simulator 渲染 (~50ms/step) 相比**开销可接受**

**关键问题：Reliability**

VLM 判断的可靠性是关键挑战。缓解方案：
1. **Multiple VLM samples**: 取 3 次 VLM 投票
2. **Confidence Threshold**: 仅当 VLM confidence > 0.8 时给奖励
3. **Calibration Set**: 用 held-out 数据校准 VLM

### 4.4 Multimodal Verifiable Reward

**完整奖励函数**:

```python
def compute_mvr_reward(trajectory, instruction, sub_goals):
    """
    Multimodal Verifiable Reward
    
    Args:
        trajectory: list of (obs_t, action_t)
        instruction: str
        sub_goals: list of str (extracted from instruction)
    
    Returns:
        total_reward: float
        components: dict of individual rewards
    """
    components = {}
    
    # 1. Final success reward
    success = is_stop_within_3m(trajectory)
    components['R_success'] = 15.0 if success else 0.0
    
    # 2. Sub-goal completion reward (核心)
    R_subgoal = 0
    for sg in sub_goals:
        completed_step = find_completion_step(trajectory, sg)
        if completed_step is not None:
            R_subgoal += 3.0
            # 时序衰减: 越早完成越多
            R_subgoal += 1.0 * gamma ** completed_step
    
    components['R_subgoal'] = R_subgoal
    
    # 3. Progress reward (geodesic 距离缩减)
    progress = compute_progress(trajectory)
    components['R_progress'] = 2.0 * progress
    
    # 4. Format reward
    components['R_format'] = -0.5 if format_error(trajectory) else 0
    
    # 5. Verifier 自身可信度调整
    verifier_confidence = vlm_avg_confidence
    components['R_subgoal'] *= verifier_confidence
    
    return sum(components.values()), components
```

**奖励塑形合法性分析**:
- $R_{\text{subgoal}}$ 是 $R_{\text{success}}$ 的**充分不必要条件** (sub-goal 完成不保证最终成功)
- $R_{\text{progress}}$ 是 potential-based shaping: $\Phi(s) = -d_{\text{goal}}(s)$
- 因此理论上**保持最优策略不变** (Ng et al., 1999)

### 4.5 GRPO 适配

**原始 GRPO objective** (ActiveVLN eq. 7):
$$\mathcal{L}_{\text{RL}} = \mathbb{E}[\text{clip}(\pi_\theta/\pi_{\text{old}}, 1-\epsilon, 1+\epsilon) \cdot A]$$

**MVR-GRPO 适配**:
- 奖励替换为 MVR 奖励
- Advantage 计算不变 (group-wise normalization)
- KL 系数可调 (与 DAPO 类似设为 0)

**完整算法伪代码**:

```python
def mvr_grpo_train(worker, vlm_verifier, sub_goal_extractor, env):
    for step in range(total_steps):
        # 1. Sample prompts
        batch = sample_prompts(task_pool, batch_size=8)
        
        # 2. Extract sub-goals
        sub_goals_list = [sub_goal_extractor(I) for I in batch.instructions]
        
        # 3. Multi-turn rollout (复用 AVLN)
        rollouts = []
        for prompt, sg in zip(batch, sub_goals_list):
            traj = rollout(worker, env, prompt, sg, vlm_verifier)
            rollouts.append(traj)
        
        # 4. Compute MVR rewards
        rewards = []
        for traj, prompt, sg in zip(rollouts, batch, sub_goals_list):
            r, _ = compute_mvr_reward(traj, prompt, sg)
            rewards.append(r)
        
        # 5. Group-wise advantage (GRPO)
        advantages = (rewards - mean(rewards)) / (std(rewards) + 1e-8)
        
        # 6. Policy update
        loss = grpo_loss(rollouts, advantages)
        worker.update(loss)
```

### 4.6 防止 Reward Hacking

**风险**: Agent 可能学会"看起来在 landmark 附近"而不在真 landmark。

**缓解策略**:
1. **硬约束**: 必须满足 final success 才算 episode success
2. **Verifier 严格性**: VLM 用 chain-of-thought 推理 (而非简单 yes/no)
3. **Sub-goal 数量自适应**: 不可超过指令 sub-goal 数量
4. **Anti-cheat 监控**: 检测异常 sub-goal 模式

---

## 5. 实验设计

### 5.1 VLM Verifier 评估

**首先单独评估 VLM verifier 的可靠性**:

| 评估维度 | 指标 | 目标 |
|---|---|---|
| Sub-goal 完成判断准确率 | Accuracy | >85% |
| False Positive 率 | FPR | <10% |
| False Negative 率 | FNR | <15% |
| VLM 推理时间 | Latency | <200ms/query |

**测试集构建**:
- 从 val-unseen 收集 ~1000 段人工标注 (sub-goal, observation, label)
- 评估 Qwen2-VL-7B, LLaVA-1.6, GPT-4V 的准确率

### 5.2 主实验

| 方法 | 描述 | 预期 SR |
|---|---|---|
| ActiveVLN (Soft success) | Baseline | 50.1 |
| + R_hard | 仅 0/1 | 48.0 |
| + R_progress | + 距离奖励 | 50.5 |
| **+ R_subgoal (Ours)** | + sub-goal 奖励 | **52-54** |
| + TDR | 时序加权 | 53.5 |
| **MVR-Complete (Ours)** | 全组件 | **54-56** |

### 5.3 消融研究

| 消融 | 目的 |
|---|---|
| **MVR-Soft (无sub-goal)** | 验证 sub-goal 关键性 |
| **MVR-仅 sub-goal** | 验证 sub-goal 单独效果 |
| **MVR-no Verifier Calib** | 验证校准的必要性 |
| **MVR-3-sample Vote** | 验证多 VLM 投票 |
| **MVR-no Progress** | 验证 progress reward |
| **MVR-no Format** | 验证 format reward |

### 5.4 跨数据集泛化

| 训练数据 | 测试数据 | 预期 SR |
|---|---|---|
| R2R | R2R Val-Unseen | 54.0 |
| R2R | RxR Val-Unseen | 48.0 |
| R2R + RxR | R2R | 55.0 |
| R2R + RxR | REVERIE | 40.0 |

### 5.5 可视化分析

1. **Sub-goal 完成热力图**: 不同 sub-goal 类型的完成率
2. **Verifier 准确率 vs reward contribution** 散点图
3. **Reward Hacking 检测**: 分析异常 sub-goal 完成模式
4. **Long-horizon 改善**: 长 episode (>20 步) 的 SR 提升

---

## 6. 可行性分析

### 6.1 技术可行性

| 风险 | 等级 | 缓解 |
|---|---|---|
| VLM verifier 不准 | 高 | 多 VLM 投票 + 人工校准 |
| Sub-goal 提取错误 | 中 | 用 GPT-4 + 自验证 |
| 计算成本增加 | 中 | VLM 推理可 batch |
| Reward hacking | 中 | 硬约束 + 监控 |

### 6.2 时间线

```
Month 1-2: 复现 ActiveVLN + 文献精读
Month 3-4: Sub-goal extraction pipeline (用 GPT-4 离线)
Month 5-6: VLM verifier 评估与校准
Month 7-8: MVR-GRPO 集成与训练
Month 9-10: 消融实验 + 跨域
Month 11-12: 论文撰写
```

### 6.3 资源

- VLM 推理: 8×A100 / L40S for Qwen2-VL-7B
- 训练: 4×L40S (与 AVLN 一致)
- 额外: GPT-4 API for sub-goal extraction (offline)

---

## 7. 风险与备选方案

### 7.1 主要风险

**风险 1**: VLM verifier 准确率不足
- **表现**: 假阳性率高，agent 学会"刷 sub-goal"
- **备选**: 用 GPT-4V 而非开源 VLM；或人工标注子集 fine-tune

**风险 2**: Sub-goal 提取错误
- **表现**: 复杂指令解析失败
- **备选**: 仅在 RxR (有 path description) 上实验

**风险 3**: 计算成本过高
- **表现**: VLM 推理慢
- **备选**: 离线预计算 sub-goal completion labels

### 7.2 简化方案

- **Sub-goal 简化版**: 仅用指令中的"地名/物体"作为 landmarks
- **Verifier 简化版**: 用 CLIP 相似度 (而非 VLM 推理)
- **仅 RxR 实验**: 利用 path description

---

## 8. 与其他方向的协同

### 8.1 + 方向 A (强烈推荐)

```
课程化 (难度由低到高) + MVR (中间信号)
→ 简单任务用 sub-goal reward 容易学会
→ 困难任务 sub-goal 提取本身就难
→ 课程化让 MVR 在简单任务上首先验证
```

### 8.2 + 方向 C

```
语言条件化策略 + MVR
→ 指令条件化调节 VLM verifier 严格性
```

---

## 9. 论文结构建议

```
3.1 Background: RLVR, Reward Shaping, PRM
3.2 Method: Multimodal Verifiable Reward (MVR)
    3.2.1 Sub-goal Extraction
    3.2.2 VLM Verifier Design
    3.2.3 MVR Composition
    3.2.4 MVR-GRPO Training
3.3 Experiments
    3.3.1 VLM Verifier Evaluation
    3.3.2 Main Results
    3.3.3 Ablation Studies
    3.3.4 Reward Hacking Analysis
    3.3.5 Cross-Dataset Generalization
3.4 Conclusion
```

---

## 10. 关键参考文献 (完整列表)

### 10.1 RLVR / R1 系列
- [RLVR-Survey-2024] Lambert, N., et al. arXiv:2403.13787.
- [GRPO-2024] Shao, Z., et al. arXiv:2402.03300.
- [R1-2025] Guo, D., et al. arXiv:2501.12948.
- [R1-Zero-2025] (related to R1)
- [Vision-R1-2025] Huang, Z., et al. arXiv:2503.06749.
- [R1-V-2025] Zhang, J., et al.
- [MM-Eureka-2025] Meng, F., et al. arXiv:2503.07365.
- [Visual-RFT-2025] Liu, Z., et al. (referenced)
- [Seg-Zero-2025] Du, H., et al. arXiv:2503.06520.

### 10.2 Reward Shaping
- [RewardShaping-1999] Ng, A. Y., et al. ICML 1999.
- [Auto-Shaping] (related)

### 10.3 PRM 系列
- [PRM-Lightman-2023] Lightman, H., et al. arXiv:2305.20050.
- [Math-Shepherd-2024] Wang, P., et al. arXiv:2312.08935.
- [Critic-2024] (related, OpenAI)

### 10.4 VLM / Multimodal Judge
- [CLIP-2021] Radford, A., et al. ICML 2021.
- [Qwen2-VL-2024] Wang, P., et al. arXiv:2409.12191.
- [LLaVA-1.5-2023] Liu, H., et al.
- [VLM-as-Judge-Survey-2024] (assumed)

### 10.5 Visual Grounding in Navigation
- [CLIP-on-Wheels-2022] Gadre, S., et al. CoRL 2022.
- [VLFM-2024] Yokoyama, N., et al. ICRA 2024.
- [Visual-Lang-Maps-2023] Huang, C., et al. ICRA 2023.

### 10.6 VLN 子目标/中间监督
- [LAW-2021] Raychaudhuri, S., et al. EMNLP 2021. **(最相关)**
- [Sub-Instr-RxR-2020] Ku, A., et al. EMNLP 2020.
- [Waypoint-2021] Krantz, J., et al. ICCV 2021.

### 10.7 RLHF / Reward Hacking
- [RLHF-2017] Christiano, P., et al. NeurIPS 2017.
- [Reward-Hacking-2017] Amodei, D., et al.
- [Specification-Gaming-2020] Krakovna, V., et al.

### 10.8 VLN 基础
- [R2R-2018] Anderson, P., et al. CVPR 2018.
- [VLN-CE-2020] Krantz, J., et al. ECCV 2020.
- [RxR-2020] Ku, A., et al. EMNLP 2020.
- [ActiveVLN-2025] Zhang, Z., et al. arXiv:2509.12618.
- [VLN-R1-2025] Qi, Z., et al. arXiv:2506.17221.
- [NaVid-2024] Zhang, J., et al. RSS 2024.

---

## 11. 一句话总结

> **方向 B 首次将 R1-style "可验证奖励" 从纯文本/数学领域推广到多模态视觉-语言导航：利用 VLM 自动验证 agent 是否经过指令中的关键地标作为中间奖励信号，将 ActiveVLN 的稀疏 0/1 success reward 转化为稠密、可验证、可分解的多模态奖励，预期在 R2R Val-Unseen 上将 SR 从 50.1 提升至 54-56，并将单 episode 关键动作识别率提升 30%+。**
