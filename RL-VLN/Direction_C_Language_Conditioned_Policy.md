# 方向 C: 语言条件化策略 (Language-Conditioned Policy) for VLN

> **方向代号**: C
> **目标空白**: G1 (样本效率) + G4 (跨域泛化) + G6 (失败回溯)
> **预期贡献**: 让指令本身调节探索策略与反思能力，跨域泛化 +5~8%
> **技术栈**: ActiveVLN + 指令编码条件 + 熵调节 + 反思 token
> **目标会议**: ICLR 2027 / CoRL 2026 / ICRA 2027
> **工作量**: 6-8 个月 (相对最易实现)
> **理论意义**: 把 "instructions as policy conditioner" 与 R1-style reasoning 结合

---

## 1. 问题陈述

### 1.1 当前策略的"指令无关"问题

**ActiveVLN** 与 **VLN-R1** 的策略 $\pi_\theta(a_t | I, h_t)$ **形式上**依赖指令 $I$，但实际训练中：

| 问题 | 表现 | 后果 |
|---|---|---|
| 指令长度未利用 | 长/短指令被同等处理 | 长指令泛化差 |
| 指令语义未充分利用 | 关键名词/方位未提取 | agent 不知该看什么 |
| 探索策略与指令难度无关 | 所有 prompt 探索温度相同 | 难指令探索不足 |
| 失败无反思 | 走错只能终止 | 同一错误重复犯 |

### 1.2 学术问题

> "在 VLN-RL 中，**指令 $I$ 是否应作为策略的动态调节器**？我们能否让 agent 根据指令的**复杂度、长度、语义内容**自适应调整探索温度、推理深度和反思行为？"

### 1.3 三个子方向

我们提出方向 C 的三个递进子方向：

- **C1: 指令条件化熵调节** —— 难指令 → 强探索
- **C2: 指令感知反思机制** —— 失败时语言反思
- **C3: 指令-子任务链式推理** —— CoT-style sub-instruction generation

---

## 2. 理论基础

### 2.1 Conditional RL 基础

**通用形式**:
$$\pi_\theta(a_t | s_t, c)$$

其中 $c$ 是条件 (conditioning) 信息。

**经典工作**:
- **Universal Value Function Approximators (UVFA)** (Schaul et al., 2015): $V(s, g)$ 同时输入状态和目标
- **Conditional RL** (Finn et al., 2017, MAML): 任务条件化快速适应
- **Decision Transformer** (Chen et al., 2021): 把 RL 视为序列建模，条件化 return-to-go

### 2.2 Language-Conditioned RL

**先驱工作**:
- **CLIPort** (Shridhar et al., 2022): 语言+图像条件化操作
- **RT-2** (Brohan et al., 2023): VLM 直接输出动作
- **Gato** (Reed et al., 2022): 通用多模态 agent
- **BC-Z** (Jang et al., 2022): zero-shot task generalization

**理论**:
- 语言 $L$ 提供**任务结构**先验
- $L$ → 行为空间 $\mathcal{A}$ 的偏置
- **跨任务泛化**: 在指令分布 $\mathcal{L}_{\text{train}}$ 上训练，可泛化到 $\mathcal{L}_{\text{test}}$

### 2.3 熵调节探索 (Entropy-Regularized Exploration)

**SAC (Haarnoja et al., 2018)**:
$$\pi^* = \arg\max_\pi \sum_t \mathbb{E}_{(s,a)\sim\rho_\pi}[r(s,a) + \alpha \mathcal{H}(\pi(\cdot | s))]$$

**关键 idea**: $\alpha$ 调节探索-利用权衡

**指令条件化熵**:
$$\alpha(c) = f(\text{complexity}(c), \text{novelty}(c))$$

**理论基础**:
- 复杂指令 → 高 $\alpha$ (强探索)
- 简单指令 → 低 $\alpha$ (利用已知)

### 2.4 Chain-of-Thought (CoT) Reasoning

**Wei et al., 2022 [CoT-2022]**:
- 在 prompt 中加入 "let's think step by step"
- LLM 性能大幅提升

**应用到 RL**:
- **Reflexion** (Shinn et al., 2023): 失败后用 LLM 反思
- **Self-Refine** (Madaan et al., 2023): 迭代自我修正
- **R1-Zero**: RL 自然涌现 CoT

