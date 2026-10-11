# Java 并发编程知识体系

> 本文档基于 JavaGuide 并发系列整理，按"基础 → 进阶 → 工具 → 实战"的脉络组织，方便系统复习。

---

## 一、基础概念

### 进程 vs 线程

- **进程**：程序的一次执行过程，是系统运行程序的**基本单位**。如启动 main 函数就是启动一个 JVM 进程。
- **线程**：进程中的一个执行单位，是比进程更小的调度单位。一个进程可以包含多个线程。

**通俗理解**：进程好比一个工厂，线程是工厂里的工人。一个工厂可以有多工人，共享工厂的资源（场地、机器），但每个工人有自己的工位（栈、程序计数器）。

| 维度 | 进程 | 线程 |
|---|---|---|
| 资源占用 | 大，独立内存 | 小，共享进程内存 |
| 切换开销 | 大 | 小（轻量级进程） |
| 通信方式 | 管道、消息队列、socket 等 | 共享变量（更简单） |
| 影响范围 | 进程间互不影响 | 同一进程内线程相互影响 |

### 并发 vs 并行

- **并发**：两个及以上作业在**同一时间段**内执行（看起来同时，轮流使用 CPU）
- **并行**：两个及以上作业在**同一时刻**执行（真正同时，需要多核 CPU）

**通俗理解**：并发是一个人吃三个馒头轮流咬，并行是三个人各吃一个馒头。

### 同步 vs 异步

- **同步**：发出调用后，必须等结果返回才能继续（阻塞等待）
- **异步**：调用发出后立即返回，结果通过回调 / Future 等方式通知（非阻塞）

### 为什么需要多线程

- **单核时代**：提高 CPU 和 IO 系统的利用率（一个线程 IO 阻塞时，其他线程可以继续用 CPU）
- **多核时代**：充分利用多核 CPU 的计算能力（计算密集型任务约等于单核耗时 / 核心数）
- **互联网需求**：百万级并发要求高并发系统，多线程是基础

**注意**：多线程不总是能提升速度，上下文切换有开销，线程数过多反而降低性能。

### 上下文切换

CPU 从一个线程切换到另一个线程时，需要保存当前线程的上下文（程序计数器、栈信息等），再加载下一个线程的上下文——这就是**上下文切换**。

- 切换时机：主动让出 CPU（sleep/wait）、时间片用完、IO 阻塞、线程终止
- 每次切换消耗 CPU 和内存资源，**频繁切换会导致效率低下**

---

## 二、Java 线程基础

### 线程模型（用户线程 vs 内核线程）

线程模型是用户线程和内核线程的关联方式：

1. **一对一**：一个用户线程对应一个内核线程（Java 平台线程采用此模型）
2. **多对一**：多个用户线程映射到一个内核线程（不能利用多核）
3. **多对多**：多个用户线程映射到多个内核线程（Go 早期 goroutine）

**Java 线程与 OS 线程的关系**：
- 平台线程（传统 new Thread()）通常 1:1 映射到 OS 内核线程
- 虚拟线程（Java 21+）由 JVM 调度，复用少量平台线程

### 线程与进程的资源分配

```
进程 A                              进程 B
├── 堆（共享）                        ├── 堆（共享）
├── 方法区 / 元空间（共享）            ├── 方法区 / 元空间（共享）
├── 线程 1                            ├── 线程 1
│   ├── 程序计数器（私有）              ├── 程序计数器（私有）
│   ├── 虚拟机栈（私有）                ├── 虚拟机栈（私有）
│   └── 本地方法栈（私有）              └── 本地方法栈（私有）
└── 线程 2
    ├── 程序计数器（私有）
    ├── 虚拟机栈（私有）
    └── 本地方法栈（私有）
```

**为什么这些区域要私有？**
- **程序计数器**：记录线程执行到哪儿了，切换回来能继续执行
- **虚拟机栈 / 本地方法栈**：保证局部变量不被其他线程访问
- **堆 / 方法区**：多线程共享，存放对象和类信息

### 创建线程的方式

严格来说，Java 只有**一种**方式创建线程：`new Thread().start()`。其他方式（实现 Runnable、Callable、线程池、CompletableFuture）都只是**使用多线程的方式**，最终都依赖 `start()`。

```java
// 1. 继承 Thread
new MyThread().start();

// 2. 实现 Runnable（推荐，避免单继承）
new Thread(() -> doWork()).start();

// 3. 实现 Callable（有返回值，可抛异常）
FutureTask<String> task = new FutureTask<>(() -> "result");
new Thread(task).start();

// 4. 线程池
ExecutorService pool = Executors.newFixedThreadPool(4);
pool.submit(() -> doWork());

// 5. CompletableFuture
CompletableFuture.runAsync(() -> doWork());
```

### 线程的生命周期与状态

