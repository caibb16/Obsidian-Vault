# ActiveVLN + SRGPO 阶段 1+2 整合（汇报版）

> 截至 2026-08-03，已完成 **SRGPO 框架接入** + **SeeNav-Agent 风格 env-verifiable 步骤奖励**。
> 审计器（GroundingDINO+CLIP / Self-Verifier）尚未接入，相关代码位置留好了接口。

---

## 0. 一句话总结

在 ActiveVLN（ICRA 2026）的稀疏 GRPO 上**叠加一层 SRGPO 风格的过程奖励**：env 端每个动作执行后给出一个步骤奖励（取值 0/1/2：距离减少 1cm / 首次进入 oracle 区域），rollout 端聚合成 batch 内一条字段，trainer 端通过"episode 优势 + 权重 × step 优势"的方式注入总 advantage。权重取 0 时退化为纯 GRPO，便于消融。

---

## 1. 训练流程全景图

```
                         训练进程 (verl.trainer.main_ppo + vLLM)
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   ┌────────────────┐        ┌────────────────────┐                       │
│   │ env server     │ HTTP   │ rollout worker     │   采样 K 条同指令轨迹 │
│   │ (Flask+Ray)    │◀──────▶│ agent_rollout_loop │   per-prompt × K     │
│   │ 127.0.0.1:5001 │        │ (parallel_env)     │                       │
│   └───────┬────────┘        └─────────┬──────────┘                       │
│           │  发送 action             │                                  │
│           │                           │  收集 obs/reward/done           │
│           ▼                           ▼                                  │
│   ┌────────────────┐        ┌────────────────────┐                       │
│   │ VLN 仿真器     │───────▶│ 训练 batch         │                       │
│   │  + 步骤打分    │ info   │  ├ outcome reward  │ 仅最后 token         │
│   │   ★ 阶段 2    │        │  ├ step reward 列  │ ★ 阶段 2 新增         │
│   │               │        │  ├ 轨迹 / 指令 id  │ ★ SRGPO 新增          │
│   │               │        │  └ response mask   │                       │
│   └────────────────┘        └─────────┬──────────┘                       │
│                                       │                                  │
│                                       ▼                                  │
│                         ┌──────────────────────────┐                     │
│                         │  优势计算 (SRGPO 分支)    │                    │
│                         │  ├ 求和 → 每条轨迹一标量  │ ★ 阶段 1+2        │
│                         │  ├ outcome 优势(同指令组) │                    │
│                         │  ├ step 优势(跨 batch)    │ ★ 阶段 1           │
│                         │  └ 两者相加              │ ★ 阶段 1           │
│                         └──────────┬───────────────┘                     │
│                                    ▼                                     │
│              actor 更新（PPO-clip 形式，无 critic）                       │
│              use_critic=False，SRGPO 走 REINFORCE 路径                   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

标 ★ 的部分是阶段 1+2 新增或改造；其余沿用 ActiveVLN 原版。
[![](https://mermaid.ink/img/pako:eNp1VG1P21YU_itHt6oEmsNCeAm1ukoU1rVaCihE_bB5ioxzTSwc27pxSBlCot1KgEUNY1PZCNvCxLZoa-kqTSOFIKT9lCnXcT7xF3ZsJyxhmfMhvvee5znPec65XiWKmaJEJKpu5pW0zGxI3JWYZAA-2dzCIpOtNCTikw9mPpaIe_yqefaZe1FuVr-AgWXK9CGbyZpB2VAG_5KWZcI7sByLPRyUyCceTYfKe27ehObLl43aOn_z9LK-T41lyFKGLNCoPQdm6rqZsyFvsiXc4m__dJ7vdsPfn3mEEv5F3V5g7965p8vZJcwZl1fgrxMQx8Lh4XbqDi4eQ1gvuw-VF6lhJ9sHSd00LRiwZCbrOtWTmGbQj2oVCk7lBD4E57tDvlN0ioXG2ZF7XnUv3vYpETVCKAQSuZ9IzPl4Xvqytf4EZMXWTEMicDsUuoOS_seb02LgzaPYDDTOLpoHP_Bvq5f1TV772Xn1U-vXI2frK765cVnf-ntjF4J2wIJsK-lusvkHD7HkHg60qJvgmkV3JxNT96_62yb8b3Xx2LXinK1f3MMi3642zg-wNq80zH1NSoDRDNUEXv6-Ua_40AG-8xtkbWoBo3mZpYCflvjm3mCbxlfUL7f7ZJ_vbHYa0Bvbb9i2AkMb9W_49oV7fNg83kM_5-MfzM0CGuF8_RrN7AZOTntj1h0PA93hwVg4b57y3SJ4XXBel3A2AkU43E6l0CqU_CCcK8XMUAjI4Gp8mmef841n_HzXuwvFF36sb0U70D2pBj2A1n7JOTjFxAjxwxq1I3f9WbNc49uVPh3yrfBNwTL6W8LL5cASHEmTgVP-w3nxe48BU4nZOFrQfe7nnpubDSm6ZgE__5HXSwI4exVQmGZrin-ey9JksHzvnqxnaR99qCpQ5-XoHFAj1R2n4JXOTlMVDJqft1d0Cqqm6-INVVXH6LiQtZm5RMUbqVvRaLizDOW1lJ0WI9bjHhbvPgrxmIBTKPjWCChA8JNfsROBLDItRUSb5ahAMpThpwyXZNUjkoidphksRcTXFFXlnG5LRDLWEGbJxkemmekgmZlbTBNR9UoXSM5KyTad1mT8gmaudhnWStmUmTNsIo6Mhn0SIq6Sx0QcDo8NjYxHRiOR6MRwdHQkOiKQFdyOhocmhiOj0WhkYhx_t9YE8qmfFvejY2v_AKipSqU?type=png)](https://mermaid-live.nodejs.cn/edit#pako:eNp1VG1P21YU_itHt6oEmpPlhZBgdZUorGu1FFCI-mHLFBnnhlg4tnXjkDKERLuVAIsaxqayEbaFiW3R1tJVmkYKQUj7KVOuk3ziL-zYTmhCM3-xr-_zPOec55x7V4mspygRSVrVC3JGYibE7yRYQgN8cvmFRSYZGYjHJu_PfJog7eOXrbMv2heVVu0rGFmmTPWaTFI0yrxZfCUNQ4f3YDkafTCaIJ_ZMj0p-7l5E1ovXjTr6_z1k8vGPtWWIUcZqkCz_gyYrqp63oSCzpbwF3_zt_Vst5_-4cxDTOEt69YCe__2XVXKLWHMmLQC_5yAGPL5_N3QPV4sirRBdYcqLVLNTHY3kqquGzBiSExSVaomMcyog-oUi1b1BD4G64dDvlOySsXm2VH7vNa-eDOkRMwRPB5IkHvx-JzD5-WvO-uPQZJNRdcSBG55PLcxpf_x5rTkevMwOgPNs4vWwU_8-9plY5PXf7Ve_tL5_cja-oZvblw2tv7d2AW3HbAgmXKmX2z-_gMseUADLeoXuGbRncn41L2r_nYF360uFr1WnLX1W_uwxLdrzfMDrM0uDWNfS8XlKFpaB175sdmoOtQRvvMH5ExqAKMFiaWAn5b55t5oV8bJaFjs9uN9vrPZa8AgdtiwbbmGNhvf8e2L9vFh63gP_ZyPfTQ3C2iE9e0rNLOfODltj1k_Hkb64e5YWK-f8N0S2F2wXpVxNtyMcLitarFTLDsgnCtZz1JwxeBqfFpnX_KNp_x81z4LpecO1rGiC2yf1NweQGe_bB2cYmCkOLBm_ai9_rRVqfPt6pAOOVY4pmAZwy3hlYprCY6kzsCq_GU9_3PAgKn4bAwt6N93Ys_NzXpkVTGAn__MG2UBrL0qyEwxFdnZz-do0l1-cFdSc3RIfpiVm50do7dBtVQ_TsYjnZumadBoYd5cUSmkFVUVb6TT6RAdF3Im05eoeCM1EQ77ektPQUmZGTFgPBpQsc-jEIsKOIWCY42ACQhO8Ct1IpBFpqSIaLI8FUiWMrzKcElWbaEEMTM0i6WI-JmiaSmvmgmS0NaQZkjaJ7qe7TGZnl_MEDFtly6QvJGSTDqtSHiDZq_-MqyVsik9r5lEDPiDjggRV8kjIvp9QW9wPDAWioyHQ4FIKOAXyIqNCnsj_sBYZGwi6B-PBCfG1gTyuRPX542EQ2v_AfHyStM)

---

## 2. 端到端数据流（按时间序）

| # | 发生位置 | 数据走向 | 备注 |
|---|---|---|---|
| ① | env server 内部初始化 | 新增 3 个状态：上一步距离、上一步 oracle 标志、当前 step reward 序列 | 阶段 2 新增 |
| ② | env 每执行一个动作 | 取仿真器最新指标：当前距离 / oracle 状态 | —— |
| ③ | env 内部分支 | 套用 SeeNav-Agent 简单规则，把当前 step reward 推进序列末尾 | 默认开启 |
| ④ | env → rollout | 整条 step reward 序列通过 info 一次性回传给 rollout | 阶段 2 新增字段 |
| ⑤ | rollout 每轮 | 把刚拿到的序列同步到 rollout 自己的累积器 | 阶段 2 rollout 累积 |
| ⑥ | rollout 收尾 | 把所有轨迹的序列打包成 batch 内一条字段（每条轨迹一个变长数组） | 阶段 2 新增字段 |
| ⑦ | trainer 主循环 | 写入"轨迹级 id"；若 SRGPO 分支发现缺 step reward 字段则填零向量 | 阶段 1 新增（防崩） |
| ⑧ | trainer 优势计算入口 | 把变长 step reward 序列求和为每条轨迹一个标量 | sum 归约 |
| ⑨ | 优势计算 | episode_adv + ω × step_adv，最终下发到 actor | 阶段 1 核心 |

---

## 3. 关键改动文件清单

### 3.1 新增文件

| 文件 | 来源 | 作用 |
|---|---|---|
| SRGPO 核心算法模块 | 从 SeeNav-Agent 移植 + 中文 docstring | 五个子功能：求和归约、联合优势、随机分块、episode 归一化、step 归一化 |

### 3.2 修改文件

| 文件 | 改动要点 |
|---|---|
| VeRL 优势计算模块 | 优势算法枚举新增 `srgpo`；新增包装函数（带零-step-rewards fallback，避免硬依赖新模块）；注册新算法入口 |
| VeRL 训练主循环 | critic-free 列表加 SRGPO；优势计算函数末尾加 SRGPO 分支；主循环写入"轨迹级 id"；缺 step reward 时填零向量 |
| 训练配置 YAML | 优势算法切到 srgpo；新增 5 个超参字段（分块大小 / 权重 / 归一化模式 / 两个约束开关） |
| VLN 环境主类 | env 初始化 / reset / step 三处新增过程奖励状态；每步执行后按 SeeNav-Agent 公式算 step reward；info 新增 4 个字段 |
| VLN 环境配置类 | 新增一个开关字段（默认开） |
| rollout 并行环境 | 端新增 step reward 累积器；收尾时把每条轨迹的序列写进 batch |

## 4. 阶段 1：SRGPO 框架接入

**目标**：在 VeRL 的 GRPO 优势计算路径上**插入一个等价分支 SRGPO**，不引入任何过程奖励（步骤奖励字段临时为空 → 自动回退零向量 → step 优势 = 0）。

> 注意：虽然 update 用了 PPO-clip surrogate loss 写法，但 **没有 critic / value network**（`use_critic=False`，与 GRPO 一致）。PPO-clip 在这里只是 clip-ratio 的实现，**不是 PPO 算法**——避免误读为带 GAE 的 PPO。

**主要步骤**：
1. 把 SeeNav-Agent 的核心算法移植为新模块，补中文 docstring。
2. 在 VeRL 的优势计算枚举里注册 `SRGPO`，并加上一个包装函数（保留 lazy import，确保不启用 SRGPO 时不强制加载新模块）。
3. trainer 的 advantage 计算函数末尾加 SRGPO 分支；训练主循环里写入"轨迹级 uid"（当前 ActiveVLN 是一条指令对应一条轨迹，所以轨迹级 uid 与指令级 uid 相同）。
4. YAML 配置加 `srgpo_*` 字段，默认 `step_advantage_w=0.5`。

**验证**：
- ✅ step 优势权重 = 0 → advantage 与 GRPO **逐 token 一致**（max diff = 0.0）
- ✅ step 优势权重 = 1 → advantage 明显变化（diff ≈ 1.16）
- ✅ 未注入步骤奖励字段时不崩溃，自动回退

**结论**：框架接对，等价性得到保证。可放心进入阶段 2 接入实际过程奖励信号。

---

## 5. 阶段 2：SeeNav-Agent 风格 env-verifiable 步骤奖励

**目标**：跳过 Self-Verifier 思路，先把 SeeNav-Agent EBNavEnv 的步骤奖励规则直接套到 ActiveVLN 上，验证端到端管道。

**奖励规则**（每个执行的非 STOP 动作）：

$$
\text{step}_r =
\underbrace{\mathbb{I}(d_{t-1} - d_t > 0.01\,\text{m})}_{\text{距离减少 }>1\text{cm}} +
\underbrace{\mathbb{I}(\text{oracle}_t \land \neg \text{oracle}_{t-1})}_{\text{首次进入 oracle 区域}}
\in \{0, 1, 2\}
$$

**实现要点**：
- `d_t = distance_to_goal`（Habitat 仿真器提供，特权信息，符合 ActiveVLN 的 soft success reward 设计哲学）
- `oracle_t = distance_to_goal <= 3.0`（VLN-CE 默认阈值）
- 状态在 env 的初始化 / reset / step 中维护；信息通过 info 一次性传出，避免多次 RPC
- 默认开启，便于默认跑 SRGPO + 简单规则的组合

**rollout 端聚合成 batch 内字段**：
- 每个 trajectory 一个可变长度的 float32 数组
- 用 object 类型的 numpy 数组承载（避免 padding 浪费）
- 在优势计算前 sum 归约成每条轨迹一个标量

**trainer 端落入优势**：
- `episode_adv + ω × step_adv`：episode 部分按"同指令"归一化，step 部分按"跨 batch 随机分块（默认 16）"归一化

**端到端验证**（使用合成 batch：两个指令 × 4 条轨迹，每条轨迹 5 步，步骤奖励全 1 或全 0）：

| 配置 | advantages | 说明 |
|---|---|---|
| GRPO baseline | `[+0.707, -0.707, +0.707, -0.707]` | 仅 outcome |
| SRGPO (ω=0) | 同上 | 与 GRPO **完全等价** (max diff = 0.0) |
| SRGPO (ω=0.5) | `[+1.219, -0.780, +0.927, -1.366]` | step 信号生效 |
| SRGPO (ω=1.0) | `[+1.732, -0.853, +1.146, -2.025]` | step 信号主导 |

✅ 全部预期行为正确，可接入训练。

---

## 6. 现在可以怎样跑

启动命令仍为 `bash examples/vlnce/r2r.sh` / `rxr.sh`，无需改环境变量；通过 YAML 配置切换训练模式：

| 目标 | 关键配置 |
|---|---|
| **纯 GRPO baseline** | step 优势权重设为 0 |
| **SRGPO + SeeNav-Agent 简单规则**（当前默认） | step 优势权重保持 0.5，env 默认开启过程奖励 |
| **只关 step reward 不关 SRGPO 框架** | 关掉 env 配置里的"启用过程奖励"开关（步骤奖励字段变空 → step 优势 = 0） |
| **换阶段 3 审计器** | 待阶段 3 接入（参考 `.claude/plans/activevln-reference-saca-dino-seenav-ag-synthetic-glacier.md`） |

---

## 7. 与原始 ActiveVLN 的差异（一句话）

> **ActiveVLN：稀疏 outcome GRPO**；**当前实现：outcome GRPO + 跨 batch 随机分组的 step 优势**，且 step 优势**信号源可换**（当前是 SeeNav-Agent 简单规则，阶段 3/4 将换成 GroundingDINO+CLIP / Self-Verifier）。

未引入任何额外感知模型；env 端的 `distance_to_goal` / `oracle_success` 来自 Habitat 仿真器（ActiveVLN 已使用），不增加 rollout 耗时。

---

## 8. 待办与下一步

- **阶段 3**（Self-Verifier 审计器）— 用 Qwen2.5-VL-3B 已 forward 的 hidden state 算 instruction ↔ last-frames 的 attention similarity，作为基线对照。
- **阶段 4**（GroundingDINO + CLIP，主方案）— SACA 简化级联，去 SAM3。
- **阶段 5**（消融 + 主实验）— 7 个实验 + 诊断实验，脚本 `scripts/ablation_runner.sh`。

完整方案见 `.claude/plans/activevln-reference-saca-dino-seenav-ag-synthetic-glacier.md`，进度跟踪在仓库根 `CLAUDE.md` 的"研究进展"章节。