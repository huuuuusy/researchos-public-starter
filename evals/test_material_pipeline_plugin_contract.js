const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

global.window = global;
const browserEventListeners = new Map();
global.addEventListener = (type, callback) => {
  const callbacks = browserEventListeners.get(type) || [];
  callbacks.push(callback);
  browserEventListeners.set(type, callbacks);
};
global.document = { querySelectorAll: () => [] };
const values = new Map();
global.localStorage = {
  getItem(key) { return values.has(key) ? values.get(key) : null; },
  setItem(key, value) { values.set(key, String(value)); },
  removeItem(key) { values.delete(key); },
};
global.fetch = async () => ({ ok: true, json: async () => ({ ok: true }) });
global.ResearchOSRequestAuth = { resolveFetcher: (fetcher) => fetcher || global.fetch };
global.ResearchOSStatePolicy = {
  readJsonArray(key) {
    try {
      const value = JSON.parse(global.localStorage.getItem(key) || "[]");
      return Array.isArray(value) ? value : [];
    } catch {
      return [];
    }
  },
  writeJsonArray(key, items, { limit = 80 } = {}) {
    global.localStorage.setItem(key, JSON.stringify((items || []).slice(0, limit)));
  },
};
global.ResearchOSStorageContract = {
  storageKeys: {
    materialIntakeInbox: "test-material-intake",
    materialUpgradeInbox: "test-material-upgrade",
    researchScoutInbox: "test-scout",
  },
  activeContextPaths: {
    materialIntake: "06_active_context/ui-material-intake-inbox.md",
    materialUpgrade: "06_active_context/ui-material-upgrade-inbox.md",
    researchScout: "06_active_context/ui-research-scout-inbox.md",
  },
};

function load(relativePath) {
  const source = fs.readFileSync(path.join(__dirname, "..", relativePath), "utf8");
  vm.runInThisContext(source, { filename: relativePath });
}

load("dashboard/src/services/action-inbox-state.js");
load("dashboard/src/services/queue-sync.js");
load("dashboard/src/services/inbox.js");
load("dashboard/src/services/plugin-runtime.js");
load("dashboard/src/services/onboarding-workbench.js");
load("dashboard/src/views/onboarding.js");
load("dashboard/src/plugins/material-pipeline.js");

const dashboardIndex = fs.readFileSync(path.join(__dirname, "..", "dashboard/index.html"), "utf8");
for (const asset of ["src/services/onboarding-workbench.js", "src/views/onboarding.js", "src/plugins/material-pipeline.js"]) {
  assert.ok(dashboardIndex.includes(`<script src="${asset}"></script>`), `${asset} must be loaded by index.html`);
}

function registry(candidateTypes = []) {
  return {
    plugins: {
      schema_id: "researchos-plugin-v1",
      core_api_version: "1",
      loaded: candidateTypes.length ? [{ id: "material_pipeline" }] : [],
      contributions: {
        candidate_types: candidateTypes.map((id) => ({ id, plugin_id: "material_pipeline", plugin_version: "1.0.0" })),
      },
    },
  };
}

