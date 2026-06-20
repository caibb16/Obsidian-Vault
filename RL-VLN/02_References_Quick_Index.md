# 关键文献快速索引 (References Quick Index)

> **生成日期**: 2026-06-20
> **目的**: 为三个方向（A/B/C）的文献综述提供快速查阅入口
> **组织方式**: 按"主题-时间"排序，每条文献标注在 ABC 三个方向中的相关性

---

## 0. 检索提示

### 0.1 推荐检索引擎
- **Google Scholar** (https://scholar.google.com): 综合
- **Semantic Scholar** (https://www.semanticscholar.org): AI 优化检索
- **arXiv** (https://arxiv.org): 最新 preprint
- **Connected Papers** (https://www.connectedpapers.com): 关联图谱
- **OpenReview** (https://openreview.net): 顶会评审 + 接收

### 0.2 推荐检索词组合

**方向 A (课程 + 分层)**:
```
curriculum learning + reinforcement learning + vision language navigation
hierarchical reinforcement learning + embodied AI
options framework + navigation
self-paced reinforcement learning
```

**方向 B (多模态奖励)**:
```
verifiable reward + vision language
multimodal reward model + RL
process reward model + navigation
VLM as judge + RLHF
visual grounding + reward shaping
```

**方向 C (语言条件化)**:
```
language conditioned policy + VLN
chain of thought + embodied agent
verbal reinforcement + navigation
instruction conditioned reinforcement learning
```

---

## 1. 必读 Top 20 文献 (硕士开题前 2 周内完成)

按"重要性 × 与论文 ABC 方向相关性"排序。

### 1.1 基石论文 (Top 5)

| # | 文献 | 简称 | 方向 | 一句话 |
|---|---|---|---|---|
| 1 | **ActiveVLN** (Zhang et al., 2025) | AVLN | A,B,C 全部 | 本仓库对应论文，最直接 baseline |
| 2 | **VLN-R1** (Qi et al., 2025) | R1 | A,B,C 全部 | 另一 SOTA，RFT 范式 |
| 3 | **DeepSeekMath (GRPO)** (Shao et al., 2024) | GRPO | A,B,C 全部 | RL 算法基础 |
| 4 | **DeepSeek-R1** (Guo et al., 2025) | R1-Zero | B,C | R1-style 训练范式 |
| 5 | **Curriculum Learning** (Bengio et al., 2009) | CL-2009 | A | 课程学习奠基 |

### 1.2 关键理论 (Top 10)

| # | 文献 | 简称 | 方向 | 一句话 |
|---|---|---|---|---|
| 6 | **Between MDPs and Semi-MDPs (Options)** (Sutton et al., 1999) | Options-1999 | A | Options 框架 |
| 7 | **Universal Value Function Approximators** (Schaul et al., 2015) | UVFA-2015 | A,C | 通用价值函数 |
| 8 | **Feudal Networks for HRL** (Vezhnevets et al., 2017) | Feudal-2017 | A | Manager-Worker 架构 |
| 9 | **Reward Shaping** (Ng et al., 1999) | RewardShaping-1999 | B | Potential-based shaping |
| 10 | **Let's Verify Step by Step (PRM)** (Lightman et al., 2023) | PRM-Lightman-2023 | B | 过程奖励模型 |
| 11 | **Chain-of-Thought Prompting** (Wei et al., 2022) | CoT-2022 | C | CoT 推理 |
| 12 | **Reflexion** (Shinn et al., 2023) | Reflexion-2023 | C | 语言反思 |
| 13 | **CLIP** (Radford et al., 2021) | CLIP-2021 | B | 视觉-语言对齐 |
| 14 | **RAGEN** (Wang et al., 2025) | RAGEN-2025 | A,B,C | 多轮 RL 通用框架 |
| 15 | **Soft Actor-Critic** (Haarnoja et al., 2018) | SAC-2018 | C | 最大熵 RL |

### 1.3 关键应用 (Top 5)

| # | 文献 | 简称 | 方向 | 一句话 |
|---|---|---|---|---|
| 16 | **Reverse Curriculum Generation** (Florensa et al., 2017) | RCL-2017 | A | 反向课程 |
| 17 | **Math-Shepherd** (Wang et al., 2024) | Math-Shepherd | B | 自动 PRM |
| 18 | **Language-Aligned Waypoints** (Raychaudhuri et al., 2021) | LAW-2021 | B | **方向 B 最相关** |
| 19 | **ReAct** (Yao et al., 2023) | ReAct-2023 | C | Reasoning + Acting |
| 20 | **DAPO** (Yu et al., 2025) | DAPO-2025 | A,B | 改进 GRPO |

---

## 2. 按方向分类的详细文献列表

### 2.1 方向 A: 课程学习 + 分层 RL (15 篇)

#### 课程学习 (5 篇)
1. **[CL-2009]** Bengio, Y., et al. **"Curriculum Learning"**. ICML 2009.
   - 关键词: curriculum, sample ordering, machine learning
2. **[SPL-2010]** Kumar, M. P., et al. **"Self-Paced Learning"**. NIPS 2010.
3. **[RCL-2017]** Florensa, C., et al. **"Reverse Curriculum Generation for RL"**. CoRL 2017.
4. **[TSCL-2017]** Matiisen, T., et al. **"Teacher-Student Curriculum Learning"**. arXiv:1707.00183.
5. **[Nav-CL-2019]** Mayo, B., et al. **"Learning to Navigate with a Curriculum"**. ICLR 2019. ⭐ **最相关**

#### 分层强化学习 (5 篇)
6. **[Options-1999]** Sutton, R. S., et al. **"Between MDPs and Semi-MDPs"**. AI 1999.
7. **[UVFA-2015]** Schaul, T., et al. **"Universal Value Function Approximators"**. ICML 2015.
8. **[Feudal-2017]** Vezhnevets, A. S., et al. **"Feudal Networks for HRL"**. ICML 2017.
9. **[HIRO-2018]** Nachum, O., et al. **"Data-Efficient HRL"**. NeurIPS 2018.
10. **[HRL-Survey-2021]** Pateria, S., et al. **"HRL: A Comprehensive Survey"**. ACM CSur 2021.

#### Embodied + Curriculum (5 篇)
11. **[ETPnav-2024]** An, D., et al. **"Evolving Topological Planning"**. TPAMI 2024.
12. **[LAW-2021]** Raychaudhuri, S., et al. **"Language-Aligned Waypoint Supervision"**. EMNLP 2021.
13. **[Struct-Mem-2021]** Wang, H., et al. **"Structured Scene Memory"**. CVPR 2021.
14. **[Waypoint-2021]** Krantz, J., et al. ICCV 2021.
15. **[HiREN-2023]** (assumed) "Hierarchical RL for Embodied Navigation"

---

### 2.2 方向 B: 多模态可验证奖励 (15 篇)

#### RLVR 基础 (5 篇)
1. **[GRPO-2024]** Shao, Z., et al. **"DeepSeekMath"**. arXiv:2402.03300.
2. **[R1-2025]** Guo, D., et al. **"DeepSeek-R1"**. arXiv:2501.12948.
3. **[RLVR-Survey-2024]** Lambert, N., et al. arXiv:2403.13787.
4. **[DAPO-2025]** Yu, Q., et al. arXiv:2503.14476.
5. **[VLM-R1-Survey-2025]** (assumed) "Multimodal R1"

#### 多模态 R1 (5 篇)
6. **[Vision-R1-2025]** Huang, Z., et al. arXiv:2503.06749.
7. **[R1-V-2025]** Zhang, J., et al.
8. **[MM-Eureka-2025]** Meng, F., et al. arXiv:2503.07365.
9. **[Seg-Zero-2025]** Du, H., et al. arXiv:2503.06520.
10. **[Visual-RFT-2025]** Liu, Z., et al.

#### 奖励设计 (5 篇)
11. **[RewardShaping-1999]** Ng, A. Y., et al. ICML 1999.
12. **[PRM-Lightman-2023]** Lightman, H., et al. arXiv:2305.20050.
13. **[Math-Shepherd-2024]** Wang, P., et al. arXiv:2312.08935.
14. **[LAW-2021]** Raychaudhuri, S., et al. ⭐ **最相关**
15. **[Subgoal-VLN-2022]** (assumed) "Subgoal-based Navigation"

---

### 2.3 方向 C: 语言条件化策略 (15 篇)

#### Language-Conditioned Policy (5 篇)
1. **[CLIPort-2022]** Shridhar, M., et al. CoRL 2022.
2. **[BC-Z-2022]** Jang, E., et al. CoRL 2022.
3. **[RT-1-2022]** Brohan, A., et al. arXiv:2203.07847.
4. **[RT-2-2023]** Brohan, A., et al. arXiv:2307.15818.
5. **[Octo-2024]** arXiv:2405.12213.

#### Conditional RL + Meta-RL (5 篇)
6. **[UVFA-2015]** Schaul, T., et al. ICML 2015.
7. **[MAML-2017]** Finn, C., et al. ICML 2017.
8. **[Decision-Transformer-2021]** Chen, L., et al. NeurIPS 2021.
9. **[PEARL-2019]** Rakelly, K., et al. ICML 2019.
10. **[GCRL-Survey-2023]** (assumed) "Goal-Conditioned RL Survey"

#### CoT + Verbal RL (5 篇)
11. **[CoT-2022]** Wei, J., et al. NeurIPS 2022.
12. **[ZeroShot-CoT-2022]** Kojima, T., et al. NeurIPS 2022.
13. **[ReAct-2023]** Yao, S., et al. ICLR 2023.
14. **[Reflexion-2023]** Shinn, N., et al. NeurIPS 2023. ⭐ **最相关**
15. **[Text2Reward-2023]** Xie, T., et al. arXiv:2309.11436.

---

## 3. 跨方向通用文献 (5 篇)

这些文献对三个方向都重要：

| 文献 | 简称 | 重要性 |
|---|---|---|
| **GRPO** (Shao et al., 2024) | GRPO | RL 算法基础，所有方向用 |
| **RAGEN** (Wang et al., 2025) | RAGEN | 多轮 RL 框架，AVLN 灵感 |
| **NaVid** (Zhang et al., 2024) | NaVid | MLLM-based VLN baseline |
| **PPO** (Schulman et al., 2017) | PPO | RL 经典基线 |
| **R2R/VLN-CE/RxR** | VLN 数据 | 评测数据集 |

---

## 4. 文献获取途径

### 4.1 优先途径
1. **arXiv** (https://arxiv.org) - 免费 preprint
2. **OpenReview** (https://openreview.net) - 顶会评审
3. **会议官网** (NeurIPS, ICML, ICLR, ICRA, IROS, RSS, CoRL)
4. **作者主页** - 通常有 PDF 链接

### 4.2 备选途径
1. **Papers With Code** (https://paperswithcode.com) - 论文+代码
2. **Semantic Scholar** - 引用追踪
3. **Google Scholar** - 通用搜索
4. **Connected Papers** - 关联图谱

### 4.3 校园资源
- 学校 VPN + Web of Science
- Scopus / Engineering Village
- 数字图书馆

---

## 5. 文献管理工具

### 5.1 推荐工具

| 工具 | 用途 | 价格 |
|---|---|---|
| **Zotero** | 文献管理 | 免费 (开源) |
| **Zotero + Better BibTeX** | LaTeX 集成 | 免费 |
| **Notion** | 笔记+综述 | 免费 (个人) |
| **Obsidian** | 双向链接笔记 | 免费 (个人) |
| **Connected Papers** | 关联可视化 | 免费 (基础) |
| **Scite.ai** | 引用上下文 | 部分免费 |

### 5.2 推荐工作流

1. **Zotero** 收集所有 PDF + bibtex
2. **Obsidian** 写文献笔记（双向链接）
3. **LaTeX + BibTeX** 写作
4. **Better BibTeX** 自动同步

---

## 6. 综述论文 (Survey Papers)

写硕士论文时**必引**的综述：

| 综述 | 引用 | 主题 |
|---|---|---|
| **Deep Learning for Embodied Vision Navigation** | Zhu et al., arXiv:2108.04097 | 具身导航 |
| **Core Challenges of Social Robot Navigation** | Mavrogiannis et al., 2023 | 机器人导航 |
| **Hierarchical Reinforcement Learning: A Survey** | Pateria et al., ACM CSur 2021 | HRL |
| **Reward Model Evaluation** | Lambert et al., 2024 | Reward Model |
| **Curriculum Learning Survey** | Soviany et al., 2022 | CL |

---

## 7. 写作引用格式 (BibTeX 模板)

```bibtex
@inproceedings{curriculum2009,
  title={Curriculum learning},
  author={Bengio, Yoshua and Louradour, J{\'e}r{\'o}me and Collobert, Ronan and Weston, Jason},
  booktitle={ICML},
  year={2009}
}

@article{options1999,
  title={Between MDPs and semi-MDPs: A framework for temporal abstraction in reinforcement learning},
  author={Sutton, Richard S and Precup, Doina and Singh, Satinder},
  journal={Artificial Intelligence},
  year={1999}
}

@misc{activevln2025,
  title={ActiveVLN: Towards Active Exploration via Multi-Turn RL in Vision-and-Language Navigation},
  author={Zhang, Zekai and Zhu, Weiye and Pan, Hewei and others},
  year={2025},
  archivePrefix={arXiv},
  eprint={2509.12618}
}
```

---

## 8. 论文各章节推荐引用数量

硕士论文 (3 章主要方法 + 综述)：
- Chapter 1 绪论: ~30 篇
- Chapter 2 相关工作: ~80 篇
- Chapter 3-5 方法: ~40 篇
- Chapter 6 结论: ~10 篇
- **总: ~120-150 篇**

**Top 会议** (NeurIPS/ICML/ICLR): 通常要求 60-100 篇
**博士论文**: 通常 200+ 篇

---

## 9. 每周文献阅读计划 (开题 2 周内)

```
Day 1-2: 5 篇基石
  - ActiveVLN, VLN-R1, GRPO, R1, CL-2009

Day 3-4: 5 篇关键理论
  - Options-1999, UVFA-2015, Feudal-2017, Ng-1999, CoT-2022

Day 5-6: 5 篇关键应用
  - RAGEN, LAW-2021, Reflexion-2023, SAC-2018, NaVid

Day 7-8: 5 篇综述
  - 4 篇综述 + 1 篇 DAgger

Day 9-10: 5 篇方向特定
  - 各方向最相关 1-2 篇

Day 11-14: 剩余 ~20 篇快速浏览
```

总计: 4 周内完成 60-80 篇核心文献阅读 + 笔记。

---

## 10. 关键文献 arXiv IDs 一览

方便复制查询：

| 文献 | arXiv ID |
|---|---|
| ActiveVLN | 2509.12618 |
| VLN-R1 | 2506.17221 |
| GRPO (DeepSeekMath) | 2402.03300 |
| DeepSeek-R1 | 2501.12948 |
| DAPO | 2503.14476 |
| RAGEN | 2504.20073 |
| DeepEyes | 2505.14362 |
| OctoNav | 2506.09839 |
| StreamVLN | 2507.05240 |
| NaVid | RSS 2024 (查官网) |
| PPO | 1707.06347 |
| Vision-R1 | 2503.06749 |
| MM-Eureka | 2503.07365 |
| Seg-Zero | 2503.06520 |
| Reflexion | 2303.11366 |
| ReAct | 2210.03629 |
| Text2Reward | 2309.11436 |
| RT-2 | 2307.15818 |
| Octo | 2405.12213 |

---

## 11. 论文使用提示

当你在某方向上写作时，可按以下顺序组织相关工作：

1. **历史脉络**: 从传统方法到 ML 再到 RL
2. **现有 SOTA**: 重点对比 AVLN, R1, NaVid, StreamVLN
3. **本方向 SOTA**: 列出与方向相关的核心论文
4. **本方向未解决问题**: 留下 gap，引出本文
5. **本方向与本文的具体差异**: 表格对比

---

## 12. 一句话总结

> **本目录 4 份核心文档 (00 总览 + 01 对比 + A/B/C 三方向) 构成了硕士论文选题的完整知识图谱：约 50 篇核心文献（已分类） + 3 个可独立成文的创新方向 + 1 个推荐组合方案 (A+B)，开题 2 周内完成 50+ 文献精读即可进入实现阶段。**
