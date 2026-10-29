---
title: Codex Thread Handoff Bridge 合同
sensitivity: public_safe
status: active
---

<p align="right"><a href="BRIDGE_CONTRACT.md">English</a> | <strong>中文</strong></p>

# Bridge 合同

连接器必须提供有界的 `list_codex_threads` 与 `read_codex_thread`，后者只接受小写 canonical UUID 或精确 `codex://threads/<UUID>`。调用者不能传路径、glob、storage root 或 alternate home；服务只从进程所有的 Codex home 派生并显式追加 `sessions`、`archived_sessions` 等已审计目录。symlink 必须拒绝，文件名 UUID 必须匹配 `session_meta.payload.id`。

默认且唯一的语义投影是 user/assistant 文本；system/developer、reasoning、raw JSONL、tool call/output、附件、auth、配置、memory、数据库与日志都在脱敏前排除。scan、源文件、单行、事件、消息、页面、列表和 cursor 都要有硬上限。

Receipt 至少报告 adapter/source version、thread identity、included roles、omitted categories、redaction、source/page truncation、返回量与 page hash。cursor 必须经过校验，并绑定 operation 与 thread，或绑定一个不可变的 source snapshot；cursor 不得在 thread 已变化时静默续读。

如果 source 超过字节上限，connector 可以使用有文档说明的有界头部或尾部窗口，但 receipt 必须报告窗口方向、source 总字节、实际扫描字节与截断状态。超大文件不得被误报为 UUID mismatch。

## 必需的脱敏

脱敏 authorization header、cookie、常见 API/access/refresh token、密码、client secret、私钥块和带凭据的 URL。脱敏只是纵深防御：不像密钥的私人事实仍可能保留，所以数据最小化和用户选定的 thread 范围是必需的。

读取 thread 不联网、不执行命令、不启动 agent，也不依赖 Codex CLI。未知 storage/event 格式必须 fail closed，并通过 synthetic fixture 增加兼容性，不能改为扫描无关文件或返回 raw 数据。

## 有界分页

跨页读取时保持已授权的任务身份不变。记录已访问过的续读 cursor 和剩余读取预算。预算耗尽、cursor 缺失或 cursor 重复时停止，并在交接回执中保留访问或截断状态。历史不完整是续接缺口：它不允许读取无关任务，也不能当作完整历史。这些步骤是使用连接器的宿主方法的义务；声明式扩展本身不运行分页循环。