(async () => {
const text = (key) => key;
const disabled = registry([]);
assert.equal(ResearchOSPluginRuntime.collectCandidateEntries({ data: disabled, context: { text } }).entries.length, 0);
assert.equal(
  (await ResearchOSPluginRuntime.runCandidateAction({
    action: "generate",
    candidateType: "material_intake",
    data: disabled,
    payload: { id: "disabled", title: "Disabled lead" },
  })).handled,
  false,
  "a candidate type absent from the manifest must fail closed",
);

const intakeOnly = registry(["material_intake"]);
const generatedIntake = await ResearchOSPluginRuntime.runCandidateAction({
  action: "generate",
  candidateType: "material_intake",
  data: intakeOnly,
  payload: {
    id: "intake-1",
    material_id: "intake-1",
    material_type: "paper",
    title: "A new paper",
    source_path: "01_knowledge/papers/example.md",
    target_hint: "01_knowledge/papers/own_papers/reading_notes/",
    status: "pending_codex_review",
    sensitivity: "local_only",
  },
});
assert.equal(generatedIntake.handled, true);
assert.equal(generatedIntake.result.ok, true);
let intakeProjection = ResearchOSPluginRuntime.collectCandidateEntries({ data: intakeOnly, context: { text } });
assert.equal(intakeProjection.entries.length, 1);
assert.equal(intakeProjection.sourceEntries.length, 1);
assert.equal(intakeProjection.entries[0].path, "01_knowledge/papers/example.md", "candidate preview uses its declared source path");
assert.equal(intakeProjection.entries[0].candidate.plugin_id, "material_pipeline");
assert.equal(intakeProjection.entries[0].candidate.candidate_type, "material_intake");
assert.equal(intakeProjection.entries[0].candidate.required_confirmation, "confirm");

const requiredEnvelopeFields = [
  "candidate_id",
  "plugin_id",
  "candidate_type",
  "source_refs",
  "summary",
  "proposed_action",
  "proposed_writeback",
  "sensitivity",
  "required_confirmation",
  "validation",
  "admission_state",
];
requiredEnvelopeFields.forEach((field) => assert.ok(Object.hasOwn(intakeProjection.entries[0].candidate, field), field));

const normalizedInbox = ResearchOSInboxService.collectUnifiedInboxEntries(
  {
    candidateEntries: intakeProjection.entries,
    candidateSourceEntries: intakeProjection.sourceEntries,
  },
  { text },
);
assert.equal(normalizedInbox.total, 1);
assert.equal(normalizedInbox.entries[0].candidate.candidate_id, "candidate:material_intake:intake-1");
assert.equal(normalizedInbox.entries[0].candidate.admission_state.decision_state, "proposed");
assert.equal(normalizedInbox.entries[0].candidate.admission_state.mutation_state, "not_requested");
assert.ok(!Object.hasOwn(normalizedInbox.entries[0].candidate.validation, "authority_state"));
assert.equal(normalizedInbox.entries[0].candidate.proposed_writeback.save_target, "01_knowledge/papers/own_papers/reading_notes/");

await ResearchOSPluginRuntime.runCandidateAction({
  action: "withdraw",
  candidateType: "material_intake",
  data: intakeOnly,
  id: "intake-1",
});
intakeProjection = ResearchOSPluginRuntime.collectCandidateEntries({ data: intakeOnly, context: { text } });
assert.equal(intakeProjection.entries.length, 0, "withdraw removes the active intake candidate");

const upgradeOnly = registry(["upgrade"]);
await ResearchOSPluginRuntime.runCandidateAction({
  action: "generate",
  candidateType: "upgrade",
  data: upgradeOnly,
  payload: {
    id: "upgrade-1",
    title: "Upgrade paper",
    path: "01_knowledge/papers/example.md",
    current_state: "M1_registered",
    target_state: "M2_refined_read",
  },
});
const upgradeProjection = ResearchOSPluginRuntime.collectCandidateEntries({ data: upgradeOnly, context: { text } });
assert.deepEqual(upgradeProjection.entries.map((entry) => entry.type), ["upgrade"]);
assert.equal(upgradeProjection.entries[0].candidate.proposed_writeback.current_state, "M1_registered");
assert.equal(upgradeProjection.entries[0].candidate.proposed_writeback.proposed_state, "M2_refined_read");

const scoutOnly = registry(["scout"]);
const scoutRecord = ResearchOSMaterialPipelinePlugin.scoutInboxRecord(
  { agent_prompt: "Search recent work", queries: ["demo query"] },
  { topic: "Recent multimodal reliability", intent: "literature" },
  { idFactory: () => "scout-1", now: () => "2026-08-05T00:00:00Z" },
);
await ResearchOSPluginRuntime.runCandidateAction({
  action: "generate",
  candidateType: "scout",
  data: scoutOnly,
  payload: scoutRecord,
});
const scoutProjection = ResearchOSPluginRuntime.collectCandidateEntries({ data: scoutOnly, context: { text } });
assert.deepEqual(scoutProjection.entries.map((entry) => entry.type), ["scout"]);
assert.equal(scoutProjection.entries[0].candidate.required_confirmation, "handoff_only");
assert.equal(scoutProjection.entries[0].candidate.proposed_action.target_agent, "research_scout");

const allTypes = registry(["material_intake", "upgrade", "scout"]);
assert.deepEqual(
  ResearchOSPluginRuntime.collectCandidateEntries({ data: allTypes, context: { text } }).entries.map((entry) => entry.type).sort(),
  ["scout", "upgrade"],
  "each manifest contribution independently controls only its candidate type",
);

const onboardingDraft = {
  name: "Dr. Example",
  role: "Researcher",
  affiliation: "Example University",
  themes: ["reliable AI", "multimodal learning"],
  scholarUrl: "https://scholar.google.com/citations?user=example",
  researchGateUrl: "",
  homepageUrl: "https://example.org",
  otherUrls: [],
  privateNotes: "Keep unpublished work local.",
};
const onboardingManifest = JSON.parse(ResearchOSMaterialPipelinePlugin.onboardingManifest(
  onboardingDraft,
  ["06_active_context/work_state/uploads/cv-example.pdf"],
  "en",
));
const onboardingManifestPath = "06_active_context/work_state/uploads/researchos-onboarding-intake-example.json";
const onboardingPrompt = ResearchOSMaterialPipelinePlugin.onboardingPrompt(onboardingManifestPath, "en");
assert.equal(onboardingManifest.schema, "researchos_onboarding_intake_v1");
assert.equal(onboardingManifest.boundary_confirmation.reusable_after_refresh, false);
assert.equal(onboardingManifest.sources.public_urls[0], "https://scholar.google.com/citations?user=example");
assert.equal(onboardingManifest.sources.local_uploaded_files[0], "06_active_context/work_state/uploads/cv-example.pdf");
assert.ok(onboardingPrompt.includes("Create 00_identity/user-card.md"));
assert.ok(onboardingPrompt.includes("Build 01_knowledge/papers/publication-index.md"));
assert.ok(!onboardingPrompt.includes("Create personal_vault/"), "the vault-scoped worker must not create a nested personal_vault directory");
assert.ok(onboardingPrompt.includes("local server performs the registered personal-vault projection refresh"));
assert.ok(!onboardingPrompt.includes("Run python3 scripts/build_public_starter_data.py"), "the vault-scoped worker must not receive an out-of-sandbox projection write");
assert.ok(onboardingPrompt.includes("zero to five representative paper cards"));
assert.ok(onboardingPrompt.includes(onboardingManifestPath));
assert.ok(!onboardingPrompt.includes("https://scholar.google.com/citations?user=example"), "the runner prompt must reference the complete local manifest instead of copying user sources into a bounded prompt");
assert.ok(onboardingPrompt.includes("Do not commit or push anything"));
assert.ok(onboardingPrompt.includes("Do not bypass login, paywalls, robots restrictions, or access controls"));
assert.ok(onboardingPrompt.includes("Reject URL credentials and loopback, local, or private-network destinations"));
assert.ok(onboardingPrompt.includes("Every generated Markdown file must begin with valid YAML frontmatter"));
assert.ok(onboardingPrompt.includes("non-empty ## Agent Summary"));
assert.ok(onboardingPrompt.includes("type: person"));
assert.ok(onboardingPrompt.includes("analysis_state: M1_registered"));
assert.ok(onboardingPrompt.includes("onboarding_origin: researchos_onboarding_v1"));
assert.ok(onboardingPrompt.includes("analysis state may be upgraded later"));
assert.ok(onboardingPrompt.includes("untrusted source data"));
assert.ok(onboardingPrompt.includes("downloaded PDFs are local source copies"));
const publicOnboarding = ResearchOSOnboardingView.renderPublicStart({
  escapeHtml: String,
  guidePath: "08_exports/public_starter/onboarding-step-by-step.md",
  previewButton: (pathValue) => `<button data-preview-path="${pathValue}">guide</button>`,
  translate: (key) => key,
});
const personalOnboarding = ResearchOSOnboardingView.renderPersonalWizard({ draft: onboardingDraft, recordCount: 0 }, { escapeHtml: String, translate: (key) => key });
const staleConsentOnboarding = ResearchOSOnboardingView.renderPersonalWizard({ draft: { ...onboardingDraft, consent: true }, recordCount: 0 }, { escapeHtml: String, translate: (key) => key });
const refreshedOnboarding = ResearchOSOnboardingView.renderPersonalWizard({ draft: {}, recordCount: 4 }, { escapeHtml: String, translate: (key) => key });
assert.ok(publicOnboarding.includes("data-onboarding-copy-command"));
assert.ok(publicOnboarding.includes("onboarding-step-by-step.md"));
assert.ok(publicOnboarding.includes('id="onboarding-public-status"'));
assert.equal((publicOnboarding.match(/<li>/g) || []).length, 4, "public onboarding should expose the complete four-step first-run path");
assert.ok(publicOnboarding.indexOf("data-onboarding-copy-command") < publicOnboarding.indexOf("<ol>"), "the public first action must appear before the mobile step cards");
assert.ok(personalOnboarding.includes("data-onboarding-step-panel=\"4\""));
assert.ok(personalOnboarding.includes('aria-labelledby="onboarding-step-title-1"'));
assert.ok(personalOnboarding.includes('id="onboarding-personal-status"'));
assert.ok(personalOnboarding.includes('aria-atomic="true"'));
assert.ok(personalOnboarding.includes("data-onboarding-files"));
assert.ok(personalOnboarding.includes("onboardingOptionalProfile"), "optional profile fields must be progressively disclosed");
assert.ok(personalOnboarding.includes("onboardingOptionalLinks"), "secondary public links must be progressively disclosed");
assert.ok(personalOnboarding.includes("onboardingOptionalBoundary"), "optional local constraints must be progressively disclosed");
assert.ok(personalOnboarding.includes("data-onboarding-review-source-list"), "boundary confirmation must show the exact public links that will be read");
assert.ok(personalOnboarding.includes("data-onboarding-review-file-list"), "boundary confirmation must show the exact local files that will be read");
assert.ok(personalOnboarding.includes('name="scholar_url" type="url"'));
assert.ok(!personalOnboarding.includes('name="scholar_url" type="url" maxlength='), "public-source URLs must not be cut off by an arbitrary UI quota");
assert.ok(!personalOnboarding.includes('name="other_urls" rows="3" maxlength='), "the source list must not have an arbitrary aggregate UI quota");
assert.ok(personalOnboarding.includes('name="bio" rows="3" maxlength="3000"'));
assert.ok(personalOnboarding.includes('data-onboarding-disclosure="open"'));
assert.ok(!/name="consent"[^>]*checked/.test(staleConsentOnboarding), "consent must never be restored from a saved draft");
assert.ok(refreshedOnboarding.includes('data-onboarding-disclosure="collapsed"'));
assert.equal(ResearchOSOnboardingWorkbench.sourceUrls(onboardingDraft).length, 2);
assert.equal(ResearchOSOnboardingWorkbench.invalidSourceUrl(onboardingDraft), "");
assert.equal(ResearchOSOnboardingWorkbench.unsafePublicSourceUrl(onboardingDraft), "");
assert.equal(ResearchOSOnboardingWorkbench.unsafePublicSourceUrl({ homepageUrl: "http://127.0.0.1:8080/private" }), "http://127.0.0.1:8080/private");
assert.equal(ResearchOSOnboardingWorkbench.unsafePublicSourceUrl({ homepageUrl: "http://[::ffff:127.0.0.1]/private" }), "http://[::ffff:127.0.0.1]/private");
assert.equal(ResearchOSOnboardingWorkbench.unsafePublicSourceUrl({ homepageUrl: "https://user:secret@example.com/profile" }), "https://user:secret@example.com/profile");
assert.equal(ResearchOSOnboardingWorkbench.unsafePublicSourceUrl({ homepageUrl: "https://example.com/profile" }), "");
for (const unsafeUrl of [
  "http://2130706433/private",
  "http://0x7f000001/private",
  "http://0177.0.0.1/private",
  "http://[::1]/private",
  "http://169.254.169.254/latest/meta-data/",
  "http://research-box.local/private",
]) {
  assert.equal(
    ResearchOSOnboardingWorkbench.unsafePublicSourceUrl({ homepageUrl: unsafeUrl }),
    unsafeUrl,
    `alternate local or link-local URL form must remain blocked: ${unsafeUrl}`,
  );
}
assert.equal(ResearchOSOnboardingWorkbench.invalidSourceService(onboardingDraft), "");
assert.equal(ResearchOSOnboardingWorkbench.sourceEntries({ homepageUrl: "https://example.com", otherUrls: ["https://orcid.org/example"] }, (key) => ({ onboardingSourceHomepageLabel: "主页", onboardingSourceOtherLabel: "其他链接" }[key] || key))[1].label, "其他链接 1");
assert.equal(
  ResearchOSOnboardingWorkbench.invalidSourceService({ scholarUrl: "https://example.com/not-scholar" }),
  "https://example.com/not-scholar",
  "service-specific source fields must not silently mislabel arbitrary public links",
);
assert.throws(
  () => ResearchOSMaterialPipelinePlugin.onboardingManifest({ ...onboardingDraft, homepageUrl: "http://127.0.0.1/private" }, [], "en"),
  /source boundary validation failed/,
  "the manifest builder must fail closed even when called outside the form-validation path",
);
assert.throws(
  () => ResearchOSMaterialPipelinePlugin.onboardingPrompt("../../tracked-file.md\ninject", "en"),
  /manifest path is invalid/,
  "the prompt must accept only the server-issued run-scoped upload path",
);
assert.equal(typeof ResearchOSOnboardingWorkbench.focusStepError, "function");
assert.equal(typeof ResearchOSOnboardingWorkbench.clearValidationState, "function");
const consentNode = { checked: true };
const consentResetRoot = { querySelector: (selector) => selector === "[name='consent']" ? consentNode : null };
assert.equal(ResearchOSOnboardingWorkbench.resetConsent(consentResetRoot), true);
assert.equal(consentNode.checked, false, "mount reset must actively revoke any browser-restored consent state");
const mountedConsentNode = { checked: true };
const onboardingMountRoot = {
  dataset: { onboardingStep: "1" },
  matches: () => false,
  querySelector: (selector) => selector === "[name='consent']" ? mountedConsentNode : null,
  querySelectorAll: () => [],
};
ResearchOSOnboardingWorkbench.bind(onboardingMountRoot);
assert.equal(mountedConsentNode.checked, false, "binding a restored onboarding form must revoke stale consent immediately");
consentNode.checked = true;
assert.equal(ResearchOSOnboardingWorkbench.resetConsentForBoundaryChange(consentResetRoot, { name: "scholar_url" }), true);
assert.equal(consentNode.checked, false, "changing a public source must revoke the previous consent");
consentNode.checked = true;
assert.equal(ResearchOSOnboardingWorkbench.resetConsentForBoundaryChange(consentResetRoot, { name: "role" }), false);
assert.equal(consentNode.checked, true, "editing a non-source profile field must not create consent churn");
assert.equal(ResearchOSOnboardingWorkbench.resetConsentForBoundaryChange(consentResetRoot, { matches: (selector) => selector === "[data-onboarding-files]" }), true);
assert.equal(consentNode.checked, false, "changing selected files must revoke the previous consent");
consentNode.checked = true;
global.document = { querySelectorAll: (selector) => selector === "[data-onboarding-personal]" ? [consentResetRoot] : [] };
for (const callback of browserEventListeners.get("pageshow") || []) callback({ persisted: true });
assert.equal(consentNode.checked, false, "BFCache pageshow restoration must revoke consent before the next run");
const onboardingStatusNode = { id: "onboarding-personal-status" };
const onboardingNameNode = {
  attributes: {},
  focusCalled: false,
  scrollCalled: false,
  setAttribute(key, value) { this.attributes[key] = value; },
  getAttribute(key) { return this.attributes[key] || null; },
  removeAttribute(key) { delete this.attributes[key]; },
  focus() { this.focusCalled = true; },
  scrollIntoView() { this.scrollCalled = true; },
};
const onboardingFocusRoot = {
  querySelector(selector) {
    if (selector === "[data-onboarding-status]") return onboardingStatusNode;
    if (selector === "[name='name']") return onboardingNameNode;
    return null;
  },
  querySelectorAll(selector) {
    if (selector === "[aria-invalid='true']" && onboardingNameNode.attributes["aria-invalid"] === "true") return [onboardingNameNode];
    return [];
  },
};
assert.equal(
  ResearchOSOnboardingWorkbench.focusStepError(onboardingFocusRoot, 1, { name: "" }, []),
  onboardingNameNode,
);
assert.equal(onboardingNameNode.attributes["aria-invalid"], "true");
assert.equal(onboardingNameNode.attributes["aria-describedby"], "onboarding-personal-status");
assert.equal(onboardingNameNode.focusCalled, true);
assert.equal(onboardingNameNode.scrollCalled, true);
ResearchOSOnboardingWorkbench.clearValidationState(onboardingFocusRoot);
assert.equal(onboardingNameNode.attributes["aria-invalid"], undefined);
assert.equal(onboardingNameNode.attributes["aria-describedby"], undefined);
assert.equal(
  ResearchOSOnboardingWorkbench.validateStep(2, { name: "Example", homepageUrl: "example.org" }, [], (key) => key),
  "onboardingInvalidUrl",
  "the step button must reject malformed public links even though it is not a native form submit",
);
assert.equal(
  ResearchOSOnboardingWorkbench.validateStep(2, { name: "Example", homepageUrl: "javascript:alert(1)" }, [], (key) => key),
  "onboardingInvalidUrl",
  "onboarding accepts only explicit http or https research sources",
);
const manyOnboardingUrls = Array.from({ length: 20 }, (_, index) => `https://example.com/${index}`);
const manyOnboardingFiles = Array.from({ length: 20 }, (_, index) => ({ name: `paper-${index}.pdf` }));
assert.equal(
  ResearchOSOnboardingWorkbench.validateStep(2, { otherUrls: manyOnboardingUrls }, [], (key) => key),
  "",
  "first-run onboarding must not impose a fixed URL-count quota",
);
assert.equal(
  ResearchOSOnboardingWorkbench.validateStep(2, { homepageUrl: `https://example.com/${"a".repeat(1500)}` }, [], (key) => key),
  "",
  "a valid long URL must not be rejected by an arbitrary character quota",
);
assert.equal(
  ResearchOSOnboardingWorkbench.validateStep(2, {}, manyOnboardingFiles, (key) => key),
  "",
  "first-run onboarding must not impose a fixed file-count quota",
);
const manySourceManifest = JSON.parse(ResearchOSMaterialPipelinePlugin.onboardingManifest(
  { ...onboardingDraft, otherUrls: manyOnboardingUrls },
  manyOnboardingFiles.map((file) => `06_active_context/work_state/uploads/${file.name}`),
  "en",
));
assert.equal(manySourceManifest.sources.public_urls.length, 22, "the run-scoped manifest must preserve every approved URL");
assert.equal(manySourceManifest.sources.local_uploaded_files.length, 20, "the run-scoped manifest must preserve every uploaded file");
assert.equal(manySourceManifest.sources.local_uploaded_files.at(-1), "06_active_context/work_state/uploads/paper-19.pdf");
const oversizedOnboardingUrls = Array.from(
  { length: 50 },
  (_, index) => `https://example.com/${index}/${"a".repeat(1400)}`,
);
assert.equal(
  ResearchOSOnboardingWorkbench.validateStep(2, { otherUrls: oversizedOnboardingUrls }, [], (key) => key),
  "",
  "the first-run flow must not impose an aggregate source-text quota",
);
const oversizedSourceManifest = JSON.parse(ResearchOSMaterialPipelinePlugin.onboardingManifest(
  { ...onboardingDraft, otherUrls: oversizedOnboardingUrls },
  [],
  "en",
));
assert.equal(oversizedSourceManifest.sources.public_urls.length, 52, "large source sets must remain complete in the local manifest");
assert.ok(oversizedSourceManifest.sources.public_urls.at(-1).length > 1400);
const manifestBackedPrompt = ResearchOSMaterialPipelinePlugin.onboardingPrompt(onboardingManifestPath, "en");
assert.ok(manifestBackedPrompt.length < 30000, "the stable runner prompt must leave room for safety and authority instructions regardless of source volume");
assert.ok(manifestBackedPrompt.includes("Authority boundary:"), "the final authority boundary must survive independently of user-source volume");

const onboardingStorageValues = new Map();
const onboardingStorage = {
  getItem(key) { return onboardingStorageValues.get(key) || null; },
  setItem(key, value) { onboardingStorageValues.set(key, String(value)); },
  removeItem(key) { onboardingStorageValues.delete(key); },
};
ResearchOSMaterialPipelinePlugin.saveOnboardingDraft({
  ...onboardingDraft,
  consent: true,
  scholarUrl: "not a URL",
  researchGateUrl: "https://example.com/not-researchgate",
  homepageUrl: "http://127.0.0.1/private",
  otherUrls: ["https://orcid.org/example", "not a URL", "javascript:alert(1)", "https://user:secret@example.com/private"],
}, onboardingStorage);
assert.equal(ResearchOSMaterialPipelinePlugin.onboardingDraft(onboardingStorage).name, "Dr. Example");
assert.equal(ResearchOSMaterialPipelinePlugin.onboardingDraft(onboardingStorage).consent, undefined, "consent must not enter browser-persistent draft state");
assert.equal(ResearchOSMaterialPipelinePlugin.onboardingDraft(onboardingStorage).scholarUrl, "", "malformed source URLs must not enter browser-persistent draft state");
assert.equal(ResearchOSMaterialPipelinePlugin.onboardingDraft(onboardingStorage).researchGateUrl, "", "service-mismatched source URLs must not enter browser-persistent draft state");
assert.equal(ResearchOSMaterialPipelinePlugin.onboardingDraft(onboardingStorage).homepageUrl, "", "rejected local addresses must not enter browser-persistent draft state");
assert.deepEqual(ResearchOSMaterialPipelinePlugin.onboardingDraft(onboardingStorage).otherUrls, ["https://orcid.org/example"], "credential-bearing sources must not enter browser-persistent draft state");
ResearchOSMaterialPipelinePlugin.clearOnboardingDraft(onboardingStorage);
assert.deepEqual(ResearchOSMaterialPipelinePlugin.onboardingDraft(onboardingStorage), {});

const busyControls = [{ disabled: false }, { disabled: false }];
const busyRoot = {
  attributes: {},
  querySelectorAll() { return busyControls; },
  setAttribute(key, value) { this.attributes[key] = value; },
};
assert.equal(ResearchOSOnboardingWorkbench.setBusy(busyRoot, true), true);
assert.equal(busyRoot.attributes["aria-busy"], "true");
assert.ok(busyControls.every((control) => control.disabled));
ResearchOSOnboardingWorkbench.setBusy(busyRoot, false);
assert.ok(busyControls.every((control) => !control.disabled));

const inboxSource = fs.readFileSync(path.join(__dirname, "..", "dashboard/src/services/inbox.js"), "utf8");
const materialPluginSource = fs.readFileSync(path.join(__dirname, "..", "dashboard/src/plugins/material-pipeline.js"), "utf8");
assert.ok(materialPluginSource.includes('if (context.publicStarter?.()) return "";'), "the public demo must not render the second real-material intake surface");
for (const retiredBranch of ["sources.materialIntakeItems", "sources.upgradeInboxItems", "sources.scoutInboxItems"]) {
  assert.ok(!inboxSource.includes(retiredBranch), `Review core must not retain ${retiredBranch}`);
}

console.log("Material pipeline plugin contract regression passed.");
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