Java 线程 6 种状态（`Thread.State`）：
- **NEW**：新建，线程对象已创建但未调用 `start()`
- **RUNNABLE**：运行，调用 `start()` 后（包含就绪 + 运行中，JVM 统一为 RUNNABLE）
- **BLOCKED**：阻塞，等待获取 monitor 锁
- **WAITING**：等待，需其他线程通知（`wait()` / `join()` / `LockSupport.park()`）
- **TIMED_WAITING**：超时等待（`sleep(long)` / `wait(long)` / `join(long)`）
- **TERMINATED**：终止，`run()` 执行完毕

状态转换图：
```
NEW ──start()──→ RUNNABLE ──→ TERMINATED
                    │
       ┌──────────┼──────────┐
       ↓          ↓          ↓
   BLOCKED    WAITING   TIMED_WAITING
   (等锁)     (等通知)   (等超时)
```

> **注意**：操作系统有 READY 和 RUNNING 之分，JVM 把这两种统一为 RUNNABLE，因为 JVM 不直接管调度。

### start() vs run()

- `start()`：启动新线程，进入就绪状态，由 JVM 调度执行 `run()`，**真正多线程**
- `run()`：普通方法调用，在当前线程中执行，**不是多线程**

**面试坑**：
```java
Thread t = new Thread(() -> System.out.println("hi"));
t.run();   // ❌ 普通调用，主线程执行
t.start(); // ✅ 新线程执行
```

### sleep() vs wait()

**共同点**：两者都可以暂停线程的执行。

| 维度 | `sleep()` | `wait()` |
|---|---|---|
| 所在类 | `Thread` 静态方法 | `Object` 实例方法 |
| 释放锁 | ❌ 不释放 | ✅ 释放 |
| 用途 | 暂停执行 | 线程间通信 |
| 唤醒方式 | 超时自动醒 | 需 `notify()` / `notifyAll()` |

**为什么 `wait()` 在 `Object` 而 `sleep()` 在 `Thread`？**
- `wait()` 需要释放对象锁，所以必须操作**对象**（Object）
- `sleep()` 不涉及锁，暂停当前线程即可

### 线程调度

- **抢占式调度**（Java 采用）：OS 决定何时切换线程，公平性好，开销大
- **协同式调度**：线程主动让出，效率高但易阻塞
- Java 线程调度委托给 OS，优先级只是建议，高优先级不一定先执行

---

## 三、Java 内存模型（JMM）

### 什么是 JMM

**JMM（Java Memory Model）** 是 JVM 规范定义的抽象规范，描述了线程之间共享变量的访问规则，以及变量在内存中存储和读取的底层细节。

**核心目标**：屏蔽不同硬件/OS 的内存访问差异，保证 Java 并发程序跨平台的一致性。

**为什么需要 JMM？** 没有 JMM 时，并发编程会遇到三大问题：

| 问题 | 描述 |
|---|---|
| 可见性 | 线程 A 修改了共享变量，线程 B 看不到 |
| 原子性 | 一个复合操作被中途打断（如 i++）|
| 有序性 | 编译器和 CPU 的指令重排序导致逻辑错乱 |

### 主内存与工作内存

JMM 把内存抽象为两层：

![[Pasted image 20261010151915.png]]

- **主内存**：所有共享变量存放的地方（对应堆内存中的对象）
- **工作内存**：每个线程私有的"副本空间"（可类比 CPU 缓存 + 寄存器）
- 线程对变量的所有操作（读 / 写）都必须在工作内存中完成

### 三大特性与解决方案

| 特性 | 含义 | 解决方式 |
|---|---|---|
| **原子性** | 一个或多个操作要么全部执行，要么全部不执行 | `synchronized` / `Lock` / `Atomic*` |
| **可见性** | 一个线程修改变量后，其他线程能立即看到 | `volatile` / `synchronized` / `final` |
| **有序性** | 程序执行的顺序按代码先后顺序（禁止重排序）| `volatile` / `synchronized` / happens-before |

### happens-before 原则（核心）

**happens-before 不是"时间先后"规则，而是"可见性"规则。**

> 如果操作 A happens-before 操作 B，那么 A 的结果对 B 可见，且 A 的执行顺序排在 B 之前（这里的"之前"是 JMM 视角下的偏序关系，不是真实物理时间）。

**核心规则**：

| 规则 | 说明 |
|---|---|
| 程序顺序规则 | 同一线程内，前面的操作 happens-before 后面的操作 |
| 锁规则 | `unlock` happens-before 后续的 `lock` |
| volatile 规则 | 写 volatile 变量 happens-before 后续读该变量 |
| 线程启动规则 | `Thread.start()` happens-before 该线程内任意操作 |
| 线程终止规则 | 线程内所有操作 happens-before 其他线程 `join()` 返回 |
| 中断规则 | `interrupt()` happens-before 被中断线程检测到中断事件 |
| 传递性 | A hb B，B hb C ⇒ A hb C |
| 对象终结规则 | 对象构造完成 happens-before finalize() 开始 |