**对 VLN 的应用**:
- agent 走错时，生成**自然语言反思** ("I should have turned left earlier")
- 反思作为 next rollout 的 context

### 2.5 Task-Conditioned Policy 的 PAC 理论

**PAC-MDP 框架** (Strehl et al., 2009):
- 条件化策略可显著减少 sample complexity
- 形式: $\tilde{O}(\sqrt{|\mathcal{C}| \cdot |\mathcal{S}| |\mathcal{A}| T / N})$

**启示**:
- 增加条件维度可降低 sample complexity
- 但需要足够多的条件-行为对应数据

---

## 3. 相关文献综述

### 3.1 Language-Conditioned Policy

1. **[CLIPort-2022]** Shridhar, M., et al. **"CLIPort: What and Where Pathways for Robotic Manipulation"**. CoRL 2022.
   - 语言+图像条件化策略

2. **[BC-Z-2022]** Jang, E., et al. **"BC-Z: Zero-Shot Task Generalization with Robotic Imitation Learning"**. CoRL 2022.

3. **[RT-1-2022]** Brohan, A., et al. **"RT-1: Robotics Transformer"**. arXiv:2203.07847.
   - 大规模机器人 transformer

4. **[RT-2-2023]** Brohan, A., et al. **"RT-2: Vision-Language-Action Models"**. arXiv:2307.15818.
   - VLM 直接输出动作

5. **[Gato-2022]** Reed, S., et al. **"A Generalist Agent"**. TMLR 2022.

6. **[Octo-2024]** Team, O., et al. **"Octo: An Open-Source Generalist Robot Policy"**. RSS 2024.
   - 通用机器人策略

7. **[Pi-0-2024]** Black, K., et al. **"π0: A Vision-Language-Action Flow Model"**. 2024.
   - 通用 VLA 模型

8. **[OpenVLA-2024]** Kim, M. J., et al. **"OpenVLA"**. arXiv:2406.09246.

9. **[HPT-2023]** (assumed) "HPT: Harnessing Pre-trained Models"

### 3.2 Conditional RL

1. **[UVFA-2015]** Schaul, T., et al. **"Universal Value Function Approximators"**. ICML 2015.
2. **[MAML-2017]** Finn, C., et al. **"Model-Agnostic Meta-Learning"**. ICML 2017.
3. **[Decision-Transformer-2021]** Chen, L., et al. **"Decision Transformer: Reinforcement Learning via Sequence Modeling"**. NeurIPS 2021.
4. **[Trajectory-Transformer-2021]** Janner, M., et al. ICML 2021.
5. **[GCRL-2022]** (related, goal-conditioned RL)

### 3.3 Entropy-Regularized & Adaptive Exploration

1. **[SAC-2018]** Haarnoja, T., et al. **"Soft Actor-Critic"**. arXiv:1801.01290.
2. **[MaxEnt-2017]** Haarnoja, T., et al. **"Reinforcement Learning with Deep Energy-Based Policies"**. ICML 2017.
3. **[Adaptive-Entropy-2020]** (related)
4. **[EMI-2023]** (assumed) entropy-modulated inference

### 3.4 Chain-of-Thought / Reasoning

1. **[CoT-2022]** Wei, J., et al. **"Chain-of-Thought Prompting"**. NeurIPS 2022.
2. **[Zero-Shot-CoT-2022]** Kojima, T., et al. **"Large Language Models are Zero-Shot Reasoners"**. NeurIPS 2022.
3. **[ReAct-2023]** Yao, S., et al. **"ReAct: Synergizing Reasoning and Acting in Language Models"**. ICLR 2023.
4. **[Reflexion-2023]** Shinn, N., et al. **"Reflexion: Language Agents with Verbal Reinforcement"**. NeurIPS 2023.
5. **[Self-Refine-2023]** Madaan, A., et al. **"Self-Refine: Iterative Refinement with Self-Feedback"**. NeurIPS 2023.
6. **[R1-Zero-2025]** Guo, D., et al. **"DeepSeek-R1"**. (涌现 CoT)

### 3.5 Verbal Reinforcement for Embodied Agents

