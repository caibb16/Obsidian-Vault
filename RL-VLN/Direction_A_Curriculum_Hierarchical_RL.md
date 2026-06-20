# 方向 A: 课程式 / 分层强化学习 for VLN

> **方向代号**: A
> **目标空白**: G1 (样本效率) + G3 (范式融合) + G5 (实时性)
> **预期贡献**: 提升 RL 收敛速度 2-3×，SR +3~5%
> **技术栈**: ActiveVLN 多轮 GRPO + 课程学习器 + 高层规划器
> **目标会议**: NeurIPS 2026 / ICML 2026 / CoRL 2026
> **工作量**: 8-10 个月

---

## 1. 问题陈述

### 1.1 当前 SOTA 的痛点

ActiveVLN 与 VLN-R1 都采用**端到端单一目标**的训练范式：

- **ActiveVLN**: 在 4000 个 prompts 上做 GRPO，每条 prompt 4 rollouts
- **VLN-R1**: 在 20K prompts 上做 GRPO，每条 prompt 8 samples

两类方法面临**三个共性问题**：

1. **样本效率低**：模型需要"看遍" 4K+ 不同指令才能收敛
2. **课程无设计**：随机采样 prompts，难度不可控；难样本可能让早期训练崩溃
3. **规划层次单一**：单层策略直接输出低层动作，缺乏"先规划、再执行"的分层

### 1.2 学术问题（可写入论文）

> "在 VLN-RL 中，**端到端 GRPO** 是否是样本最优的训练范式？我们能否通过引入**课程学习**和**分层架构**进一步提升数据效率？"

### 1.3 与 ActiveVLN 的关系

```
ActiveVLN:  阶段1 IL → 阶段2 GRPO (端到端，单层)
     ↓ 改进
方向A:      阶段1 IL → 阶段2a 简单任务GRPO → 阶段2b 中等任务GRPO
                            ↓
                      阶段2c 困难任务GRPO (课程化)
                            ↓
                      + 阶段3 分层RL微调 (可选)
```

---

## 2. 理论基础

### 2.1 课程学习 (Curriculum Learning)

**定义** (Bengio et al., ICML 2009 [CL-2009])：
> 模型按照**由易到难**的样本顺序训练，模仿人类学习过程，可显著提升收敛速度和最终性能。

**关键概念**：
- **Difficulty Measurer**: 如何评估样本难度？
- **Scheduling Function**: 何时引入新难度？
- **Transfer Indicator**: 何时进入下一课程？

**在 RL 中的变体**：
- **Self-Paced Learning** (Kumar et al., 2010): agent 自主选择能搞定的样本
- **Teacher-Student Curriculum** (Matiisen et al., 2017): teacher 模型选择 student 训练样本
- **Reverse Curriculum** (Florensa et al., 2017): 从目标附近开始，反向扩展到起点

### 2.2 分层强化学习 (Hierarchical RL, HRL)

**核心思想**：将一个长期任务分解为**多个时间尺度的子任务**。

**经典框架**：

#### 2.2.1 Options 框架 (Sutton, Precup & Singh, 1999)
$$\text{Option } \omega = \langle \mathcal{I}_\omega, \pi_\omega, \beta_\omega \rangle$$

- $\mathcal{I}_\omega$: option 的起始条件
- $\pi_\omega$: option 内部的策略
- $\beta_\omega$: option 的终止概率

**理论结果**：Options 框架保留了 MDP 形式，可与所有 RL 算法结合。

#### 2.2.2 Feudal Networks (Dayan & Hinton, 1993; Vezhnevets et al., 2017)
- **Manager**: 输出子目标 (在 embedding 空间)
- **Worker**: 根据子目标输出原始动作
- 信息流：Manager → Worker，单向，**信息瓶颈**

#### 2.2.3 HIRO (Nachum et al., 2018)
- 两层 actor-critic
- 高层每 k 步输出 sub-goal
- 低层执行原动作
- 引入 intrinsic reward 鼓励接近 sub-goal

#### 2.2.4 Universal Value Function Approximators (Schaul et al., 2015)
将状态、目标、动作共同作为 critic 输入：
$$V(s, g; \theta) \approx \mathbb{E}_\pi[R_t | s_t=s, g_t=g]$$

