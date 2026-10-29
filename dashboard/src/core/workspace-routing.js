/* ResearchOS maintenance header.
 * 中文：ResearchOS dashboard 浏览器端核心基础能力「workspace routing」；供 app、service、view 复用。
 * English: Browser-side core primitive for workspace routing in the ResearchOS dashboard; shared by app, services, and views.
 */

(function attachResearchOSWorkspaceRouting(global) {
  const SurfaceContract = global.ResearchOSSurfaceContract || {};
  const taskWorkspaceMap = SurfaceContract.taskWorkspaceMap || Object.freeze({});
  const targetWorkspaceMap = SurfaceContract.targetWorkspaceMap || Object.freeze({});
  const canonicalSurface = SurfaceContract.canonicalSurface || ((value) => String(value || ""));

  function workspaceForTarget(targetId, fallback = "") {
    return targetWorkspaceMap[String(targetId || "")] || canonicalSurface(fallback);
  }

  global.ResearchOSWorkspaceRouting = {
    targetWorkspaceMap,
    taskWorkspaceMap,
    workspaceForTarget,
  };
})(window);
