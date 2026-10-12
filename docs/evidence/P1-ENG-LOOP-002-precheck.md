# P1-ENG-LOOP-002 — 阶段 B 只读预检读数（B-pre）

> 本文件是同名提案「B-pre答复落实（2026-10-07）」§3 的产出位置。另含同名提案「补核答复落实」§3 指定的「只读补核原始读数与逐维度用量」一节（B0a 原节与接受节不覆盖）；B0b/B1/Play 未执行、未授权。读数是事实记录，不是门值、verdict 或 AC 满足声明；B-main 维度确定与 N-3 逐码处置由接受角色核清后另行申请。

## B0a原始读数与逐维度用量

- 轮次：`B0a只读预检`（Implementation，Opus 子代理，supervisor 派发；Dispatch-Id 见本批提交尾注）。
- 授权来源：`docs/authorizations.md` 2026-10-07「P1-ENG-LOOP-002 — 用户首签 N-2 B-pre 只读预检、(h) 正式用户验证、(j) 不启用 5060 备用臂、(k) 本人经 SSH 启动板上服务」信封（只读 SSH ≤ 2 次、每次 ≤ 10 min；ping 累计 ≤ 10 包、单次 ≤ 5 包；其余维度 0）。
- 合同：同名提案「B-pre答复落实」§3 第 1–4 条与停止条件；冻结操作单 `docs/evidence/P1-ENG-LOOP-002-play-ops.md` 只读引用其 §2 清单，未改。

### 1. 本机、目标设备与 SSH 别名来源

| 项 | 读数 | 来源 |
|---|---|---|
| 本机 | `MacBook-Air.local`，macOS 26.6.2（25G83），arm64；即 Unity 主机（MacBook Air） | 本机 `hostname`、`sw_vers`、`uname -m` |
| SSH 别名 | `Host Jetson`：HostName `100.100.100.100`（Tailscale 地址）、User `jetson`、端口 22、IdentityFile 为既有本机私钥路径（未读、未复制、未存键） | 本机 `~/.ssh/config` 只读；`ssh -G Jetson` 有效配置（`ssh -G` 不连接） |
| 目标设备 | 板 hostname `jetson`，`Linux 6.8.12-1021-tegra aarch64`，登录用户 `jetson` | 下文原始 stdout R01 |
| SSH 调用形式 | `ssh -o BatchMode=yes -o ConnectTimeout=20 Jetson 'timeout 420 bash -s' < remote.sh`：脚本经 stdin 传入远端 shell 执行，板上不落脚本文件；`-o` 只作用于本次调用，未改 `~/.ssh/config` 或任何系统/沙箱设置 | 本机命令 |

### 2. 命令原文

本机 ping（Mac → Jetson，Tailscale 地址由 `ssh -G Jetson` 运行时解析）：

```
H=$(ssh -G Jetson 2>/dev/null | awk '/^hostname /{print $2}')
ping -c 5 -i 1 -t 15 "$H"
```

远端只读脚本 `remote.sh`（逐字；全部为读操作：`date/hostname/uname/id/python3 --version/df/free/ss -ltn/pgrep/ls/find -printf/du`；未运行 llama `--version`、未 import 部署包、未加载模型、未构建/测试、未发 HTTP）：

```bash
set +e
sec() { printf '\n=== %s\n' "$1"; }
sec "R00 board_utc_start"; date -u +%FT%TZ
sec "R01 hostname/uname/user"; hostname; uname -srm; id -un
sec "R02 python3"; command -v python3; python3 --version 2>&1; echo "rc=$?"
sec "R03 df -B1 (/ and HOME)"; df -B1 / "$HOME" 2>&1; echo "rc=$?"
sec "R04 df -h (all)"; df -h 2>&1; echo "rc=$?"
sec "R05 free -b"; free -b 2>&1; echo "rc=$?"
sec "R06 ss -ltn"; ss -ltn 2>&1; echo "rc=$?"
sec "R07 residual process names (read-only pgrep)"; pgrep -a -f 'llama-server|language_serve' 2>&1; echo "rc=$?"
sec "R08 ls -la ~/eng-jet"; ls -la "$HOME/eng-jet" 2>&1; echo "rc=$?"
sec "R09 existing deploy code dir ~/eng-jet/code (depth<=2)"; ls -ld "$HOME/eng-jet/code" 2>&1; find "$HOME/eng-jet/code" -maxdepth 2 -printf '%y %s %p\n' 2>&1 | head -n 80; echo "rc=$?"
sec "R10 planned new deploy root candidates (existence only)"; ls -ld "$HOME"/eng-loop2* "$HOME"/eng-jet/eng-loop2* "$HOME"/eng-jet/*loop* 2>&1; echo "rc=$?"
sec "R11 all *.gguf / *.gguf.part under ~/eng-jet (type bytes mtime path)"; find "$HOME/eng-jet" -xdev \( -name '*.gguf' -o -name '*.gguf.part' \) -printf '%y %s %TY-%Tm-%TdT%TH:%TM:%.2TS %p\n' 2>&1; echo "rc=$?"
sec "R12 all llama-server under ~/eng-jet"; find "$HOME/eng-jet" -xdev -name 'llama-server' -printf '%y %s %m %p %l\n' 2>&1; echo "rc=$?"
sec "R13 build bin dirs"; for d in "$HOME"/eng-jet/stageb-build-*/build/bin; do ls -la "$d" 2>&1; done; echo "rc=$?"
sec "R14 C2 diagnostic dirs (depth<=3)"; find "$HOME/eng-jet/stageb-c2-diagnostic" "$HOME/eng-jet/stageb-c2-json-diagnostic" -maxdepth 3 -printf '%y %s %p\n' 2>&1 | head -n 120; echo "rc=$?"
sec "R15 stageb-transfer-* dirs gguf/archive"; ls -la "$HOME"/eng-jet/stageb-transfer-* 2>&1 | grep -E 'gguf|archive|total|^d' ; echo "rc=$?"
sec "R16 du -sb ~/eng-jet (read-only)"; du -sb "$HOME/eng-jet" 2>&1 | tail -n 3; echo "rc=$?"
sec "R99 board_utc_end"; date -u +%FT%TZ
```

### 3. 尝试逐次记录（含起止、退出码与墙钟）

| # | 动作 | 方向 | 起（UTC） | 止（UTC） | 墙钟 | 退出码 | 包数 / 结果 |
|---|---|---|---|---|---|---|---|
| P1 | `ping -c 5` | MacBook Air → Jetson（`100.100.100.100`） | 2026-10-07T03:56:35Z | 2026-10-07T03:56:39Z | ≈ 4 s | 0 | 发 5 / 收 5，丢包 0.0% |
| S1 | 只读 SSH 第 1 次（唯一一次） | MacBook Air → Jetson（`Host Jetson`） | 2026-10-07T03:56:44Z | 2026-10-07T03:56:45Z | 1.218 s（本机 epoch 差） | 0 | 成功；stdout 11,885 B、stderr 0 B；板端 `date -u` 起止均 2026-10-07T03:56:45Z |

未发生失败尝试或重试；第二次 SSH 未使用。

### 4. 原始输出

P1 ping stdout（stderr 为空）：

```
PING 100.100.100.100 (100.100.100.100): 56 data bytes
64 bytes from 100.100.100.100: icmp_seq=0 ttl=64 time=46.681 ms
64 bytes from 100.100.100.100: icmp_seq=1 ttl=64 time=12.741 ms
64 bytes from 100.100.100.100: icmp_seq=2 ttl=64 time=8.784 ms
64 bytes from 100.100.100.100: icmp_seq=3 ttl=64 time=14.539 ms
64 bytes from 100.100.100.100: icmp_seq=4 ttl=64 time=14.827 ms

--- 100.100.100.100 ping statistics ---
5 packets transmitted, 5 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 8.784/19.514/46.681/13.753 ms
```

S1 SSH stdout（逐字；stderr 为空，0 B）：