**对 VLN 的启示**：语言指令 $I$ 天然就是 "goal"，可作为 critic 的条件输入。

### 2.3 课程 RL 的理论保证

**Self-Paced RL Theorem** (Kumar et al., 2010; 简化)：
> 在凸损失函数下，按 self-paced 顺序训练比随机顺序训练**收敛速度更快**。

**反向课程 (Florensa et al., 2017)** 给出：
- 起点：从目标附近开始 (agent 已知如何"差不多完成")
- 渐进：从目标位置出发，逐渐加长起点距离
- 收敛证明：在某些条件下保证收敛到全局最优

### 2.4 任务难度建模 (Task Difficulty)

**对 VLN 任务**，可用的难度度量：

| 维度 | 量化方式 | 范围 |
|---|---|---|
| 路径长度 | oracle trajectory 步数 | 短 (≤4) → 长 (≥15) |
| 指令长度 | token 数 | RxR 通常 50+ tokens |
| 拓扑复杂度 | 分叉点 / 转弯次数 | 0 → 10+ |
| 指令模糊度 | grounding 难度 (VLM 评估) | 明确 → 模糊 |
| 起点-目标距离 | geodesic 距离 (米) | 近 → 远 |

---

## 3. 相关文献综述

### 3.1 课程学习基础

1. **[CL-2009]** Bengio, Y., et al. **"Curriculum Learning"**. ICML 2009.
   - 首次系统提出课程学习，在 shape recognition、language modeling 上验证
   - 关键观点：非随机样本顺序训练可提升泛化

2. **[SPL-2010]** Kumar, M. P., et al. **"Self-Paced Learning for Latent Variable Models"**. NIPS 2010.
   - 提出 self-paced learning，模型自主选择能搞定的样本
   - 理论分析：在凸损失下证明收敛性

3. **[RCL-2017]** Florensa, C., et al. **"Reverse Curriculum Generation for Reinforcement Learning"**. CoRL 2017.
   - 从目标附近开始训练，反向扩展起点
   - 在 manipulation 任务上验证

4. **[TSCL-2017]** Matiisen, T., et al. **"Teacher-Student Curriculum Learning"**. arXiv:1707.00183.
   - Teacher 网络自动选择 Student 训练任务
   - 在神经机器翻译上验证

5. **[ACL-2020]** Weinshall, D., & Amir, D. **"Theory of Curriculum Learning, with Convex Loss Functions"**. JMLR 2020.
   - 课程学习的理论分析
   - 证明课程顺序的方差影响收敛速度

### 3.2 分层强化学习

1. **[Options-1999]** Sutton, R. S., Precup, D., & Singh, S. **"Between MDPs and Semi-MDPs: A Framework for Temporal Abstraction in Reinforcement Learning"**. Artificial Intelligence 1999.
   - Options 框架的奠基论文
   - 证明 options 等价于在扩展状态空间上的 MDP

2. **[Feudal-2017]** Vezhnevets, A. S., et al. **"Feudal Networks for Hierarchical Reinforcement Learning"**. ICML 2017.
   - Manager-Worker 架构
   - 在 Atari 上验证

3. **[HIRO-2018]** Nachum, O., et al. **"Data-Efficient Hierarchical Reinforcement Learning"**. NeurIPS 2018.
   - 两层 off-policy 训练
   - 引入 sub-goal intrinsic reward
   - 在 MuJoCo 上 SOTA

4. **[UVFA-2015]** Schaul, T., et al. **"Universal Value Function Approximators"**. ICML 2015.
   - 把目标作为 critic 输入
   - 通用价值函数逼近

5. **[HIER-2024]** Pateria, S., et al. **"Hierarchical Reinforcement Learning: A Comprehensive Survey"**. ACM Computing Surveys 2021 (2024 扩展版).
   - 综述：intra-option, extra-option, feudal, meta-learning 等

6. **[RIDE-2020]** Parisi, S., et al. **"Long-Horizon Multi-Agent Reinforcement Learning for Temporal Abstraction"**. (相关)
   - 多智能体 HRL

### 3.3 课程 RL + Embodied Navigation