1. **[Reflexion-2023]** Shinn, N., et al. (引)
2. **[Voyager-2023]** Wang, G., et al. **"Voyager: An Open-Ended Embodied Agent with LLMs"**. 2023.
3. **[SayCan-2022]** Ahn, M., et al. **"Do As I Can, Not As I Say"**. arXiv:2204.01691.
4. **[Code-as-Policies-2023]** Singh, I., et al. **"Code as Policies"**. ICRA 2023.

### 3.6 Multi-Turn CoT in VLN

1. **[CoT-VLN-2023]** (assumed) "Chain-of-Thought for VLN"
2. **[NaviAgent-2024]** (assumed)
3. **[MapGPT-2024]** Chen, J., et al. **"MapGPT"**. (related)
4. **[Nav-CoT-2024]** (assumed)

### 3.7 Instruction-Conditioned in VLN

1. **[RxR-PATH-2020]** Ku, A., et al. (引) —— RxR 包含 path description
2. **[InstructNav-2024]** Long, Y., et al. (引) —— 零样本指令导航
3. **[Discuss-Nav-2024]** Long, Y., et al. (引) —— 多专家讨论

### 3.8 Embodied RL + Language Feedback

1. **[RLHF-2017]** Christiano, P., et al. NeurIPS 2017.
2. **[LIVING-RL-2023]** (related)
3. **[Text2Reward-2023]** Xie, T., et al. **"Text2Reward"**. arXiv:2309.11436.
   - **最相关**：用语言生成 reward function

---

## 4. 方法学设计

### 4.1 整体框架

```
┌─────────────────────────────────────────────────────────────┐
│       Language-Conditioned Policy for VLN (LCP-VLN)          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Input: Instruction I                                       │
│       ↓                                                    │
│  ┌─────────────────────┐                                   │
│  │ Instruction Encoder │  → φ(I): instruction embedding    │
│  │ (Qwen2-VL encoder)  │                                   │
│  └────────┬────────────┘                                   │
│           ↓                                                │
│  ┌──────────────────────────────────────────┐               │
│  │      Difficulty Analyzer                 │               │
│  │   d(I) = α·L(I) + β·entities + γ·hops   │               │
│  └─────┬─────────────────────────────┬──────┘               │
│        ↓                             ↓                      │
│  ┌────────────┐              ┌────────────────┐            │
│  │ α(I):      │              │ Sub-task Gen:  │            │
│  │ entropy    │              │ CoT-style      │            │
│  │ coefficient│              │ decomposition  │            │
│  └─────┬──────┘              └────┬───────────┘            │
│        ↓                         ↓                        │
│  ┌──────────────────────────────────────────┐               │
│  │   Worker π_θ with conditioning            │               │
│  │   π_θ(a_t | I, h_t, g_t, α(I))          │               │
│  └────────┬──────────────────────────────────┘              │
│           ↓                                                │
│  ┌──────────────────────────────────────────┐               │
│  │   Reflection Module (on failure)          │               │
│  │   r ← LLM("Why did I fail at I?")        │               │
│  │   next attempt uses r as context         │               │
│  └──────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 子方向 C1: 指令条件化熵调节

**核心 idea**: 复杂指令 → 高探索温度；简单指令 → 低温度

**指令复杂度度量**:
$$d(I) = \alpha \cdot \frac{|I|}{\bar{|I|}} + \beta \cdot \text{entities}(I) + \gamma \cdot \text{hops}(I)$$

其中:
- $|I|$: 指令 token 数
- $\text{entities}(I)$: 实体数量 (用 NER 提取)
- $\text{hops}(I)$: 推理跳数 (粗略用逗号数)

**熵系数调节**:
$$\alpha(I) = \alpha_0 + \alpha_1 \cdot \sigma(d(I) - d_{\text{mean}})$$

**Policy 形式**:
$$\pi_\theta(a_t | I, h_t) \propto \exp\left(\frac{Q_\theta(h_t, a_t; I)}{\alpha(I)}\right)$$

**训练**:
- 主损失: GRPO (与 ActiveVLN 一致)
- 辅助损失: 鼓励 $\alpha(I)$ 与真实难度对齐
$$\mathcal{L}_{\text{aux}} = -\mathbb{E}_I[\log P(\alpha(I) | I)]$$

**优势**:
- 简单指令快速收敛
- 复杂指令充分探索
- 总样本效率提升

### 4.3 子方向 C2: 反思机制 (Reflexion-style)

**核心 idea**: 失败时让 LLM 生成语言反思，下次重试时使用

**流程**:

```python
def lcp_vln_with_reflection(worker, llm, env, instruction, max_attempts=3):
    reflection = ""
    
    for attempt in range(max_attempts):
        # 1. Build prompt with reflection
        prompt = f"""Instruction: {instruction}
        
Previous attempt reflection: {reflection if reflection else "None"}
        """
        
        # 2. Rollout
        traj = worker.rollout(env, prompt)
        
        # 3. If success, return
        if is_success(traj):
            return traj
        
        # 4. Generate reflection via LLM
        reflection = llm(f"""I tried to follow: "{instruction}"
        My trajectory: {summarize(traj)}
        I failed because: ...
        
        What should I do differently next time?
        Concrete actionable reflection:""")
    
    return None