```

=== R00 board_utc_start
2026-10-07T03:56:45Z

=== R01 hostname/uname/user
jetson
Linux 6.8.12-1021-tegra aarch64
jetson

=== R02 python3
/usr/bin/python3
Python 3.12.3
rc=0

=== R03 df -B1 (/ and HOME)
Filesystem        1B-blocks        Used    Available Use% Mounted on
/dev/nvme0n1p1 249326301184 76443365376 160143331328  33% /
/dev/nvme0n1p1 249326301184 76443365376 160143331328  33% /
rc=0

=== R04 df -h (all)
Filesystem       Size  Used Avail Use% Mounted on
/dev/nvme0n1p1   233G   72G  150G  33% /
tmpfs            3.7G  140K  3.7G   1% /dev/shm
tmpfs            1.5G  2.3M  1.5G   1% /run
tmpfs            5.0M   12K  5.0M   1% /run/lock
efivarfs         256K   36K  221K  14% /sys/firmware/efi/efivars
/dev/nvme0n1p10   63M  110K   63M   1% /boot/efi
tmpfs            749M  100K  749M   1% /run/user/1000
rc=0

=== R05 free -b
               total        used        free      shared  buff/cache   available
Mem:      7849054208  1849991168  2258702336     2658304  3979407360  5999063040
Swap:              0           0           0
rc=0

=== R06 ss -ltn
State  Recv-Q Send-Q  Local Address:Port  Peer Address:PortProcess
LISTEN 0      4096       127.0.0.54:53         0.0.0.0:*          
LISTEN 0      4096   100.100.100.100:46273      0.0.0.0:*          
LISTEN 0      4096          0.0.0.0:22         0.0.0.0:*          
LISTEN 0      4096    127.0.0.53%lo:53         0.0.0.0:*          
LISTEN 0      4096             [::]:22            [::]:*          
rc=0

=== R07 residual process names (read-only pgrep)
rc=1

=== R08 ls -la ~/eng-jet
total 76
drwxrwxr-x 19 jetson jetson 4096 Oct  6 17:31 .
drwxr-x--- 17 jetson jetson 4096 Oct  4 23:33 ..
drwxrwxr-x  2 jetson jetson 4096 Oct  2 19:37 bundle
drwxrwxr-x  7 jetson jetson 4096 Oct  2 17:13 code
drwxrwxr-x  5 jetson jetson 4096 Oct  5 01:27 edgellm-venv
drwxrwxr-x  3 jetson jetson 4096 Oct  2 17:13 frames
drwxrwxr-x  8 jetson jetson 4096 Oct  3 00:50 home
drwxrwxr-x  9 jetson jetson 4096 Oct  3 12:29 logs
drwxrwxr-x  5 jetson jetson 4096 Oct  3 00:49 results
drwxrwxr-x  4 jetson jetson 4096 Oct  3 12:29 runtime
drwx------  5 jetson jetson 4096 Oct  5 18:03 stageb-3b-diagnostic-20261005T220121Z
drwx------ 12 jetson jetson 4096 Oct  5 22:28 stageb-base-prompt
drwx------  5 jetson jetson 4096 Oct  4 23:33 stageb-build-20261005T033318Z
drwx------  3 jetson jetson 4096 Oct  6 13:44 stageb-c2-diagnostic
drwx------  3 jetson jetson 4096 Oct  6 17:31 stageb-c2-json-diagnostic
drwx------  6 jetson jetson 4096 Oct  5 01:27 stageb-install-20261005T052742Z
drwx------  2 jetson jetson 4096 Oct  4 18:53 stageb-transfer-20261004T225001Z
drwxrwxr-x  6 jetson jetson 4096 Oct  2 19:40 sysvenv
drwxr-xr-x  3 jetson jetson 4096 Oct  2 19:40 wheels
rc=0

=== R09 existing deploy code dir ~/eng-jet/code (depth<=2)
drwxrwxr-x 7 jetson jetson 4096 Oct  2 17:13 /home/jetson/eng-jet/code
d 4096 /home/jetson/eng-jet/code
d 4096 /home/jetson/eng-jet/code/config
f 1197 /home/jetson/eng-jet/code/config/det-assoc-v1.models.json
d 4096 /home/jetson/eng-jet/code/outputs
d 4096 /home/jetson/eng-jet/code/outputs/eng-det
d 4096 /home/jetson/eng-jet/code/docs
d 4096 /home/jetson/eng-jet/code/docs/evidence
d 4096 /home/jetson/eng-jet/code/tools
d 4096 /home/jetson/eng-jet/code/tools/__pycache__
d 4096 /home/jetson/eng-jet/code/tools/eng_jet
f 0 /home/jetson/eng-jet/code/tools/__init__.py
d 4096 /home/jetson/eng-jet/code/controller
f 98839 /home/jetson/eng-jet/code/controller/track_loop.py
d 4096 /home/jetson/eng-jet/code/controller/__pycache__
f 1456 /home/jetson/eng-jet/code/controller/sensor_protocol.py
f 7569 /home/jetson/eng-jet/code/controller/pose_gmc.py
f 23779 /home/jetson/eng-jet/code/controller/rate3_protocol.py
f 28165 /home/jetson/eng-jet/code/controller/qualification_protocol.py
f 32851 /home/jetson/eng-jet/code/controller/reanchor.py
f 16116 /home/jetson/eng-jet/code/controller/world_estimate.py
f 1406 /home/jetson/eng-jet/code/controller/body_entry.py
f 27928 /home/jetson/eng-jet/code/controller/resident_core.py
f 25686 /home/jetson/eng-jet/code/controller/det_assoc_tracker.py
f 3825 /home/jetson/eng-jet/code/controller/geolocate.py
f 23171 /home/jetson/eng-jet/code/controller/rate2_protocol.py
f 69 /home/jetson/eng-jet/code/controller/__init__.py
f 1465 /home/jetson/eng-jet/code/controller/gimbal_entry.py
f 2999 /home/jetson/eng-jet/code/controller/tracking_entry.py
f 19186 /home/jetson/eng-jet/code/controller/body_planner.py
f 28561 /home/jetson/eng-jet/code/controller/standoff_planner.py
f 20377 /home/jetson/eng-jet/code/controller/trackers.py
f 20403 /home/jetson/eng-jet/code/controller/run_log.py
f 9175 /home/jetson/eng-jet/code/controller/scenario_tether.py
f 2297 /home/jetson/eng-jet/code/controller/protocol.py
rc=0

=== R10 planned new deploy root candidates (existence only)
ls: cannot access '/home/jetson/eng-loop2*': No such file or directory
ls: cannot access '/home/jetson/eng-jet/eng-loop2*': No such file or directory
ls: cannot access '/home/jetson/eng-jet/*loop*': No such file or directory
rc=2

=== R11 all *.gguf / *.gguf.part under ~/eng-jet (type bytes mtime path)
f 1107409952 2026-10-04T18:53:34 /home/jetson/eng-jet/stageb-transfer-20261004T225001Z/Qwen3VL-2B-Instruct-Q4_K_M.gguf
f 819394848 2026-10-04T18:53:44 /home/jetson/eng-jet/stageb-transfer-20261004T225001Z/mmproj-Qwen3VL-2B-Instruct-F16.gguf
f 1107409952 2026-10-06T13:45:03 /home/jetson/eng-jet/stageb-c2-diagnostic/20261006T174450Z/model/c2-merged-Q4_K_M.gguf
f 723869 2026-10-03T13:47:54 /home/jetson/eng-jet/stageb-build-20261005T033318Z/src/ggml-org-llama.cpp-836d571/models/ggml-vocab-llama-spm.gguf
f 627549 2026-10-03T13:47:54 /home/jetson/eng-jet/stageb-build-20261005T033318Z/src/ggml-org-llama.cpp-836d571/models/ggml-vocab-bert-bge.gguf
f 7818140 2026-10-03T13:47:54 /home/jetson/eng-jet/stageb-build-20261005T033318Z/src/ggml-org-llama.cpp-836d571/models/ggml-vocab-llama-bpe.gguf
f 1720710 2026-10-03T13:47:54 /home/jetson/eng-jet/stageb-build-20261005T033318Z/src/ggml-org-llama.cpp-836d571/models/ggml-vocab-refact.gguf
f 5928681 2026-10-03T13:47:54 /home/jetson/eng-jet/stageb-build-20261005T033318Z/src/ggml-org-llama.cpp-836d571/models/ggml-vocab-qwen2.gguf
f 1340998 2026-10-03T13:47:54 /home/jetson/eng-jet/stageb-build-20261005T033318Z/src/ggml-org-llama.cpp-836d571/models/ggml-vocab-baichuan.gguf
f 6821877 2026-10-03T13:47:54 /home/jetson/eng-jet/stageb-build-20261005T033318Z/src/ggml-org-llama.cpp-836d571/models/ggml-vocab-nomic-bert-moe.gguf
f 10874545 2026-10-03T13:47:54 /home/jetson/eng-jet/stageb-build-20261005T033318Z/src/ggml-org-llama.cpp-836d571/models/ggml-vocab-command-r.gguf
f 1766807 2026-10-03T13:47:54 /home/jetson/eng-jet/stageb-build-20261005T033318Z/src/ggml-org-llama.cpp-836d571/models/ggml-vocab-gpt-2.gguf
f 15776467 2026-10-03T13:47:54 /home/jetson/eng-jet/stageb-build-20261005T033318Z/src/ggml-org-llama.cpp-836d571/models/ggml-vocab-gemma-4.gguf
f 726019 2026-10-03T13:47:54 /home/jetson/eng-jet/stageb-build-20261005T033318Z/src/ggml-org-llama.cpp-836d571/models/ggml-vocab-phi-3.gguf
f 1771393 2026-10-03T13:47:54 /home/jetson/eng-jet/stageb-build-20261005T033318Z/src/ggml-org-llama.cpp-836d571/models/ggml-vocab-mpt.gguf
f 4825676 2026-10-03T13:47:54 /home/jetson/eng-jet/stageb-build-20261005T033318Z/src/ggml-org-llama.cpp-836d571/models/ggml-vocab-aquila.gguf
f 3970167 2026-10-03T13:47:54 /home/jetson/eng-jet/stageb-build-20261005T033318Z/src/ggml-org-llama.cpp-836d571/models/ggml-vocab-deepseek-llm.gguf
f 5928682 2026-10-03T13:47:54 /home/jetson/eng-jet/stageb-build-20261005T033318Z/src/ggml-org-llama.cpp-836d571/models/ggml-vocab-qwen35.gguf
f 1719346 2026-10-03T13:47:54 /home/jetson/eng-jet/stageb-build-20261005T033318Z/src/ggml-org-llama.cpp-836d571/models/ggml-vocab-starcoder.gguf
f 1156067 2026-10-03T13:47:54 /home/jetson/eng-jet/stageb-build-20261005T033318Z/src/ggml-org-llama.cpp-836d571/models/ggml-vocab-deepseek-coder.gguf
f 2287728 2026-10-03T13:47:54 /home/jetson/eng-jet/stageb-build-20261005T033318Z/src/ggml-org-llama.cpp-836d571/models/ggml-vocab-falcon.gguf
f 1771431 2026-10-03T13:47:54 /home/jetson/eng-jet/stageb-build-20261005T033318Z/src/ggml-org-llama.cpp-836d571/models/ggml-vocab-gpt-neox.gguf
rc=0

=== R12 all llama-server under ~/eng-jet
f 72424 775 /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/llama-server 
rc=0

=== R13 build bin dirs
total 76792
drwxrwxr-x  2 jetson jetson     4096 Oct  5 00:02 .
drwx------ 14 jetson jetson     4096 Oct  4 23:33 ..
lrwxrwxrwx  1 jetson jetson       17 Oct  4 23:33 libggml-base.so -> libggml-base.so.0
lrwxrwxrwx  1 jetson jetson       22 Oct  4 23:33 libggml-base.so.0 -> libggml-base.so.0.25.3
-rwxrwxr-x  1 jetson jetson   877152 Oct  4 23:33 libggml-base.so.0.25.3
lrwxrwxrwx  1 jetson jetson       16 Oct  4 23:34 libggml-cpu.so -> libggml-cpu.so.0
lrwxrwxrwx  1 jetson jetson       21 Oct  4 23:34 libggml-cpu.so.0 -> libggml-cpu.so.0.25.3
-rwxrwxr-x  1 jetson jetson  1068776 Oct  4 23:34 libggml-cpu.so.0.25.3
lrwxrwxrwx  1 jetson jetson       17 Oct  4 23:57 libggml-cuda.so -> libggml-cuda.so.0
lrwxrwxrwx  1 jetson jetson       22 Oct  4 23:57 libggml-cuda.so.0 -> libggml-cuda.so.0.25.3
-rwxrwxr-x  1 jetson jetson 61451472 Oct  4 23:57 libggml-cuda.so.0.25.3
lrwxrwxrwx  1 jetson jetson       12 Oct  4 23:57 libggml.so -> libggml.so.0
lrwxrwxrwx  1 jetson jetson       17 Oct  4 23:57 libggml.so.0 -> libggml.so.0.25.3
-rwxrwxr-x  1 jetson jetson    78152 Oct  4 23:57 libggml.so.0.25.3
lrwxrwxrwx  1 jetson jetson       20 Oct  5 00:01 libllama-common.so -> libllama-common.so.0
lrwxrwxrwx  1 jetson jetson       24 Oct  5 00:01 libllama-common.so.0 -> libllama-common.so.0.5.0
-rwxrwxr-x  1 jetson jetson  5433840 Oct  5 00:01 libllama-common.so.0.5.0
-rwxrwxr-x  1 jetson jetson  3542712 Oct  5 00:02 libllama-server-impl.so
lrwxrwxrwx  1 jetson jetson       13 Oct  4 23:58 libllama.so -> libllama.so.0
lrwxrwxrwx  1 jetson jetson       17 Oct  4 23:58 libllama.so.0 -> libllama.so.0.5.0
-rwxrwxr-x  1 jetson jetson  4542696 Oct  4 23:58 libllama.so.0.5.0
lrwxrwxrwx  1 jetson jetson       12 Oct  5 00:00 libmtmd.so -> libmtmd.so.0
lrwxrwxrwx  1 jetson jetson       16 Oct  5 00:00 libmtmd.so.0 -> libmtmd.so.0.5.0
-rwxrwxr-x  1 jetson jetson  1830624 Oct  5 00:00 libmtmd.so.0.5.0
-rwxrwxr-x  1 jetson jetson    72424 Oct  5 00:02 llama-server
rc=0

=== R14 C2 diagnostic dirs (depth<=3)
d 4096 /home/jetson/eng-jet/stageb-c2-diagnostic
d 4096 /home/jetson/eng-jet/stageb-c2-diagnostic/20261006T174450Z
d 4096 /home/jetson/eng-jet/stageb-c2-diagnostic/20261006T174450Z/config
d 4096 /home/jetson/eng-jet/stageb-c2-diagnostic/20261006T174450Z/config/yolo
d 4096 /home/jetson/eng-jet/stageb-c2-diagnostic/20261006T174450Z/config/mpl
d 4096 /home/jetson/eng-jet/stageb-c2-diagnostic/20261006T174450Z/cache
d 4096 /home/jetson/eng-jet/stageb-c2-diagnostic/20261006T174450Z/cache/cuda
d 4096 /home/jetson/eng-jet/stageb-c2-diagnostic/20261006T174450Z/cache/llama
d 4096 /home/jetson/eng-jet/stageb-c2-diagnostic/20261006T174450Z/cache/hf
d 4096 /home/jetson/eng-jet/stageb-c2-diagnostic/20261006T174450Z/model
f 1107409952 /home/jetson/eng-jet/stageb-c2-diagnostic/20261006T174450Z/model/c2-merged-Q4_K_M.gguf
d 4096 /home/jetson/eng-jet/stageb-c2-diagnostic/20261006T174450Z/tmp
d 4096 /home/jetson/eng-jet/stageb-c2-json-diagnostic
d 4096 /home/jetson/eng-jet/stageb-c2-json-diagnostic/20261006T213111Z
d 4096 /home/jetson/eng-jet/stageb-c2-json-diagnostic/20261006T213111Z/attempt-1
d 4096 /home/jetson/eng-jet/stageb-c2-json-diagnostic/20261006T213111Z/attempt-1/config
d 4096 /home/jetson/eng-jet/stageb-c2-json-diagnostic/20261006T213111Z/attempt-1/cache
d 4096 /home/jetson/eng-jet/stageb-c2-json-diagnostic/20261006T213111Z/attempt-1/tmp
rc=0

=== R15 stageb-transfer-* dirs gguf/archive
total 2423544
drwx------  2 jetson jetson       4096 Oct  4 18:53 .
drwxrwxr-x 19 jetson jetson       4096 Oct  6 17:31 ..
-rw-r--r--  1 jetson jetson   37831966 Oct  4 18:53 archive.tar.gz
-rw-r--r--  1 jetson jetson  819394848 Oct  4 18:53 mmproj-Qwen3VL-2B-Instruct-F16.gguf
-rw-r--r--  1 jetson jetson 1107409952 Oct  4 18:53 Qwen3VL-2B-Instruct-Q4_K_M.gguf
rc=0

=== R16 du -sb ~/eng-jet (read-only)
10653045123	/home/jetson/eng-jet
rc=0

=== R99 board_utc_end
2026-10-07T03:56:45Z
```

### 5. 事实摘录（§3 第 2 条清单；源目录与计划新部署根分列）

路径中的 UTC 目录名、字节数均取自上文原始 stdout 对应 R 号，此处只做摘录，不是新读数；sha 未读（AC-16 板端 sha 核实留 B-main）。

| 清单项 | 读数 | 原始 |
|---|---|---|
| C2 合并 Q4_K_M GGUF | 存在；普通文件；1,107,409,952 B；`~/eng-jet/stageb-c2-diagnostic/<UTC>/model/c2-merged-Q4_K_M.gguf`（全 `~/eng-jet` 下唯一名含 `c2` 的 GGUF） | R11、R14 |
| 官方 base Q4_K_M GGUF（同字节数，**不是** C2） | 存在；1,107,409,952 B；`~/eng-jet/stageb-transfer-<UTC>/Qwen3VL-2B-Instruct-Q4_K_M.gguf` | R11、R15 |
| mmproj F16 | 存在；普通文件；819,394,848 B；`~/eng-jet/stageb-transfer-<UTC>/mmproj-Qwen3VL-2B-Instruct-F16.gguf`（全 `~/eng-jet` 下唯一 mmproj） | R11、R15 |
| llama-server 二进制 | 存在；普通文件、权限 775；72,424 B；`~/eng-jet/stageb-build-<UTC>/build/bin/llama-server`（全 `~/eng-jet` 下唯一）；同目录另有 `libllama-server-impl.so`、`libllama.so.*`、`libmtmd.so.*`、`libggml*.so.*`（含 `libggml-cuda.so.0.25.3` 61,451,472 B） | R12、R13 |
| 既有部署目录（源，JET-001） | `~/eng-jet/code` 存在；深度 ≤ 2 清单中**无** `tools/language_serve.py`、`tools/eng_loop2/`、`tools/eng_sft/`、`controller/language_bridge.py`、`controller/language_selector.py`，即不含本项 `config/p1-eng-loop-002-board-deploy.json` 闭集 | R08、R09 |
| 计划新部署根（`$BOARD_ROOT`） | 合同与操作单未给具体路径（操作单「以 B0a 读数为准」）；只核了候选名 `~/eng-loop2*`、`~/eng-jet/eng-loop2*`、`~/eng-jet/*loop*`：**均不存在**；未创建 | R10 |
| 系统 `python3`（`$BOARD_PY` 候选） | `/usr/bin/python3`，Python 3.12.3；未 import 任何部署模块 | R02 |
| `df` | `/`（`/dev/nvme0n1p1`，`$HOME` 同盘）：总 249,326,301,184 B、已用 76,443,365,376 B、可用 160,143,331,328 B（33%） | R03、R04 |
| `free` | 内存总 7,849,054,208 B、used 1,849,991,168 B、available 5,999,063,040 B；Swap 0 | R05 |
| `ss -ltn` | 监听：`0.0.0.0:22`、`[::]:22`、`127.0.0.53%lo:53`、`127.0.0.54:53`、`100.100.100.100:46273`；**18081 未监听**；无 llama-server/language_serve 进程（`pgrep` rc=1） | R06、R07 |
| `~/eng-jet` 占用 | `du -sb` 10,653,045,123 B | R16 |
| Tailscale 往返 | 5/5、丢包 0.0%、min/avg/max/stddev = 8.784/19.514/46.681/13.753 ms | P1 |

### 6. 逐维度用量（对照 N-2 信封）

| 维度 | 上限 | 实际 | 余（只作差额，不是自动重试许可） |
|---|---:|---:|---:|
| 只读 SSH 次数（成功/失败/重试共账） | 2 | 1（S1 成功） | 1 |
| 单次 SSH 墙钟 | 10 min | S1 1.218 s | — |
| ping 包（单次 ≤ 5） | 累计 10 | 5（1 次运行） | 5 |
| 推理请求 | 0 | 0 | — |
| 板上写入（文件/目录/部署） | 0 | 0 | — |
| 服务启动 | 0 | 0 | — |
| 文件传输（scp/rsync/sftp） | 0 | 0 | — |
| HTTP（含 `/status`、`/health`） | 0 | 0 | — |
| scenario/session/run ID | 0 | 0 | — |
| Unity Play | 0 | 0 | — |
| 5060 / API / GPU / 下载 / 安装 / 云 | 0 | 0 | — |
| SSH/系统/沙箱设置修改、存键 | 不改 | 未改、未存 | — |

本机写入仅本证据文件（及会话 scratchpad 中的原始输出副本，不入仓）；未写 `runtime/`，未创建 scenario/session/run 目录。附带披露：SSH 登录会由板上系统自行记录登录日志（sshd/journald/wtmp），`ls`/`find`/`du` 可能按挂载选项更新目录访问时间；二者均非角色写入，未在板上创建或修改任何文件。

### 7. 未核 / UNKNOWN（原因）

- **Unity 主机 → 板服务 HTTP 可达性：未核**——零 HTTP；SSH/ping/ss 不证明服务端口可达，按合同留 B-main。
- **资产 sha256（GGUF/mmproj/llama-server）与 `llama-server --version`：未核**——按 §3 第 2 条留 B-main（AC-16）。字节数相同的官方 base Q4 与 C2 Q4 只能靠 sha 区分。
- **`100.100.100.100:46273` 监听者归属：UNKNOWN**——非特权 `ss -ltn` 不显示进程；`pgrep` 未见 llama-server/language_serve；端口不是旧服务 18081。未追加特权命令。
- **llama-server 对同目录共享库的实际动态依赖：未核**——只看到同目录 `.so` 文件名，未运行 `ldd`。
- **板时区：未读**——R11 的 mtime 为板本地时间，未用于任何判定。
- **系统 Python 3.12.3 能否运行部署闭集：未核**——未 import，按合同不做。

### 8. 停止条件逐项与交接受核清的观察点

