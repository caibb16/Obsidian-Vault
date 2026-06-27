
## 一、 随机信号与噪声基础 (Random Signals & Noise)

**1. 常见概率分布与随机变量**

- **瑞利分布 (Rayleigh):** 若 $X_1, X_2 \sim \mathcal{N}(0, \sigma^2)$ 且相互独立，则其包络 $R = \sqrt{X_1^2 + X_2^2}$ 服从瑞利分布。
    
- **高斯分布 (Gaussian):** 尾部概率常使用 $Q$ 函数表示：$Q(x) = \int_x^\infty \frac{1}{\sqrt{2\pi}} e^{-u^2/2} du$。
    
- **指数分布 (Exponential):** $f_N(n) = \lambda e^{-\lambda n} \, (n \ge 0)$。注意其单边特性，在接收机判决时（如 $Y = S+N$），接收值必然大于发送值 $Y \ge S$。
    

**2. 随机过程与广义平稳 (WSS)**

- **WSS 三大条件:** 1) 均值为常数 $E[X(t)] = m_X$；
    
    2) 自相关函数仅与时间间隔 $\tau$ 有关 $R_X(t_1, t_2) = R_X(\tau)$；
    
    3) 功率有限（方差有限）。
    
- **高斯白噪声 (AWGN):** * 单边功率谱密度为 $N_0$，双边功率谱密度为 $S_n(f) = \frac{N_0}{2}$。
    
    - 自相关函数为：$R_n(\tau) = \frac{N_0}{2} \delta(\tau)$。
        

**3. 带通与低通信号的能量关系**

- 带通信号 $x(t)$ 的能量是其低通等效信号 $x_l(t)$ 能量的**一半**: $\mathcal{E}_x = \frac{1}{2} \mathcal{E}_{x_l}$。
    

## 二、 信号空间与调制 (Signal Space & Modulation)

**1. 信号的正交性**

- 两个正弦信号 $u_i(t) = \cos(2\pi f_i t)$ 在 $0 \le t \le T$ 内正交的最小频率间隔 $\Delta f_{\min}$：
    
    - **相干检测 (Coherent):** $\Delta f_{\min} = \frac{1}{2T}$。
        
    - **非相干检测 (Non-coherent):** $\Delta f_{\min} = \frac{1}{T}$。
        

**2. 典型数字调制方案的频谱与效率**

- **M-PSK / M-QAM:**
    
    - 主瓣宽度 (Mainlobe width): $B_T = \frac{2}{T}$。
        
    - 频谱效率 (Spectral efficiency): $\eta = \frac{R_b}{B_T} = 0.5 \log_2 M$ (bps/Hz)。
    - 功率谱密度 (Power Spectral Density): $S(f) = \frac{|G(f)|^2}{T}$。
        
- **On-Off Signaling vs Antipodal (双极性):**
    
    - 在 AWGN 信道下达到相同的误码率，On-Off 信号（如 0 和 $A$）所需的能量是 Antipodal 信号（如 $-A/2$ 和 $A/2$）的 **2倍**。
        

**3. 载波与符号同步 (Synchronization)**

- **相干与非相干区别:** 相干检测需要接收端有与发送端同频同相的本地载波，设备复杂但性能好；非相干检测无需本地同步载波（如包络检波），结构简单但抗噪性能稍差。
    
- **ML 相位估计 (Maximum Likelihood):** $\hat{\phi}_{ML} = -\tan^{-1} \left( \frac{\text{Im}[\sum I_n^* y_n]}{\text{Re}[\sum I_n^* y_n]} \right)$。这通常是一个无偏估计 (unbiased estimate)。
    

## 三、 最佳接收机 (Optimum Receivers for AWGN)

**1. 匹配滤波器 (Matched Filter)**

- **时域冲激响应:** $h(t) = k \cdot s(T - t)$ (通常取 $k=1$)。
    
- **频域传输函数:** $H(f) = k \cdot S^*(f) e^{-j2\pi f T}$。
    
- 在抽样时刻 $t=T$ 达到最大输出信噪比：$\text{SNR}_{\max} = \frac{2E}{N_0}$。
    

**2. 最佳检测准则**