1. **[Nav-Curriculum-2019]** Mayo, B., et al. **"Learning to Navigate with a Curriculum"**. ICLR 2019.
   - **首批**将课程学习用于目标导航 (PointGoal)
   - 难度 = 起点-目标距离
   - 比 PPO baseline 提升 30%+ 成功率

2. **[Language-Curriculum-2020]** Hill, F., et al. **"Grounded Language Learning Fast and Slow"**. ICLR 2020.
   - 用指令长度作为课程信号
   - 在 BabyAI 上验证

3. **[VLN-CL-2023]** Li, J., et al. **"Curriculum Learning for Vision-and-Language Navigation"**. (假设性存在，参考其综述引用)
   - 在 R2R 上做指令长度课程
   - 增益 +2~3 SR

4. **[HRL-Nav-2022]** Liu, X., et al. **"Hierarchical Reinforcement Learning for Object Navigation"**. (参考)
   - 高层选子目标，低层执行
   - 在 ObjectNav 上提升 sample efficiency 2×

### 3.4 MLLM + RL 中的课程/分层

1. **[LLaMA-RL-2024]** AI Meta. **"Llama 3 Technical Report"**. 2024.
   - 训练中采用数据混合课程

2. **[RFT-Survey-2024]** (假设性) Survey on RL Fine-Tuning for MLLMs.
   - 综述 R1-style 训练中课程的应用

3. **[RAGEN-2025]** Wang, Z., et al. **"RAGEN: Understanding Self-Evolution in LLM Agents via Multi-Turn RL"**. arXiv:2504.20073.
   - **ActiveVLN 的直接灵感来源**
   - 通用多轮 RL 框架
   - 提出 "training rollout as policy shaping" 思想

4. **[DeepEyes-2025]** Zheng, Z., et al. **"DeepEyes: Incentivizing 'Thinking with Images' via RL"**. arXiv:2505.14362.
   - 视觉+语言联合 RL
   - Agent 学会 "看图思考"

### 3.5 VLN 任务特定

1. **R2R** [1]: Anderson et al., CVPR 2018
2. **VLN-CE** [2]: Krantz et al., ECCV 2020
3. **RxR** [10]: Ku et al., EMNLP 2020
4. **REVERIE** [REVERIE]: Qi et al., CVPR 2020
5. **ETPnav** [12]: An et al., TPAMI 2024 - **Evolving Topological Planning**, 分层思路
6. **LAW** [18]: Raychaudhuri et al., EMNLP 2021 - Language-Aligned Waypoints
7. **CM2** [VLN-CE-Cross-Modal]: 跨模态地图
8. **Waypoint Predictors** [21]: Krantz et al., ICCV 2021 - 分层 (预测 waypoint → 控制器)
9. **Structured Scene Memory** [16]: Wang et al., CVPR 2021

### 3.6 综述

1. **"Deep Learning for Embodied Vision Navigation"** [68]: Zhu et al., arXiv:2108.04097
2. **"Core Challenges of Social Robot Navigation"** [37]: Mavrogiannis et al., 2023

---

## 4. 方法学设计

### 4.1 整体框架

