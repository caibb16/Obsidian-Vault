
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
    
- 极值性: $H(X) \le \log_2 n$ (等概率时取等号)。
    
- 若 $Y = g(X)$ 且 $g$ 为确定性函数，则 $H(Y) \le H(X)$ (只有当 $g$ 是一对一映射时取等号)。
    

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
    
- **AWGN 连续信道 (Shannon 公式):** $C = B \log_2\left(1 + \frac{S}{N}\right)$。
    
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