**理解要点**：
- 单线程内 happens-before 自动成立；**跨线程必须程序员主动建立**（volatile、synchronized、Lock、线程操作等）
- 没有 happens-before 关系的两个操作，JVM 可以任意重排序，CPU/缓存也可以让结果不可见

**经典反例**：
```java
int a = 0;
boolean flag = false;

// 线程 A
a = 1;          // ①
flag = true;    // ②

// 线程 B
if (flag) {     // ③
    System.out.println(a);  // ④ 可能输出 0！
}
```

① 和 ② 在不同线程执行，**没有 happens-before 关系**，JVM 可能重排 ② 到 ① 之前，导致线程 B 看到 flag=true 但 a 还是 0。

**正确做法**：给 `flag` 加 `volatile`，则 ② hb ③ 成立，再由传递性得 ① hb ④。

### volatile 关键字

volatile 是 Java 提供的**最轻量级的同步机制**，提供两个语义：

1. **保证可见性**：写 volatile 立即刷回主内存；读 volatile 立即从主内存读取
2. **禁止指令重排序**：通过内存屏障实现

**底层实现：内存屏障**

| 操作 | 屏障 | 作用 |
|---|---|---|
| volatile 写 | StoreStore 屏障 | 防止上面的普通写与 volatile 写重排序 |
| volatile 写 | StoreLoad 屏障 | 防止 volatile 写与下面的 volatile 读/写重排序 |
| volatile 读 | LoadLoad 屏障 | 防止下面的普通读与 volatile 读重排序 |
| volatile 读 | LoadStore 屏障 | 防止下面的普通写与 volatile 读重排序 |

**特别注意**：
- volatile **保证可见性和有序性，但不保证原子性**（如 `i++` 仍需用 `AtomicInteger`）
- 适合场景：一写多读、状态标志位、双重检查锁定（DCL）

### volatile vs synchronized

| 维度 | volatile | synchronized |
|---|---|---|
| 原子性 | ❌ | ✅ |
| 可见性 | ✅ | ✅ |
| 有序性 | ✅ | ✅ |
| 阻塞 | 非阻塞 | 可能阻塞 |
| 性能 | 更轻量 | 更重 |

---

## 四、锁机制

### synchronized 关键字

`synchronized` 是 Java 内置的**可重入、互斥**锁，可修饰实例方法、静态方法、代码块。

```java
// 1. 修饰实例方法（锁：当前对象 this）
public synchronized void method() { ... }

// 2. 修饰静态方法（锁：Class 对象）
public static synchronized void staticMethod() { ... }

// 3. 修饰代码块（推荐，粒度细）
synchronized (lockObject) { ... }
```

**底层原理**：
- **同步代码块**：基于 `monitorenter` / `monitorexit` 字节码指令，进入 monitor 时加 1，退出时减 1
- **同步方法**：JVM 通过方法的 ACC_SYNCHRONIZED 标志位实现
- **对象头**：每个对象都有一个 monitor（监视器锁），锁信息存在对象头的 Mark Word 中

**锁升级（Java 6 之后的优化）**：

```
无锁 → 偏向锁 → 轻量级锁（自旋锁）→ 重量级锁
```

| 锁状态 | 适用场景 | 加锁开销 |
|---|---|---|
| 偏向锁 | 同一线程多次进入 | 几乎无开销（CAS 一次） |
| 轻量级锁 | 短时间内的轻度竞争 | 自旋消耗 CPU |
| 重量级锁 | 激烈竞争 | 线程阻塞、上下文切换 |

**升级过程**：
1. 对象刚创建时无锁
2. 第一次有线程访问 → 升级为偏向锁（记录线程 ID）
3. 第二个线程来争用 → 偏向锁撤销，升级为轻量级锁（自旋）
4. 自旋超过阈值（JDK1.6 后自适应）→ 升级为重量级锁（OS 互斥量）

**注意**：
- **可重入**：同一线程可多次进入同一把锁（基于计数器），防止死锁
- **不可中断**：一旦阻塞，只能等锁释放（vs ReentrantLock 可中断）
- 锁对象不能是 String 常量、Integer、Long 等包装类（可能指向同一对象导致死锁）

### ReentrantLock

ReentrantLock 是 JDK 1.5 提供的 `java.util.concurrent` 包下的**可重入互斥锁**，是 synchronized 的增强版。

```java
ReentrantLock lock = new ReentrantLock();
lock.lock();
try {
    // 临界区
} finally {
    lock.unlock();  // 必须手动释放！
}
```