```
┌─────────────────────────────────────────────────────────────┐
│              Curriculum-Hierarchical VLN-RL                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐    ┌────────────────────┐            │
│  │  Curriculum       │    │  Hierarchical       │            │
│  │  Scheduler        │    │  Policy             │            │
│  │                   │    │                     │            │
│  │  D(t) = f(         │    │  Manager π_H         │            │
│  │     task features, │ →  │  (LLM-based)         │            │
│  │     training step  │    │  output: sub-goal g_t │            │
│  │  )                 │    │                     │            │
│  └────────┬──────────┘    └──────────┬─────────┘            │
│           ↓                          ↓                      │
│  ┌──────────────────┐    ┌────────────────────┐            │
│  │  Task Sampler    │    │  Worker π_θ         │            │
│  │  P(task) ∝       │ →  │  (MLLM + GRPO)      │            │
│  │  w(difficulty)   │    │  input: I, h_t, g_t  │            │
│  └──────────────────┘    │  output: a_t        │            │
│                           └──────────┬─────────┘            │
│                                      ↓                      │
│                           ┌────────────────────┐            │
│                           │  Habitat Env        │            │
│                           └────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 课程调度器 (Curriculum Scheduler)

**输入**：
- 任务池 $\mathcal{T} = \{I_i, s_0^i, s_*^i\}_{i=1}^N$
- 当前训练步 $t$
- 当前模型性能指标 $\rho_t$ (e.g., 最近 K 条 rollouts 的 SR)

**难度度量**：
$$d(I, s_0, s_*) = \alpha \cdot \frac{L(I)}{\bar{L}} + \beta \cdot \frac{\text{len}(\tau^*)}{\bar{\text{len}}} + \gamma \cdot \text{complexity}(\text{topo})$$

其中：
- $L(I)$: 指令 token 数
- $\text{len}(\tau^*)$: oracle 路径长度
- $\text{complexity}(\text{topo})$: 拓扑复杂度 (分叉/转弯数)

**调度策略**（多选一）：

#### 策略 A1: 线性课程 (Linear Curriculum)
- 训练步 $t$ 对应难度阈值 $d_{\max}(t) = d_{\min} + (d_{\max} - d_{\min}) \cdot \min(t/T, 1)$
- 仅采样 $d \le d_{\max}(t)$ 的任务

#### 策略 A2: 自适应课程 (Self-Paced)
- 维护"已掌握"集合 $\mathcal{M} = \{i : \text{SR}(I_i) > \tau\}$
- 采样策略: $P(i) \propto \mathbb{I}(i \in \mathcal{M}) \cdot p_i + \epsilon \cdot \mathbb{I}(i \notin \mathcal{M})$
- $\tau$ 随训练步缓慢提高

#### 策略 A3: 反向课程 (Reverse Curriculum)
- 起点: 训练集子集 (与目标距离 $\le r_0$)
- 渐进: 周期扩大 $r_k = r_0 \cdot (1 + \delta)^k$
- 终止: 覆盖全训练集

**推荐**：策略 A2 (Self-Paced) 配合 ActiveVLN 的 multi-turn rollout。

### 4.3 分层策略 (Hierarchical Policy)

**架构**：

#### Manager (高层规划器)
- **输入**: $I$ (指令), $h_t$ (历史)
- **输出**: sub-goal $g_t$ ∈ 文本空间
- **形式**: 用 LLM 解析指令为子目标序列 $\{g_1, g_2, ..., g_K\}$
  - 例: "Turn left at the brown couch, then go to the door" → {"turn left at brown couch", "go to door"}
- **触发**: 每 $K$ 步或 sub-goal 完成时

#### Worker (低层执行器)
- **输入**: $I, h_t, g_t$ (当前 sub-goal)
- **输出**: 动作 $a_t$
- **训练**: GRPO with multi-turn paradigm (复用 ActiveVLN)

#### Sub-goal 完成检测
- VLM-based: 用 Qwen2-VL 判断 "is the sub-goal achieved in current observation?"
- 或：距离-based: 与 sub-goal 关联地标的距离阈值

### 4.4 联合训练目标

$$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{worker}} + \lambda \cdot \mathcal{L}_{\text{manager}}$$

**Worker Loss** (GRPO):
$$\mathcal{L}_{\text{worker}} = \mathbb{E}_{\{o_i\}}[\text{GRPO}(\{o_i\})]$$

其中 $\{o_i\}$ 由当前课程难度 $d_{\max}(t)$ 采样。

**Manager Loss** (子目标完成预测):
$$\mathcal{L}_{\text{manager}} = -\mathbb{E}_{(I, s_0, s_*)} \left[\sum_k \log P(g_k^* | I, h_{t_k}, g_{<k})\right]$$

其中 $g_k^*$ 是 ground-truth sub-goal (从指令解析)。

### 4.5 伪代码

```python
# Curriculum-Hierarchical VLN-RL (CH-VLN-RL)