- **MAP准则 (最大后验概率):** $\hat{s} = \arg\max_{s_m} P(s_m | r)$。使发生错误的概率最小。
    
    - $P(s_m | r) = \frac{p(r | s_m) P(s_m)}{p(r)}$  
        
- **ML准则 (最大似然):** 当所有符号等概率发送时 ($P(s_m) = 1/M$)，MAP 退化为 ML 准则：$\hat{s} = \arg\max_{s_m} p(r | s_m)$。
    
- 高斯白噪声下的 ML 判决等价于**最小几何距离准则**: 选择使欧式距离 $|r - s_m|^2$ 最小的信号。
    

**3. 错误概率计算 (Error Probability)**

- **二进制 Antipodal (如 BPSK):** $P_e = Q\left(\sqrt{\frac{2E_b}{N_0}}\right)$。
    
- **二进制 正交信号 (Orthogonal):** $P_e = Q\left(\sqrt{\frac{E_b}{N_0}}\right)$。
    
- **拉普拉斯噪声 (Laplacian) 下的判决:** $p(n) = \frac{1}{\sqrt{2}\sigma} e^{-\sqrt{2}|n|/\sigma}$，输入 $r = \pm A + n$ 时，最优判决门限仍为 0，错误概率为 $P_e = \frac{1}{2} e^{-\sqrt{2}A/\sigma}$。
    

**4. 联合边界 (Union Bound)**

- 对 M 元信号体系：$P_e \le \sum_{m=1}^M \sum_{m' \neq m} P(s_m) Q\left( \frac{d_{mm'}}{\sqrt{2N_0}} \right)$。
    
- 重点关注最小距离 $d_{\min}$。
    

## 四、 信息论基础 (Information Theory)

**1. 信源熵 (Entropy)**

- 离散无记忆信源 (DMS): $H(X) = -\sum_{i} P(x_i) \log_2 P(x_i)$ (单位: bits/symbol)。
  - example：高斯随机变量的熵为 $H(X) = \frac{1}{2} \log_2(2\pi e \sigma^2)$。
    
- 极值性: $H(X) \le \log_2 n$ (等概率时取等号)。
    
- 若 $Y = g(X)$ 且 $g$ 为确定性函数，则 $H(Y) \le H(X)$ (只有当 $g$ 是一对一映射时取等号)。

- 条件熵: $H(X|Y) = H(X,Y) - H(Y)= H(X) - H(X|Y)$，条件熵 $H(X|Y)$ 表示在已知 $Y$ 的情况下对 $X$ 的不确定性。
  - $$H(X|Y) = -\sum_{i,j} P(x_i,y_j) \log_2 P(x_i|y_j)$$
    

**2. 哈夫曼编码 (Huffman Coding)**

- **步骤:** 
	1) 将概率从大到小排序；
    
    2) 每次合并最小的两个概率；
    
    3) 合并树的左支赋 0，右支赋 1 (或相反)；
    
    4) 从根节点到叶子节点读取码字。
    
- **平均码长:** $\bar{L} = \sum p_i l_i$。
    
- **编码效率:** $\eta = \frac{H(X)}{\bar{L}}$。
    

**3. 互信息与信道容量 (Mutual Info & Capacity)**

- **互信息:** $I(X;Y) = H(Y) - H(Y|X) = H(X) - H(X|Y)$。
    
- **信道容量:** $C = \max_{p(x)} I(X;Y)$。
    
- **二进制对称信道 (BSC, 错误率p):** 容量 $C = 1 - H_b(p) = 1 + p\log_2 p + (1-p)\log_2(1-p)$。
    
- **AWGN 连续信道 (Shannon 公式):** $C = B \log_2\left(1 + \frac{S}{N}\right)= B \log_2\left(1 + \frac{P}{N_0W}\right)$。
    
- 对于特定的不对称转移矩阵，利用输出简并对称性假设 $P(x)$ ，使得 $H(Y)$ 最大，计算 $C$。
    

**4. 率失真函数 (Rate Distortion)**

- 给定最大允许平均失真 $D$，所需的最小编码速率 $R(D)$。
    