**核心特性**：
1. **可重入**：与 synchronized 一样
2. **可中断**：`lockInterruptibly()` 可以在等待锁时响应中断
3. **公平 / 非公平**：构造时可选（默认非公平，吞吐量更大）
4. **超时锁**：`tryLock(long timeout, TimeUnit unit)` 避免永久等待
5. **条件变量**：支持多个 `Condition`，可精确唤醒指定线程（vs synchronized 只能全唤）

```java
// 条件变量实现生产者-消费者
Condition notFull = lock.newCondition();
Condition notEmpty = lock.newCondition();
notEmpty.await();   // 等待
notFull.signal();   // 精确唤醒
```

### synchronized vs ReentrantLock

| 维度 | synchronized | ReentrantLock |
|---|---|---|
| 实现 | JVM 关键字 | JDK 类（CAS + AQS）|
| 释放锁 | 自动 | 必须手动 `unlock()`（建议 try-finally）|
| 可中断 | ❌ | ✅ `lockInterruptibly()` |
| 公平锁 | ❌ | ✅ 构造可选 |
| 条件变量 | 1 个（wait/notify）| 多个 `Condition` |
| 性能 | 优化后差距不大 | 高竞争时略优 |

**选择建议**：能用 synchronized 就用 synchronized（简洁、自动释放），需要高级特性时再用 ReentrantLock。

### ReentrantReadWriteLock

读写分离的锁，提升读多写少场景的性能：
- **读锁（共享锁）**：多个线程可同时读
- **写锁（排他锁）**：写时独占
- **互斥关系**：读-写互斥、写-写互斥；读-读共享

```java
ReentrantReadWriteLock rwLock = new ReentrantReadWriteLock();
ReadLock readLock = rwLock.readLock();
WriteLock writeLock = rwLock.writeLock();
```

**注意**：读锁升级为写锁会死锁；写锁降级为读锁是允许的（持有写锁时可再获取读锁）。

### StampedLock（了解）

JDK 1.8 引入的**乐观读写锁**，比 ReentrantReadWriteLock 性能更高：
- 三种访问模式：写锁、悲观读锁、乐观读
- 乐观读不阻塞写，验证戳（stamp）后决定是否重读
- **不可重入**，使用复杂，谨慎用

### 悲观锁 vs 乐观锁

| 类型 | 思路 | 适用场景 | 例子 |
|---|---|---|---|
| **悲观锁** | 总认为会冲突，先加锁再操作 | 写多读少 | `synchronized`、`ReentrantLock` |
| **乐观锁** | 总认为不冲突，提交时再验证 | 读多写少 | `AtomicInteger`、版本号机制 |

### CAS 与原子类

**CAS（Compare And Swap）** 是乐观锁的核心：
- 内存值 V、预期值 A、新值 B
- 当且仅当 V == A 时，将 V 改为 B，否则什么都不做
- 由 CPU 指令（如 cmpxchg）保证原子性

```java
// AtomicInteger 内部基于 CAS
AtomicInteger count = new AtomicInteger(0);
count.incrementAndGet();  // 等价于 i++，但线程安全
```

**CAS 三大问题**：

1. **ABA 问题**：值从 A → B → A，CAS 误以为没变
2. **循环开销**：高竞争时自旋消耗 CPU
3. **单变量原子操作**：仅能保证一个变量的原子性（Java 1.5 后 AtomicReference 可包装多个）

### ABA 问题及解决

**场景**：
```
线程1：读到 A
线程2：A → B → A
线程1：CAS 看到还是 A，修改成功，但实际已被改过
```

**解决**：加**版本号（时间戳）**，每次修改都更新版本号。
- JDK 提供 `AtomicStampedReference`、`AtomicMarkableReference`
- 数据库场景用乐观锁时也是同样思路：`UPDATE ... WHERE version = ?`

---

## 五、ThreadLocal

### 是什么 / 解决什么问题

通常创建的变量可以被多个线程访问和修改，为了解决多线程环境下的数据竞争和安全问题，让每个线程有自己的专属本地变量，引入 `ThreadLocal` 类，允许每个线程绑定自己的值。

当你创建一个 `ThreadLocal` 变量时，每个访问该变量的线程都会拥有一个独立的副本。

### 底层原理

`ThreadLocal` 本身**不存值**，值实际存在当前线程的 `ThreadLocalMap` 中。

每个 `Thread` 内部维护一个 `ThreadLocalMap`（可理解为定制化的 `HashMap`）：

```java
public class Thread implements Runnable {
    ThreadLocal.ThreadLocalMap threadLocals = null;          // 普通 ThreadLocal
    ThreadLocal.ThreadLocalMap inheritableThreadLocals = null; // InheritableThreadLocal
}
```

数据结构：

```
Thread → ThreadLocalMap → Entry[ThreadLocal(弱引用), value(强引用)]
```