```

**反思的存储与重用**:
- 维护 episode-level reflection buffer
- 相似任务共享反思 (用 instruction embedding 检索)

**理论**:
- 类似 Reflexion 的 verbal RL
- 经验回放 + 语言摘要

### 4.4 子方向 C3: 子任务链式推理

**核心 idea**: 模仿 R1，让 agent 在动作前先生成 sub-task

**形式**:
```
Input:  I = "go past the brown couch, then turn left at the door"

Output:
  Thought: First, I need to identify the brown couch.
  Sub-task 1: Find and pass the brown couch
  Action 1: FORWARD
  
  Thought: Now I should look for the door on the left
  Sub-task 2: Find the door
  Action 2: TURN_LEFT
  
  ...
```

**实现**:
- 在 prompt 中加入 "think step by step"
- 用 SFT 训练 (从 RxR path description 学习)
- RL 微调

**SFT 数据构造**:
```python
def make_cot_data(instruction, trajectory):
    sub_instructions = extract_sub_instructions(instruction)
    cot = ""
    for sub_i, action in zip(sub_instructions, trajectory):
        cot += f"Thought: {sub_i}\nAction: {action}\n"
    return cot
```

**RL 阶段**:
- Reward: success + format (CoT 格式正确)
- GRPO 训练

### 4.5 完整算法

```python
def train_lcp_vln(worker, llm_reflector, sub_task_gen, env):
    """Language-Conditioned Policy for VLN"""
    
    # 阶段1: IL with CoT-style data (从 RxR path desc)
    worker = sft_with_cot(worker, cot_data)
    
    # 阶段2: GRPO with language conditioning
    for step in range(total_steps):
        # 1. Sample batch
        batch = sample_prompts(B)
        
        # 2. Compute instruction embeddings & difficulties
        inst_embeds = worker.encode_instructions(batch)
        difficulties = compute_difficulty(batch)
        
        # 3. Set entropy coefficient per prompt
        alphas = compute_alphas(difficulties)
        
        # 4. Multi-turn rollouts with reflection on failure
        rollouts = []
        for prompt in batch:
            reflection = ""
            for attempt in range(max_attempts):
                traj = worker.rollout(
                    env, 
                    prompt=build_prompt(prompt, reflection),
                    entropy_coef=alpha_for(prompt)
                )
                if is_success(traj):
                    rollouts.append(traj)
                    break
                reflection = llm_reflector(prompt, traj)
        
        # 5. GRPO update
        rewards = [compute_reward(t) for t in rollouts]
        advantages = normalize(rewards)
        loss = grpo_loss(rollouts, advantages)
        worker.update(loss)
