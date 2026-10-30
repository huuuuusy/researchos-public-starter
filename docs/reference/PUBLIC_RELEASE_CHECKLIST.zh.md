<p align="right">
  <a href="PUBLIC_RELEASE_CHECKLIST.md">English</a> | <strong>中文</strong>
</p>

# 公开发布检查清单

- [ ] 在获准重建后运行 `python3 scripts/build_public_starter_data.py --check`；文件 hash 一致不能单独证明生成物与来源一致。
- [ ] 确认公开仓库是独立的 Git 项目。
- [ ] 确认根目录采用自定义 `ResearchOS Source-Available Research License`，而不是 PolyForm 许可证。
- [ ] 确认 `docs/reference/COMMERCIAL_USE.zh.md` 给出有意设置的公开书面授权联系路线。
- [ ] 确认 `corpus/` 为空，或只包含公开安全说明。
- [ ] 确认所有示例材料都是虚构、已清洗或明确授权公开的内容。
- [ ] 确认关键 Markdown 文档都有独立英文版和中文版。
- [ ] 确认英文文档不包含中文正文。
- [ ] 确认中文文档以中文为主，只在代码名、路径、命令、产品名和必要技术标识处保留英文。
- [ ] 运行 `python3 scripts/build_public_starter_data.py --write`，然后逐条运行 `.github/workflows/validate.yml` 中的步骤，即本仓库的 CI：投影构建、边界与合同校验器，以及 Python 和 JavaScript 回归测试。在本机运行其中的 `validate_release_metadata.py` 时，要在已提交、没有未提交改动的工作树上带 `--expected-commit "$(git rev-parse HEAD)" --require-clean`。
- [ ] 根据 `validate_task_extensions.py` 与 `validate_agent_architecture.py` 的结果，确认禁用示例不进入运行时，公开扩展不能绕过 authority 或 sensitivity 规则，前端模块均已注册、server 模块可达、已删除兼容代码/旧演示没有重新出现、owner 体量预算通过。
- [ ] 运行 `python3 scripts/plan_context.py --list --lang zh-CN` 及选定语言对应命令，确认核心/启用扩展均可达且不会装载冻结语言任务文案。
- [ ] 确认安全扫描同时覆盖代码和文档，并能发现本地路径、密钥、真实敏感人物和私人语义残留。
- [ ] 确认没有私人 sibling repository 的名称或路径、federation/catalog 元数据、operator 标识、请求回执或共享运行态。
- [ ] 确认公开 task extension 仍是本地声明式描述，不发现或调用私人系统。
- [ ] 本地打开仪表盘并完成一次浏览器冒烟检查。
- [ ] 完成当前 Unified Desk 的事项选择、日期预览与刷新恢复、组件查看、交接预览/复制；核对英文与中文界面、冻结内容语言和 `390 x 844` 移动端。Now/Library 是语义职责；页面中隐藏的兼容工作区标签不在本项检查的旅程之内。
- [ ] 单独核对现有 Agent/CLI 中的任务/结果边界、显式写回候选、连续性回执和本人确认；核对仍适用的真人交互验收与无障碍要求，未完成项保持开放，不用三项工作台任务代替。旧浏览器任务不能冒充当前项目事实。
- [ ] 确认本仓库的默认运行态为 `copy_only`，不探测本机 Codex，拒绝所有提交给 `codex` 或 `claude_code` provider 的 runner 请求，且不会启动线程或命令；另行验证 personal-vault 可显示受控 workspace-write 动作。
- [ ] 确认 `dashboard/index.html` 指向公开服务端口 `8880`，而不是其他本地服务端口。
- [ ] 从全新复制的文件夹启动，分别验证一条命令的 demo 路径和一个小型 personal-vault fixture。

打发布 tag 之前：

- [ ] 根据最终 commit 刷新 `docs/releases/v1.0.0.md` 及其中文版本中的验证快照；发布敏感改动后不得沿用旧工作树的计数或摘要。
- [ ] 在最终 clean commit 上运行 `python3 scripts/validate_release_metadata.py --release-date YYYY-MM-DD --expected-commit "$(git rev-parse HEAD)" --require-clean`；用外部参数把最终元数据、产物摘要与发布证据绑定到精确 ref，避免把 commit hash 自引用地写入生成文件。
- [ ] 确认 GitHub description 不再使用陈旧版本名，并补充公开安全 topics。
- [ ] 对公开项目名、署名、联系路线、仓库 description/topics 和确切 tag/Release 分别记录维护者明确决定。
- [ ] 批准后再启用 private vulnerability reporting、创建确认过的 tag/Release，并在未登录状态复查公开页面。

英文版本见 `docs/reference/PUBLIC_RELEASE_CHECKLIST.md`。