- 同一线程中声明**多个** `ThreadLocal`，共用同一个 `ThreadLocalMap`，key 为 `ThreadLocal` 实例本身，value 为 `set()` 的值
- 多个线程访问**同一个** `ThreadLocal`，拿到的是各自 `ThreadLocalMap` 里的副本，互不干扰

### 内存泄漏

**根本原因**：`ThreadLocalMap` 的 `Entry` 继承自 `WeakReference<ThreadLocal<?>>`，即 **key 是弱引用，value 是强引用**。

```java
static class Entry extends WeakReference<ThreadLocal<?>> {
    Object value;
    Entry(ThreadLocal<?> k, Object v) { super(k); value = v; }
}
```

- 当 `ThreadLocal` 实例失去强引用后，下次 GC 会回收 key（弱引用），但 value 仍被 `Entry` 强引用，无法回收
- 如果线程持续存活（如线程池中的核心线程），value 会一直残留在内存中 → **内存泄漏**

**泄漏的两个必要条件**（缺一不可）：

1. `ThreadLocal` 实例不再被强引用
2. 线程持续存活（线程池场景）

### 为什么 key 用弱引用？（经典面试追问）

引用链路：

```
强引用（栈/静态变量）──→ ThreadLocal 实例
                              ↑
Thread ──→ ThreadLocalMap ──→ Entry ── key（弱引用）──┘
                              │
                              └─── value（强引用）──→ 实际存储的对象
```

- **强引用方案**：忘记 `remove()` → `ThreadLocal` 和 value 都泄漏，**无任何补救机会**
- **弱引用方案（采用）**：忘记 `remove()` → GC 仍能回收 `ThreadLocal`，`get()`/`set()`/`remove()` 触发时还会顺带清理 key 为 null 的过期 entry
- 弱引用是**兜底防御**，**降低了风险但没消除风险**——自清理是被动触发的，必须手动 `remove()`

### 正确使用方式（《阿里 Java 开发手册》强制）

```java
private static final ThreadLocal<UserContext> HOLDER = new ThreadLocal<>();

public void process() {
    try {
        HOLDER.set(buildContext());
        doBusiness();
    } finally {
        HOLDER.remove();   // 必须在 finally 中清理
    }
}
```

三个关键点：

1. 声明为 `static final`，避免重复创建 `ThreadLocal` 实例导致旧实例泄漏
2. `try-finally` 保证 `remove()` 一定执行（即使业务抛异常）
3. 用完立即清理，不要依赖下次 `set()` 覆盖——不同 `ThreadLocal` 之间的过期条目会长期残留

### 线程池下的数据脏读

线程池的核心线程会被**复用**，如果上一个任务没清理 `ThreadLocal`，下一个被分配到同一线程的任务就会读到残留值 → **数据串号**（如用户 A 的请求读到用户 B 的身份信息）。

美团技术团队曾在《Java 线程池实现原理及其在美团业务中的实践》中记录过此类线上事故。

### 异步场景失效及跨线程传递

**问题**：值存在当前 `Thread` 里，任务切换到其他线程时无法自动传递。

**方案一：InheritableThreadLocal**（JDK 1.2 原生）

- 创建**子线程**时，把父线程的 `ThreadLocal` 值复制一份给子线程
- **致命缺陷**：只在**线程创建时**复制一次，**线程池场景下失效**——线程被复用，复制的是首次的旧值，会产生脏数据

**方案二：TransmittableThreadLocal (TTL)**（阿里开源，推荐）

- 核心是 **CRR 三阶段**（基于装饰器模式，在任务提交/执行时机介入）：
  - **Capture（捕获）**：提交任务时，把当前线程的 TTL 值抓取快照，与任务绑定
  - **Replay（回放）**：工作线程执行前，把快照值 set 到该线程，并备份旧值
  - **Restore（恢复）**：任务执行结束后，恢复线程到执行前状态
- 接入方式：
  1. `TtlExecutors.getTtlExecutorService(executor)` 包装线程池
  2. 通过 `-javaagent` 字节码增强，**业务代码零改造**
- 与 `InheritableThreadLocal` 区别：前者**跟线程绑定**（创建时有效），后者**跟任务绑定**（完美支持线程池）

---

## 六、线程池

### 为什么要用线程池

直接 `new Thread()` 的问题：
- 每次创建/销毁线程消耗大量资源
- 无限制创建线程可能导致 OOM
- 缺乏统一管理（任务排队、拒绝策略等）

线程池的好处：
- **降低资源消耗**：复用已创建的线程
- **提高响应速度**：任务到达时无需等待线程创建
- **提高可管理性**：统一分配、调优、监控

### 创建线程池的两种方式

**方式一：通过 `Executors` 工厂（不推荐）**

