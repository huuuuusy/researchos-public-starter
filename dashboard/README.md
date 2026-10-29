<p align="right">
  <strong>English</strong> | <a href="README.zh.md">中文</a>
</p>

# Dashboard Guide

The primary ResearchOS route is Markdown plus a repository-aware agent or CLI. The Dashboard is optional and frozen. It is one Unified Desk: select a research item, preview the calendar, inspect its components, and copy a bounded handoff to your agent client. It is not evidence of validated research benefit.

## Run

```bash
python3 scripts/start_researchos.py --mode dashboard --port 8880
```

The other modes, including the status check, are listed in [Section 4 of the User Manual](../docs/user-manual.en.md#4-the-optional-dashboard). For the first material set and the separate, git-ignored personal-vault projection, follow [Section 5](../docs/user-manual.en.md#5-your-own-material); this version does not show the first-run setup form that the [onboarding steps](../08_exports/public_starter/onboarding-step-by-step.md) use. Personal-vault execution depends on its separately registered runtime and permissions; starting the public demo never enables it.

Open the dashboard only through the launcher. `serve_dashboard.py` sends `Cache-Control: no-store` on every response, so neither the script and stylesheet references in `index.html` nor the imports in `style.css` carry `?v=` cache numbers, and the validators reject new ones; another static server may let the browser keep stale JS or CSS.

## Shortest UI Loop

1. Select an item on the Unified Desk. Calendar changes preview attention; they do not reschedule canonical work.
2. Inspect the item's state and select only the components needed for the task.
3. Copy the handoff and continue in your agent client. A copy action does not prove that a task ran or a file changed.
4. Verify the returned result or proposed durable change against its source and applicable authorization before admitting it to Markdown/Git.

`Now` and `Library` remain semantic roles and compatibility routes; they do not require separate screens. Work and Review belong to an exact item. Review distinguishes candidates, human disposition, mutation/validation state and receipts; archiving is not completion or acceptance.

## Client / Shell Boundary

The Dashboard hosts capability plugins and owns presentation, routing, accessibility and render lifecycle. It does not own canonical authority, domain writes, provider policy or admission decisions. Public-starter displays fictional or sanitized records and remains copy-only: no local Codex probe, provider execution or canonical writeback. Legacy routes fail closed without an exact item identity. Headless tools remain usable without the Dashboard.

See the [Client Shell Contract](../09_templates/data_contracts/researchos-client-shell-v1.json) for machine-readable boundaries, and [Section 4 of the User Manual](../docs/user-manual.en.md#4-the-optional-dashboard) for current interactions, language behavior and runtime details. This entrypoint does not duplicate their full workflows.