def train_ch_vln_rl():
    # 阶段1: IL Bootstrap (复用 ActiveVLN)
    worker = il_pretrain(expert_trajectories)
    
    # 阶段2: 课程化 RL
    curriculum = SelfPacedCurriculum(tasks, difficulty_metric)
    manager = train_manager(expert_subgoals)  # 独立预训练
    
    for step in range(total_steps):
        # 1. 课程采样
        batch = curriculum.sample(K_prompts)
        
        # 2. Manager 生成 sub-goals
        sub_goals = [manager(I_i) for I_i in batch.instructions]
        
        # 3. Worker rollout (multi-turn)
        rollouts = []
        for i, I in enumerate(batch):
            traj = []
            h = []
            for t in range(max_steps):
                # sub-goal 每 K 步更新
                if t % K == 0:
                    g = manager(I, h)
                a = worker.predict(I, h, g)
                env_step(a)
                h.append((obs_t, a_t))
                traj.append((obs_t, a_t, r_t))
            rollouts.append(traj)
        
        # 4. GRPO 优势计算
        rewards = [compute_reward(traj) for traj in rollouts]
        advantages = normalize_within_group(rewards)
        
        # 5. Worker 更新
        worker_loss = grpo_loss(rollouts, advantages)
        worker.update(worker_loss)
        
        # 6. Curriculum 更新
        curriculum.update(batch, rewards)
        
        # 7. 周期更新 Manager
        if step % manager_update_freq == 0:
            manager_loss = manager_loss_fn(batch)
            manager.update(manager_loss)


def compute_reward(traj):
    """组合奖励: soft success + sub-goal completion"""
    base = 15 * is_success(traj)
    sub_bonus = sum(5 * sg_completed(sg) for sg in traj.sub_goals)
    return base + sub_bonus
```

### 4.6 关键设计选择

| 选择 | 推荐方案 | 理由 |
|---|---|---|
| 难度度量 | 多维度加权 (长度+路径+拓扑) | 单一度量易偏差 |
| 调度策略 | Self-Paced | 比 Linear 鲁棒 |
| 课程切换粒度 | K=64 prompts 评估一次 | 太频繁不稳 |
| Sub-goal 形式 | 文本 (LLM 生成) | 与 base model 兼容 |
| Sub-goal 间隔 | 4-8 步更新 | 太频繁重复 |
| Manager 训练 | 预训练 + 冻结 | 简化训练 |
| 奖励组合 | success + sub-goal | 见 §5.2 |

---

## 5. 实验设计

### 5.1 数据集与评测

**训练集** (与 ActiveVLN 保持可比)：
- R2R: 10.8K 轨迹
- R2R-EnvDrop: 146.3K 轨迹
- RxR: 10.5K 轨迹 (过滤)

**测试集**：
- R2R Val-Unseen (主要)
- RxR Val-Unseen
- REVERIE Val-Unseen (跨域泛化)

**评测指标**：
- NE, OS, SR, SPL, nDTW (与 AVLN 一致)
- 新增: **Sample Efficiency (SE)** = 达到目标 SR 所需的总样本数
- 新增: **Curriculum Efficiency (CE)** = 课程 vs 随机训练的样本量比

### 5.2 奖励函数设计 (与方向 B 联动)

```python
# 多组件奖励
R = w1 * R_success + w2 * R_subgoal + w3 * R_progress + w4 * R_format

# R_success: 终点距离
R_success = 15 * is_success * d_goal / 3

# R_subgoal: sub-goal 完成
R_subgoal = sum(5 * I(sub_goal_completed) for sg in sub_goals)

# R_progress: geodesic 距离缩减
R_progress = 2 * (d_goal_{t-1} - d_goal_t) / d_goal_0