- Bernoulli信源: $R(D) = H(p) - H(D)$ (当 $0 \le D \le \min(p, 1-p)$ 时)。
    
- 结论：当信源熵大于信道容量 $H(X) > C$ 时，无失真传输是不可能的。为了寻找最小失真，令 $R(D) = C$ 求解 $D$。
    

## 五、 信道编码 (Channel Coding)

**1. 线性分组码 (Linear Block Codes, n, k)**

- **生成矩阵 (Generator Matrix** $G$**):** 大小为 $k \times n$。
    
    - 系统码形式 (Systematic): $G = [I_k | P]$ (或 $[P | I_k]$)。
        
    - 编码过程: 码字 $c = u \cdot G$ (所有加法为模2加 / XOR)。
        
- **校验矩阵 (Parity-check Matrix** $H$**):** 大小为 $(n-k) \times n$。
    
    - 对应系统码: $H = [P^T | I_{n-k}]$。
        
    - 正交性质: $G \cdot H^T = 0$。
        
- **伴随式解码 (Syndrome Decoding):**
    
    - 接收向量 $r = c + e$ ($e$ 为错误图样)。
        
    - 伴随式 $s = r \cdot H^T = (c+e)H^T = eH^T$。
        
    - 查表法: 根据 $s$ 找到对应的最可能错误图样 $e$，估计发送码字 $\hat{c} = r + e$。
        
- **未检出错误概率 (Undetected Error Prob):** $P_u(E) = \sum_{i=1}^n A_i p^i (1-p)^{n-i}$，其中 $A_i$ 为重量为 $i$ 的码字数量 (Weight Distribution)。
    

**2. 汉明距离与纠错能力**

- **最小距离** $d_{\min}$**:** 线性码中，等于非零码字的最小重量，也等于 $H$ 矩阵中线性相关的最小列数。
- **重量分布多项式**: $A(x) = \sum_{i=0}^n A_i x^i = 1+\sum_{i=d_{\min}}^n A_i x^i$，其中 $A_i$ 为重量为 $i$ 的码字数量。
    
- **纠错与检错:**
    
    - 检错能力: $e \le d_{\min} - 1$  
        
    - 纠错能力: $t = \lfloor \frac{d_{\min} - 1}{2} \rfloor$  
        
- **Singleton 界:** $d_{\min} \le n - k + 1$。达到该界的码称为 MDS 码。
    

**3. 循环码 (Cyclic Codes)**

- 码字多项式 $c(X) = c_0 + c_1 X + \dots + c_{n-1} X^{n-1}$。
    
- 生成多项式 $g(X)$ 是 $X^n + 1$ 的一个因式，其阶数为 $n-k$。
    
- **系统编码方法:**
    
    1. 信息多项式 $u(X)$ 乘以 $X^{n-k}$。
        
    2. 除以 $g(X)$，得到余数 $r(X)$。
        
    3. 码字多项式 $c(X) = X^{n-k}u(X) + r(X)$。
        

**4. 卷积码 (Convolutional Codes)**

- **状态图与网格图 (Trellis):** 记忆深度为 $K$，状态数为 $2^{K-1}$。
    
- **Viterbi 解码算法:** 基于最大似然序列估计，通过网格图逐步计算路径度量 (Path Metric, 如汉明距离)，并在每个状态节点**保留累积距离最小（最可能）的幸存路径** (Surviving Path)，丢弃其他路径。


# 《数字通信》期末半开卷考试终极冲刺材料（第9-16章）

---

## 📡 第一部分：频域与带限信道传输（第9、10、11章）

### 一、 奈奎斯特第一准则（无 ISI 方案）
1. **时域条件**：抽样时刻无码间串扰（ISI）：
   $$x(nT_s) = \begin{cases} 1, & n=0 \\ 0, & n \neq 0 \end{cases}$$
2. **频域条件**（等效平移叠加为常数）：
   $$\sum_{m=-\infty}^{\infty} X\left(f - \frac{m}{T_s}\right) = T_s$$