```java
Executors.newFixedThreadPool(4);     // 固定大小
Executors.newCachedThreadPool();     // 弹性伸缩
Executors.newSingleThreadExecutor(); // 单线程
Executors.newScheduledThreadPool(4); // 定时任务
```

> **《阿里 Java 开发手册》强制**：线程池**不允许**使用 `Executors` 创建，而是要通过 `ThreadPoolExecutor` 构造方式，明确参数。

**原因**：`Executors` 很多方法用 `LinkedBlockingQueue`（无界队列）或 `SynchronousQueue`，可能堆积大量请求导致 OOM。

**方式二：通过 `ThreadPoolExecutor` 构造（推荐）**

### ThreadPoolExecutor 核心参数

```java
public ThreadPoolExecutor(
    int corePoolSize,      // 核心线程数（即使空闲也不回收，除非 allowCoreThreadTimeOut）
    int maximumPoolSize,   // 最大线程数
    long keepAliveTime,    // 空闲线程存活时间（非核心线程）
    TimeUnit unit,         // 时间单位
    BlockingQueue<Runnable> workQueue,   // 任务队列
    ThreadFactory threadFactory,         // 线程工厂（建议自定义命名）
    RejectedExecutionHandler handler     // 拒绝策略
)
```

### 任务执行流程

```
提交任务
   │
   ↓
核心线程未满？──→ 是 ──→ 创建核心线程执行
   │
   否
   ↓
队列未满？──→ 是 ──→ 入队等待
   │
   否
   ↓
最大线程未满？──→ 是 ──→ 创建非核心线程执行
   │
   否
   ↓
执行拒绝策略
```

### 拒绝策略（4 种）

| 策略 | 行为 | 适用场景 |
|---|---|---|
| **AbortPolicy（默认）** | 抛 `RejectedExecutionException` | 默认选择，业务能感知失败 |
| **CallerRunsPolicy** | 让提交任务的线程自己执行 | 不能丢任务，且能承受延迟 |
| **DiscardPolicy** | 静默丢弃 | 允许丢失任务 |
| **DiscardOldestPolicy** | 丢弃队首最老任务，提交新任务 | 允许丢老任务 |

### 阻塞队列

| 队列 | 特点 |
|---|---|
| `LinkedBlockingQueue` | 链表，无界（容量 Integer.MAX_VALUE，可能 OOM）|
| `ArrayBlockingQueue` | 数组，**有界**，必须指定大小 |
| `SynchronousQueue` | 不存储元素，必须有线程取才会提交成功 |
| `PriorityBlockingQueue` | 优先级队列 |
| `DelayQueue` | 延时队列 |

### 线程数怎么定

**理论公式**（美团技术团队经验）：

- **CPU 密集型**（加密、计算、压缩）：`N_cpu + 1`（1 为备线程，应对缺页中断）
- **IO 密集型**（数据库、文件、网络）：`2 × N_cpu`
- **公式**：`线程数 = N_cpu × (1 + W/C)`
  - N_cpu = CPU 核心数（Runtime.getRuntime().availableProcessors()）
  - W = 线程等待时间
  - C = 线程计算时间

**实际建议**：先压测，按业务类型分类，每类独立线程池。

### 线程池状态

```
RUNNING → SHUTDOWN → STOP → TIDYING → TERMINATED
```

- `RUNNING`：接受新任务，处理队列任务
- `SHUTDOWN`：不接受新任务，处理队列任务（`shutdown()`）
- `STOP`：不接受新任务，不处理队列任务，中断正在执行的任务（`shutdownNow()`）
- `TIDYING`：所有任务终止，workerCount = 0
- `TERMINATED`：terminated() 方法执行完毕

### 动态线程池

生产环境建议**动态调参**：
- 美团动态线程池：基于配置中心（Nacos/Apollo）实时调整核心参数
- Hippo4j：国产开源动态线程池框架
- 核心是封装 `ThreadPoolExecutor` + 配置中心 + 监控告警

---

## 七、并发工具类

### Future / FutureTask / CompletableFuture

**Future** 是 JDK 1.5 提供的异步结果占位符：

```java
ExecutorService pool = Executors.newFixedThreadPool(4);
Future<String> future = pool.submit(() -> "result");

// 阻塞获取
String result = future.get();           // 永久等待
String r2 = future.get(1, TimeUnit.SECONDS);  // 超时
boolean done = future.isDone();        // 是否完成
future.cancel(true);                  // 取消（可中断）
```

**Future 的缺陷**：
- 只能阻塞获取结果
- 无法链式调用（结果A完成后再处理）
- 无法组合多个 Future
- 没有异常处理

**CompletableFuture**（JDK 1.8 引入）是 Future 的**增强版**，解决了上述所有问题：

