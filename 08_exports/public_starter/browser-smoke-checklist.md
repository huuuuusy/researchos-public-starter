<p align="right">
  <strong>English</strong> | <a href="browser-smoke-checklist.zh.md">中文</a>
</p>

# Browser Smoke Checklist

After starting the dashboard, use this checklist to confirm that the public version shows demo data rather than non-public content.

| Area | Action | Pass Criteria |
| --- | --- | --- |
| Workbench | Open the dashboard and start one task from a goal, link/path, or file name. | The current Work Session appears before suggestions and does not become durable memory. |
| Workbench result | Submit one goal and source, then follow up. | A complete copyable task packet appears. No local/remote execution or forced file is created. |
| Assets | Search globally, select one demo card, and choose `Use in current task`. | The card joins the working deck without creating a Review item. |
| Review | Choose `Propose write-back`, then edit the goal or deck and finish the session. | Only the proposed durable change enters Review; completion moves it to history. Public durable-writeback actions remain copy-only. |
| Language | Switch the page language, then refresh. | UI copy changes and the Work Session persists; active prompt/template language does not change without a rebuild. |
| Boundary | Inspect Workbench and Review controls plus the browser console. | Public-starter remains copy-only; no local/remote provider, arbitrary command, durable writeback, private path, or console error appears. |
| Mobile | Repeat the three tabs at `390 x 844`. | Text and controls do not overlap and the page has no horizontal overflow. |

If real sensitive content, local paths, API keys, or non-public project state appear, stop the release and return to safe export review.
