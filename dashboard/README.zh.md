<p align="right">
  <a href="README.md">English</a> | <strong>中文</strong>
</p>

# Dashboard 指南

ResearchOS 的主路径是 Markdown 加能读取仓库的代理或 CLI。Dashboard 是可选的，已经冻结。它只有一个 Unified Desk：选择研究事项、预览日历、查看组件，再复制有界任务包到 Agent 客户端。它不证明研究收益已验证。

## 启动

```bash
python3 scripts/start_researchos.py --mode dashboard --port 8880
```

其他模式，包括状态检查，见[用户手册第 4 节](../docs/user-manual.zh.md#4-可选的-dashboard)。第一组材料和独立、被 Git 忽略的 personal-vault 投影按[第 5 节](../docs/user-manual.zh.md#5-用自己的材料)准备；本版页面不显示[入门步骤](../08_exports/public_starter/onboarding-step-by-step.zh.md)所用的首次设置表单。Personal-vault 执行取决于另行登记的 runtime 与权限；启动公开演示不会启用它。

请只通过启动脚本打开页面。`serve_dashboard.py` 对每个响应都发 `Cache-Control: no-store`，所以 `index.html` 的脚本、样式引用和 `style.css` 的样式导入都不带 `?v=` 缓存号，校验器也拒绝新加的缓存号；换用别的静态服务器时，浏览器可能沿用旧的 JS 或 CSS。

## 最短界面流程

1. 在 Unified Desk 选择事项。日历变化只预览注意力，不改动 canonical 工作安排。
2. 核对事项状态，只选择本任务需要的组件。
3. 复制任务包，在 Agent 客户端继续。复制不证明任务已运行或文件已改变。
4. 对照来源及适用授权核验结果和长期变更，再决定是否纳入 Markdown/Git。

`Now` 与 `Library` 保留为语义角色和兼容路由，不要求独立屏幕。Work 与 Review 属于明确事项。Review 区分候选、本人裁决、写入/验证状态和回执；归档不等于完成或接受。

## Client / Shell 边界

Dashboard 承载 capability plugins，拥有呈现、路由、可访问性与渲染生命周期；不拥有 canonical authority、领域写入、provider policy 或采纳决定。Public-starter 只呈现虚构或脱敏记录，保持 copy-only：不探测本地 Codex、不执行 provider、不写回 canonical。旧路由缺少确切事项身份时拒绝继续。无 Dashboard 时仍能使用 headless 工具。

机器边界见 [Client Shell Contract](../09_templates/data_contracts/researchos-client-shell-v1.json)，当前交互、语言行为和运行细节见[用户手册第 4 节](../docs/user-manual.zh.md#4-可选的-dashboard)。本入口不重复这些 owner 的完整工作流。

Agent 客户端或 CLI 返回结果后，先核对来源和完成标准；只有明确授权的长期变化才进入确认与验证。Dashboard 的复制动作不代表任务执行完成。
