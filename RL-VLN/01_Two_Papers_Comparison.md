# 两篇核心论文深度对比：ActiveVLN vs VLN-R1

> **生成日期**: 2026-06-20
> **目的**: 为后续三个创新方向提供 baseline 与问题边界
> **来源**: `paper/Zhang 等 - 2025 - ActiveVLN...pdf` & `paper/Qi 等 - 2025 - VLN-R1...pdf`

---

## 1. 论文概览

| 字段 | ActiveVLN (AVLN) | VLN-R1 (R1) |
|---|---|---|
| **作者** | Zhang, Zhu, Pan, Wang, Xu, Sun, Zheng | Qi, Zhang, Yu, Wang, Zhao |
| **机构** | SUSTech + Spatialtemporal AI + MBZUAI + Tencent Youtu | HKU + Shanghai AI Lab |
| **arXiv** | 2509.12618 (2025-09-16) | 2506.17221 (2025-06-25) |
| **代码** | 本仓库 (ActiveVLN) | https://vlnr1.github.io |
| **Backbone** | Qwen2.5-VL-3B | Qwen2-VL-2B / 7B |
| **数据集** | R2R + RxR (177K) | R2R + RxR (1.8M SFT + 20K RFT) |
| **评测** | R2R/RxR Val-Unseen | R2R/RxR Val-Unseen |
| **环境** | Habitat (CE) | Habitat (CE) |

---

## 2. 任务定义（两篇共识）

**VLN-CE 任务 (Krantz et al., ECCV 2020)**：

```
Episode = (s_0, I, s*)
s_0: 起点 (位置+朝向)
I:   自然语言指令
s*:  目标位置

每个 step t：
  v_t: 前向 RGB 图像
  a_t ~ π_θ(a_t | I, h_t)
  a_t ∈ {FORWARD, LEFT, RIGHT, STOP}

终止条件：agent 发出 STOP
成功条件：STOP 时与 s* 的 geodesic 距离 < 3m
```

**评测指标**：
- **NE** (Navigation Error): 终点到目标的距离
- **OS** (Oracle Success): 路径上任意点距目标 < 3m
- **SR** (Success Rate): 终点距目标 < 3m
- **SPL** (SR weighted by Path Length): SR × (reference_path / max(predicted, reference))
- **nDTW** (normalized Dynamic Time Warping): 路径对齐度 (RxR 评测)

---

## 3. 共同问题动机（WHY）

两篇论文**一致指出**当前 VLN 的三大瓶颈：

### 3.1 IL+DAgger 的成本困境
- IL 仅学专家策略，**遇未见状态会累积误差** (协变量偏移)
- DAgger 需不断收集专家修正 → **人工成本高、训练慢**
- 现有 SOTA (NaVid, UniNaVid, StreamVLN) 都重度依赖 DAgger

### 3.2 RL 在 VLN 中的应用空白
- **PPO** 需要 critic 模型，训练代价大
- **GRPO** (源自 DeepSeekMath, Shao et al. 2024) 在 LLM 推理上取得成功，但 VLN 领域应用稀少
- 现有少量 RL-VLN 工作 (如 [8] 文中所引 R1) **依赖专家轨迹做 reward shaping**，未真正与环境交互

### 3.3 探索能力受限
- IL 训练分布的策略无法**发现非专家路径**
- 在 val-unseen 场景下，**未见过指令/拓扑**会显著掉点

---

## 4. 方法分歧 (HOW)

### 4.1 ActiveVLN 的方法

**核心理念**：**多轮 (multi-turn) 范式 + 主动探索 + GRPO**

```
┌─────────────────── Stage 1: IL Bootstrap ───────────────────┐
│  Qwen2.5-VL-3B  +  167.6K 专家轨迹 (R2R+R2R-EnvDrop+RxR)   │
│  冻结 vision encoder，仅训练 connector + LLM               │
│  Cross-entropy loss, lr=2e-5, batch=64, 20h                 │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────── Stage 2: Multi-turn GRPO ────────────────┐
│  1. 启动 simulator HTTP server (并行多个环境)              │
│  2. 每个 prompt 采样 G=4 条 rollouts                       │
│  3. Soft success reward: 15·I(success)·d_goal/3            │
│  4. Action chunking: 一次预测 3 步                          │
│  5. Dynamic early-stop: T_max = α·|τ*|, α=2                 │
│  6. Scene preloading + scene caching                       │
│  7. GRPO objective (group-wise normalization)              │
└─────────────────────────────────────────────────────────────┘
```