停止条件逐项：链路/认证——成功；必需文件（C2 Q4、mmproj、llama-server）——均存在；读数不全——清单项全部取得（计划新部署根因合同未命名，只报候选名不存在）；残留监听/共享槽位——18081 未监听、无相关进程，`46273` 归属 UNKNOWN 见 §7；需改设置/写板/启动/HTTP/推理——未发生；上限——SSH 1/2、ping 5/10，未达；合同歧义——见下列观察点。成功取齐后按合同在 B0a 停下，不进入 B0b/B1/Play，不改冻结操作单。

供接受角色核清（只列事实与待定点，不自行解释合同）：

1. **`$BOARD_ROOT` 未命名**：板上没有本项部署根，既有 `~/eng-jet/code` 是 JET-001 的部署、不含本项闭集；B-main 的部署根路径、新建方式与磁盘口径需由接受/用户确定。
2. **同字节双 Q4**：官方 base Q4 与 C2 合并 Q4 字节数相同（1,107,409,952 B）；B-main 的 `--weights` 须按 JET 核清链以 sha 指定 C2 文件，不能按字节或文件名后缀选。
3. **llama-server 为薄可执行文件**（72,424 B），同目录有 `libllama-server-impl.so` 等共享库；冻结操作单 §3 第 4 步 `runtime_binary_sha256` 只列 `<llama-server>` 一个文件，是否需把同目录共享库纳入身份范围由接受裁定。
4. **`46273` 监听者归属 UNKNOWN**（见 §7），是否影响 B-main 服务端口选择或需用户本人确认，由接受判断。
5. **板端资源读数**（§5 `df`/`free`/`du`）可供 B-main 磁盘峰值、内存维度回填；swap 为 0。


## Acceptance B0a核清（2026-10-07）

本节只记接受结论与指针，§1–8原始记录不覆盖：已记录N-2用量在信封内（SSH1/2、1.218s；ping5/10；其余0）；§5摘录与§4原文一致。毫秒墙钟及stdout字节数是实现记录，未附本机epoch原值/独立原流，板端同秒date不能独立重算；不把此限制掩成实测复算。R07 rc1/R10 rc2分别表示无匹配进程/目录模式不匹配，不据SSH总rc0认定逐项通过。

五项观察点均已裁定或归用户；完整理由、§5.2确定计划/当前申请值及N-3逐码申请唯一落点为 `docs/proposals/P1-ENG-LOOP-002-closed-loop-four-numbers.md`「B0a核清」§1–5和「B0a核清回填：确定上限与可申请范围」。共享库依赖、精确根/链接/权限、监听归属等仍UNKNOWN，HTTP/真实模型/部署可运行性未核；engineering§9前置没有凭本节消失。仅推荐另签一次≤600s零模型只读补核，完整运行维度本轮不请求签发；本角色未代答/签额/执行补核，不增改AC或冻结操作单，不记任何硬件性能/Unity通过。

## 只读补核原始读数与逐维度用量

- 轮次：`只读补核`（Implementation，Opus 子代理，supervisor 派发；Dispatch-Id 见本批提交尾注）。
- 授权来源：`docs/authorizations.md` 2026-10-07「P1-ENG-LOOP-002 — 用户签 (i) B-main 只读补核子范围（SSH ≤1、≤600 s）；共享库先取事实再定；46273 保持不碰；N-3 待补核后随完整额度确认」信封（MacBook Air → 同一 Jetson 既有 SSH ≤ 1 次、墙钟 ≤ 600 s、重试 0；其余维度 0）。
- 合同：同名提案「补核答复落实」§2–3（命令闭集、产出与停止闭集）；「B0a核清」§2 双Q4行（「本机state/板原verify源缺失则UNKNOWN并停，不能按字节/文件名/mtime猜」）。
- **结论：本机静态准备第一步（定位 JET 来源链）即命中 §3 停止闭集「本机来源缺失」——C2 `state.q4`→传板 verify-q4 链的原件不在本机（MacBook Air）。按 §2「来源不在本机只能报UNKNOWN…停下回接受，不能联网取件」与 §3 停止闭集，保存已得事实后停止：未发起 SSH（0/1），未进入部署依赖静态清单与板端读数，不进入 B0b/B1/Play，不改冻结操作单。**

### 本机静态来源与部署依赖清单

执行机器：`MacBook-Air.local`（macOS 26.6.2，即 Unity 主机 MacBook Air；与 B0a 同机）。

| 序 | 静态步骤（§2 顺序） | 结果 | 来源 |
|---|---|---|---|
| L0 | 既有 SSH 别名只读 | `Host Jetson` 存在：HostName `100.100.100.100`、User `jetson`、端口 22（`ssh -G` 有效配置，不连接）；私钥未读 | `~/.ssh/config` 只读、`ssh -G Jetson` rc=0 |
| L1 | C2 `state.q4` → 传板 verify-q4 链 | **缺失**：JET 原件根 `outputs/eng-jet/P1-ENG-JET-001/stageb-c2-diagnostic/`（JET 提案「阶段BC2诊断核清」开头所称 OUT，仅本机、不在 git）在本机不存在，`state.json`/`budget.jsonl`/`checkpoint.json`/`steps/*/receipt.json` 均无；`stageb-c2-json-diagnostic/` 亦不存在。本机该目录只有 JET 阶段 A 遗留件。git 跟踪文件中提到 `c2-merged-Q4_K_M` 的只有账本与本文件 B0a 节（只有板路径/字节，无 sha 期望、不是来源链原件）。JET stage B 的 `src` 路径前缀为 `~/…`，与 JET 提案「阶段BC2JSON诊断授权落实」§1「唯一设备沿本项Mac mini」一致：原件推断在 Mac mini（**推断，未核**） | 下文「命令与原始stdout/stderr」L1 段 |
| L2 | mmproj transfer 期望 | 可解析：`docs/evidence/P1-ENG-JET-001-stageb-transfer.json` `objects` 中 cls=G 且 basename=`mmproj-Qwen3VL-2B-Instruct-F16.gguf` 唯一 1 项，含 `expected_bytes`、64 位 `expected_sha256` 与 `board_final`（值见原始输出；sha 值未打印、运行时解析） | L2 段 |
| L3 | server 来源路径/期望与 bindir 链接信息 | 路径与 stat 期望可解析：`docs/evidence/P1-ENG-JET-001-stageb-build-rerun.json` `products.llama_server_stat_raw` 首段 = `board_batch_dir.path` + `/build/bin/llama-server`（一致），regular/72,424 B/775；`products.bin_ls` 26 行在。该 JSON **无 server sha 字段**；JET 现行链要求的「上轮 server_sha256_now」在 L1 同一缺失根的 precheck 收据里，故 **server sha 期望本机亦 UNKNOWN** | L3 段 |
| L4 | `config/p1-eng-loop-002-board-deploy.json` 闭集源码与传递导入的文本/AST 静态读取、标准库要求与板端待核文件列表 | **未执行**（L1 命中停止闭集后停止；不是失败）。闭集清单文件本身在仓库（16 条路径），未据此生成要求列表 | — |

### 命令与原始stdout/stderr

本机命令（均只读；未连接 Jetson、未 import 仓库模块或第三方包、未跑测试/评分、未写 `runtime/`）：

```
date -u +%FT%TZ; python3 -c 'import time;print(time.time())'
grep -n -A6 '^Host Jetson' ~/.ssh/config | sed -E 's/(IdentityFile).*/\1 <既有本机私钥路径，未读>/'
ssh -G Jetson 2>/dev/null | awk '/^(hostname|user|port|batchmode|connecttimeout) /'
python3 <scratchpad>/resolve.py     # 系统 python3 标准库；脚本只在会话临时目录、不入仓；sha 值不打印
```

L0 stdout（stderr 空；最后一行为 shell 打印的 awk 管道 rc）：

```
2026-10-07T04:24:23Z
1791347063.289799
1:Host Jetson
2-  HostName 100.100.100.100
3-  User jetson
4-  IdentityFile <既有本机私钥路径，未读>
5-
6-Host win5060
7-  HostName 100.100.100.100
user jetson
hostname 100.100.100.100
port 22
batchmode no
connecttimeout none
ssh -G rc=0
```

L1–L3 `resolve.py` stdout（逐字；stderr 空，rc=0）：

```
epoch_start 1791347084.754155
== L1 C2 chain originals (JET OUT roots, outputs/ untracked)
outputs/eng-jet/P1-ENG-JET-001/stageb-c2-diagnostic exists=False
outputs/eng-jet/P1-ENG-JET-001/stageb-c2-json-diagnostic exists=False
   state.json exists=False
   budget.jsonl exists=False
   checkpoint.json exists=False
outputs/eng-jet/P1-ENG-JET-001 entries: ['assets-local.json', 'board-manifest.json', 'bundle', 'ledger-events.jsonl', 's0', 'sr', 'zero-write.json']
git grep -l c2-merged-Q4_K_M rc=0: ['docs/authorizations.md', 'docs/evidence/P1-ENG-LOOP-002-precheck.md']
git ls-files outputs/eng-jet count: 0
== L2 mmproj (docs/evidence/P1-ENG-JET-001-stageb-transfer.json, tracked)
mmproj objects (cls=G, basename match): 1
  keys: ['alloc_rounded', 'attempt', 'basename', 'board_final', 'board_part', 'board_verify', 'cls', 'expected_bytes', 'expected_sha256', 'identity', 'rename', 'reserved_bytes', 'scp', 'sent_bytes', 'sent_bytes_basis', 'seq', 'src', 'src_hash_offline', 'src_repo_relative', 'src_restat', 'src_stat_plan', 'status']
  expected_bytes: 819394848 expected_sha256 len: 64 board_final: /home/jetson/eng-jet/stageb-transfer-20261004T225001Z/mmproj-Qwen3VL-2B-Instruct-F16.gguf
  board_dir: /home/jetson/eng-jet/stageb-transfer-20261004T225001Z
== L3 server/bindir (docs/evidence/P1-ENG-JET-001-stageb-build-rerun.json, tracked)
llama_server_stat_raw path: /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/llama-server | type/bytes/mode: ['regular file', '72424', '775']
board_batch_dir.path: /home/jetson/eng-jet/stageb-build-20261005T033318Z path==batch/build/bin/llama-server: True
bin_ls present: True lines: 26
server sha256 field in build-rerun products: []
server sha expectation (JET 上轮 server_sha256_now) source = C2 diag precheck receipt under L1 root: exists=False
epoch_end 1791347084.842261 elapsed_s 0.088
```

另：只读确认外接盘 `/Volumes/T7`（顶层与 `TetheredDroneTracking/` 副本，`find -maxdepth 6`）中无 `stageb-c2-diagnostic` 目录、`stageb-transfer*.json`、`stageb-build-rerun*.json`；本机 `~` 下（排除 `Library`，`-maxdepth 7`）同样无前者。未联网取件。

### 逐次尝试与逐维度用量

| 维度 | 上限 | 实际 | 说明 |
|---|---:|---:|---|
| 只读 SSH 次数（成功/失败/重试共账） | 1 | **0** | 停于连接前；`ssh -G` 不连接、不计 |
| SSH 墙钟（连接尝试开始至退出） | 600 s | **0** | 无连接；本机静态步骤 epoch 见原始输出（resolve.py 0.088 s） |
| ping | 0 | 0 | — |
| 模型加载 / `--version` / Python import / 推理 / HTTP / 服务 | 0 | 0 | — |
| 板写入 / 文件传输 / scenario·session·run ID / Play / runtime 写入 / 回放·评分 | 0 | 0 | — |
| 5060 / API / GPU·h / 下载 / 安装 / 云 | 0 | 0 | — |
| 设置修改、提权、触碰 46273 | 不做 | 未做 | — |

本机写入仅本证据节与状态板交接（及会话 scratchpad 中的解析脚本与输出副本，不入仓）。N-2 原账（SSH 1/2、ping 5/10）与 N-1 用量不变、未借用。

### 资产/共享库/部署根/监听事实

本轮**无新板端读数**；以下只说明状态，不重复 B0a 读数：

- C2 Q4：本机来源链 UNKNOWN（L1）；板端 sha 未读。B0a R11/R14 的板路径与字节仍只是存在性事实，按「B0a核清」§2 不能据字节/文件名选定。
- mmproj：本机期望可解析（L2）；板端 sha 未读。
- llama-server 与共享库：本机路径/stat 期望与 bindir 清单可解析（L3），server sha 期望本机 UNKNOWN；`readelf`/`ldd`/共享库 sha 未读，用户「先取事实再定」的事实仍缺。
- 部署根 `/home/jetson/eng-loop2`：父目录/链接/权限未读（B0a R10 只证候选模式当时不存在）。
- 监听：18081/18082 占用与 46273 归属本轮未读；B0a R06 快照不更新、46273 保持 UNKNOWN 且未触碰。

### 停止条件与UNKNOWN

- 命中项（§3 停止闭集）：**本机来源缺失**——C2 `state.q4`→verify-q4 链原件（及同根下 server sha 期望所在 precheck 收据）不在本机。按合同保存已得事实并停止后续，不追加连接、不联网取件、不按字节/文件名/mtime 猜 C2，不以 mmproj/server 可解析部分为由单独连接（§2 要求先核来源链；部分补核也会消耗唯一一次 SSH）。
- 未命中项：链路/认证、工具缺失、身份不符、链接异常、父目录权限、依赖、端口占用/残留进程、46273、上限——均因未连接而**未评估**（不是通过）。
- UNKNOWN：C2 Q4 本机期望、server sha 本机期望、部署闭集标准库要求（L4 未执行）、板端全部补核项（路径/父目录/链接/权限、三文件与依赖 sha、`readelf`/`ldd`、Python 标准库文件、`df`/`free`、`ss -ltnp`/`pgrep`）。
- 供接受核清（只列事实与待定点，不自行解释合同、不选方案）：
  1. 本只读子范围信封的 SSH 1 次与 600 s 均未使用；是否在来源到位后由同一信封续执行，由接受/用户裁定，本角色不自行认定。
  2. 原件推断在 Mac mini（`~/…` 前缀、JET 阶段 B 执行设备）；使其在 MacBook Air 可读（例如用户本人把 JET `stageb-c2-diagnostic/` 原件根只读复制到本机同一相对路径）或改由其他机器执行，均涉及信封外动作（本机间文件复制/换执行机器），须用户决定；信封执行机器为 MacBook Air。


## Mac mini只读补核原始读数与逐维度用量

- 轮次：`Mac mini只读补核`（Implementation，Opus 子代理，supervisor 派发；Dispatch-Id `P1-ENG-LOOP-002-Macmini只读补核-20261007T045609Z-3a2d`，base_head `3cb2008`）。
- 授权来源（新条目）：`docs/authorizations.md` 2026-10-07「P1-ENG-LOOP-002 — 用户选 SUB:1 方案 B：只读补核改在 Mac mini 执行，边界同 Air 原信封只换机器；Air 未用余额作废」；原「用户签 (i) B-main 只读补核子范围…」条的命令/停止闭集沿用，其 Air 余额已作废、未叠加。
- 实际执行机器：`zc5s-Mac-mini.local`（macOS 15.8 / 24H23，arm64）→ 同一 Jetson（`Host Jetson`）。合同：同名提案「SUB1换机答复落实」§2 与「补核答复落实」§2–3。
- **结论：连接前三项前提（别名、C2 来源链原件现存且完整、部署闭集静态清单与可靠限时）均在 mini 核齐后，发起唯一一次只读 SSH（成功，rc=0，本机墙钟 4.489 s）。三文件（C2 Q4 / mmproj / llama-server）类型、字节、realpath 与 sha256 均与运行时解析的来源期望一致，路径各级非链接；ldd 依赖闭包 20 项全部解析、无缺库，bindir 23 项与 JET C2 预检清单逐项相同；计划根 `/home/jetson/eng-loop2` 及 code/logs 均不存在；18081/18082 未被监听，两类相关进程无匹配。唯一命中的停止闭集项是「补核快照仍无法辨明 46273 归属」（非特权 `ss -ltnp` 无进程列），它是脚本最后一项读数，未因此追加探测。读齐即本子范围结束：未进入 B0b/B1/Play，未改冻结操作单，不产正式 assets/收据/性能证据。**