3. **升余弦滚降滤波器 (Raised Cosine Filter)**：
   * **绝对带宽**：$B = \frac{1+\alpha}{2T_s} = \frac{R_s(1+\alpha)}{2}$（其中 $\alpha$ 为滚降系数，$0 \le \alpha \le 1$）。
   - $\alpha=0$ 时为理想矩形低通（奈奎斯特最小带宽 $B_0 = \frac{1}{2T_s}$）；$\alpha=1$ 时带宽加倍。
   * **频带利用率**：$\eta = \frac{R_s}{B} = \frac{2}{1+\alpha} \text{ (Baud/Hz)}$。

### 二、 部分响应系统 (Partial Response Signaling)
* **核心思想**：人为、受控地在相邻码元间引入 ISI，使绝对带宽严格控制在奈奎斯特带宽 $B = \frac{1}{2T_s}$，以此达到理论极限的频谱利用率（$2 \text{ Baud/Hz}$）。
* **双二进制信号 (Duobinary / Class I)**：
   * **预编码 (Precoding)**：为防止接收端解调时出现**差错传播 (Error Propagation)**，发送端在映射前先进行模2加运算：
     $$b_k = a_k \oplus b_{k-1} \pmod 2 \quad (a_k \in \{0,1\})$$
   * **电平映射**：$c_k = 2b_k - 1 \in \{-1, +1\}$。
   * **接收端采样值**：$I_k = c_k + c_{k-1} \in \{-2, 0, +2\}$。
   * **判决规则**：若 $I_k = \pm 2$，则判 $\hat{a}_k = 0$；若 $I_k = 0$，则判 $\hat{a}_k = 1$。

### 三、 自适应均衡器准则（最大似然、最小均方误差）
1. **峰值畸变准则与迫零 (ZF) 均衡器**：
   * **原理**：完全消除 ISI，满足 $C(f) = \frac{1}{X(f)}$。
   * **缺点**：会产生**噪声放大效应 (Noise Enhancement)**，在信道传输函数存在深谱零点时性能极差。
2. **最小均方误差 (MMSE) 均衡器准则**：
   * **目标**：在最小化 ISI 的同时抑制加性噪声。代价函数为 $J = E[|e_k|^2] = E[|I_k - \hat{I}_k|^2]$。
   * **正交性原理**：误差矢量与输入矢量正交 $E[e_k \mathbf{v}_{k-m}^*] = 0$，由此推导出 **Wiener-Hopf 方程**：$\sum_{j=-N}^{N} c_j \Gamma_{m-j} = \xi_m$。
3. **判决反馈均衡器 (DFE)**：
   * 由前向滤波器 (FFF) 和反馈滤波器 (FBF) 组成。利用已判决符号消除拖尾 ISI，**绝对不放大噪声**。

### 四、 OFDM（正交频分复用）系统
1. **系统框图与原理**：
   * **发送端**：输入数据 $\to$ 串并变换 $\to$ 星座映射 $\to$ **IFFT 调制** $\to$ **加循环前缀 (CP)** $\to$ D/A $\to$ 射频发送。
   * **接收端**：射频接收 $\to$ A/D $\to$ **去循环前缀 (CP)** $\to$ **FFT 解调** $\to$ 均衡/解映射 $\to$ 并串变换 $\to$ 输出。
   * **正交性条件**：子载波间隔 $\Delta f = \frac{1}{T_{sub}}$（$T_{sub}$ 为有效符号周期）。
2. **循环前缀 (CP) 的指标与计算**：
   * **构造条件**：CP 的时间长度 $T_{cp}$ 必须大于信道的最大多径时延扩展 $\tau_{max}$（即 $T_{cp} > \tau_{max}$）。
   * **作用**：将信道的线性卷积转化为循环卷积，消除码间串扰 (ISI) 与子载波间干扰 (ICI)。
   * **总符号周期**：$T_{total} = T_{sub} + T_{cp}$。
   * **功率/频谱效率损失因子**：$\eta_{loss} = \frac{T_{sub}}{T_{sub} + T_{cp}}$。

---

## ⏳ 第二部分：时域与衰落信道传输（第13、14章）