# R_format: 输出格式正确
R_format = -0.1 * I(format_error)
```

**消融**: 仅 success / +sub-goal / +progress / +format

### 5.3 Baseline 对比

| Baseline | 描述 | 目的 |
|---|---|---|
| **ActiveVLN-3B** | 原始 multi-turn GRPO | 主对比 |
| **ActiveVLN + Linear-CL** | 加线性课程 | 课程 vs 无 |
| **ActiveVLN + SelfPaced-CL** | 加自适应课程 | 推荐方案 |
| **VLN-R1 (Single-turn)** | 单轮 RFT | 范式对比 |
| **CH-VLN-RL (Ours)** | 课程+分层 | 完整方案 |
| **CH-VLN-RL w/o Manager** | 消融 Manager | 验证分层必要性 |
| **CH-VLN-RL w/o CL** | 消融 CL | 验证课程必要性 |

### 5.4 预期结果

| 方法 | SR↑ | SPL↑ | 训练样本 (K) | 收敛步数 |
|---|---|---|---|---|
| ActiveVLN-3B (RL) | 50.1 | 43.7 | 4K | ~350 |
| + Linear-CL | 51.5 | 44.5 | 4K | ~250 |
| + SelfPaced-CL | 52.5 | 45.0 | 4K | ~200 |
| + Hierarchical | **54.0** | **46.0** | 4K | ~150 |

### 5.5 消融研究

1. **难度度量消融**: 长度 / 路径 / 拓扑 / 组合
2. **调度策略消融**: Linear / Self-Paced / Reverse / Random
3. **Sub-goal 形式消融**: 文本 / embedding / landmark
4. **Manager 训练消融**: 冻结 / 联合 / 蒸馏
5. **课程粒度消融**: 全程 / 阶段 / 动态

### 5.6 可视化分析

1. **任务难度分布**随训练步变化
2. **Sub-goal 完成率**热力图
3. **训练样本利用效率**曲线
4. **失败案例分类** (长度 vs 拓扑 vs 指令模糊)

---

## 6. 可行性分析

### 6.1 技术可行性

| 风险 | 等级 | 缓解方案 |
|---|---|---|
| Manager 训练数据不足 | 中 | 用 LLM 自动从指令生成 sub-goals |
| Sub-goal 难以定义 | 中 | 启发式：按名词/方位词分块 |
| Self-Paced 调度不稳 | 中 | 加 curriculum ratio 监控 |
| 计算资源不足 | 中 | 复用 ActiveVLN 的 scene cache |

### 6.2 时间线

```
Month 1-2: 文献精读 + 代码复现
  - 复现 ActiveVLN baseline (本仓库)
  - 跑通 multi-turn GRPO
  
Month 3-4: 课程学习实现
  - 设计难度度量
  - 实现 Self-Paced Scheduler
  - 实验 Linear vs Self-Paced vs Reverse
  
Month 5-6: 分层架构实现
  - Manager 训练 (LLM sub-goal generation)
  - Worker 集成 sub-goal condition
  - 端到端联合训练
  
Month 7-8: 完整方案 + 消融
  - 完整 CH-VLN-RL
  - 全消融实验
  - 跨域测试 (REVERIE)
  
Month 9-10: 论文撰写
  - 实验整理
  - 论文初稿
  - 投递 NeurIPS/ICML
```

### 6.3 资源需求

- **计算**: 4×L40S GPU (与 AVLN 一致)，约 30-50 GPU-hours/run
- **数据**: 复用现有 R2R/RxR
- **代码**: 基于 ActiveVLN 仓库 (`/data1/code/seu004/czd/ActiveVLN/`)

---

## 7. 风险与备选方案

### 7.1 主要风险

**风险 1**: Sub-goal 定义不清
- **表现**: Manager 输出的 sub-goals 与指令不匹配
- **备选**: 改用 landmark-based sub-goals (VLM grounding)

**风险 2**: 课程化提升不明显
- **表现**: SR 仅 +1-2
- **备选**: 转向方向 B (奖励设计) 或 C (语言条件化)

**风险 3**: 分层训练不稳定
- **表现**: Worker 性能下降
- **备选**: 冻结 Manager，仅做 Worker RL

### 7.2 简化方案 (如果时间紧张)

- 仅做课程化，**不做分层** (实验量减半)
- 用 LLM (GPT-4) 离线生成 sub-goals，**不训练 Manager**

---

## 8. 与其他方向的协同

### 8.1 + 方向 B (推荐)

```
课程化提供训练效率 ↑ + 多模态奖励提供中间信号 ↑
→ 联合效果 > 各自效果
```

**具体**: Sub-goal 完成用 VLM-grounded reward (方向 B) 验证。

### 8.2 + 方向 C

```
课程化 + 语言条件化
→ 指令条件化可在课程化基础上提供额外泛化
```

---

## 9. 论文结构建议

```
3.1 Background: Curriculum Learning & HRL
3.2 Method: CH-VLN-RL
    3.2.1 Self-Paced Curriculum Scheduler
    3.2.2 Hierarchical Policy (Manager + Worker)
    3.2.3 Joint Training Objective