```

### 4.6 关键设计选择

| 选择 | 推荐 | 理由 |
|---|---|---|
| 复杂度度量 | 长度+实体+跳数 组合 | 单一度量偏差 |
| 熵系数范围 | α ∈ [0.1, 0.5] | 过大难收敛 |
| 反思频率 | 每 3 步一次 | 太频繁干扰 |
| 反思存储 | Episode-level | 跨 episode 难泛化 |
| CoT 训练 | SFT 预训练 | 比直接 RL 稳 |
| 反思 LLM | Qwen2-7B | 平衡性能与成本 |

---

## 5. 实验设计

### 5.1 数据集与评测

**训练**: R2R + RxR (含 path description) + REVERIE
**测试**: R2R Val-Unseen, RxR Val-Unseen, REVERIE Val-Unseen
**评测指标**:
- NE, OS, SR, SPL, nDTW
- **新指标: 跨域 SR Drop** = (in-domain SR - cross-domain SR) / in-domain SR

### 5.2 子方向 C1 主实验

| 方法 | 描述 | 预期 SR |
|---|---|---|
| ActiveVLN | Baseline | 50.1 |
| + 固定熵 | α=0.2 | 49.5 |
| **+ 指令条件化熵 (Ours)** | α(I) | **52.0** |

**分析维度**:
- 不同长度指令的 SR 提升
- 熵系数与难度的相关性
- 收敛曲线对比

### 5.3 子方向 C2 主实验

| 方法 | 描述 | 预期 SR |
|---|---|---|
| ActiveVLN | No reflection | 50.1 |
| + 1 attempt | No reflection loop | 50.1 |
| + 2 attempts + reflection | **Ours** | **53.0** |
| + 3 attempts + reflection | Ours-3 | 54.5 |

**分析维度**:
- 失败-重试成功率
- 反思质量 vs SR 关系
- 反思多样性

### 5.4 子方向 C3 主实验

| 方法 | 描述 | 预期 SR |
|---|---|---|
| ActiveVLN (无 CoT) | Baseline | 50.1 |
| + CoT SFT only | SFT with thought | 51.5 |
| + CoT SFT + GRPO | **Ours** | **53.0** |
| + CoT + Reflection | Full | **55.0** |

### 5.5 跨域泛化

| 训练 → 测试 | Baseline SR | 条件化熵 | +Reflection | +CoT |
|---|---|---|---|---|
| R2R → R2R | 50.1 | 52.0 | 53.0 | 53.0 |
| R2R → RxR | 35.0 | 38.0 | 40.0 | 42.0 |
| R2R → REVERIE | 25.0 | 28.0 | 30.0 | 32.0 |

### 5.6 消融研究

- **C1 消融**: 固定/线性/自适应/无熵调节
- **C2 消融**: 1/2/3 attempts, 反思有无, LLM 大小
- **C3 消融**: CoT SFT/RL/格式约束

---

## 6. 可行性分析

### 6.1 技术可行性

| 风险 | 等级 | 缓解 |
|---|---|---|
| 反思 LLM 不准 | 中 | 用 GPT-4 替代开源 |
| 复杂度度量偏差 | 低 | 多维度组合 |
| CoT 数据不足 | 中 | 用 RxR path desc |
| 计算开销 | 中 | 反思可离线 |

### 6.2 时间线 (相对最快)

```
Month 1-2: 复现 AVLN + CoT 数据准备
Month 3-4: C1 指令条件化熵
Month 5-6: C2 反思机制
Month 7-8: C3 CoT (可选) + 完整实验
```

### 6.3 资源

- 与 AVLN 相同 (4×L40S)
- 反思 LLM 可离线调用
- CoT 数据可预生成

---

## 7. 风险与备选方案

### 7.1 主要风险

**风险 1**: 反思机制不稳定
- **表现**: 反思反而误导 agent
- **备选**: 仅在明显失败时触发反思 (confidence < 0.3)

**风险 2**: CoT 数据噪声
- **表现**: 训练 CoT 时引入错误
- **备选**: 用 GPT-4 生成+人工抽检

**风险 3**: 跨域泛化提升有限
- **表现**: 与 baseline 持平
- **备选**: 与方向 A (课程) 或 B (MVR) 组合

### 7.2 简化方案

- **仅做 C1** (条件化熵) —— 改动最小
- **仅做 C2** (反思) —— 工程量适中
- **仅做 C3** (CoT) —— 需要 CoT 数据

---

## 8. 与其他方向的协同

### 8.1 + 方向 A (推荐)

```
课程化 + 语言条件化
→ 课程化提供"按难度训练"
→ 语言条件化提供"按指令调节"
→ 双重调节可极大提升 sample efficiency
```

### 8.2 + 方向 B

```
MVR 验证 sub-goal + CoT 生成 sub-goal
→ CoT 给出 sub-goal 序列
→ MVR 用 VLM 验证 sub-goal 完成
→ 闭环
```

---

## 9. 论文结构建议

```
3.1 Background: Conditional RL, Language-Conditioned Policy, CoT
3.2 Method: Language-Conditioned Policy for VLN
    3.2.1 Instruction-Conditioned Entropy
    3.2.2 Verbal Reflection Mechanism
    3.2.3 Sub-task Chain-of-Thought (optional)
