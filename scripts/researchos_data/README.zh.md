# 公开数据 Helper 边界

## Agent Summary

本仓库 在这里保留一组刻意收窄的 owner：`maintenance_pipeline.py` 管理本地 auto-update 顺序，`task_extensions.py` 负责通过验证的声明式任务路线，`plugin_lifecycle.py` 负责可逆安装仓库随附示例，`conversation_contract.py` 负责结果与写回权威，`repository_layout.py` 负责个人材料层；frontend/style manifests 只作为只读验证输入。

请改用这些入口：

- `scripts/build_public_starter_data.py`：生成 demo 或 personal-vault 投影；
- `scripts/start_researchos.py`：启动本地 runtime；
- `scripts/manage_plugins.py`：安装、停用、启用或卸载仓库随附示例；
- `scripts/validate_public_safety.py`：检查发布安全；
- `scripts/check_all_links.py` 与 `evals/`：检查链接和回归行为。

新行为必须放到有文档说明的入口和明确 owner 模块后面，并补回归测试。若重新加入无入口 data helper，`scripts/validate_agent_architecture.py` 会失败。