### 本机静态来源与部署依赖清单

按「SUB1换机答复落实」§2 顺序执行；每步通过才进入下一步（上一轮 Air 的「报缺后续读」偏差本轮未重犯：M1–M6 全 OK 后才做 D，D 完成后才准备 SSH）。

| 序 | 步骤 | 结果 | 原流 |
|---|---|---|---|
| L0 | `Host Jetson` 别名只读（`ssh -G`，不连接，不读私钥） | 存在：HostName `100.100.100.100`、User `jetson`、端口 22；mini 配置无 IdentityFile 行（用缺省密钥，未读）；`ssh-keygen -F` 只读 known_hosts 有该地址三条主机键 | 下文 L0/KH 段 |
| M1 | JET 原件根 `outputs/eng-jet/P1-ENG-JET-001/stageb-c2-diagnostic/` | 现存：state.json、budget.jsonl（1,521 行可解析）、checkpoint.json、summary.md、16 份 steps 收据 | resolve.py 原流 |
| M2 | state.board.step → board 收据 | 唯一；ALL_609_ROWS_DONE、服务 still_alive=0、端口已释放，predictions/outputs 各 609 行 | 同上 |
| M3 | C2 `state.q4` → 本机现算 → 传板 `005-verify-q4` 原流 → admitted → `server.argv --model` | 本机文件 regular/非链接，字节与 sha 现算等于 state；verify-q4 原流与收据 board_verify 逐字相同且等于 state；admitted 路径 = `--model`，basename 一致（双 Q4 不按文件名/字节/mtime 猜） | 同上 |
| M4 | mmproj：board_paths / `--mmproj` / `stageb-transfer.json` cls=G board_final / 上轮 precheck.blocks.mmproj | 四方一致；transfer 期望唯一 1 项，上轮板读数类型/字节/sha 与 transfer 期望相同 | 同上 |
| M5 | server：board_paths / argv[0] / `stageb-build-rerun.json` stat 与 batch 目录 / `server_sha256_now` / 上轮 precheck.blocks.server | 一致；server_sha256_now 64 位，与上轮板读数相同；bindir 上轮 23 项（9 普通文件 + 14 链接）与 bindir_resolve 14 行取作链接对照 | 同上 |
| M6 | 交叉核：之后的 JSON 诊断 `1-BOARD_VERIFY` 收据 | model/mmproj/server sha、bindir、bindir_resolve 与 M3–M5 相同（仅一致性，不作期望来源） | 同上 |
| D | `config/p1-eng-loop-002-board-deploy.json` 16 条路径（14 个 .py）及传递导入的 AST 静态读取 | 模块级导入闭包 14 文件全在清单内，外部仅标准库 27 个顶层模块（另 5 个子模块 http.client/server、urllib.error/parse/request）；函数内（惰性、分支相关）导入可达清单外 5 文件与第三方，见下「部署闭集观察」 | deps.py 原流 |
| T | 可靠限时 | 本机无 GNU `timeout`（`command -v timeout gtimeout` 空）；用系统 python3 `subprocess` 进程组守护，硬上限 560 s 终止（预留 40 s）；远端 `timeout -k 5 480 bash -s`，单个 sha 另限 150/120 s，sha 前检查已用秒数（>360/380 s 即停） | run_ssh.py |

L0（stdout；stderr 空）：

```
2026-10-07T04:57:01Z
1791349021.879599
1:Host Jetson
2-  HostName 100.100.100.100
3-  User jetson
user jetson
hostname 100.100.100.100
port 22
batchmode no
stricthostkeychecking ask
userknownhostsfile ~/.ssh/known_hosts ~/.ssh/known_hosts2
connecttimeout none
ssh -G rc=0
```

KH（`ssh-keygen -F 100.100.100.100 -f ~/.ssh/known_hosts`，键值由 sed 遮蔽）：

```
# Host 100.100.100.100 found: line 4
100.100.100.100 ssh-ed25519 <key>
# Host 100.100.100.100 found: line 5
100.100.100.100 ssh-rsa <key>
# Host 100.100.100.100 found: line 6
100.100.100.100 ecdsa-sha2-nistp256 <key>
rc=0
```

resolve.py（系统 `/usr/bin/python3` 3.9.6 标准库；stdout 逐字，stderr 空，rc=0；sha 只打印前 12 位，全值在 remote.sh 自动生成段与板端原流）：

```
epoch_start 1791349155.335856
== M1 OUT originals exist
OK   exists state.json
OK   exists budget.jsonl
OK   exists checkpoint.json
OK   exists summary.md
steps receipts: 16
budget.jsonl lines parsed: 1521 | checkpoint keys: ['caps', 'done_steps', 'last_step', 'outcome', 'tally', 'utc']
== M2 board step receipt (state.board.step)
OK   state.board.step present | outputs/eng-jet/P1-ENG-JET-001/stageb-c2-diagnostic/steps/board-20261006T174450Z
OK   board receipt exists | outputs/eng-jet/P1-ENG-JET-001/stageb-c2-diagnostic/steps/board-20261006T174450Z/receipt.json
OK   receipt.step == board
OK   receipt execution ALL_609_ROWS_DONE
OK   server stopped still_alive=0
OK   port released
OK   board predictions.jsonl 609 rows | 609
OK   board outputs.jsonl 609 rows | 609
OK   board step unique among receipts | ['board-20261006T174450Z']
== M3 C2 Q4: state.q4 -> local recompute -> verify-q4 raw -> admitted -> server.argv --model
OK   state.q4.basename present
OK   state.q4.bytes present
OK   state.q4.path present
OK   state.q4.sha256 present
OK   local q4 file exists, regular, not symlink | outputs/eng-jet/P1-ENG-JET-001/stageb-c2-diagnostic/gguf/c2-merged-Q4_K_M.gguf
OK   local q4 bytes == state | 1107409952
OK   local q4 sha == state | sha12=e87413fc5c17
OK   raw 005-verify-q4.stdout exists
OK   verify-q4 raw: regular file|bytes == state | regular file|1107409952
OK   verify-q4 raw: sha == state
OK   receipt transfer.board_verify == verify-q4 raw text
OK   admitted path == server.argv --model | /home/jetson/eng-jet/stageb-c2-diagnostic/20261006T174450Z/model/c2-merged-Q4_K_M.gguf
OK   admitted type/bytes regular/state
OK   --model basename == state.q4.basename
== M4 mmproj: receipt.board_paths.mmproj / argv --mmproj / transfer.json cls=G board_final / prev precheck.blocks.mmproj
OK   transfer.json cls=G mmproj unique | 1
OK   board_paths.mmproj == transfer board_final | /home/jetson/eng-jet/stageb-transfer-20261004T225001Z/mmproj-Qwen3VL-2B-Instruct-F16.gguf
OK   argv --mmproj == board_paths.mmproj
OK   prev precheck mmproj type/bytes == transfer expected | regular file|819394848
OK   prev precheck mmproj sha == transfer expected_sha256 | sha12=c3d5afbef528
== M5 server: board_paths.server / argv[0] / build-rerun stat & batch dir / server_sha256_now / prev precheck.blocks.server
OK   argv[0] == board_paths.server | /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/llama-server
OK   build-rerun stat_raw path == board_paths.server | /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/llama-server|regular file|72424|775|2026-10-05 00:02:20.633243711 -0400
OK   build-rerun board_batch_dir + /build/bin/llama-server == server
OK   server_sha256_now is 64 hex | sha12=5ed4a1791624
OK   prev precheck server type/bytes regular/72424 == build-rerun stat | regular file|72424
OK   prev precheck server sha == server_sha256_now
prev bindir entries: 23 | files: 9 | links: 14 | bindir_resolve lines: 14
== M6 cross-check with later JSON-diag 1-BOARD_VERIFY (same board paths/sha; consistency only)
OK   json-diag model path == --model
OK   json-diag model block == regular/bytes/sha state
OK   json-diag mmproj block == prev
OK   json-diag server_sha256_now == prev
OK   json-diag bindir block == prev
OK   json-diag bindir_resolve block == prev
problems: []
RESULT CHAIN_OK
epoch_end 1791349155.968655 elapsed_s 0.633
```

deps.py（同上解释器；`ast`/`sysconfig` 只定位文件、不 import 被分析模块；stdout 逐字，stderr 空，rc=0。「local kind」是本机 3.9 标准库的文件定位，仅用于列板端待核路径，不代表板端 3.12 结论）：

```
epoch_start 1791349219.844809
manifest paths: 16 | .py: 14 | non-.py: ['config/p1-eng-loop-002-board-deploy.json', 'config/vlm-three-state.schema.json']
local analyzer: system python 3.9.6 (file-location lookup only, no import) stdlib dir: /Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9
== A. module-level import closure from manifest .py (needed at import time)
files: 14 | outside manifest: []
internal module-level edges outside manifest: []
forbidden module-level: []
external top-level modules at module level (name | kind | first use):
  __future__ | stdlib_py | controller/language_bridge.py:18
  argparse | stdlib_py | tools/language_serve.py:31
  base64 | stdlib_py | tools/eng_loop2/llama_adapter.py:21
  collections | stdlib_pkg | controller/reanchor.py:3
  dataclasses | stdlib_py | controller/language_bridge.py:20
  errno | builtin | controller/language_bridge.py:21
  hashlib | stdlib_py | controller/language_selector.py:15
  http | stdlib_pkg | tools/eng_loop2/llama_adapter.py:22
  io | stdlib_py | tools/language_serve.py:34
  itertools | builtin | controller/language_selector.py:16
  json | stdlib_pkg | controller/language_bridge.py:22
  math | stdlib_ext | controller/language_bridge.py:23
  os | stdlib_py | controller/language_bridge.py:24
  pathlib | stdlib_py | controller/language_bridge.py:25
  platform | stdlib_py | tools/language_serve.py:37
  re | stdlib_py | controller/language_bridge.py:26
  shutil | stdlib_py | tools/language_serve.py:39
  signal | stdlib_py | tools/language_serve.py:40
  socket | stdlib_py | tools/eng_loop2/llama_adapter.py:25
  subprocess | stdlib_py | tools/language_serve.py:41
  sys | builtin | controller/language_selector.py:19
  tempfile | stdlib_py | controller/protocol.py:7
  threading | stdlib_py | controller/reanchor.py:9
  time | builtin | controller/language_bridge.py:27
  types | stdlib_py | controller/reanchor.py:11
  typing | stdlib_py | controller/language_bridge.py:28
  urllib | stdlib_pkg | controller/language_selector.py:22
== B. function-level (lazy, branch-dependent) imports inside manifest files
  controller/language_selector.py:127 tools.eng_sft.parse -> internal tools/eng_sft/parse.py IN_MANIFEST
  controller/language_selector.py:216 tools.eng_sft -> internal tools/eng_sft/__init__.py IN_MANIFEST
  controller/language_selector.py:216 tools.eng_sft.prompt_v2 -> internal tools/eng_sft/prompt_v2.py IN_MANIFEST
  controller/language_selector.py:381 resource -> external stdlib_ext
  controller/language_selector.py:383 types -> external stdlib_py
  controller/language_selector.py:393 tools.eng_sft -> internal tools/eng_sft/__init__.py IN_MANIFEST
  controller/language_selector.py:393 tools.eng_sft.train_lora -> internal tools/eng_sft/train_lora.py NOT_IN_MANIFEST FORBIDDEN_FOR_LLAMA_BRANCH(A2e)
  controller/trackers.py:174 cv2 -> external NOT_FOUND_LOCAL_STDLIB
  controller/trackers.py:391 cv2 -> external NOT_FOUND_LOCAL_STDLIB
  controller/trackers.py:525 controller.det_assoc_tracker -> internal controller/det_assoc_tracker.py NOT_IN_MANIFEST
  tools/eng_loop2/deploy_digest.py:148 argparse -> external stdlib_py
  tools/eng_sft/prompt_v2.py:209 pathlib -> external stdlib_py
  tools/language_serve.py:654 controller.language_bridge -> internal controller/language_bridge.py IN_MANIFEST
  tools/language_serve.py:655 tools.eng_loop2 -> internal tools/eng_loop2/__init__.py IN_MANIFEST
  tools/language_serve.py:655 tools.eng_loop2.deploy_digest -> internal tools/eng_loop2/deploy_digest.py IN_MANIFEST
  tools/language_serve.py:655 tools.eng_loop2.llama_adapter -> internal tools/eng_loop2/llama_adapter.py IN_MANIFEST
  tools/language_serve.py:702 tools.eng_loop2 -> internal tools/eng_loop2/__init__.py IN_MANIFEST
  tools/language_serve.py:702 tools.eng_loop2.llama_adapter -> internal tools/eng_loop2/llama_adapter.py IN_MANIFEST
  tools/language_serve.py:750 tools.eng_loop2 -> internal tools/eng_loop2/__init__.py IN_MANIFEST
  tools/language_serve.py:750 tools.eng_loop2.llama_adapter -> internal tools/eng_loop2/llama_adapter.py IN_MANIFEST
  tools/language_serve.py:898 controller.language_selector -> internal controller/language_selector.py IN_MANIFEST
== C. full transitive closure incl. lazy (what a lazy branch could reach; not executed)
files: 19 | outside manifest: ['controller/det_assoc_tracker.py', 'controller/pose_gmc.py', 'tools/eng_asset/receipts.py', 'tools/eng_sft/receipts.py', 'tools/eng_sft/train_lora.py']
third-party/non-stdlib top-level reachable: ['PIL', 'cv2', 'numpy', 'peft', 'torch', 'transformers', 'ultralytics']
dynamic-import keywords in module-level closure files: []
epoch_end 1791349220.036491 elapsed_s 0.192
```

**部署闭集观察（静态，交接受；不自行解释合同）**：A 段显示模块级导入闭包自足、仅标准库，A2(e) 禁止项在模块级为空。B 段显示三处函数内导入会离开清单：`controller/language_selector.py:393` 的 `tools.eng_sft.train_lora`（A2(e) 点名 llama-server 分支不得 import）、`controller/trackers.py:525` 的 `controller.det_assoc_tracker`（再到 `pose_gmc`）、`controller/trackers.py:174/391` 的 `cv2`；C 段经惰性分支可达第三方 PIL/cv2/numpy/peft/torch/transformers/ultralytics。llama-server 运行分支是否触达这些惰性导入属运行时分支事实，静态读取无法证明，记 UNKNOWN；本轮不 import、不运行任何部署代码。

### 命令与原始stdout/stderr

本机命令（均只读；除下列唯一 SSH 外不连接 Jetson；未 import 仓库模块或第三方包；未跑测试/评分；未写 `runtime/`）：

