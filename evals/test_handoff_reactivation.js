const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const records = new Map();
global.window = global;
global.localStorage = {
  getItem(key) {
    return records.has(key) ? records.get(key) : null;
  },
  setItem(key, value) {
    records.set(key, String(value));
  },
};

for (const relativePath of [
  "dashboard/src/services/doing-board-state.js",
  "dashboard/src/services/inbox.js",
]) {
  const source = fs.readFileSync(path.join(__dirname, "..", relativePath), "utf8");
  vm.runInThisContext(source, { filename: relativePath });
}

const item = { type: "project", title: "Reactivated project", status: "done" };
const first = ResearchOSDoingBoardState.upsertItem([item], item, "today");
assert.equal(first.item.status, "local", "legacy Today drafts must migrate to an honest browser-local status when reactivated");
assert.equal(
  ResearchOSDoingBoardState.normalizeItem({ type: "task", title: "Legacy Today draft", status: "today" }).status,
  "local",
  "stored legacy Today labels must migrate during dashboard startup"
);

const actionId = ResearchOSDoingBoardState.itemKey(first.item);
const governedItem = ResearchOSDoingBoardState.normalizeItem({
  admission_state: {
    schema_id: "researchos-admission-state-v1",
    decision_state: "proposed",
    mutation_state: "not_requested",
    validation_state: "unvalidated",
    authority_role: "none",
  },
  current_state: "No canonical memory change has occurred",
  evidence_state: "candidate",
  impact_scope: "This session only",
  proposed_state: "Return candidate results",
  sensitivity: "internal",
  title: "Governed task",
  type: "task",
});
const governedCandidate = ResearchOSInboxService.candidateEnvelopeForEntry({
  actionId: ResearchOSDoingBoardState.itemKey(governedItem),
  raw: governedItem,
  status: governedItem.status,
  title: governedItem.title,
  type: "task",
});
assert.equal(governedCandidate.evidence_state, "candidate");
assert.equal(governedCandidate.admission_state.decision_state, "proposed");
assert.equal(governedCandidate.admission_state.mutation_state, "not_requested");
assert.equal(governedCandidate.sensitivity, "internal");
assert.equal(governedCandidate.transition.current_state, "No canonical memory change has occurred");
assert.equal(governedCandidate.transition.proposed_state, "Return candidate results");
assert.equal(governedCandidate.transition.impact_scope, "This session only");
assert.equal(governedCandidate.transition.validation_state, "unvalidated");

const sameTitleFirst = ResearchOSDoingBoardState.upsertItem([], { type: "task", title: "Same visible title" });
const sameTitleSecond = ResearchOSDoingBoardState.upsertItem(sameTitleFirst.items, { type: "task", title: "Same visible title" });
assert.equal(sameTitleSecond.items.length, 2, "two unbound tasks must not collapse merely because their titles match");
assert.notEqual(sameTitleSecond.items[0].id, sameTitleSecond.items[1].id, "new unbound tasks require distinct opaque identities");

const handoffFirst = ResearchOSDoingBoardState.upsertItem([], {
  type: "task", title: "Original task title", path: "old.md", work_session_id: "session-identity-fixture",
});
const handoffSecond = ResearchOSDoingBoardState.upsertItem(handoffFirst.items, {
  type: "task", title: "Revised task title", path: "new.md", work_session_id: "session-identity-fixture",
});
assert.equal(handoffSecond.items.length, 1, "the same Work Session handoff must update one record across title or path changes");
assert.equal(handoffSecond.item.id, "handoff:work-session:session-identity-fixture");
assert.equal(handoffSecond.item.title, "Revised task title");
assert.equal(ResearchOSDoingBoardState.itemKey(handoffSecond.item), handoffSecond.item.id, "handoff lookup must use the stable record id");

const legacyIdentity = ResearchOSDoingBoardState.normalizeItem({ type: "task", title: "Legacy title-only task" });
assert.equal(legacyIdentity.id, "task:Legacy title-only task", "legacy persisted records must retain their recoverable historical key");
assert.equal(legacyIdentity.identity_kind, "legacy");
for (const storageKey of ["active-archive", "resolved-archive"]) {
  ResearchOSInboxService.archiveUnifiedInboxEntry({
    storageKey,
    type: "task",
    id: actionId,
    entry: { title: item.title },
  });
  assert.ok(ResearchOSInboxService.loadUnifiedInboxArchive(storageKey)[`task:${actionId}`]);
  ResearchOSInboxService.restoreUnifiedInboxEntry({ storageKey, type: "task", id: actionId });
  assert.equal(ResearchOSInboxService.loadUnifiedInboxArchive(storageKey)[`task:${actionId}`], undefined);
}

assert.equal(
  ResearchOSInboxService.completedRunCanArchiveEntry(
    { status: "completed", finished_at: "2026-07-10T10:00:00Z" },
    { updatedAt: "2026-07-11T10:00:00Z" }
  ),
  false,
  "an older completed run must not archive a newly re-added handoff"
);
assert.equal(
  ResearchOSInboxService.completedRunCanArchiveEntry(
    { status: "completed", finished_at: "2026-07-12T10:00:00Z" },
    { updatedAt: "2026-07-11T10:00:00Z" }
  ),
  true,
  "a completion newer than the handoff may archive it"
);

console.log("Handoff reactivation regression passed.");