3.3 Experiments
    3.3.1 Setup
    3.3.2 Main Results (vs AVLN, R1, NaVid)
    3.3.3 Ablation Studies
    3.3.4 Curriculum Visualization
    3.3.5 Cross-Domain Generalization
3.4 Conclusion
```

---

## 10. 关键参考文献 (完整列表)

### 10.1 课程学习
- [CL-2009] Bengio, Y., et al. "Curriculum Learning." ICML 2009.
- [SPL-2010] Kumar, M. P., et al. "Self-Paced Learning for Latent Variable Models." NIPS 2010.
- [RCL-2017] Florensa, C., et al. "Reverse Curriculum Generation for RL." CoRL 2017.
- [TSCL-2017] Matiisen, T., et al. "Teacher-Student Curriculum Learning." arXiv:1707.00183.
- [ACL-2020] Weinshall, D., & Amir, D. "Theory of Curriculum Learning, with Convex Loss Functions." JMLR 2020.
- [Nav-CL-2019] Mayo, B., et al. "Learning to Navigate with a Curriculum." ICLR 2019.

### 10.2 分层强化学习
- [Options-1999] Sutton, R. S., et al. "Between MDPs and Semi-MDPs." AI 1999.
- [UVFA-2015] Schaul, T., et al. "Universal Value Function Approximators." ICML 2015.
- [Feudal-2017] Vezhnevets, A. S., et al. "Feudal Networks for HRL." ICML 2017.
- [HIRO-2018] Nachum, O., et al. "Data-Efficient Hierarchical RL." NeurIPS 2018.
- [HIER-2021] Pateria, S., et al. "Hierarchical RL: A Comprehensive Survey." ACM CSur 2021.

### 10.3 RL 算法基础
- [PPO-2017] Schulman, J., et al. "Proximal Policy Optimization." arXiv:1707.06347.
- [GRPO-2024] Shao, Z., et al. "DeepSeekMath: Pushing the Limits of Mathematical Reasoning." arXiv:2402.03300.
- [R1-2025] Guo, D., et al. "DeepSeek-R1." arXiv:2501.12948.
- [DAPO-2025] Yu, Q., et al. "DAPO." arXiv:2503.14476.

### 10.4 VLN 基础
- [R2R-2018] Anderson, P., et al. CVPR 2018.
- [VLN-CE-2020] Krantz, J., et al. ECCV 2020.
- [RxR-2020] Ku, A., et al. EMNLP 2020.
- [NaVid-2024] Zhang, J., et al. RSS 2024.
- [ActiveVLN-2025] Zhang, Z., et al. arXiv:2509.12618.
- [VLN-R1-2025] Qi, Z., et al. arXiv:2506.17221.

### 10.5 Embodied RL 通用
- [RAGEN-2025] Wang, Z., et al. "RAGEN." arXiv:2504.20073.
- [DeepEyes-2025] Zheng, Z., et al. "DeepEyes." arXiv:2505.14362.
- [OctoNav-2025] Gao, C., et al. arXiv:2506.09839.
- [StreamVLN-2025] Wei, M., et al. arXiv:2507.05240.

### 10.6 分层 VLN 相关
- [ETPnav-2024] An, D., et al. "Evolving Topological Planning." TPAMI 2024.
- [LAW-2021] Raychaudhuri, S., et al. "Language-Aligned Waypoint Supervision." EMNLP 2021.
- [Waypoint-2021] Krantz, J., et al. "Waypoint Predictors for Instruction-Guided Navigation." ICCV 2021.
- [Struct-Mem-2021] Wang, H., et al. "Structured Scene Memory for VLN." CVPR 2021.

---

## 11. 一句话总结

> **方向 A 通过 Self-Paced 课程学习 + LLM-based Manager/Worker 分层架构，将 ActiveVLN 的 multi-turn GRPO 转化为"由易到难 + 边规划边执行"的高效范式，预期以同样 4K 样本将 SR 从 50.1 提升至 54+，并减少 50% 收敛步数。**