```
date -u +%FT%TZ; python3 -c 'import time;print(time.time())'
grep -n -A4 '^Host Jetson' ~/.ssh/config | sed -E 's/(IdentityFile).*/\1 <既有本机私钥路径，未读>/'
ssh -G Jetson 2>/dev/null | awk '/^(hostname|user|port|batchmode|connecttimeout|stricthostkeychecking|userknownhostsfile) /'
ssh-keygen -F 100.100.100.100 -f ~/.ssh/known_hosts | sed -E 's/(ssh-[a-z0-9]+|ecdsa-[a-z0-9-]+) .*/\1 <key>/'
/usr/bin/python3 <scratchpad>/resolve.py <scratchpad>/expect.json     # M1–M6
/usr/bin/python3 <scratchpad>/deps.py <scratchpad>/stdmods.json       # D
/usr/bin/python3 <scratchpad>/gen.py <scratchpad>                     # 由 expect.json/stdmods.json 生成 remote.sh
bash -n <scratchpad>/remote.sh                                        # 仅语法检查，rc=0
/usr/bin/python3 <scratchpad>/run_ssh.py <scratchpad>                 # 唯一一次 SSH
```

会话临时脚本不入仓，sha256：remote.sh `f0c73455f60e6babb4e5ebbb80a1fea60e8de90624730e392e31dad4ba926272`、resolve.py `63435198e15771a1e336b10464a9520ac7e234a93aee1f20595e98d8027ec927`、deps.py `de2e4a6f031fce4e692fd999d1f92f97bc10e69549dd5c91dd740098f0a705f1`、gen.py `649c0a7d3520cc244151cc3daace5bec090998c32ec57672157ce9e106ceef24`、run_ssh.py `2f0d5a0c760fc0a8f89cd43cd3dc29d8909a5a345f994e99c435812c4d13939e`。deps.py 是第三版：前两版（本机、零消耗）禁止项匹配写错且未区分模块级/函数内，改正后重跑，上表为第三版原流。

SSH 调用（run_ssh.py 记录，逐字）：

```
cmd ['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=20', 'Jetson', 'timeout -k 5 480 bash -s']
epoch_start 1791349384.004076 utc_start 2026-10-07T05:03:04.004076Z
epoch_end 1791349388.493555 utc_end 2026-10-07T05:03:08.493555Z
wall_epoch_s 4.489 wall_monotonic_s 4.490
ssh_rc 0 killed_by_local_limit False
```

远端脚本 remote.sh（gen.py 自动生成，经 stdin 送入远端 `bash -s`，板上不落文件；只用 `date/hostname/uname/id/command -v/test/stat/readlink/sha256sum/readelf/ldd/python3 --version/df/free/ss -ltnp/pgrep/timeout` 及 shell 变量、循环、条件、printf；期望值为 resolve.py 运行时解析结果的自动嵌入，不是手抄）：

```bash
set +e
export LC_ALL=C
sec(){ printf '\n=== %s\n' "$1"; }
rc(){ printf 'rc=%s\n' "$1"; }
STOP(){ printf '\n=== STOP %s\n' "$1"; date -u +%FT%TZ; printf 'remote_elapsed_s=%s\n' "$SECONDS"; exit 3; }
budget(){ if [ "$SECONDS" -gt "$1" ]; then STOP "TIME_BUDGET before $2 (elapsed=${SECONDS}s > ${1}s)"; fi; }
Q4='/home/jetson/eng-jet/stageb-c2-diagnostic/20261006T174450Z/model/c2-merged-Q4_K_M.gguf'; Q4B=1107409952; Q4S='e87413fc5c17b8f91a581bbd670c10846ef4cb180b69b8eb701d2f8dbd71d0c7'
MM='/home/jetson/eng-jet/stageb-transfer-20261004T225001Z/mmproj-Qwen3VL-2B-Instruct-F16.gguf'; MMB=819394848; MMS='c3d5afbef5287953acd57b4043d2269456e5761a4eaccb3b71b062996970aea5'
SRV='/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/llama-server'; SRVB=72424; SRVS='5ed4a17916244553d3265b0d601cf527adbf8b562508f6c9b4498becd3bc7f98'
BIN=${SRV%/*}
sec "R00 board_utc_start / device"; date -u +%FT%TZ; H=$(hostname); printf 'hostname=%s\n' "$H"; uname -srm; M=$(uname -m); id -un; id -u
[ "$H" = "jetson" ] && [ "$M" = "aarch64" ] || STOP "DEVICE_MISMATCH host=$H arch=$M"
sec "R01 tools on disk (command -v)"; MISSING=
for t in date hostname uname id test stat readlink ls sha256sum readelf ldd python3 df free ss pgrep timeout; do p=$(command -v "$t"); r=$?; printf '%s|%s|rc=%s\n' "$t" "$p" "$r"; [ $r -eq 0 ] || MISSING="$MISSING $t"; done
[ -z "$MISSING" ] || STOP "TOOL_MISSING:$MISSING"
chk3(){
  tag=$1; f=$2; eb=$3; es=$4
  sec "R02-$tag path chain (file then each parent: name|type|mode|owner|bytes) + realpath + sha256"
  d=$f
  while [ "$d" != "/" ]; do
    s=$(stat -c '%n|%F|%a|%U:%G|%s' -- "$d" 2>&1); r=$?; printf '%s|rc=%s\n' "$s" "$r"
    [ $r -eq 0 ] || STOP "STAT_FAIL $tag $d"
    if [ -L "$d" ]; then STOP "LINK_IN_PATH $tag $d"; fi
    d=${d%/*}; [ -z "$d" ] && d=/
  done
  rl=$(readlink -f -- "$f"); printf 'readlink_f=%s\n' "$rl"; [ "$rl" = "$f" ] || STOP "REALPATH_DIFF $tag"
  typ=$(stat -c '%F' -- "$f"); sz=$(stat -c '%s' -- "$f")
  [ "$typ" = "regular file" ] || STOP "TYPE $tag $typ"
  if [ "$sz" = "$eb" ]; then printf 'bytes_match=yes\n'; else STOP "BYTES_MISMATCH $tag $sz != $eb"; fi
  budget 360 "sha $tag"
  out=$(timeout -k 2 150 sha256sum -- "$f" 2>&1); r=$?; printf '%s\nrc=%s\n' "$out" "$r"
  [ $r -eq 0 ] || STOP "SHA_FAIL $tag rc=$r"
  if [ "${out%% *}" = "$es" ]; then printf 'sha_match=yes\n'; else printf 'sha_match=NO\n'; STOP "SHA_MISMATCH $tag"; fi
}
chk3 Q4 "$Q4" "$Q4B" "$Q4S"
chk3 MMPROJ "$MM" "$MMB" "$MMS"
chk3 SERVER "$SRV" "$SRVB" "$SRVS"
sec "R03 readelf -h server"; readelf -h -- "$SRV" 2>&1; rc $?
sec "R03 readelf -l server"; readelf -l -- "$SRV" 2>&1; rc $?
sec "R03 readelf -d server"; readelf -d -- "$SRV" 2>&1; rc $?
sec "R04 bindir listing now (name|f/l|bytes|link target) vs JET C2 precheck.blocks.bindir"
declare -A PREV
while IFS= read -r l; do [ -n "$l" ] && PREV["$l"]=1; done <<'__PREV__'
libggml-cuda.so.0.25.3|f|61451472|
libllama-common.so|l|20|libllama-common.so.0
libggml-base.so.0|l|22|libggml-base.so.0.25.3
libggml-cuda.so|l|17|libggml-cuda.so.0
libllama.so.0|l|17|libllama.so.0.5.0
libllama-common.so.0|l|24|libllama-common.so.0.5.0
libmtmd.so.0.5.0|f|1830624|
libllama.so.0.5.0|f|4542696|
llama-server|f|72424|
libggml.so.0.25.3|f|78152|
libggml-base.so|l|17|libggml-base.so.0
libggml.so.0|l|17|libggml.so.0.25.3
libllama.so|l|13|libllama.so.0
libggml-base.so.0.25.3|f|877152|
libggml.so|l|12|libggml.so.0
libggml-cpu.so.0|l|21|libggml-cpu.so.0.25.3
libggml-cpu.so|l|16|libggml-cpu.so.0
libggml-cuda.so.0|l|22|libggml-cuda.so.0.25.3
libggml-cpu.so.0.25.3|f|1068776|
libmtmd.so|l|12|libmtmd.so.0
libmtmd.so.0|l|16|libmtmd.so.0.5.0
libllama-common.so.0.5.0|f|5433840|
libllama-server-impl.so|f|3542712|
__PREV__
n=0; diff=0
for f in "$BIN"/*; do b=${f##*/}; if [ -L "$f" ]; then t=l; tg=$(readlink -- "$f"); elif [ -d "$f" ]; then t=d; tg=; else t=f; tg=; fi; sz=$(stat -c %s -- "$f"); line="$b|$t|$sz|$tg"; printf '%s\n' "$line"; n=$((n+1)); if [ -n "${PREV[$line]}" ]; then unset "PREV[$line]"; else printf 'NEW_OR_CHANGED %s\n' "$line"; diff=1; fi; done
for k in "${!PREV[@]}"; do printf 'MISSING_FROM_NOW %s\n' "$k"; diff=1; done
printf 'entries_now=%s bindir_same_as_prev=%s\n' "$n" "$([ $diff -eq 0 ] && echo yes || echo NO)"; [ $diff -eq 0 ] || STOP "BINDIR_DIFF"
sec "R05 ldd server"; LDD=$(ldd -- "$SRV" 2>&1); r=$?; printf '%s\nrc=%s\n' "$LDD" "$r"; [ $r -eq 0 ] || STOP "LDD_FAIL"
case "$LDD" in *"not found"*) STOP "LDD_NOT_FOUND";; esac
DEPS=()
while read -r a b c d; do if [ "$b" = "=>" ]; then [ -n "$c" ] && [ "${c#/}" != "$c" ] && DEPS+=("$c"); elif [ -n "$a" ] && [ "${a#/}" != "$a" ]; then DEPS+=("$a"); fi; done <<< "$LDD"
printf 'deps_resolved=%s\n' "${#DEPS[@]}"
sec "R06 dependency closure files (ldd_path|link?|realpath|type|bytes|mode|sha256|rc)"
for p in "${DEPS[@]}"; do budget 380 "dep sha"; if [ -L "$p" ]; then L=link; else L=nolink; fi; rp=$(readlink -f -- "$p"); st=$(stat -c '%F|%s|%a' -- "$rp" 2>&1); out=$(timeout -k 2 120 sha256sum -- "$rp" 2>&1); r=$?; printf '%s|%s|%s|%s|%s|rc=%s\n' "$p" "$L" "$rp" "$st" "${out%% *}" "$r"; [ $r -eq 0 ] || STOP "DEP_SHA_FAIL $p"; done
sec "R07 readelf -d for resolved deps inside server bindir"
for p in "${DEPS[@]}"; do case "$p" in "$BIN"/*) printf -- '--- %s\n' "$p"; readelf -d -- "$p" 2>&1; rc $?;; esac; done
sec "R08 python3 interpreter + stdlib files for deploy-closure module-level imports"
PY=$(command -v python3); PYR=$(readlink -f -- "$PY"); printf 'python3=%s realpath=%s\n' "$PY" "$PYR"; python3 --version 2>&1; rc $?
SLD=/usr/lib/${PYR##*/}; printf 'stdlib_dir=%s\n' "$SLD"; stat -c '%n|%F|%a' -- "$SLD" 2>&1; r=$?; rc $r; [ $r -eq 0 ] || STOP "STDLIB_DIR_UNKNOWN"
MISS=
for m in __future__ argparse base64 collections dataclasses hashlib http io json os pathlib platform re shutil signal socket subprocess tempfile threading types typing urllib; do if [ -f "$SLD/$m.py" ]; then printf '%s|py|%s\n' "$m" "$SLD/$m.py"; elif [ -f "$SLD/$m/__init__.py" ]; then printf '%s|pkg|%s\n' "$m" "$SLD/$m/__init__.py"; else printf '%s|MISSING\n' "$m"; MISS="$MISS $m"; fi; done
for s in http/client.py http/server.py urllib/error.py urllib/parse.py urllib/request.py; do if [ -f "$SLD/$s" ]; then printf '%s|file\n' "$SLD/$s"; else printf '%s|MISSING\n' "$SLD/$s"; MISS="$MISS $s"; fi; done
for m in errno itertools math sys time resource; do set -- "$SLD"/lib-dynload/"$m".cpython-*; if [ -e "$1" ]; then printf '%s|ext_file|%s\n' "$m" "$1"; else printf '%s|no_ext_file(builtin_or_UNKNOWN)\n' "$m"; fi; done
[ -z "$MISS" ] || STOP "STDLIB_FILE_MISSING:$MISS"
sec "R09 planned deploy root + parents (read-only; access check only, no write)"
for d in /home /home/jetson; do stat -c '%n|%F|%a|%U:%G' -- "$d" 2>&1; r=$?; rc $r; [ $r -eq 0 ] || STOP "PARENT_STAT_FAIL $d"; [ -L "$d" ] && STOP "LINK_PARENT $d"; done
printf 'readlink_f_home=%s\n' "$(readlink -f -- /home/jetson)"; if [ -w /home/jetson ]; then printf 'home_jetson_writable_by_user=yes(access test only)\n'; else printf 'home_jetson_writable_by_user=no\n'; fi
EXIST=
for d in /home/jetson/eng-loop2 /home/jetson/eng-loop2/code /home/jetson/eng-loop2/logs; do if [ -e "$d" ] || [ -L "$d" ]; then stat -c '%n|%F|%a|%U:%G' -- "$d" 2>&1; EXIST="$EXIST $d"; else printf '%s|ABSENT\n' "$d"; fi; done
[ -z "$EXIST" ] || STOP "PLANNED_ROOT_EXISTS:$EXIST"
sec "R10 df -B1 / and HOME; free -b"; df -B1 / /home/jetson 2>&1; rc $?; free -b 2>&1; rc $?
sec "R11 ss -ltnp (non-privileged)"; SS=$(ss -ltnp 2>&1); r=$?; printf '%s\nrc=%s\n' "$SS" "$r"; [ $r -eq 0 ] || STOP "SS_FAIL"
OCC=; L46=
while read -r st rq sq loc peer rest; do case "$loc" in *:18081|*:18082) OCC="$OCC $loc";; esac; case "$loc" in *:46273) L46="$st $rq $sq $loc $peer $rest";; esac; done <<< "$SS"
printf 'listen_18081_18082=%s\n' "${OCC:-none}"; printf 'line_46273=%s\n' "${L46:-absent}"
case "$L46" in "") O46=absent_from_snapshot;; *users:*) O46=visible;; *) O46=UNKNOWN_no_process_column;; esac; printf 'owner_46273=%s\n' "$O46"
sec "R12 pgrep llama-server"; pgrep -a -f llama-server 2>&1; R1=$?; rc $R1
sec "R12 pgrep language_serve"; pgrep -a -f language_serve 2>&1; R2=$?; rc $R2
sec "R99 board_utc_end"; date -u +%FT%TZ; printf 'remote_elapsed_s=%s\n' "$SECONDS"
HIT=; [ -n "$OCC" ] && HIT="$HIT PORT_OCCUPIED"; [ $R1 -eq 0 ] && HIT="$HIT RESIDUAL_LLAMA"; [ $R2 -eq 0 ] && HIT="$HIT RESIDUAL_LANGUAGE_SERVE"; [ "$O46" = visible ] || HIT="$HIT OWNER_46273_$O46"
printf 'final_stop_hits=%s\n' "${HIT:-none}"
exit 0
```

