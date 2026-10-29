/* ResearchOS maintenance header.
 * 中文：外部画像快照的启动边界；页面加载只读取现有快照，绝不自行触发外发或写回。
 * English: Startup boundary for external-profile snapshots; page load reads the current snapshot and never initiates egress or writes.
 */

(function attachResearchOSDailyProfileRefreshClient(global) {
  async function refreshIfDue() {
    return {
      ok: true,
      skipped: true,
      dashboard_rebuilt: false,
      reason: "explicit_authorization_required",
    };
  }

  global.ResearchOSDailyProfileRefreshClient = Object.freeze({ refreshIfDue });
})(window);
