# ActiveVLN + SRGPO 阶段 1+2 整合（汇报版）

> 截至 2026-08-03，已完成 **SRGPO 框架接入** + **SeeNav-Agent 风格 env-verifiable 步骤奖励**。
> 审计器（GroundingDINO+CLIP / Self-Verifier）尚未接入，相关代码位置留好了接口。

---

## 0. 一句话总结

在 ActiveVLN（ICRA 2026）的稀疏 GRPO 上**叠加一层 SRGPO 风格的过程奖励**：env 端每个动作执行后给出一个 `step_reward ∈ {0,1,2}`（距离减少 1cm / 首次进入 oracle 区域），rollout 端聚合成 `raw_step_rewards`，trainer 端通过 `episode_adv + ω · step_adv` 注入 advantage。可在 `srgpo_step_advantage_w=0` 时退化为纯 GRPO，便于消融。

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
│           │  env.step(action)        │                                  │
│           │                           │  收集 obs/reward/done           │
│           ▼                           ▼                                  │
│   ┌────────────────┐        ┌────────────────────┐                       │
│   │ VLNCEEnv       │───────▶│ DataProto          │                       │
│   │  step():       │ info   │  ├ token_level_rw  │ 仅最后一个 token      │
│   │   _execute     │        │  ├ raw_step_rewards│ ★ 阶段 2 新增 (object)│
│   │   _pending_S_t?│        │  ├ uid / traj_uid  │ ★ SRGPO 新增         │
│   │   _compute...  │        │  └ response_mask   │                       │
│   └────────────────┘        └─────────┬──────────┘                       │
│                                       │                                  │
│                                       ▼                                  │
│                         ┌──────────────────────────┐                     │
│                         │  trainer.compute_advantage│                    │
│                         │  estimator == SRGPO      │                    │
│                         │  ├ compute_step_rewards() │ ★ sum→标量 (bs,)   │
│                         │  ├ episode_norm_reward() │  GRPO outcome adv  │
│                         │  ├ build_step_group()    │  跨 batch 随机分块  │
│                         │  └ step_norm_reward()    │  z-score 归一化      │
│                         │  adv = ep + ω·step        │                    │
│                         └──────────┬───────────────┘                     │
│                                    ▼                                     │
│                  actor/critic update (PPO-clip + KL)                     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

蓝色标 ★ 的部分是阶段 1+2 新增或改造；其余沿用 ActiveVLN 原版。

---

## 2. 端到端数据流（按时间序）

| # | 位置 | 数据 | 备注 |
|---|---|---|---|
| ① | `VLNCEEnv.__init__` | `_prev_distance_to_goal=None`, `_prev_orcale_success=False`, `_step_reward_list=[]` | 阶段 2 新增 |
| ② | `VLNCEEnv.step(action)` 每执行一个 `_execute_action` | 查 `_get_metrics()` 得 `distance_to_goal / orcale_success` | —— |
| ③ | 同上 | `step_r = (d2g < prev_d2g − 0.01) ? 1 : 0`<br>`step_r += (orcale && !prev_orcale) ? 1 : 0`<br>`_step_reward_list.append(step_r)` | **SeeNav-Agent EBNavEnv 规则移植**，默认开启（`enable_process_reward=True`） |
| ④ | 同上，写入 `info` | `"step_reward"` / `"step_reward_list"` / `"last_distance_to_goal"` / `"last_orcale_success"` | 阶段 2 新增字段 |
| ⑤ | `parallel_env_vlnce.py` 每 turn | `step_reward_lists[idx] = list(info["step_reward_list"])` | 阶段 2 rollout 累积器 |
| ⑥ | rollout 末尾构造 DataProto | `raw_step_rewards = np.empty(bsz, dtype=object)`<br>每项 = `np.asarray(list, dtype=float32)` 或空数组 | 阶段 2 新增字段 |
| ⑦ | `ray_trainer.fit()` 拼装 batch | `batch.non_tensor_batch["traj_uid"]` 写入<br>SRGPO 缺 `raw_step_rewards` 时填零向量 fallback | 阶段 1 新增（防崩） |
| ⑧ | `ray_trainer.compute_advantage` (SRGPO 分支) | `step_rewards = compute_step_rewards(batch)` → `(bs,)` 标量 | sum 归约 |
| ⑨ | `compute_srgpo_outcome_advantage` | `episode_adv` + `ω · step_adv` | 阶段 1 核心 |

---

## 3. 关键改动文件清单

### 3.1 新增文件

| 文件 | 来源 | 作用 |
|---|---|---|
| `verl/workers/agent/srgpo_core.py` | 从 SeeNav-Agent 移植 + 中文 docstring | `compute_step_rewards` / `compute_srgpo_outcome_advantage` / `build_step_group` / `episode_norm_reward` / `step_norm_reward` |

### 3.2 修改文件