```java
CompletableFuture.supplyAsync(() -> queryOrder(), pool)
    .thenApply(order -> enrich(order))           // 同步转换
    .thenApplyAsync(order -> saveCache(order), pool)  // 异步转换
    .thenCombine(CompletableFuture.supplyAsync(() -> queryUser()),
                (order, user) -> merge(order, user))  // 合并
    .whenComplete((res, ex) -> log(res, ex))     // 异常处理
    .exceptionally(ex -> fallback());
```

**常用方法分类**：

| 类别 | 方法 |
|---|---|
| 创建 | `supplyAsync` / `runAsync` |
| 结果转换 | `thenApply` / `thenApplyAsync` |
| 结果消费 | `thenAccept` / `thenRun` |
| 组合 | `thenCombine` / `thenCompose` |
| 等待 | `allOf` / `anyOf` |
| 异常 | `exceptionally` / `whenComplete` / `handle` |

### AQS 原理

**AQS（AbstractQueuedSynchronizer）** 是 JUC 包下 ReentrantLock、CountDownLatch、Semaphore 等同步器的**底层基石**。

**核心思想**：
- 用一个 `volatile int state` 表示资源状态（如锁是否被占用、剩余许可数）
- 等待线程用 **CLH 双向队列** 排队
- 子类通过重写 `tryAcquire` / `tryRelease` 等方法管理 state

```
head ←──→ node1 ←──→ node2 ←──→ tail
         (等待线程)
```

**加锁流程（以 ReentrantLock 为例）**：

1. 调用 `lock()` → CAS 尝试将 state 从 0 改为 1
2. 成功 → 当前线程持有锁
3. 失败 → 包装成 Node 加入等待队列，park 阻塞
4. 释放锁时 unpark 后继节点，唤醒线程继续争抢

**核心方法**（模板方法模式，子类按需重写）：

- `tryAcquire` / `tryRelease`（独占模式）
- `tryAcquireShared` / `tryReleaseShared`（共享模式）
- `isHeldExclusively`（判断是否独占）

### CountDownLatch

倒计时门闩：让一个或多个线程等待其他线程完成操作后再执行。

```java
CountDownLatch latch = new CountDownLatch(3);

// 3 个工作线程
for (int i = 0; i < 3; i++) {
    new Thread(() -> {
        doWork();
        latch.countDown();  // 计数减 1
    }).start();
}

latch.await();   // 主线程阻塞等待计数到 0
System.out.println("all done");
```

**应用场景**：主线程等待多个子任务完成（如并发压测、并行任务汇总）。

**特点**：
- 计数为 0 后门闩永久打开（**不能重置**）
- 基于 AQS 的共享模式实现

### CyclicBarrier

循环栅栏：让一组线程互相等待到达同一个屏障点。

```java
CyclicBarrier barrier = new CyclicBarrier(3, () -> {
    System.out.println("all threads arrived");  // 最后一个到达的线程执行
});

for (int i = 0; i < 3; i++) {
    new Thread(() -> {
        doPart();
        barrier.await();  // 等待其他线程
        doNext();
    }).start();
}
```

**与 CountDownLatch 的区别**：

| 维度 | CountDownLatch | CyclicBarrier |
|---|---|---|
| 计数 | 只能减 | 加减都可，到 0 归零 |
| 用途 | 一个等 N 个 | N 个互相等 |
| 可重用 | ❌ 一次性 | ✅ 可循环用 |
| 触发动作 | 等待者 | 最后一个到达者 |

**应用场景**：分阶段计算（每阶段必须所有线程就绪才能开始下一阶段）、多人游戏加载。

### Semaphore

信号量：控制同时访问资源的线程数（类似令牌桶）。

```java
Semaphore sem = new Semaphore(3);  // 最多 3 个并发

for (int i = 0; i < 10; i++) {
    new Thread(() -> {
        sem.acquire();
        try {
            doWork();   // 同一时刻只有 3 个线程能进入
        } finally {
            sem.release();
        }
    }).start();
}
```

**应用场景**：限流、数据库连接池、池化资源管理。

**Exchanger**：两个线程间交换数据（较少用）。

---

## 八、死锁

### 什么是死锁

两个或两个以上的线程在执行过程中，因争夺资源而造成一种**相互等待**的现象，若无外力干涉将永远无法推进。

**经典代码示例**：

```java
public class DeadLockDemo {
    private static Object resource1 = new Object(); // 资源 1
    private static Object resource2 = new Object(); // 资源 2

    public static void main(String[] args) {
        new Thread(() -> {
            synchronized (resource1) {
                System.out.println(Thread.currentThread() + "get resource1");
                try { Thread.sleep(1000); } catch (InterruptedException e) {}
                synchronized (resource2) {
                    System.out.println(Thread.currentThread() + "get resource2");
                }
            }
        }, "线程 1").start();

        new Thread(() -> {
            synchronized (resource2) {
                System.out.println(Thread.currentThread() + "get resource2");
                try { Thread.sleep(1000); } catch (InterruptedException e) {}
                synchronized (resource1) {
                    System.out.println(Thread.currentThread() + "get resource1");
                }
            }
        }, "线程 2").start();
    }
}
```

