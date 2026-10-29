---
title: Codex Thread Handoff 安全边界
sensitivity: public_safe
status: active
---

<p align="right"><a href="SECURITY.md">English</a> | <strong>中文</strong></p>

# 安全边界

需要保护的资产包括对话文本、本地身份与路径、误粘贴凭证、隐藏指令/reasoning、tool payload，以及 Codex home 下的其他文件。MCP caller 和 session 文件内容都视为不可信；本地用户控制进程配置，caller 永远不能控制 storage roots。

公开包只能包含协议、测试和设置说明，不得包含真实 endpoint、token、用户名、home path、thread UUID、session fixture、project label 或私有 connector 输出。任意路径输入、symlink escape、raw fallback、无界读取、未绑定 source 的 cursor、URL credential 都是 release blocker。Regex 脱敏不能识别所有私人事实，因此数据最小化和用户主动选择 thread 才是第一道边界。

远程可达时使用 authenticated HTTPS、最小权限、token rotation、loopback binding 和可停止的服务生命周期。Tunnel 只提供 reachability，不自动提供 multi-tenant isolation 或内容安全。