SSH stdout（逐字，35,675 B，sha256 `b3dba5e83c7e1175b7578ecf77793f4232b7dc928700926bb8577a5dbff79c4c`；stderr 0 B；SSH 总 rc=0。每条子命令 rc 在原流内）：

```

=== R00 board_utc_start / device
2026-10-07T05:03:04Z
hostname=jetson
Linux 6.8.12-1021-tegra aarch64
jetson
1000

=== R01 tools on disk (command -v)
date|/usr/bin/date|rc=0
hostname|/usr/bin/hostname|rc=0
uname|/usr/bin/uname|rc=0
id|/usr/bin/id|rc=0
test|test|rc=0
stat|/usr/bin/stat|rc=0
readlink|/usr/bin/readlink|rc=0
ls|/usr/bin/ls|rc=0
sha256sum|/usr/bin/sha256sum|rc=0
readelf|/usr/bin/readelf|rc=0
ldd|/usr/bin/ldd|rc=0
python3|/usr/bin/python3|rc=0
df|/usr/bin/df|rc=0
free|/usr/bin/free|rc=0
ss|/usr/bin/ss|rc=0
pgrep|/usr/bin/pgrep|rc=0
timeout|/usr/bin/timeout|rc=0

=== R02-Q4 path chain (file then each parent: name|type|mode|owner|bytes) + realpath + sha256
/home/jetson/eng-jet/stageb-c2-diagnostic/20261006T174450Z/model/c2-merged-Q4_K_M.gguf|regular file|600|jetson:jetson|1107409952|rc=0
/home/jetson/eng-jet/stageb-c2-diagnostic/20261006T174450Z/model|directory|700|jetson:jetson|4096|rc=0
/home/jetson/eng-jet/stageb-c2-diagnostic/20261006T174450Z|directory|700|jetson:jetson|4096|rc=0
/home/jetson/eng-jet/stageb-c2-diagnostic|directory|700|jetson:jetson|4096|rc=0
/home/jetson/eng-jet|directory|775|jetson:jetson|4096|rc=0
/home/jetson|directory|750|jetson:jetson|4096|rc=0
/home|directory|755|root:root|4096|rc=0
readlink_f=/home/jetson/eng-jet/stageb-c2-diagnostic/20261006T174450Z/model/c2-merged-Q4_K_M.gguf
bytes_match=yes
e87413fc5c17b8f91a581bbd670c10846ef4cb180b69b8eb701d2f8dbd71d0c7  /home/jetson/eng-jet/stageb-c2-diagnostic/20261006T174450Z/model/c2-merged-Q4_K_M.gguf
rc=0
sha_match=yes

=== R02-MMPROJ path chain (file then each parent: name|type|mode|owner|bytes) + realpath + sha256
/home/jetson/eng-jet/stageb-transfer-20261004T225001Z/mmproj-Qwen3VL-2B-Instruct-F16.gguf|regular file|644|jetson:jetson|819394848|rc=0
/home/jetson/eng-jet/stageb-transfer-20261004T225001Z|directory|700|jetson:jetson|4096|rc=0
/home/jetson/eng-jet|directory|775|jetson:jetson|4096|rc=0
/home/jetson|directory|750|jetson:jetson|4096|rc=0
/home|directory|755|root:root|4096|rc=0
readlink_f=/home/jetson/eng-jet/stageb-transfer-20261004T225001Z/mmproj-Qwen3VL-2B-Instruct-F16.gguf
bytes_match=yes
c3d5afbef5287953acd57b4043d2269456e5761a4eaccb3b71b062996970aea5  /home/jetson/eng-jet/stageb-transfer-20261004T225001Z/mmproj-Qwen3VL-2B-Instruct-F16.gguf
rc=0
sha_match=yes

=== R02-SERVER path chain (file then each parent: name|type|mode|owner|bytes) + realpath + sha256
/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/llama-server|regular file|775|jetson:jetson|72424|rc=0
/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin|directory|775|jetson:jetson|4096|rc=0
/home/jetson/eng-jet/stageb-build-20261005T033318Z/build|directory|700|jetson:jetson|4096|rc=0
/home/jetson/eng-jet/stageb-build-20261005T033318Z|directory|700|jetson:jetson|4096|rc=0
/home/jetson/eng-jet|directory|775|jetson:jetson|4096|rc=0
/home/jetson|directory|750|jetson:jetson|4096|rc=0
/home|directory|755|root:root|4096|rc=0
readlink_f=/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/llama-server
bytes_match=yes
5ed4a17916244553d3265b0d601cf527adbf8b562508f6c9b4498becd3bc7f98  /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/llama-server
rc=0
sha_match=yes

=== R03 readelf -h server
ELF Header:
  Magic:   7f 45 4c 46 02 01 01 00 00 00 00 00 00 00 00 00 
  Class:                             ELF64
  Data:                              2's complement, little endian
  Version:                           1 (current)
  OS/ABI:                            UNIX - System V
  ABI Version:                       0
  Type:                              DYN (Position-Independent Executable file)
  Machine:                           AArch64
  Version:                           0x1
  Entry point address:               0x1180
  Start of program headers:          64 (bytes into file)
  Start of section headers:          70568 (bytes into file)
  Flags:                             0x0
  Size of this header:               64 (bytes)
  Size of program headers:           56 (bytes)
  Number of program headers:         9
  Size of section headers:           64 (bytes)
  Number of section headers:         29
  Section header string table index: 28
rc=0

=== R03 readelf -l server

Elf file type is DYN (Position-Independent Executable file)
Entry point 0x1180
There are 9 program headers, starting at offset 64

Program Headers:
  Type           Offset             VirtAddr           PhysAddr
                 FileSiz            MemSiz              Flags  Align
  PHDR           0x0000000000000040 0x0000000000000040 0x0000000000000040
                 0x00000000000001f8 0x00000000000001f8  R      0x8
  INTERP         0x0000000000000238 0x0000000000000238 0x0000000000000238
                 0x000000000000001b 0x000000000000001b  R      0x1
      [Requesting program interpreter: /lib/ld-linux-aarch64.so.1]
  LOAD           0x0000000000000000 0x0000000000000000 0x0000000000000000
                 0x0000000000001cf7 0x0000000000001cf7  R E    0x10000
  LOAD           0x000000000000fc90 0x000000000001fc90 0x000000000001fc90
                 0x00000000000003a0 0x00000000000003d8  RW     0x10000
  DYNAMIC        0x000000000000fca0 0x000000000001fca0 0x000000000001fca0
                 0x0000000000000240 0x0000000000000240  RW     0x8
  NOTE           0x0000000000000254 0x0000000000000254 0x0000000000000254
                 0x0000000000000044 0x0000000000000044  R      0x4
  GNU_EH_FRAME   0x0000000000001aa8 0x0000000000001aa8 0x0000000000001aa8
                 0x000000000000006c 0x000000000000006c  R      0x4
  GNU_STACK      0x0000000000000000 0x0000000000000000 0x0000000000000000
                 0x0000000000000000 0x0000000000000000  RW     0x10
  GNU_RELRO      0x000000000000fc90 0x000000000001fc90 0x000000000001fc90
                 0x0000000000000370 0x0000000000000370  R      0x1

 Section to Segment mapping:
  Segment Sections...
   00     
   01     .interp 
   02     .interp .note.gnu.build-id .note.ABI-tag .gnu.hash .dynsym .dynstr .gnu.version .gnu.version_r .rela.dyn .rela.plt .init .plt .text .fini .rodata .eh_frame_hdr .eh_frame .gcc_except_table 
   03     .init_array .fini_array .dynamic .got .data .bss 
   04     .dynamic 
   05     .note.gnu.build-id .note.ABI-tag 
   06     .eh_frame_hdr 
   07     
   08     .init_array .fini_array .dynamic .got 
rc=0

=== R03 readelf -d server

Dynamic section at offset 0xfca0 contains 32 entries:
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libllama-server-impl.so]
 0x0000000000000001 (NEEDED)             Shared library: [libstdc++.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libgcc_s.so.1]
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [ld-linux-aarch64.so.1]
 0x000000000000001d (RUNPATH)            Library runpath: [/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin:]
 0x000000000000000c (INIT)               0xf88
 0x000000000000000d (FINI)               0x1928
 0x0000000000000019 (INIT_ARRAY)         0x1fc90
 0x000000000000001b (INIT_ARRAYSZ)       8 (bytes)
 0x000000000000001a (FINI_ARRAY)         0x1fc98
 0x000000000000001c (FINI_ARRAYSZ)       8 (bytes)
 0x000000006ffffef5 (GNU_HASH)           0x298
 0x0000000000000005 (STRTAB)             0x678
 0x0000000000000006 (SYMTAB)             0x2e8
 0x000000000000000a (STRSZ)              1111 (bytes)
 0x000000000000000b (SYMENT)             24 (bytes)
 0x0000000000000015 (DEBUG)              0x0
 0x0000000000000003 (PLTGOT)             0x1fee0
 0x0000000000000002 (PLTRELSZ)           504 (bytes)
 0x0000000000000014 (PLTREL)             RELA
 0x0000000000000017 (JMPREL)             0xd90
 0x0000000000000007 (RELA)               0xbe0
 0x0000000000000008 (RELASZ)             432 (bytes)
 0x0000000000000009 (RELAENT)            24 (bytes)
 0x000000000000001e (FLAGS)              BIND_NOW
 0x000000006ffffffb (FLAGS_1)            Flags: NOW PIE
 0x000000006ffffffe (VERNEED)            0xb20
 0x000000006fffffff (VERNEEDNUM)         4
 0x000000006ffffff0 (VERSYM)             0xad0
 0x000000006ffffff9 (RELACOUNT)          11
 0x0000000000000000 (NULL)               0x0
rc=0

=== R04 bindir listing now (name|f/l|bytes|link target) vs JET C2 precheck.blocks.bindir
libggml-base.so|l|17|libggml-base.so.0
libggml-base.so.0|l|22|libggml-base.so.0.25.3
libggml-base.so.0.25.3|f|877152|
libggml-cpu.so|l|16|libggml-cpu.so.0
libggml-cpu.so.0|l|21|libggml-cpu.so.0.25.3
libggml-cpu.so.0.25.3|f|1068776|
libggml-cuda.so|l|17|libggml-cuda.so.0
libggml-cuda.so.0|l|22|libggml-cuda.so.0.25.3
libggml-cuda.so.0.25.3|f|61451472|
libggml.so|l|12|libggml.so.0
libggml.so.0|l|17|libggml.so.0.25.3
libggml.so.0.25.3|f|78152|
libllama-common.so|l|20|libllama-common.so.0
libllama-common.so.0|l|24|libllama-common.so.0.5.0
libllama-common.so.0.5.0|f|5433840|
libllama-server-impl.so|f|3542712|
libllama.so|l|13|libllama.so.0
libllama.so.0|l|17|libllama.so.0.5.0
libllama.so.0.5.0|f|4542696|
libmtmd.so|l|12|libmtmd.so.0
libmtmd.so.0|l|16|libmtmd.so.0.5.0
libmtmd.so.0.5.0|f|1830624|
llama-server|f|72424|
entries_now=23 bindir_same_as_prev=yes

=== R05 ldd server
	linux-vdso.so.1 (0x0000ffffb7bca000)
	libllama-server-impl.so => /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libllama-server-impl.so (0x0000ffffb7880000)
	libstdc++.so.6 => /lib/aarch64-linux-gnu/libstdc++.so.6 (0x0000ffffb75d0000)
	libgcc_s.so.1 => /lib/aarch64-linux-gnu/libgcc_s.so.1 (0x0000ffffb7590000)
	libc.so.6 => /lib/aarch64-linux-gnu/libc.so.6 (0x0000ffffb73d0000)
	/lib/ld-linux-aarch64.so.1 (0x0000ffffb7b80000)
	libllama-common.so.0 => /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libllama-common.so.0 (0x0000ffffb6f80000)
	libmtmd.so.0 => /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libmtmd.so.0 (0x0000ffffb6dd0000)
	libllama.so.0 => /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libllama.so.0 (0x0000ffffb6a10000)
	libggml.so.0 => /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libggml.so.0 (0x0000ffffb69e0000)
	libggml-base.so.0 => /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libggml-base.so.0 (0x0000ffffb6900000)
	libm.so.6 => /lib/aarch64-linux-gnu/libm.so.6 (0x0000ffffb6850000)
	libggml-cpu.so.0 => /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libggml-cpu.so.0 (0x0000ffffb66c0000)
	libggml-cuda.so.0 => /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libggml-cuda.so.0 (0x0000ffffb31b0000)
	libgomp.so.1 => /lib/aarch64-linux-gnu/libgomp.so.1 (0x0000ffffb3130000)
	libcudart.so.13 => /usr/local/cuda/targets/sbsa-linux/lib/libcudart.so.13 (0x0000ffffb3060000)
	libcublas.so.13 => /usr/local/cuda/targets/sbsa-linux/lib/libcublas.so.13 (0x0000ffffaee00000)
	libdl.so.2 => /lib/aarch64-linux-gnu/libdl.so.2 (0x0000ffffb3030000)
	libpthread.so.0 => /lib/aarch64-linux-gnu/libpthread.so.0 (0x0000ffffb3000000)
	librt.so.1 => /lib/aarch64-linux-gnu/librt.so.1 (0x0000ffffb2fd0000)
	libcublasLt.so.13 => /usr/local/cuda/targets/sbsa-linux/lib/libcublasLt.so.13 (0x0000ffff85000000)
rc=0
deps_resolved=20

=== R06 dependency closure files (ldd_path|link?|realpath|type|bytes|mode|sha256|rc)
/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libllama-server-impl.so|nolink|/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libllama-server-impl.so|regular file|3542712|775|dd22449e8aa1d10ab5a22e9273697a6135647ae77545d53ae9526393ef38b5e6|rc=0
/lib/aarch64-linux-gnu/libstdc++.so.6|link|/usr/lib/aarch64-linux-gnu/libstdc++.so.6.0.33|regular file|2633224|644|6e3112d35cfc86db7ee85b27e1746f67408e2837ff8628b46386c3eabd5682a4|rc=0
/lib/aarch64-linux-gnu/libgcc_s.so.1|nolink|/usr/lib/aarch64-linux-gnu/libgcc_s.so.1|regular file|133696|644|f2d3ad2bf0b61f6bc944cc37d7b6ab7f88d2582b41ff989ca164803f56cc5f20|rc=0
/lib/aarch64-linux-gnu/libc.so.6|nolink|/usr/lib/aarch64-linux-gnu/libc.so.6|regular file|1722920|755|6e3cc56b98887cb3cc2a9fe78b6dd4610184aa27bd05d592cb287db93e82d494|rc=0
/lib/ld-linux-aarch64.so.1|link|/usr/lib/aarch64-linux-gnu/ld-linux-aarch64.so.1|regular file|203968|755|49005ef8e9db9a45691ff875e6ca18dd8723c7ec5c1a863a276a1186dbf22774|rc=0
/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libllama-common.so.0|link|/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libllama-common.so.0.5.0|regular file|5433840|775|3326c975ca67ed9d3a7865b4fa70ada43c015e6c26abb2ec827180fb5eda8a4a|rc=0
/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libmtmd.so.0|link|/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libmtmd.so.0.5.0|regular file|1830624|775|ba2b983b9c7031b596068cb1965d5cc4b9bcc703dba1d6392ee52b4308d14657|rc=0
/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libllama.so.0|link|/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libllama.so.0.5.0|regular file|4542696|775|c6357c30e47ff7acb50bfa8d176e6519b82bdbb5f62197dd603152818e510df5|rc=0
/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libggml.so.0|link|/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libggml.so.0.25.3|regular file|78152|775|37393689134dfd0da163d2aaf053d61218176eab48d81886803587e079a28d63|rc=0
/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libggml-base.so.0|link|/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libggml-base.so.0.25.3|regular file|877152|775|2149963a6c16ef86e277cde3e77dbf35598e5912fcde293eeb223f7183dc8881|rc=0
/lib/aarch64-linux-gnu/libm.so.6|nolink|/usr/lib/aarch64-linux-gnu/libm.so.6|regular file|591800|644|24be585ff27080ba6301d8b3e1c92a54a3832829a9efde744cad4b876a73681a|rc=0
/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libggml-cpu.so.0|link|/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libggml-cpu.so.0.25.3|regular file|1068776|775|74f09544895ab66bca5494435266726bfa0e4e1148609d6ec53a4b5fb692c034|rc=0
/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libggml-cuda.so.0|link|/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libggml-cuda.so.0.25.3|regular file|61451472|775|54643120ac81182f0e2abde772818fea3543eb32f442b3c9c3f305e636323998|rc=0
/lib/aarch64-linux-gnu/libgomp.so.1|link|/usr/lib/aarch64-linux-gnu/libgomp.so.1.0.0|regular file|397088|644|33c8bcb7d33228fe5101bfeb201bcaff4563d4ecf09497229b9deba522ebaf3d|rc=0
/usr/local/cuda/targets/sbsa-linux/lib/libcudart.so.13|link|/usr/local/cuda-13.2/targets/sbsa-linux/lib/libcudart.so.13.2.75|regular file|773384|644|2537479bafd2d6f3066a21fb54a2d05cd044bb0bf3705ea51ac3f0ccb0c02665|rc=0
/usr/local/cuda/targets/sbsa-linux/lib/libcublas.so.13|link|/usr/local/cuda-13.2/targets/sbsa-linux/lib/libcublas.so.13.4.0.1|regular file|67751616|644|826486b8869144621e3a477cddcd28f56733c7c80c6f998b898384fc09e10f91|rc=0
/lib/aarch64-linux-gnu/libdl.so.2|nolink|/usr/lib/aarch64-linux-gnu/libdl.so.2|regular file|67440|644|f196e378b444da9e982e8930e1595e9ad6a723d890e0647bc60d8fcf581a93c8|rc=0
/lib/aarch64-linux-gnu/libpthread.so.0|nolink|/usr/lib/aarch64-linux-gnu/libpthread.so.0|regular file|67440|644|1ce5833f596169e194b95a6f288c98d80b7b907a1ded2389746cd00235b3a456|rc=0
/lib/aarch64-linux-gnu/librt.so.1|nolink|/usr/lib/aarch64-linux-gnu/librt.so.1|regular file|67512|644|8e38ca286d0bbb7acc9a6741ecd26c6e76924ec69eb9196ee20f70fa91350e12|rc=0
/usr/local/cuda/targets/sbsa-linux/lib/libcublasLt.so.13|link|/usr/local/cuda-13.2/targets/sbsa-linux/lib/libcublasLt.so.13.4.0.1|regular file|606744240|644|b7aa42c190c2e7490abd6ea987883e05678e26222b7f9f1c9b96374fcbddbf04|rc=0

=== R07 readelf -d for resolved deps inside server bindir
--- /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libllama-server-impl.so

Dynamic section at offset 0x2af150 contains 37 entries:
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libllama-common.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libmtmd.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libllama.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libggml.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libggml-base.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libstdc++.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libm.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libgcc_s.so.1]
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [ld-linux-aarch64.so.1]
 0x000000000000000e (SONAME)             Library soname: [libllama-server-impl.so]
 0x000000000000001d (RUNPATH)            Library runpath: [/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin:]
 0x000000000000000c (INIT)               0x84ae0
 0x000000000000000d (FINI)               0x241f30
 0x0000000000000019 (INIT_ARRAY)         0x2bbab0
 0x000000000000001b (INIT_ARRAYSZ)       48 (bytes)
 0x000000000000001a (FINI_ARRAY)         0x2bbae0
 0x000000000000001c (FINI_ARRAYSZ)       8 (bytes)
 0x000000006ffffef5 (GNU_HASH)           0x228
 0x0000000000000005 (STRTAB)             0x1b0d8
 0x0000000000000006 (SYMTAB)             0x58f8
 0x000000000000000a (STRSZ)              325256 (bytes)
 0x000000000000000b (SYMENT)             24 (bytes)
 0x0000000000000003 (PLTGOT)             0x2bffe8
 0x0000000000000002 (PLTRELSZ)           47208 (bytes)
 0x0000000000000014 (PLTREL)             RELA
 0x0000000000000017 (JMPREL)             0x79278
 0x000000006ffffef6 (TLSDESC_PLT)        0x8c590
 0x000000006ffffef7 (TLSDESC_GOT)        0x2bffd8
 0x0000000000000007 (RELA)               0x6c678
 0x0000000000000008 (RELASZ)             52224 (bytes)
 0x0000000000000009 (RELAENT)            24 (bytes)
 0x000000006ffffffe (VERNEED)            0x6c408
 0x000000006fffffff (VERNEEDNUM)         5
 0x000000006ffffff0 (VERSYM)             0x6a760
 0x000000006ffffff9 (RELACOUNT)          513
 0x0000000000000000 (NULL)               0x0
rc=0
--- /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libllama-common.so.0

Dynamic section at offset 0x40ef00 contains 35 entries:
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libllama.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libggml.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libggml-base.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libstdc++.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libm.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libgcc_s.so.1]
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [ld-linux-aarch64.so.1]
 0x000000000000000e (SONAME)             Library soname: [libllama-common.so.0]
 0x000000000000001d (RUNPATH)            Library runpath: [/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin:]
 0x000000000000000c (INIT)               0xabaf0
 0x000000000000000d (FINI)               0x35d9a0
 0x0000000000000019 (INIT_ARRAY)         0x419c30
 0x000000000000001b (INIT_ARRAYSZ)       80 (bytes)
 0x000000000000001a (FINI_ARRAY)         0x419c80
 0x000000000000001c (FINI_ARRAYSZ)       8 (bytes)
 0x000000006ffffef5 (GNU_HASH)           0x228
 0x0000000000000005 (STRTAB)             0x22218
 0x0000000000000006 (SYMTAB)             0x7110
 0x000000000000000a (STRSZ)              419614 (bytes)
 0x000000000000000b (SYMENT)             24 (bytes)
 0x0000000000000003 (PLTGOT)             0x41ffe8
 0x0000000000000002 (PLTRELSZ)           55296 (bytes)
 0x0000000000000014 (PLTREL)             RELA
 0x0000000000000017 (JMPREL)             0x9e2f0
 0x000000006ffffef6 (TLSDESC_PLT)        0xb4ad0
 0x000000006ffffef7 (TLSDESC_GOT)        0x41ffe0
 0x0000000000000007 (RELA)               0x8afd0
 0x0000000000000008 (RELASZ)             78624 (bytes)
 0x0000000000000009 (RELAENT)            24 (bytes)
 0x000000006ffffffe (VERNEED)            0x8ad50
 0x000000006fffffff (VERNEEDNUM)         5
 0x000000006ffffff0 (VERSYM)             0x88936
 0x000000006ffffff9 (RELACOUNT)          857
 0x0000000000000000 (NULL)               0x0
rc=0
--- /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libmtmd.so.0

Dynamic section at offset 0x18f9b8 contains 35 entries:
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libllama.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libggml.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libggml-base.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libstdc++.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libm.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libgcc_s.so.1]
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [ld-linux-aarch64.so.1]
 0x000000000000000e (SONAME)             Library soname: [libmtmd.so.0]
 0x000000000000001d (RUNPATH)            Library runpath: [/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin:]
 0x000000000000000c (INIT)               0x24d38
 0x000000000000000d (FINI)               0x14e470
 0x0000000000000019 (INIT_ARRAY)         0x19de00
 0x000000000000001b (INIT_ARRAYSZ)       416 (bytes)
 0x000000000000001a (FINI_ARRAY)         0x19dfa0
 0x000000000000001c (FINI_ARRAYSZ)       8 (bytes)
 0x000000006ffffef5 (GNU_HASH)           0x228
 0x0000000000000005 (STRTAB)             0xaec8
 0x0000000000000006 (SYMTAB)             0x2750
 0x000000000000000a (STRSZ)              63421 (bytes)
 0x000000000000000b (SYMENT)             24 (bytes)
 0x0000000000000003 (PLTGOT)             0x19ffe8
 0x0000000000000002 (PLTRELSZ)           16272 (bytes)
 0x0000000000000014 (PLTREL)             RELA
 0x0000000000000017 (JMPREL)             0x20da8
 0x000000006ffffef6 (TLSDESC_PLT)        0x277c0
 0x000000006ffffef7 (TLSDESC_GOT)        0x19ffe0
 0x0000000000000007 (RELA)               0x1b360
 0x0000000000000008 (RELASZ)             23112 (bytes)
 0x0000000000000009 (RELAENT)            24 (bytes)
 0x000000006ffffffe (VERNEED)            0x1b1d0
 0x000000006fffffff (VERNEEDNUM)         5
 0x000000006ffffff0 (VERSYM)             0x1a686
 0x000000006ffffff9 (RELACOUNT)          124
 0x0000000000000000 (NULL)               0x0
rc=0
--- /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libllama.so.0

Dynamic section at offset 0x39e910 contains 34 entries:
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libggml.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libggml-base.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libstdc++.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libm.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libgcc_s.so.1]
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [ld-linux-aarch64.so.1]
 0x000000000000000e (SONAME)             Library soname: [libllama.so.0]
 0x000000000000001d (RUNPATH)            Library runpath: [/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin:]
 0x000000000000000c (INIT)               0xae880
 0x000000000000000d (FINI)               0x307930
 0x0000000000000019 (INIT_ARRAY)         0x3a59b8
 0x000000000000001b (INIT_ARRAYSZ)       56 (bytes)
 0x000000000000001a (FINI_ARRAY)         0x3a59f0
 0x000000000000001c (FINI_ARRAYSZ)       8 (bytes)
 0x000000006ffffef5 (GNU_HASH)           0x1f0
 0x0000000000000005 (STRTAB)             0x2f380
 0x0000000000000006 (SYMTAB)             0xaae0
 0x000000000000000a (STRSZ)              330958 (bytes)
 0x000000000000000b (SYMENT)             24 (bytes)
 0x0000000000000003 (PLTGOT)             0x3affe8
 0x0000000000000002 (PLTRELSZ)           52824 (bytes)
 0x0000000000000014 (PLTREL)             RELA
 0x0000000000000017 (JMPREL)             0xa1a28
 0x000000006ffffef6 (TLSDESC_PLT)        0xb7230
 0x000000006ffffef7 (TLSDESC_GOT)        0x3affe0
 0x0000000000000007 (RELA)               0x83338
 0x0000000000000008 (RELASZ)             124656 (bytes)
 0x0000000000000009 (RELAENT)            24 (bytes)
 0x000000006ffffffe (VERNEED)            0x83108
 0x000000006fffffff (VERNEEDNUM)         5
 0x000000006ffffff0 (VERSYM)             0x8004e
 0x000000006ffffff9 (RELACOUNT)          548
 0x0000000000000000 (NULL)               0x0
rc=0
--- /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libggml.so.0

Dynamic section at offset 0xfd58 contains 32 entries:
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libggml-cpu.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libggml-cuda.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libggml-base.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libstdc++.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libgcc_s.so.1]
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [ld-linux-aarch64.so.1]
 0x000000000000000e (SONAME)             Library soname: [libggml.so.0]
 0x000000000000001d (RUNPATH)            Library runpath: [/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin:]
 0x000000000000000c (INIT)               0x2740
 0x000000000000000d (FINI)               0x7380
 0x0000000000000019 (INIT_ARRAY)         0x1fd40
 0x000000000000001b (INIT_ARRAYSZ)       16 (bytes)
 0x000000000000001a (FINI_ARRAY)         0x1fd50
 0x000000000000001c (FINI_ARRAYSZ)       8 (bytes)
 0x000000006ffffef5 (GNU_HASH)           0x1f0
 0x0000000000000005 (STRTAB)             0xc80
 0x0000000000000006 (SYMTAB)             0x2f0
 0x000000000000000a (STRSZ)              4118 (bytes)
 0x000000000000000b (SYMENT)             24 (bytes)
 0x0000000000000003 (PLTGOT)             0x1ffe8
 0x0000000000000002 (PLTRELSZ)           1944 (bytes)
 0x0000000000000014 (PLTREL)             RELA
 0x0000000000000017 (JMPREL)             0x1fa8
 0x0000000000000007 (RELA)               0x1e58
 0x0000000000000008 (RELASZ)             336 (bytes)
 0x0000000000000009 (RELAENT)            24 (bytes)
 0x000000006ffffffe (VERNEED)            0x1d68
 0x000000006fffffff (VERNEEDNUM)         4
 0x000000006ffffff0 (VERSYM)             0x1c96
 0x000000006ffffff9 (RELACOUNT)          4
 0x0000000000000000 (NULL)               0x0
rc=0
--- /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libggml-base.so.0

Dynamic section at offset 0xbfd28 contains 30 entries:
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libgomp.so.1]
 0x0000000000000001 (NEEDED)             Shared library: [libstdc++.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libm.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libgcc_s.so.1]
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [ld-linux-aarch64.so.1]
 0x000000000000000e (SONAME)             Library soname: [libggml-base.so.0]
 0x000000000000000c (INIT)               0x167e0
 0x000000000000000d (FINI)               0x913f0
 0x0000000000000019 (INIT_ARRAY)         0xce958
 0x000000000000001b (INIT_ARRAYSZ)       32 (bytes)
 0x000000000000001a (FINI_ARRAY)         0xce978
 0x000000000000001c (FINI_ARRAYSZ)       8 (bytes)
 0x000000006ffffef5 (GNU_HASH)           0x1f0
 0x0000000000000005 (STRTAB)             0x7a30
 0x0000000000000006 (SYMTAB)             0x1bf8
 0x000000000000000a (STRSZ)              34748 (bytes)
 0x000000000000000b (SYMENT)             24 (bytes)
 0x0000000000000003 (PLTGOT)             0xcffe8
 0x0000000000000002 (PLTRELSZ)           13608 (bytes)
 0x0000000000000014 (PLTREL)             RELA
 0x0000000000000017 (JMPREL)             0x132b8
 0x0000000000000007 (RELA)               0x10b58
 0x0000000000000008 (RELASZ)             10080 (bytes)
 0x0000000000000009 (RELAENT)            24 (bytes)
 0x000000006ffffffe (VERNEED)            0x109c8
 0x000000006fffffff (VERNEEDNUM)         6
 0x000000006ffffff0 (VERSYM)             0x101ec
 0x000000006ffffff9 (RELACOUNT)          334
 0x0000000000000000 (NULL)               0x0
rc=0
--- /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libggml-cpu.so.0

Dynamic section at offset 0xefc48 contains 32 entries:
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libggml-base.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libgomp.so.1]
 0x0000000000000001 (NEEDED)             Shared library: [libstdc++.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libm.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libgcc_s.so.1]
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [ld-linux-aarch64.so.1]
 0x000000000000000e (SONAME)             Library soname: [libggml-cpu.so.0]
 0x000000000000001d (RUNPATH)            Library runpath: [/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin:]
 0x000000000000000c (INIT)               0x12cf8
 0x000000000000000d (FINI)               0xbd924
 0x0000000000000019 (INIT_ARRAY)         0xfef18
 0x000000000000001b (INIT_ARRAYSZ)       8 (bytes)
 0x000000000000001a (FINI_ARRAY)         0xfef20
 0x000000000000001c (FINI_ARRAYSZ)       8 (bytes)
 0x000000006ffffef5 (GNU_HASH)           0x1f0
 0x0000000000000005 (STRTAB)             0x5d18
 0x0000000000000006 (SYMTAB)             0x15d8
 0x000000000000000a (STRSZ)              33078 (bytes)
 0x000000000000000b (SYMENT)             24 (bytes)
 0x0000000000000003 (PLTGOT)             0xfffe8
 0x0000000000000002 (PLTRELSZ)           10344 (bytes)
 0x0000000000000014 (PLTREL)             RELA
 0x0000000000000017 (JMPREL)             0x10490
 0x0000000000000007 (RELA)               0xe5d0
 0x0000000000000008 (RELASZ)             7872 (bytes)
 0x0000000000000009 (RELAENT)            24 (bytes)
 0x000000006ffffffe (VERNEED)            0xe440
 0x000000006fffffff (VERNEEDNUM)         6
 0x000000006ffffff0 (VERSYM)             0xde4e
 0x000000006ffffff9 (RELACOUNT)          27
 0x0000000000000000 (NULL)               0x0
rc=0
--- /home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin/libggml-cuda.so.0

Dynamic section at offset 0x34bf1f8 contains 33 entries:
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libggml-base.so.0]
 0x0000000000000001 (NEEDED)             Shared library: [libcudart.so.13]
 0x0000000000000001 (NEEDED)             Shared library: [libcublas.so.13]
 0x0000000000000001 (NEEDED)             Shared library: [libstdc++.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libm.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libgcc_s.so.1]
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [ld-linux-aarch64.so.1]
 0x000000000000000e (SONAME)             Library soname: [libggml-cuda.so.0]
 0x000000000000001d (RUNPATH)            Library runpath: [/home/jetson/eng-jet/stageb-build-20261005T033318Z/build/bin:]
 0x000000000000000c (INIT)               0x38300
 0x000000000000000d (FINI)               0xcd2dfc
 0x0000000000000019 (INIT_ARRAY)         0x34ceb50
 0x000000000000001b (INIT_ARRAYSZ)       1176 (bytes)
 0x000000000000001a (FINI_ARRAY)         0x34cefe8
 0x000000000000001c (FINI_ARRAYSZ)       8 (bytes)
 0x000000006ffffef5 (GNU_HASH)           0x1f0
 0x0000000000000005 (STRTAB)             0xa270
 0x0000000000000006 (SYMTAB)             0x27b8
 0x000000000000000a (STRSZ)              127653 (bytes)
 0x000000000000000b (SYMENT)             24 (bytes)
 0x0000000000000003 (PLTGOT)             0x34cffe8
 0x0000000000000002 (PLTRELSZ)           21864 (bytes)
 0x0000000000000014 (PLTREL)             RELA
 0x0000000000000017 (JMPREL)             0x32d98
 0x0000000000000007 (RELA)               0x2a0e0
 0x0000000000000008 (RELASZ)             36024 (bytes)
 0x0000000000000009 (RELAENT)            24 (bytes)
 0x000000006ffffffe (VERNEED)            0x29f50
 0x000000006fffffff (VERNEEDNUM)         7
 0x000000006ffffff0 (VERSYM)             0x29516
 0x000000006ffffff9 (RELACOUNT)          1119
 0x0000000000000000 (NULL)               0x0
rc=0

=== R08 python3 interpreter + stdlib files for deploy-closure module-level imports
python3=/usr/bin/python3 realpath=/usr/bin/python3.12
Python 3.12.3
rc=0
stdlib_dir=/usr/lib/python3.12
/usr/lib/python3.12|directory|755
rc=0
__future__|py|/usr/lib/python3.12/__future__.py
argparse|py|/usr/lib/python3.12/argparse.py
base64|py|/usr/lib/python3.12/base64.py
collections|pkg|/usr/lib/python3.12/collections/__init__.py
dataclasses|py|/usr/lib/python3.12/dataclasses.py
hashlib|py|/usr/lib/python3.12/hashlib.py
http|pkg|/usr/lib/python3.12/http/__init__.py
io|py|/usr/lib/python3.12/io.py
json|pkg|/usr/lib/python3.12/json/__init__.py
os|py|/usr/lib/python3.12/os.py
pathlib|py|/usr/lib/python3.12/pathlib.py
platform|py|/usr/lib/python3.12/platform.py
re|pkg|/usr/lib/python3.12/re/__init__.py
shutil|py|/usr/lib/python3.12/shutil.py
signal|py|/usr/lib/python3.12/signal.py
socket|py|/usr/lib/python3.12/socket.py
subprocess|py|/usr/lib/python3.12/subprocess.py
tempfile|py|/usr/lib/python3.12/tempfile.py
threading|py|/usr/lib/python3.12/threading.py
types|py|/usr/lib/python3.12/types.py
typing|py|/usr/lib/python3.12/typing.py
urllib|pkg|/usr/lib/python3.12/urllib/__init__.py
/usr/lib/python3.12/http/client.py|file
/usr/lib/python3.12/http/server.py|file
/usr/lib/python3.12/urllib/error.py|file
/usr/lib/python3.12/urllib/parse.py|file
/usr/lib/python3.12/urllib/request.py|file
errno|no_ext_file(builtin_or_UNKNOWN)
itertools|no_ext_file(builtin_or_UNKNOWN)
math|no_ext_file(builtin_or_UNKNOWN)
sys|no_ext_file(builtin_or_UNKNOWN)
time|no_ext_file(builtin_or_UNKNOWN)
resource|ext_file|/usr/lib/python3.12/lib-dynload/resource.cpython-312-aarch64-linux-gnu.so

=== R09 planned deploy root + parents (read-only; access check only, no write)
/home|directory|755|root:root
rc=0
/home/jetson|directory|750|jetson:jetson
rc=0
readlink_f_home=/home/jetson
home_jetson_writable_by_user=yes(access test only)
/home/jetson/eng-loop2|ABSENT
/home/jetson/eng-loop2/code|ABSENT
/home/jetson/eng-loop2/logs|ABSENT

=== R10 df -B1 / and HOME; free -b
Filesystem        1B-blocks        Used    Available Use% Mounted on
/dev/nvme0n1p1 249326301184 76443381760 160143314944  33% /
/dev/nvme0n1p1 249326301184 76443381760 160143314944  33% /
rc=0
               total        used        free      shared  buff/cache   available
Mem:      7849054208  1859661824  1545420800     2666496  4683075584  5989392384
Swap:              0           0           0
rc=0

=== R11 ss -ltnp (non-privileged)
State  Recv-Q Send-Q  Local Address:Port  Peer Address:PortProcess
LISTEN 0      4096       127.0.0.54:53         0.0.0.0:*          
LISTEN 0      4096   100.100.100.100:46273      0.0.0.0:*          
LISTEN 0      4096          0.0.0.0:22         0.0.0.0:*          
LISTEN 0      4096    127.0.0.53%lo:53         0.0.0.0:*          
LISTEN 0      4096             [::]:22            [::]:*          
rc=0
listen_18081_18082=none
line_46273=LISTEN 0 4096 100.100.100.100:46273 0.0.0.0:* 
owner_46273=UNKNOWN_no_process_column

=== R12 pgrep llama-server
rc=1

=== R12 pgrep language_serve
rc=1

=== R99 board_utc_end
2026-10-07T05:03:08Z
remote_elapsed_s=4
final_stop_hits= OWNER_46273_UNKNOWN_no_process_column
```

