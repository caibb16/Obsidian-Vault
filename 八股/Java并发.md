### 线程的生命周期与状态
- NEW: 初始状态，线程被创建出来但没有被调用 `start()`。
- RUNNABLE: 运行状态，线程被调用了 `start()` 等待运行的状态。
- BLOCKED：阻塞状态，需要等待锁释放。
- WAITING：等待状态，表示该线程需要等待其他线程做出一些特定动作（通知或中断）。
- TIMED_WAITING：超时等待状态，可以在指定的时间后自行返回而不是像 WAITING 那样一直等待。
- TERMINATED：终止状态，表示该线程已经运行完毕。
![[Pasted image 20260906202324.png]]
### Thread#sleep() 方法和 Object#wait() 方法对比

**共同点**：两者都可以暂停线程的执行。

**区别**：

- **`sleep()` 方法没有释放锁，而 `wait()` 方法释放了锁**。
- `wait()` 通常被用于线程间交互/通信，`sleep()` 通常被用于暂停执行。
- `wait()` 方法被调用后，线程不会自动苏醒，需要别的线程调用同一个对象上的 `notify()` 或者 `notifyAll()` 方法。`sleep()` 方法执行完成后，线程会自动苏醒，或者也可以使用 `wait(long timeout)` 超时后线程会自动苏醒。
- `sleep()` 是 `Thread` 类的静态本地方法，`wait()` 则是 `Object` 类的本地方法。
### 死锁
代码模拟如下：
```java
public class DeadLockDemo {
    private static Object resource1 = new Object();//资源 1
    private static Object resource2 = new Object();//资源 2

    public static void main(String[] args) {
        new Thread(() -> {
            synchronized (resource1) {
                System.out.println(Thread.currentThread() + "get resource1");
                try {
                    Thread.sleep(1000);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                System.out.println(Thread.currentThread() + "waiting get resource2");
                synchronized (resource2) {
                    System.out.println(Thread.currentThread() + "get resource2");
                }
            }
        }, "线程 1").start();

        new Thread(() -> {
            synchronized (resource2) {
                System.out.println(Thread.currentThread() + "get resource2");
                try {
                    Thread.sleep(1000);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                System.out.println(Thread.currentThread() + "waiting get resource1");
                synchronized (resource1) {
                    System.out.println(Thread.currentThread() + "get resource1");
                }
            }
        }, "线程 2").start();
    }
}
```
Output:
```plain
Thread[线程 1,5,main]get resource1
Thread[线程 2,5,main]get resource2
Thread[线程 1,5,main]waiting get resource2
Thread[线程 2,5,main]waiting get resource1
```
### ThreadLocal
通常创建的变量可以被多个线程访问和修改，为了解决多线程环境下的数据竞争和安全问题，让每个线程有自己的专属本地变量，引入`ThreadLocal`类，允许每个线程绑定自己的值。
当你创建一个 `ThreadLocal` 变量时，每个访问该变量的线程都会拥有一个独立的副本。

### JMM
**JMM（Java 内存模型）** 是 JVM 规范定义的抽象规范，描述了线程之间共享变量的访问规则，以及变量在内存中存储和读取的底层细节，用于屏蔽不同硬件/OS 的内存访问差异，保证 Java 并发程序跨平台的一致性。

**两大内存区域：**
- **主内存**：所有线程共享的变量存储区域。
- **工作内存**：每个线程私有的副本空间（类比 CPU 缓存+寄存器）。线程对变量的读写都在工作内存中完成，不能直接操作主内存。

**三大特性：**
- **原子性**：一组操作不可中断。`synchronized` / `Lock` / `Atomic*`。
- **可见性**：一个线程修改后，其他线程能立即看到。`volatile` / `synchronized` / `final`。
- **有序性**：禁止指令重排序导致逻辑错乱。`volatile` / `synchronized` / happens-before。

**happens-before 原则（核心判定准则）：**
A happens-before B ⇒ A 的所有修改对 B 都可见。
单线程内happens-before天然成立，多线程下happens-before需要程序员显式建立。
- 程序顺序规则：同一线程内，前面的操作 happens-before 后面的操作。
- 锁规则：`unlock` happens-before 后续的 `lock`。
- volatile 规则：写 volatile happens-before 后续读 volatile。
- 线程启动规则：`Thread.start()` happens-before 线程内任意操作。
- 线程终止规则：线程内所有操作 happens-before 其他线程 `join()` 返回。
- 传递性：A hb B，B hb C ⇒ A hb C。

**volatile 底层实现：**
通过**内存屏障（Memory Barrier）** 防止重排序并保证可见性。
- 写 volatile 后插入 StoreStore + StoreLoad 屏障，强制立即刷回主内存。
- 读 volatile 前插入 LoadLoad + LoadStore 屏障，强制从主内存重新加载。
- volatile **保证可见性和有序性，但不保证原子性**（如 `i++` 仍需用 `AtomicInteger`）。
