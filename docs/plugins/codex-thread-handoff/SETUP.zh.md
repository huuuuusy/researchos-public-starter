---
title: Codex Thread Handoff 设置
sensitivity: public_safe
status: active
---

<p align="right"><a href="SETUP.md">English</a> | <strong>中文</strong></p>

# 设置

1. 在 ResearchOS 根目录运行 `python3 scripts/manage_plugins.py install codex_thread_handoff`，再运行 `python3 scripts/manage_plugins.py status codex_thread_handoff`；这一步只建立任务合同。
2. 运行一个满足 [BRIDGE_CONTRACT.zh.md](BRIDGE_CONTRACT.zh.md) 的本地只读 MCP connector，并仅绑定 loopback；token 不进入 URL 或 source control。
3. 个人/开发模式优先参考 OpenAI 官方 [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)：`tunnel-client` 从本机发起出站 HTTPS，可转发 stdio 或 HTTP MCP，而无需公开 listener 或开放入站端口。它不是公开 plugin submission endpoint；用户自有且带认证的 HTTPS tunnel 也可作为替代。
4. 在客户端注册 connector。tool schema 变化后必须重启本地服务并刷新或重建 connector，因为客户端可能缓存工具列表。ChatGPT 中还要在已安装插件的管理页确认刷新后的操作，再通过“在聊天中试用”或会话输入区的插件选择器进入已启用插件的新会话；不能只用旧会话判断部署是否成功。
5. 分别核验插件 enabled、两个必需工具出现、测试会话已附加插件、有界 list receipt、长 thread 至少两页、隐藏角色/tool payload 不出现、fake secret 被脱敏，以及 connector/thread 消失时 fail closed。全部满足后才称为 `ready`。