### 一、 衰落信道定义与参数分类
1. **时延扩展与相干带宽**（定义时域选择性）：
   * 多径时延扩展为 $\tau_{max}$，相干带宽 $B_c \approx \frac{1}{\tau_{max}}$。
   * **平坦衰落 (Flat Fading)**：信号带宽 $B \ll B_c$（时域码元周期 $T_s \gg \tau_{max}$），无 ISI。
   * **频率选择性衰落**：信号带宽 $B \gg B_c$（时域码元周期 $T_s \ll \tau_{max}$），产生严重 ISI。
2. **多普勒扩展与相干时间**（定义时变特性）：
   * 最大多普勒频移 $f_d = \frac{v}{\lambda}$，相干时间 $T_c \approx \frac{1}{f_d}$。
   * **慢衰落 (Slow Fading)**：码元周期 $T_s \ll T_c$，信道在一个或多个码元周期内恒定。
   * **快衰落 (Fast Fading)**：码元周期 $T_s \gg T_c$，信道在单码元周期内剧烈变化，导致载波相位无法追踪。

### 二、 衰落信道容量
1. **遍历容量 (Ergodic Capacity)**（长时延编码，经历所有信道状态）：
   $$C_{ergodic} = E_H \left[ B \log_2 \left( 1 + \frac{P |h|^2}{N_0 B} \right) \right]$$
   * **遍历 CSI 分配**：若收发两端均已知 CSI，采用 **水注法 (Water-filling)** 动态分配功率：信道好时多发，信道差时少发或不发。
2. **中断容量 (Outage Capacity)**：适用于慢衰落、时延受限系统。
   $$P_{out} = \Pr \left( B \log_2(1 + \gamma |h|^2) < R_{target} \right)$$

### 三、 接收机设计与误码率（$P_e$）分析
1. **AWGN 最佳接收机**：由**匹配滤波器 (MF)**（冲激响应 $h(t) = s^*(T-t)$）或相关器进行理想采样，再进行门限判决。
2. **AWGN 信道瞬时误码率**（以 BPSK 为例）：
   $$P_e(\gamma) = Q\left(\sqrt{2\gamma}\right)$$
3. **瑞利衰落信道平均误码率（对信噪比积分）**：
   * 瑞利衰落下的瞬时信噪比 $\gamma$ 服从指数分布：$p(\gamma) = \frac{1}{\bar{\gamma}} e^{-\frac{\gamma}{\bar{\gamma}}}$（$\bar{\gamma}$ 为平均信噪比）。
   * **积分推导与性能劣化**：
     $$\bar{P}_e = \int_0^{\infty} P_e(\gamma) p(\gamma) d\gamma = \int_0^{\infty} Q\left(\sqrt{2\gamma}\right) \frac{1}{\bar{\gamma}} e^{-\frac{\gamma}{\bar{\gamma}}} d\gamma = \frac{1}{2} \left( 1 - \sqrt{\frac{\bar{\gamma}}{1+\bar{\gamma}}} \right) \approx \frac{1}{4\bar{\gamma}} \quad (\bar{\gamma} \gg 1)$$
   * **重要结论**：AWGN 信道中误码率随信噪比呈**指数下降**；而瑞利衰落信道中由于缺乏多径分集，误码率仅随信噪比呈**线性倒数下降**（性能大幅度恶化，曲线变平缓）。

---

## 🌌 第三部分：空域与多天线系统（第15章）

### 一、 MIMO 容量公式含义与证明
1. **容量数学公式**：
   $$C = B \log_2 \det \left( \mathbf{I}_{N_r} + \frac{\rho}{N_t} \mathbf{H}\mathbf{H}^H \right)$$
   * **参数含义**：$\mathbf{H}$ 为 $N_r \times N_t$ 的信道矩阵，$\mathbf{I}_{N_r}$ 为单位矩阵，$\rho$ 为总接收信噪比。
2. **公式证明与奇异值分解 (SVD)**：
   * 对信道矩阵进行 SVD 分解：$\mathbf{H} = \mathbf{U} \mathbf{\Sigma} \mathbf{V}^H$。
   * 带入行列式公式，利用 $\det(\mathbf{I} + \mathbf{A}\mathbf{B}) = \det(\mathbf{I} + \mathbf{B}\mathbf{A})$ 展开，可将 MIMO 信道解耦为 $r = \text{rank}(\mathbf{H}) \le \min(N_t, N_r)$ 个**独立的并行子信道**：
     $$C = \sum_{i=1}^{r} B \log_2 \left( 1 + \frac{\rho}{N_t} \lambda_i \right)$$
     （其中 $\lambda_i = \sigma_i^2$ 为 $\mathbf{H}\mathbf{H}^H$ 的非零特征值）。
   * **结论**：在高信噪比（$\rho \to \infty$）下，MIMO 容量随天线数呈**线性增长增益（空间复用增益）**。