**关键公式**：
$$\mathcal{L}_{RL} = \mathbb{E}_{\{o_i\}}\left[\frac{1}{G}\sum_{i=1}^{G}\frac{1}{|o_i|}\sum_{t=1}^{|o_i|}\min\left(\frac{\pi_\theta}{\pi_{\theta_{old}}}A_{i,t}, \text{clip}\left(\frac{\pi_\theta}{\pi_{\theta_{old}}}, 1-\epsilon, 1+\epsilon\right)A_{i,t}\right)\right]$$

**关键技术贡献**：
1. **Multi-turn 范式** (图2b): 动作自回归地从过去 obs+actions 生成 → 让 GRPO 梯度能传到所有前置动作
2. **Dynamic early-stopping**: 自适应截断长尾失败轨迹
3. **Engineering**: simulator HTTP server, scene cache/preload

### 4.2 VLN-R1 的方法

**核心理念**：**VLN-Ego 数据集 + SFT + RFT (GRPO + TDR)**

```
┌─────────────────── 数据准备: VLN-Ego ───────────────────────┐
│  90 个 Matterport3D 场景 (61 训 / 11 val / 18 测试)         │
│  动作级标注: instruction + ego video + 6-step action        │
│  630K R2R + 1.2M RxR (英文) 训练样本                        │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────── Stage 1: SFT ────────────────────────────┐
│  预测 next 6 actions: "A. Move forward 25cm, B. Turn..."    │
│  Long-Short Memory Sampling: 近期高密度+远期低密度         │
│  6-discrete action space (单轮预测完整轨迹)                  │
│  Cross-entropy loss, lr=5e-6, 36h × 8 A800                  │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────── Stage 2: RFT (GRPO + TDR) ───────────────┐
│  1. 同 prompt 采样 8 个候选                                  │
│  2. Time-Decayed Reward:                                    │
│     R_raw = Σ_{k=0}^{n-1} γ^k · I(α_{t+k} = α*_{t+k})    │
│  3. GRPO 优势函数 + 可选 KL 约束 (β=0.04)                   │
│  4. 12h/epoch, 8 sample/prompt                              │
└─────────────────────────────────────────────────────────────┘
```

**关键公式 (TDR)**：
$$R_{\text{raw}} = \sum_{k=0}^{n-1} \gamma^k \cdot \mathbb{I}(\alpha_{t+k} = \alpha^*_{t+k})$$

其中 γ 是衰减因子 (论文中用指数衰减)，强调**位置感知一致性**。

### 4.3 关键方法对比表

| 维度 | ActiveVLN | VLN-R1 |
|---|---|---|
| **范式** | Multi-turn (动态环境交互) | Single-turn + 6-step 预测 |
| **奖励函数** | Soft success: 15·I·d/3 | TDR: γ^k·I (0/1 hard) |
| **数据需求** | 4K prompts (RL阶段) | 1.8M SFT + 20K RFT |
| **样本/组** | 4 rollouts | 8 samples |
| **动作空间** | 3-action chunk (合并) | 6-discrete (完整文字) |
| **历史采样** | 全历史 (KV cache 复用) | Long-Short Memory Sampling |
| **目标** | 主动探索 | 可验证奖励+时序加权 |
| **动态停止** | T_max = α·|τ*| | 无 |
| **simulator** | HTTP server (解耦) | 内嵌 |
| **训练时长** | 20h (IL) + 20h (RL) | 36h (SFT) + 12h/epoch (RFT) |
| **backbone** | Qwen2.5-VL-3B | Qwen2-VL-2B/7B |

---

## 5. 实验结果对比 (WHAT)

### 5.1 R2R Val-Unseen (VLN-CE)