### 死锁的 4 个必要条件（缺一不可）

1. **互斥条件**：资源一次只能被一个线程使用
2. **请求并保持**：线程持有资源时又请求新资源，不释放已有资源
3. **不剥夺条件**：线程已获得的资源，未使用完前不能被强行剥夺
4. **循环等待**：多个线程形成头尾相接的循环等待资源关系

**通俗理解**：A 等 B 的锁，B 等 A 的锁，谁都不放手。

### 死锁的诊断

- **jstack / jconsole**：JDK 自带工具，查看线程状态和锁等待
- **日志关键字**："Found one Java-level deadlock"
- **arthas**：阿里开源的 Java 诊断工具，`thread -b` 可直接定位阻塞线程

### 死锁的预防与避免

1. **破坏循环等待**：按固定顺序加锁（最常用）
2. **破坏请求并保持**：一次性申请所有资源（`Lock.tryLock(timeout)` 替代 `lock()`）
3. **破坏不剥夺**：超时放弃已持有资源
4. **使用高级工具**：优先用 `ReentrantLock` 的 `tryLock(long, TimeUnit)`、`ConcurrentHashMap` 等线程安全类
5. **减少嵌套加锁**：尽量避免一个方法里同时持有两把锁

**推荐方案**：使用并发工具类（ConcurrentHashMap、ConcurrentLinkedQueue 等），从设计上避免手动加锁。

---

## 九、Java 21 虚拟线程（Virtual Threads）

### 什么是虚拟线程

JDK 19 引入、**JDK 21 正式发布**的轻量级线程（Project Loom），由 JVM 调度而不是操作系统调度。

```java
// 启动虚拟线程
Thread virtualThread = Thread.ofVirtual().start(() -> {
    System.out.println("virtual thread running");
});

// 或使用工厂
Thread.ofVirtual().name("vt-").start(() -> doWork());

// 也可搭配线程池
ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();
executor.submit(() -> doWork());
```

### 虚拟线程 vs 平台线程

| 维度 | 平台线程（传统 Thread）| 虚拟线程 |
|---|---|---|
| 实现 | 1:1 映射到 OS 内核线程 | M:N 映射到少量平台线程（Carrier）|
| 创建开销 | 大（MB 级栈）| 极小（KB 级栈）|
| 数量限制 | 千级别 | 百万级 |
| 调度者 | OS 内核 | JVM |
| 阻塞代价 | 阻塞 OS 线程 | 释放 Carrier，调度其他虚拟线程 |

**通俗理解**：平台线程像专用通道（一辆车占一个车道），虚拟线程像共享通道（很多车共用一个车道，堵车时换车道）。

### 优缺点

**优点**：
- 显著提升**高并发 IO 密集型**场景的吞吐量
- 写法和传统 Thread 一致，无需改业务代码
- 适合 Web 服务器、网关、微服务等高并发服务

**缺点 / 注意事项**：
- **不适用于 CPU 密集型**（虚拟线程多了会无意义切换）
- **不要用 synchronized**：JVM 在 synchronized 内不会卸载虚拟线程，会 pinned 到平台线程上，反而浪费资源；改用 `ReentrantLock`
- **谨慎使用 ThreadLocal**：百万虚拟线程可能内存爆炸
- 旧代码库的反射、JNI 等需测试

### 实践建议

- 新项目（Spring Boot 3.2+、Tomcat 10.1+）已原生支持虚拟线程
- 启动参数 `-Djdk.tracePinnedThreads=short` 可排查 pinned 问题
- 替代异步回调的另一种方案（同步写法 + 虚拟线程 = 异步效果）

---

## 十、面试高频速记

| 主题 | 核心要点 |
|---|---|
| **JMM** | 主存+工作内存，三性（原子/可见/有序），happens-before 不是时间序是可见性 |
| **volatile** | 内存屏障，可见+有序但不原子 |
| **synchronized** | monitor 锁，可重入，锁升级（偏向→轻量→重量）|
| **ReentrantLock** | 可重入+AQS，可中断/公平/多Condition |
| **ThreadLocal** | 线程副本，弱key强value，必 try-finally remove |
| **线程池** | 7参数，4拒绝策略，CPU/IO 线程数公式 |
| **CAS/ABA** | 乐观锁思想，ABA 用版本号或 AtomicStampedReference |
| **AQS** | state + CLH 队列 + 模板方法，独占/共享两种模式 |
| **死锁** | 4 必要条件，按序加锁，tryLock 避免 |
| **虚拟线程** | M:N 调度，高并发 IO 场景，不用 synchronized、慎用 ThreadLocal |