### 逐次尝试与逐维度用量

| # | 动作 | 方向 | 起（本机 epoch / UTC） | 止（本机 epoch / UTC） | 墙钟 | 退出码 | 结果 |
|---|---|---|---|---|---|---|---|
| S1 | 只读 SSH 第 1 次（唯一一次） | Mac mini → Jetson（`Host Jetson`） | 1791349384.004076 / 2026-10-07T05:03:04.004Z | 1791349388.493555 / 2026-10-07T05:03:08.494Z | 4.489 s（monotonic 4.490 s） | 0 | 成功；远端末行 `remote_elapsed_s=4`，板 `date -u` 05:03:04Z→05:03:08Z |

未发生失败尝试或重试；本机限时未触发（killed_by_local_limit False）。

| 维度（mini 子范围单列） | 上限 | 实际 | 说明 |
|---|---:|---:|---|
| 只读 SSH 次数（成功/失败/重试共账） | 1 | **1** | S1 |
| SSH 墙钟（连接尝试开始至退出） | 600 s | **4.489 s** | 本机 epoch 差 |
| 重试 | 0 | 0 | — |
| ping | 0 | 0 | — |
| 模型加载 / llama `--version`/`--help` / 仓库或第三方 import / 推理 / HTTP（含 loopback/status/health） / 服务启动·驻留 | 0 | 0 | `ldd` 与 `readelf` 只读 ELF 元数据；未执行 llama-server |
| 板写入 / 文件传输·复制 / scenario·session·run ID / Play / runtime 写入 / 回放·评分 | 0 | 0 | stdin 脚本与原流为 SSH 记录，不是部署传输；`[ -w ]` 只是访问权测试，未写文件 |
| 5060 / 外部 API / GPU·h / 下载 / 安装 / 云 | 0 | 0 | — |
| 设置修改、提权/sudo、触碰 100.100.100.100:46273 | 不做 | 未做 | `-o` 选项仅作用于本次调用；46273 只在 `ss` 快照中读到，未连接 |