| 文件 | 关键改动 |
|---|---|
| `verl/trainer/ppo/core_algos.py` | `AdvantageEstimator.SRGPO = "srgpo"`；新增 `_srgpo_outcome_advantage` 包装（带零-step-rewards fallback，避免硬依赖 srgpo_core）；`@register_adv_est(SRGPO) compute_srgpo_outcome_advantage` |
| `verl/trainer/ppo/ray_trainer.py` | `use_critic=False` 列表加 SRGPO；`compute_advantage()` 新增 SRGPO 分支；`fit()` 写 `traj_uid`；SRGPO 缺失 `raw_step_rewards` 时填零向量 |
| `examples/vlnce/train_vlnce_4gpus.yaml` | `algorithm.adv_estimator: srgpo`；新增 `srgpo_step_group_size=16 / step_advantage_w=0.5 / mode=mean_std_norm / intask=false / intraj=false` |
| `vlnce_server/env.py` | `VLNCEEnv.__init__/reset/step` 新增过程奖励状态；`step()` 每个 `_execute_action` 后按 SeeNav-Agent 公式算 `step_reward`；`info` 加 4 个字段 |
| `vlnce_server/env_config.py` | `VLNCEEnvConfig.enable_process_reward: bool = True`（默认开） |
| `verl/workers/agent/parallel_env_vlnce.py` | rollout 端新增 `step_reward_lists` 累积；最终 DataProto 写 `raw_step_rewards` (object array of float32 arrays) |

---

## 4. 阶段 1：SRGPO 框架接入

**目标**：在 VeRL 的 GRPO 优势计算路径上**插入一个等价分支 SRGPO**，不引入任何过程奖励（`raw_step_rewards` 临时为空 → 自动回退零向量 → `step_adv=0`）。

**主要步骤**：
1. 把 SeeNav-Agent 的 `core_srgpo.py` 整段复制为 `verl/workers/agent/srgpo_core.py`，补中文 docstring。
2. 在 `core_algos.py` 注册 `AdvantageEstimator.SRGPO` + wrapper（保留 lazy import，确保不启用 SRGPO 时不强制加载 srgpo_core）。
3. `ray_trainer.py` 在 `compute_advantage()` 末尾加 SRGPO 分支；`fit()` 写入 `traj_uid`（从 `uid` 复制即可，ActiveVLN 当前是 1 轨迹/指令）。
4. YAML 配置加 `algorithm.srgpo_*` 字段，默认 `step_advantage_w=0.5`。

**验证**：
- ✅ `srgpo_step_advantage_w=0.0` → advantage 与 GRPO **逐 token 一致**（max diff = 0.0）
- ✅ `srgpo_step_advantage_w=1.0` → advantage 明显变化（diff ≈ 1.16）
- ✅ 未注入 `raw_step_rewards` 时不崩溃，自动回退

**结论**：框架接对，等价性得到保证。可放心进入阶段 2 接入实际过程奖励信号。

---

## 5. 阶段 2：SeeNav-Agent 风格 env-verifiable 步骤奖励

**目标**：跳过 Self-Verifier 思路，先把 SeeNav-Agent EBNavEnv 的 `compute_step_reward` 规则直接套到 ActiveVLN 上，验证端到端管道。

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
- 状态在 `__init__/reset/step` 中维护；信息通过 `info["step_reward_list"]` 一次性传出，避免多次 RPC
- 默认开启（`VLNCEEnvConfig.enable_process_reward=True`），便于默认跑 SRGPO + 简单规则的组合

**rollout 端聚合成 `raw_step_rewards`**：
- 每个 trajectory 一个可变长度的 float32 数组
- 用 `dtype=object` 的 numpy 数组承载（避免 padding 浪费）
- 在 `compute_step_rewards` 中 `sum` 归约成 `(bs,)` 标量（每条 trajectory 一个总和）

**trainer 端落入优势**：
- `compute_srgpo_outcome_advantage(episode_adv + ω·step_adv)`：episode 部分按 `uid`（同指令）归一化，step 部分按 `step_group_size`（默认 16）跨 batch 随机分块归一化

**端到端验证**（使用合成 batch `raw_step_rewards=[1,1,1,1,1]` / `[0,0,0,0,0]` 各 4 条轨迹）：

| 配置 | advantages | 说明 |
|---|---|---|
| GRPO baseline | `[+0.707, -0.707, +0.707, -0.707]` | 仅 outcome |
| SRGPO (ω=0) | 同上 | 与 GRPO **完全等价** (max diff = 0.0) |
| SRGPO (ω=0.5) | `[+1.219, -0.780, +0.927, -1.366]` | step 信号生效 |
| SRGPO (ω=1.0) | `[+1.732, -0.853, +1.146, -2.025]` | step 信号主导 |

✅ 全部预期行为正确，可接入训练。

---

## 6. 现在可以怎样跑

| 目标 | 配置 |
|---|---|
| **纯 GRPO baseline** | `algorithm.srgpo_step_advantage_w: 0.0` |
| **SRGPO + SeeNav-Agent 简单规则**（当前默认） | `algorithm.srgpo_step_advantage_w: 0.5`（env 默认开 `enable_process_reward`） |
| **只关 step reward 不关 SRGPO 框架** | `VLNCEEnvConfig.enable_process_reward: False`（`raw_step_rewards` 变空数组 → step_adv=0） |
| **换 stage 3 审计器** | 待阶段 3 接入（参考 `reference/design/activevln-reference-saca-dino-seenav-ag-synthetic-glacier.md`） |

启动命令仍为 `bash examples/vlnce/r2r.sh` / `rxr.sh`，无需改环境变量。

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