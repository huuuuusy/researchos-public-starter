<p align="right">
  <a href="README.md">English</a> | <strong>中文</strong>
</p>

# 数据契约

定义 dashboard、导出、候选记录、关系解释和验证脚本之间的公开安全字段约定。

- `researchos-primitive-contract-v1.md/json`：source、card、relation、candidate、confirmation、action、validation、export 等基础对象。
- `researchos-capability-registry-v1.md/json`：可暴露给 dashboard 或 Agent 的能力注册格式。
- `researchos-relation-semantics-contract-v1.md/json`：关系类型、关系状态和人物关系安全规则。
- `researchos-extension-contract-v1.md`：新增资产类别、资源对象、工作流对象、dashboard 界面和导出目标前的扩展契约。
- `researchos-task-extension-v1.schema.json`：dashboard builder 与 `scripts/plan_context.py` 共用的声明式任务扩展 schema。
- `researchos-task-intent-v1.schema.json`：不可信客户端请求合同；它不能授予权限、runtime scope、幂等性或长期权威。
- `researchos-task-envelope-v1.schema.json`：服务端拥有的 pre-policy 执行 envelope；它分开保存请求值与实际运行事实，授权保持未解析，公开投影必须剥离整份 envelope。
- `researchos-projection-envelope-v1.schema.json`：浏览器侧版本化插件投影边界，显式携带敏感度、新鲜度、状态、错误与 payload。
- `researchos-client-shell-v1.json`：可选 Dashboard application shell 的机器可读边界，声明语义 surface catalog、profile-defined routing、事项内 Work/Review、允许端口、插件宿主角色、禁止所有权与无 Dashboard 闭环。
- `researchos-metadata-profile-v1.schema.json`：新 Markdown metadata 使用的严格 lifecycle、authority、sensitivity、export 与 owner 词汇；legacy 读取保持独立兼容投影。