| 方法 | 模型大小 | 训练数据 | Stage | NE↓ | OS↑ | SR↑ | SPL↑ | ΔSR |
|---|---|---|---|---|---|---|---|---|
| NaVid [3] | 7B | - | IL | 5.90 | 46.7 | 33.1 | 30.7 | - |
| NaVid + DAgger | 7B | - | DAgger | 5.50 | 49.1 | 37.4 | 35.9 | +4.3 |
| StreamVLN [6] | 7B | 1M | IL | 6.05 | 53.8 | 45.5 | 41.6 | - |
| StreamVLN + DAgger | 7B | 1M | DAgger | 5.47 | 57.8 | 50.8 | 45.7 | +5.3 |
| **VLN-R1 (Qi et al.)** | **2B** | 1.8M | SFT | 8.27 | 33.0 | 21.2 | 15.9 | - |
| **VLN-R1 (Qi et al.)** | **2B** | 1.8M | **RFT** | **7.00** | **37.5** | **25.6** | **20.5** | **+4.4** |
| **VLN-R1 (Qi et al.)** | 7B | 1.8M | **RFT** | **7.00** | **41.2** | **30.2** | **21.8** | **+5.3** |
| **ActiveVLN** | **3B** | 177K | IL | 6.83 | 42.7 | 38.5 | 33.7 | - |
| **ActiveVLN** | **3B** | 177K | DAgger | 6.11 | 50.2 | 45.4 | 41.5 | +6.9 |
| **ActiveVLN** | **3B** | 177K | **RL** | **5.31** | **58.3** | **50.1** | **43.7** | **+11.6** |

**关键观察**：
- ActiveVLN-RL 的 +11.6 SR 是所有方法中**最大提升**
- ActiveVLN 3B RL (50.1) > StreamVLN 7B DAgger (50.8)，**小模型+RL** 接近大模型+DAgger
- VLN-R1 7B RFT (30.2) < StreamVLN 7B IL (45.5)，R1 在大模型上**绝对值较低**

### 5.2 RxR Val-Unseen (VLN-CE)

| 方法 | 模型 | 训练数据 | NE↓ | SR↑ | SPL↑ | nDTW↑ |
|---|---|---|---|---|---|---|
| NaVILA [5] | 8B | + VQA | 6.77 | 49.3 | 44.0 | 58.8 |
| UniNaVid [4] | 7B | 2.4M + Others | 6.24 | 48.7 | 40.9 | - |
| StreamVLN [6] | 7B | 1M + Others | 6.22 | 52.9 | 46.0 | 61.9 |
| **ActiveVLN w/o RL** | **3B** | 177K | 7.25 | 41.0 | 34.1 | - |
| **ActiveVLN** | **3B** | 177K | **5.84** | **50.7** | 41.2 | 58.1 |

**关键观察**：
- ActiveVLN 用 1/10 数据达到**最低 NE** (5.84)
- 不用其他数据 (如 VQA)，纯 VLN 训练

---

## 6. 消融研究关键发现

### 6.1 ActiveVLN 关键消融

| 消融 | 结论 |
|---|---|
| **Multi-turn vs Single-turn** | Multi-turn IL baseline 略低 (38.5 vs 39.7)，但 RL 后 multi-turn 大幅领先 (50.1 vs 40.3) → **RL 强烈依赖 multi-turn 范式** |
| **奖励设计** | Soft success > Hard success > Path align. (nDTW 项) → **过度模仿专家反而降低 SR** |
| **Dynamic early-stop** | 移除后 rollout 时间 +10.9%，且长尾失败未被剪除 |
| **Scene preload/cache** | 各自加速 4.68% / 2.24% |

### 6.2 VLN-R1 关键消融

| 消融 | 结论 |
|---|---|
| **Action space** | 6-discrete > 8 > 4 > 1 (单步太短信息不足) |
| **History Memory** | Long-Short Memory > Avg(16) > Exp Decay > Avg(8) |
| **Generations (RFT)** | k=8 > 6 > 4 > 2，更多采样提供更稳定优势 |
| **Reward Function** | TDR (Exponential Decay) > Linear Distance > Uniform > Hard (binary) |

### 6.3 共识与分歧

**共识**：
- **GRPO 优于 PPO/DPO**：无需 critic，训练更稳
- **多步预测比单步好**：信息更丰富
- **奖励设计敏感**：binary 奖励信号不够
- **时序加权重要**：后期动作比早期更重要 (TDR 的关键洞察)

**分歧**：
- **Single vs Multi-turn**：R1 用单轮+多步预测，AVLN 用多轮+chunk，**两种范式均能 work**；Multi-turn 后期潜力大
- **数据量级**：R1 用 1.8M SFT + 20K RFT，AVLN 用 167K+4K → **数据效率有 ~10× 差距**
- **专家依赖**：R1 仍需完整 SFT (专家轨迹)，AVLN 几乎不依赖专家轨迹 (IL bootstrap only)

