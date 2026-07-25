# artifacts.md — 制品解析(ANR trace / tombstone / dropbox)

制品是 logcat 之外的**结构化取证文件**:单文件、无时间轴,按各自格式解析。
对 ANR/native crash,**制品才是主证据**,logcat 里的 `am_anr`/`tombstoned` 只是入口线索。
证据指针指向**制品 `文件:行号`**(与 logcat 指针同等,R1/R11)。

## 定位(路径不写死)
不同项目落盘位置不同,但**文件夹名是原生的**,按原生名递归查找:
`find <日志根> -type d \( -name anr -o -name tombstones -o -name dropbox \)`。
先确认存在再纳入取证范围(S1)。

## ANR trace(`/data/anr/traces.txt` 或 `anr/anr_*`)
关键结构,按序看:
1. **头部**:进程名/pid、ANR 原因(Input dispatching timed out / Broadcast / Service)、
   **CPU 负载快照**(判断是全局卡还是单进程卡)。
2. **主线程(`"main"` tid=1)栈**:栈顶就是卡点。看是在:等锁(`- waiting to lock <addr> held by tid=N`)、
   binder 等待(`BinderProxy.transactNative`)、还是 IO/sleep。
3. **锁持有链**:顺着"held by tid=N"找到持锁线程,看它又卡在哪——**死锁/长事务的根因在链的末端**。
4. 提取:卡点方法、锁地址、持锁线程的栈。以 `anr文件:行号` 入账,与时间线并列。

## tombstone(`tombstones/tombstone_NN`)
1. **abort message**(若有):最直接的原因(assert 失败/CHECK/自定义 abort)。
2. **signal**:SIGSEGV(段错误)/SIGABRT(主动 abort)/SIGBUS 等 + fault addr。
3. **backtrace**:`#00` 起的调用栈,栈顶帧是崩溃点;看 so 名与偏移。
4. **寄存器/memory near**:辅助判断空指针(addr≈0)还是野指针/越界。
5. 提取:signal、栈顶帧(库+符号+偏移)、abort message。以 `tombstone文件:行号` 入账。

## dropbox(`dropbox/*@*.txt`)
系统崩溃/ANR 的持久化副本(`system_app_crash`、`system_server_anr` 等),内容多为上面两类的封装。
用途:logcat 已轮转丢失时的补充来源;取其中的 exception 类型 + 栈首帧。

## 与红线的关系
- 制品行同样回指原始 `文件:行号`(R11)。
- 制品"未见某项"仍受 R13 约束——但制品一般完整,不像 logcat 有 chatty/丢行;若制品被截断需注明。
- 源码开关关时,制品给出的栈/符号可支撑**形态 B**结论(定位到方法/组件),无需源码即可闭合。