3.3 Experiments
    3.3.1 Main Results
    3.3.2 Cross-Domain Generalization
    3.3.3 Ablation Studies
    3.3.4 Qualitative Analysis
3.4 Conclusion
```

---

## 10. 关键参考文献 (完整列表)

### 10.1 Language-Conditioned Policy
- [CLIPort-2022] Shridhar, M., et al. CoRL 2022.
- [BC-Z-2022] Jang, E., et al. CoRL 2022.
- [RT-1-2022] Brohan, A., et al. arXiv:2203.07847.
- [RT-2-2023] Brohan, A., et al. arXiv:2307.15818.
- [Gato-2022] Reed, S., et al. TMLR 2022.
- [Octo-2024] arXiv:2405.12213.
- [Pi-0-2024] Black, K., et al.
- [OpenVLA-2024] Kim, M. J., et al. arXiv:2406.09246.

### 10.2 Conditional RL / Meta-RL
- [UVFA-2015] Schaul, T., et al. ICML 2015.
- [MAML-2017] Finn, C., et al. ICML 2017.
- [Decision-Transformer-2021] Chen, L., et al. NeurIPS 2021.
- [Trajectory-Transformer-2021] Janner, M., et al. ICML 2021.
- [PEARL-2019] Rakelly, K., et al. ICML 2019.

### 10.3 Entropy-Regularized RL
- [SAC-2018] Haarnoja, T., et al. arXiv:1801.01290.
- [MaxEnt-2017] Haarnoja, T., et al. ICML 2017.
- [Soft-DQN-2024] (related)

### 10.4 CoT / Reasoning
- [CoT-2022] Wei, J., et al. NeurIPS 2022.
- [ZeroShot-CoT-2022] Kojima, T., et al. NeurIPS 2022.
- [ReAct-2023] Yao, S., et al. ICLR 2023.
- [Reflexion-2023] Shinn, N., et al. NeurIPS 2023.
- [Self-Refine-2023] Madaan, A., et al. NeurIPS 2023.
- [R1-Zero-2025] Guo, D., et al. arXiv:2501.12948.

### 10.5 Verbal Reinforcement / Embodied Agents
- [Reflexion-2023] Shinn, N., et al. (引)
- [Voyager-2023] Wang, G., et al.
- [SayCan-2022] Ahn, M., et al. arXiv:2204.01691.
- [Text2Reward-2023] Xie, T., et al. arXiv:2309.11436.
- [Code-as-Policies-2023] Singh, I., et al. ICRA 2023.

### 10.6 Multi-Turn CoT in VLN
- [Nav-CoT-2024] (assumed)
- [MapGPT-2024] Chen, J., et al. (related)
- [Discuss-Nav-2024] Long, Y., et al. (引)

### 10.7 Instruction-Conditioned VLN
- [InstructNav-2024] Long, Y., et al. (引)
- [RxR-2020] Ku, A., et al. (引)
- [InstructBLIP-2023] Dai, W., et al. (related)

### 10.8 PAC Learning Theory
- [PAC-MDP-2009] Strehl, A. L., et al.
- [Generalization-RL-2024] (related surveys)

### 10.9 VLN 基础
- [R2R-2018] Anderson, P., et al. CVPR 2018.
- [VLN-CE-2020] Krantz, J., et al. ECCV 2020.
- [RxR-2020] Ku, A., et al. EMNLP 2020.
- [REVERIE-2020] Qi, Y., et al. CVPR 2020.
- [ActiveVLN-2025] Zhang, Z., et al. arXiv:2509.12618.
- [VLN-R1-2025] Qi, Z., et al. arXiv:2506.17221.
- [NaVid-2024] Zhang, J., et al. RSS 2024.

---

## 11. 一句话总结

> **方向 C 让指令本身成为策略的动态调节器：通过指令条件化熵 (难指令→强探索)、失败后的语言反思机制 (Reflexion-style)、和子任务链式推理 (CoT-style) 三个子机制，让 agent 的探索温度、反思行为和推理深度随指令自适应调整，预期将 ActiveVLN 在跨域任务 (R2R→REVERIE) 上的 SR drop 从 ~50% 缩小到 ~35%，同时将 RxR (长指令) 的 SR 从 50.7 提升至 54+。**