---

## 7. 共同未解空白 (The "Gap")

| 编号 | 空白 | 详细描述 | 关联方向 |
|---|---|---|---|
| **G1** | 样本效率低 | 两篇都需 4K+ prompts 做 RL；如何用更少样本达到 SOTA？ | A, C |
| **G2** | 奖励稀疏 | 只有 final success / TDR (0/1)，无中间信号 | B |
| **G3** | 范式融合 | Multi-turn + Single-turn 各有优劣，能否融合？ | A |
| **G4** | 跨域泛化 | 仅 R2R/RxR (室内)，室外/动态人/工业场景缺 | C |
| **G5** | 实时性 | Rollout 106.9s (AVLN)，RL 阶段 12h/epoch (R1) | A (课程化) |
| **G6** | 失败回溯 | agent 走错只能终止，无反思/重试 | C (语言反思) |
| **G7** | 多人协作 | single agent only | (其他方向) |
| **G8** | World Model | 无环境模型 → rollout 必须真仿真 | (其他方向) |

---

## 8. 结论：方向选择的依据

| 空白 | 推荐方向 | 理由 |
|---|---|---|
| G1, G3 | **A 课程式分层** | 课程化直接降低样本需求；分层利用 multi-turn 优势 |
| G2 | **B 多模态可验证** | 中间信号是 RL 经典问题，VLM 提供新工具 |
| G1, G4 | **C 语言条件化** | 指令条件化是天然跨域工具 |

**最强组合：A + B**（共同解决 G1+G2+G3）

---

## 9. 详细参考文献（来自两篇论文 [N] 编号）

### 9.1 ActiveVLN 参考文献

- [1] Anderson et al. **R2R**. CVPR 2018
- [2] Krantz et al. **VLN-CE**. ECCV 2020
- [3] Zhang et al. **NaVid**. RSS 2024
- [4] Zhang et al. **UniNaVid**. RSS 2025
- [5] Cheng et al. **NaVILA**. RSS 2025
- [6] Wei et al. **StreamVLN**. arXiv:2507.05240
- [7] Ross et al. **DAgger**. AISTATS 2011
- [8] Qi et al. **VLN-R1**. arXiv:2506.17221
- [9] Gao et al. **OctoNav**. arXiv:2506.09839
- [10] Ku et al. **RxR**. EMNLP 2020
- [31] Shao et al. **DeepSeekMath (GRPO)**. arXiv:2402.03300
- [32] Guo et al. **DeepSeek-R1**. arXiv:2501.12948
- [33] Schulman et al. **PPO**. arXiv:1707.06347
- [34] Zheng et al. **DeepEyes**. arXiv:2505.14362
- [35] Wang et al. **RAGEN**. arXiv:2504.20073
- [40] Bai et al. **Qwen2.5-VL**. arXiv:2502.13923
- [42] Yu et al. **DAPO**. arXiv:2503.14476
- [43] Zhang et al. **MapNav**. arXiv:2502.13451

### 9.2 VLN-R1 参考文献

- [2] Anderson et al. **R2R**. CVPR 2018
- [6] Chen et al. **Topological Planning**. CVPR 2021
- [14] Guo et al. **DeepSeek-R1**. arXiv:2501.12948
- [16] Hong et al. **Discrete-Continuous Bridge**. CVPR 2022
- [21] Krantz et al. **Waypoint Predictors**. ICCV 2021
- [23] Krantz et al. **VLN-CE**. ECCV 2020
- [24] Ku et al. **RxR**. EMNLP 2020
- [29] Liu et al. **DeepSeek-V3**. arXiv:2412.19437
- [44] Rajbhandari et al. **ZeRO**. arXiv:1910.02054
- [45] Raychaudhuri et al. **LAW Supervision**. EMNLP 2021
- [47] Schulman et al. **PPO**. arXiv:1707.06347
- [49] Shao et al. **DeepSeekMath (GRPO)**. arXiv:2402.03300
- [55] Wang et al. **Qwen2-VL**. arXiv:2409.12191
- [60] Zhang et al. **NaVid**. RSS 2024
