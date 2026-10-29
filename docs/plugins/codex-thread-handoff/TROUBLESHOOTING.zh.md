---
title: Codex Thread Handoff 排错
sensitivity: public_safe
status: active
---

<p align="right"><a href="TROUBLESHOOTING.md">English</a> | <strong>中文</strong></p>

# 排错

- 插件已安装但工具不存在：插件和 connector 是两个控制面。检查 bridge，重启后刷新或重建客户端 connector 以替换缓存 schema。
- 工具已出现但当前 ChatGPT 会话禁用它：工具发现和会话运行时启用是两项检查。在已安装插件的管理页刷新操作，然后通过“在聊天中试用”或会话输入区的插件选择器进入已启用插件的会话；旧会话在全局操作列表刷新后仍可能保留旧运行时。
- 工具存在但 thread 找不到：使用小写 canonical UUID 或精确 URI，确认 session 位于 allowlisted roots；不能通过增加任意 path 参数绕过。
- 读取提前结束：检查 receipt 中的 `next_cursor`/`next_offset` 与 source/page truncation，只沿返回的 cursor 继续；达到硬上限时明确未读完整。
- 本地可用但 ChatGPT 不可用：检查 authenticated HTTPS、精确 MCP endpoint、tunnel health 和 connector 状态，凭证不要放 query string。
- 格式变化：fail closed，并为新 Codex event shape 增加 synthetic fixture；不要扩大扫描或返回 raw JSONL。
- 安全 fallback：让用户粘贴最小相关片段，并标注为手工提供的上下文，不假装 connector 已验证。