Air 子范围原账（SSH 0/1、墙钟 0/600 s，未用余额已作废）、N-2 原账（SSH 1/2、ping 5/10）与 N-1 用量不变，未借用、未叠加。附带披露：SSH 登录会在板上产生系统登录日志与文件访问时间变化，属系统行为，不计为部署写入。

### 资产/共享库/部署根/监听事实

手维护摘要只指向上文原流（R 段号），派生路径/SHA 以原流为准。

- **设备**：R00 hostname `jetson`、`Linux 6.8.12-1021-tegra aarch64`、用户 `jetson`(1000)，与 B0a 相同。JET 收据 `board_paths.target` 记的是有线地址，本轮经 `Host Jetson`（Tailscale 地址）连接；同板由 hostname 与三文件 sha 相同支持，未核硬件序列号。
- **三文件身份（R02）**：C2 Q4、mmproj、llama-server 均 regular file、`readlink -f` 等于原路径、文件及各级父目录非链接，字节与 sha256 等于 M3/M4/M5 运行时期望（`sha_match=yes` ×3）。父目录权限与属主见 R02 原流（`/home/jetson` 750）。这些只是本项自身的板端身份读数；按 H-12 与 AC-16，不把 JET 旧结果当 AC-16 证据，也不产正式 assets。
- **共享库（R03–R07）**：server 为 AArch64 PIE，解释器 `/lib/ld-linux-aarch64.so.1`，NEEDED 5 项，RUNPATH 为 JET 构建目录 `…/stageb-build-20261005T033318Z/build/bin`。`ldd` 解析 20 项（不含 vdso），无 `not found`：8 个 bindir 库（含 libggml-cuda）、9 个系统库（`/lib`→`/usr/lib` 链接终点另列）、3 个 CUDA 13.2 库（`/usr/local/cuda` 链接到 `cuda-13.2`）；逐项 realpath/类型/字节/sha 见 R06，闭包实体合计 759,979,752 B。bindir 23 项与 JET C2 预检清单逐项相同（R04 `bindir_same_as_prev=yes`）。**限制**：库没有历史 sha 期望，本轮 sha 是首次读数、不能「对旧值匹配」；`libcuda.so`（驱动）等运行时 dlopen 的库不在 NEEDED/ldd 闭包，静态不可见；单个 llama-server 的 sha 仍不代表整个推理栈身份。是否扩大身份绑定按用户「先取事实再定」交接受转呈，本轮不选。
- **解释器与标准库（R08）**：`/usr/bin/python3` → `/usr/bin/python3.12`，`Python 3.12.3`；`/usr/lib/python3.12` 下 D 段模块级 22 个 .py/包模块和 5 个子模块文件全部存在；errno/itertools/math/sys/time 无扩展文件（内建或 UNKNOWN，静态不可证），惰性用到的 resource 有扩展文件。标准库再往下的 C 模块（如 _socket、_hashlib、select）未枚举，记 UNKNOWN。这只是在盘事实，不等于可 import 或可运行。
- **部署根（R09）**：`/home`（755 root）与 `/home/jetson`（750 jetson）均为目录、非链接，`readlink -f` 不变；以 `[ -w ]` 访问测试判断当前用户对 `/home/jetson` 可写（未写文件）；`/home/jetson/eng-loop2`、`code`、`logs` 均 ABSENT。根不存在属预期，本轮不创建。
- **磁盘/内存（R10，瞬时）**：`/` 与 HOME 同盘 `/dev/nvme0n1p1`，可用 160,143,314,944 B；内存 total 7,849,054,208 B、available 5,989,392,384 B，swap 0。不作服务工作集或峰值结论。
- **监听/进程（R11–R12）**：监听仅 53（本地 DNS）、22、`100.100.100.100:46273`；18081/18082 未被监听（`listen_18081_18082=none`）。46273 仍在，非特权快照无进程列（`owner_46273=UNKNOWN_no_process_column`）。`pgrep -a -f llama-server` 与 `pgrep -a -f language_serve` 均 rc=1（只说明这两个模式无匹配，不说明没有其他进程）。

### 停止条件与UNKNOWN

- **命中**：「补核快照仍无法辨明46273归属」（R11 最后一项读数；`final_stop_hits= OWNER_46273_UNKNOWN_no_process_column`）。按用户已答的「不清楚，保持不碰」记 UNKNOWN，不提权、不 sudo、不连接；仍须用户确认互斥后才能放行服务。命中在脚本末尾，没有跳过的后续读数。
- **未命中（已读到、在闭集内通过）**：设备不符、工具缺失、来源缺失/歧义（M1–M6）、资产身份不符、链接异常、父目录权限不能核实、依赖未解析/缺库、bindir 变化、标准库 .py/包文件缺失、计划根已存在、18081/18082 被占用、两类相关残留进程、上限或余时不足（远端 4 s、本机 4.489 s）。
- **UNKNOWN（本轮静态/非特权读数证明不了）**：46273 归属；内建模块（errno/itertools/math/sys/time）及标准库再往下的 C 模块；运行时 dlopen 的库（如 CUDA 驱动 `libcuda.so`）；llama-server 分支是否触达清单外的惰性导入（train_lora / det_assoc_tracker / cv2 等）；模型能否加载、服务能否就绪、HTTP/`response_format` 行为与性能（全部未执行，属后续首次运行的合同核验）。
- **交接受核清的待定点**（只列事实，不选方案）：(1) 共享库身份范围：闭包事实已取得（R05–R07），转呈「保持三文件并披露限制」还是「修订扩大绑定」；(2) 46273 仍 UNKNOWN，交用户确认互斥；(3) 部署闭集的惰性导入是否需要合同或测试层面的说明；(4) 完整 B-main 运行信封与 N-3 十一码是否转呈用户。本轮不签额、不改 AC、不改冻结操作单，读齐后停止。
