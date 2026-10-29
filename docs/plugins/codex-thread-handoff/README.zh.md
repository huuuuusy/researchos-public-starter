---
title: Thread Handoff 插件（id codex_thread_handoff）
sensitivity: public_safe
status: instrumented
---

<p align="right"><a href="README.md">English</a> | <strong>中文</strong></p>

# Thread Handoff（`codex_thread_handoff`）

该可选插件定义如何在 ChatGPT 或其他 MCP 客户端续接一个 Agent 客户端任务。文档目录把 id 写成连字符形式（`codex-thread-handoff/`）。插件 id 沿用它最初实现时的客户端 Codex；交接包本身不限定客户端。它把两个控制面分开：ResearchOS 只安装声明式任务合同；用户另行配置能访问本地 Codex session 的只读 MCP 连接器。安装插件不会暴露电脑、创建 tunnel 或自动使连接器就绪。

## 用途

把一个选定的 Codex thread 读成有界、脱敏的 user/assistant 上下文，不手工复制粘贴、不任意访问 `~/.codex` 就能续接工作。

## 使用与非目标

用户提供 canonical UUID 或 `codex://threads/<UUID>`，并希望另一个客户端理解或续接该任务时使用。它不是 session viewer、agent runner、shell、任意 workspace reader、reasoning/tool payload exporter、thread editor 或自动 memory writer。

## 可用性与一致性

私有 ResearchOS、Public Starter 和 personal vault 使用完全一致的 manifest 与任务语义。私有版可以已有域名和连接器；公开用户提供自己的。公开包不包含私有 endpoint、token、路径、thread ID 或内容。

就绪状态分四种，分别报告：

- `installed`：本地 manifest 存在且已启用；
- `connector_configured`：MCP endpoint 已在客户端注册；
- `connector_verified`：客户端能看到必需工具，且健康/读取探测成功；
- `ready`：选定的 thread 可以按合同读取。

ChatGPT 的工具可用性还受会话运行时约束。连接器 schema 更新后，应在已安装插件的管理页刷新操作，再通过“在聊天中试用”进入一个已启用插件的新会话，或在会话输入区显式选择该插件。旧会话可能已经能看到新工具名称，却仍提示当前会话运行时禁用了插件；这不能作为 bridge 不可用的证据。

## 依赖

需要 ResearchOS 核心，以及一个独立运行、按 [BRIDGE_CONTRACT.zh.md](BRIDGE_CONTRACT.zh.md) 提供 `list_codex_threads` 与 `read_codex_thread` 的 MCP 连接器。连接器可以是用户已有的私有 bridge，也可以是另一个符合合同的本地实现。读取 thread 不得依赖定位或启动 Codex CLI 可执行文件。

## 生命周期

本地、可逆安装：

```bash
python3 scripts/manage_plugins.py install codex_thread_handoff
```

`disable`、`enable` 和 `uninstall` 使用同一个 id，见[安装随附示例](../../governance-guide.zh.md#安装随附示例)。这些命令只管理 Git 忽略的本地目录中一份已审阅的 manifest，并重新校验插件宿主；它们不安装连接器、不开放网络访问，也不写 canonical memory。

## 数据、权限与导出

ResearchOS 插件是声明式的，不请求网络、命令或 canonical-write 权限。外部连接器负责本地 session 访问，必须使用固定的存储 allowlist、严格的 UUID 解析、有界分页、角色裁剪、脱敏和回执。thread 派生内容默认 `local_only`，从不进入自动导出；公开复用需要用户另行审阅。

## 验证

运行：

```bash
python3 scripts/validate_task_extensions.py
python3 -m unittest evals.test_codex_thread_handoff_extension
python3 scripts/validate_plugin_standard.py
```

然后按 [SETUP.zh.md](SETUP.zh.md) 用用户明确选定的 thread 验证连接器合同。不要把这个真实 UUID 提交到公开 fixture。

## 故障恢复

bridge 更新后工具缺失时，重启本地服务并刷新或重建客户端连接器，替换缓存的 MCP schema。工具已出现但当前会话运行时禁用插件时，通过“在聊天中试用”或会话插件选择器进入已启用插件的会话。thread 找不到时，检查 canonical UUID 和固定的 session roots。receipt 报告截断时，用返回的 cursor 继续，不得推断省略的内容已经读过。见 [TROUBLESHOOTING.zh.md](TROUBLESHOOTING.zh.md)。

## 价值与替代

对照对象是手工复制粘贴。只有真实交接能保留 provenance、减少上下文损失，足以抵消连接器配置、本地维护、格式漂移和残余脱敏风险时才保留。一次性或高度敏感的工作，手工摘录最小片段仍是最安全的后备。

## 退役

当受支持的宿主原生交接以更低负担提供同等的 local-only 权威、有界分页、脱敏/省略回执和公开/私有语义一致性，或真实使用显示它不比手工转移更好时退役。

## 过程与实现

本功能的数学伪代码、控制流程与实现边界见下文。扩展、桥接合同与就绪检查规定连接器使用，实际读取由宿主执行；分页和脱敏义务属于该方法合同。安装本身不证明连接器就绪。

数学符号是插件简写，定义见[插件目录首页](../README.zh.md)。插件体系处于冻结状态，见[治理指南](../../governance-guide.zh.md#任务扩展与插件)。

| 插件、形态与部署 | 核心算子或约束 | 含义、定义与核查 |
| --- | --- | --- |
| 任务交接 (`codex_thread_handoff`); $\mathsf P_i^{\mathrm{task}}$, 可选 | $H_{t,h}^a:=H_t^a\vert_h$; $Z_t=D_{\omega_t^u}(H_{t,h}^a,q_t)$ | 先把获准历史限制到指定任务 $h$，再选择续接所需上下文。连接器与回执记录访问、脱敏和截断；受限定义域排除无关任务历史。 |

### 任务交接

明确指定的任务 $h$、续接问题与连接器就绪状态；输出：带访问和截断状态的有界续接包。

```pseudocode
请求历史前，验证目标任务身份与连接器就绪状态
将读取限制到 $H_{t,h}^a\leftarrow H_t^a\vert_h$ 及获准访问预算
当仍需读取页面且预算未耗尽时：
    若已完成或游标重复：退出循环
    获取所需页面，记录游标与访问消耗
移除排除字段，保留省略或截断状态
令 $Z_t\leftarrow D_{\omega_t^u}(H_{t,h}^a,q_t)$
// 交接说明可供续做的根据，不表示已经执行续做
返回当前意图、决定、未决工作与来源引用
```

**算法解释。** 交接应提供足以恢复工作的根据，同时保留访问边界。任务身份限定读什么，游标与预算限定读多少，省略和截断状态说明交接尚未覆盖什么。
