<p align="right">
  <a href="README.md">English</a> | <strong>中文</strong>
</p>

# 脚本入口

本目录保存公开 starter 的运行和验证脚本。不要从每个 helper 文件开始读，先用下面几个入口。

| 入口 | 用途 | 边界 |
| --- | --- | --- |
| `python3 scripts/start_researchos.py` | 查看或启动 dashboard、CLI、GUI、public-starter 模式。 | 只是运行入口；provider 是执行适配器，不是记忆权威。 |
| `python3 scripts/receipt_cli.py --help` | 无需 Dashboard/server，在 Agent 客户端或终端中构建、校验或查看 ContextReceipt/HandoffReceipt JSON。 | 仅使用显式相对文件或 stdin/stdout；不发现材料、不调用 provider、不外发、不写 canonical、不覆盖文件、不签发人类判断。 |
| `python3 scripts/build_public_starter_data.py --write` | 从虚构 case 文件生成 demo records 和 dashboard 投影。 | 只读取公开 starter 材料，不读取非 demo 工作区材料。 |
| `python3 scripts/build_public_starter_data.py --disable-cases --write` | 关闭 demo case 后重新生成数据，同时保留示例文件作为参考。 | 在替换为用户自己的公开安全材料前使用。 |
| `python3 scripts/plan_context.py <task-id> --lang zh-CN` | 输出 20 个 public-safe task ID 或 13 个兼容别名的最小路线；`--intent-json`、`--prior-receipt-json` 与 `--headless-json` 提供 typed、有边界的任务连续性。 | 只读且 copy-only；route receipt 不授予 mutation、external effect、network、command 或 canonical write。 |
| `python3 scripts/query_plugin_portfolio.py` | 查询四个非 owning capability groups 及其声明式 contributions，不读取 Dashboard 字段。 | 只提供分组投影；登记、启用或测试通过都不等于 capability admitted。 |
| `python3 scripts/query_research_agenda.py` | 回答当前主导任务数，并返回覆盖与完整性证据。显式视图为 `lead-active`、`lead-all`、`support-active`、`support-all`、`waiting`、`queued`、`conditional`、`paused`、`review`、`unclassified` 与 `all`；旧的 `lead`/`support` 只表示活跃项。 | 从所选议程 Markdown 生成只读投影；缺失或无效的 responsibility fail closed，不从活动推断归属。 |
| `python3 scripts/validate_task_extensions.py` | 检查扩展 API 版本、读取上限、authority、语言和公开安全字段。 | Fail closed；不会启用或执行扩展。 |
| `python3 scripts/validate_plugin_standard.py` | 检查显式治理、来源与许可、部署、效果、组合、路由、成熟度证明与退役；加 `--public-root` 检查语义变体一致性。 | Fail closed；不安装、不执行，也不吸收 capability。 |
| `python3 scripts/manage_plugins.py install method_comparison` | 安装、校验、停用、启用或卸载仓库随附的示例插件。 | 只使用 Git 忽略的本地状态；可逆，不联网、不执行远程代码、不写 canonical memory。 |
| `python3 scripts/plan_evolution.py` | 显示有路径边界的维护候选；只有精确确认 plan ID 后才运行固定安全子集。 | 公开 demo 保持只读；personal-vault checkpoint 仅存本地并由 Git 忽略。 |
| `python3 scripts/validate_evolution_control.py` | 检查计划、固定步骤、确认、运行模式和公私隔离契约。 | 只报告，不执行维护。 |
| `python3 scripts/check_all_links.py` | 检查公开 starter 内部 Markdown 链接。 | 只报告问题，不改写文档。 |
| `python3 scripts/validate_runtime_config.py` | 检查运行配置与 provider 登记边界。 | 公开 starter 默认 demo-first，不提交本地 API key。 |
| `python3 scripts/validate_public_safety.py` | 扫描文档、代码、配置和 demo 数据中的私人语义残留、用户路径、密钥和 raw corpus payload。 | 只是发布闸门，不上传或发布任何内容。 |
| `python3 scripts/validate_docs_bilingual.py` | 确认面向读者的中英文文档持续成对、互相链接，并保持相关工具的名称、项目 URL、顺序、快照日期和非背书边界一致。 | 只是文档闸门，不自动翻译、不判断外部来源是否仍为官方或可访问，也不改写文件。 |
| `python3 scripts/validate_positioning_consistency.py` | 保持中英文活跃入口一致声明：小型文件化科研工具、Agent/CLI 负责主要执行、Dashboard 是收窄的跨会话注意力与控制面。 | 定位闸门；拒绝入口并列、dashboard-first、Workbench-first 和含混的“次要 Dashboard”表述。 |
| `python3 scripts/validate_release_metadata.py` | 保持发布说明、引用信息、更新记录、页面许可和产物 SHA-256 摘要一致。 | 只是发布元数据闸门，不创建 tag 或公开发布。`CITATION.cff` 声明 `date-released` 后，必须传入 `--expected-commit <full-sha> --require-clean`（`--release-date YYYY-MM-DD` 可选，须与之一致）。 |
| `python3 scripts/validate_agent_architecture.py` | 检查 Agent 代码路线、受支持导入、前端脚本注册和 owner 文件体量预算。 | 只是架构闸门，不改写代码。 |
| `python3 -m unittest discover -s evals -p 'test_*.py'` | 运行构建器、前端、runner、本地文件 bridge 和安全回归测试，包括 metadata profile、Rule evolution、admission state 与 RuntimeProfile 的 schema/owner 一致性。 | 只在本地测试。 |

Helper package：

- `researchos_data/`：受支持 owner 包括维护、声明式任务、插件宿主/归属/生命周期、对话 authority、仓库布局、公开 catalog，以及只读 frontend/style manifests；`validate_agent_architecture.py` 会拒绝未登记 helper。
- `researchos_kernel/` 与 `researchos_adapters/`：各自负责什么、依赖朝哪个方向，只在[代码地图](../docs/system-reference.zh.md#代码地图)写一次。
- `researchos_server/`：本地 dashboard server owner package；store、Codex runner、preview/source 和 maintenance 各自拥有规则，`serve_dashboard.py` 只负责 HTTP 路由与依赖装配。

修改代码前先读 `docs/system-reference.zh.md` 中的代码地图，不要先扫描所有 helper 或生成 JSON。