### 二、 MIMO 接收机算法对比 (ML / MSE)
设接收信号矢量 $\mathbf{y} = \mathbf{H}\mathbf{x} + \mathbf{n}$：
1. **最大似然 (ML) 接收机（非线性）**：
   - 算法：$\hat{\mathbf{x}} = \arg\min_{\mathbf{x}} \|\mathbf{y} - \mathbf{H}\mathbf{x}\|^2$。
   - 特点：性能最佳，能获得满分集增益，但复杂度随天线数呈指数爆炸增长。
2. **迫零 (ZF) 接收机（线性）**：
   - 算法：乘以伪逆 $\mathbf{G}_{ZF} = (\mathbf{H}^H \mathbf{H})^{-1} \mathbf{H}^H$。完全消除干扰，但会导致**噪声放大**。
3. **最小均方误差 (MMSE) 接收机（线性）**：
   - 算法：$\mathbf{G}_{MMSE} = \left( \mathbf{H}^H \mathbf{H} + \frac{N_0}{E_s} \mathbf{I} \right)^{-1} \mathbf{H}^H$。
   - 特点：在消除天线间干扰和抑制噪声放大之间取得最佳折中。

### 三、 分集阶数与自由度 (DoF)
1. **分集自由度 / 空间复用增益 (DoF)**：
   $$\text{DoF} = \lim_{\rho \to \infty} \frac{C(\rho)}{\log_2 \rho} = \min(N_t, N_r)$$
   代表系统在空间中能够同时传输的独立数据流的最大几何数量。
2. **最大分集阶数 (Diversity Order)**：
   $$d_{max} = N_t \times N_r$$
   代表相互独立的衰落路径总数。分集阶数越大，误码率曲线在高信噪比下的下降斜率越陡峭。

---

## 👥 第四部分：多用户通信（第16章）

### 一、 多用户信道容量概念
1. **多址接入信道 (MAC)**：多传一（上行链路，如多手机对单基站）。
   * **双用户 MAC 容量域边界**：
     $$R_1 \le B \log_2\left(1 + \frac{P_1}{N_0 B}\right), \quad R_2 \le B \log_2\left(1 + \frac{P_2}{N_0 B}\right)$$
     $$R_1 + R_2 \le B \log_2\left(1 + \frac{P_1 + P_2}{N_0 B}\right)$$
   * 两个用户独立分担总带宽容量。边界交点可以通过 **连续干扰消除 (SIC)** 接收机达到。
2. **广播信道 (BC)**：一传多（下行链路，如单基站对多手机）。
   * **脏纸编码 (DPC, Dirty Paper Coding)**：下行广播信道容量域的理论最优边界方案。其核心原理是：如果发送端能够预先获知干扰信号，则可以通过预编码发送信息，使接收端在完全不增加发射功率的前提下彻底消除该干扰。

### 二、 多用户接收机检测技术
1. **传统单用户检测 (SU-MUD)**：
   * 将其他所有用户的信号均简单地视为**加性高斯白噪声干扰**。
   * **缺点**：若多用户物理距离不等，会遭遇严重的**远近效应 (Near-Far Effect)**，基站附近的强信号会完全淹没远端用户的弱信号，必须依赖严格的功率控制。
2. **多用户检测 (MUD) 接收机**：
   * **线性检测（ZF-MUD / MMSE-MUD）**：利用解相关矩阵消除用户特征码（如 CDMA 序列）之间的多用户干扰 (MUI)。
   * **连续干扰消除 (SIC) 接收机**：按照信号接收功率由大到小的顺序进行级联剥离。先判决并重构信号最强的用户，将其从总信号中减去（剔除干扰），再对次强的用户进行判决，以此类推。