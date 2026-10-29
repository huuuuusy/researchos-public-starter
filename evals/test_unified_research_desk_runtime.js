/* The UI language must never select an inactive source/template language. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(root, "dashboard/index.html"), "utf8");
const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map((match) => match[1]);
assert.equal(new Set(ids).size, ids.length, "DOM identities must be unique across active and compatibility hosts");

function fixture(uiLanguage, contentLanguage, runtimeScope = "public_starter") {
  let selectedLanguage;
  const context = {
    console,
    Date: class FixedDate extends Date { constructor(value) { super(value === undefined ? "2026-09-06T12:00:00" : value); } },
    URLSearchParams,
    document: {
      readyState: "loading",
      documentElement: { lang: uiLanguage },
      querySelector: () => ({ dataset: { runtimeScope } }),
      addEventListener: () => {},
      getElementById: () => null,
      querySelectorAll: () => [],
    },
    ResearchOSResearchPortfolioModel: {
      build: (portfolio, text, language) => {
        selectedLanguage = language;
        return { items: [{ id: "demo-item", title: "Evidence review", nextStep: "Review the evidence", continuationSource: "/workspace/demo", sourcePath: language === "en" ? "demo/source.md" : "demo/source.zh.md" }] };
      },
    },
    ResearchOSAssetOverviewModel: { buildAssetOverviewModel: () => ({cardBoxes: []}) },
    ResearchOSItemCompositionModel: { build: () => ({components: []}) },
  };
  context.window = context;
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(root, "dashboard/src/core/contracts.js"), "utf8"), context);
  context.ResearchOSInteractions = {bindAll() {}};
  vm.runInContext(fs.readFileSync(path.join(root, "dashboard/src/plugins/research-portfolio-workbench.js"), "utf8"), context);
  for (const file of ["research-portfolio-copy", "unified-desk-calendar", "unified-desk-handoff", "unified-research-desk"]) {
    vm.runInContext(fs.readFileSync(path.join(root, `dashboard/src/plugins/${file}.js`), "utf8"), context);
  }
  const desk = context.ResearchOSUnifiedResearchDesk;
  const data = {
    config: { content_language: contentLanguage, language_freeze: {active_language: contentLanguage} },
    asset_graph: { card_view_consolidation: { placement: { commitments: [{
      id: "demo-item", mandatory_visibility: true, placement_basis: ["attention_state:today"], primary_region: "Current",
    }] } } },
  };
  const projected = desk.projectionPayload(data);
  Object.assign(desk.state, projected, { data, selectedTaskId: "demo-item" });
  return {context, desk, selectedLanguage: () => selectedLanguage};
}

for (const contentLanguage of ["en", "zh-CN"]) {
  const { context, desk, selectedLanguage } = fixture("zh-CN", contentLanguage);
  const before = desk.buildSession();
  assert.equal(selectedLanguage(), contentLanguage, "projected item sources must use the frozen content language");
  assert.equal(before.templateLanguage, contentLanguage);
  assert.deepEqual([...before.sourceHints], ["/workspace/demo", contentLanguage === "en" ? "demo/source.md" : "demo/source.zh.md"]);
  assert.equal(before.portfolioBinding.continuationSource, "/workspace/demo", "task preparation must preserve the executable workspace separately from canonical authority");
  context.document.documentElement.lang = "en";
  const after = desk.buildSession();
  assert.equal(after.templateLanguage, contentLanguage, "UI language switching must not select frozen templates");
  assert.deepEqual([...after.sourceHints], [...before.sourceHints]);
  assert.equal(after.evidenceBoundary, before.evidenceBoundary, "prompt boundary copy must follow content language");
  assert.equal(after.portfolioBinding.itemId, before.portfolioBinding.itemId);
  assert.equal(desk.state.portfolioModel.items[0].primaryRegion, "Current", "the visible desk must consume the shared placement projection");
  assert.equal(desk.state.portfolioModel.items[0].mandatoryVisibility, true);
  assert.equal(desk.state.effectsEnabled, false, "changing presentation never enables Public effects");
}

function checkPlacementProjectionFallback() {
  const {desk} = fixture("en", "en");
  desk.state.portfolioModel.items = [
    {id: "current", primaryRegion: "Current"},
    {id: "review", primaryRegion: "Review"},
  ];
  desk.state.placementFilter = "Current";
  desk.state.data = {asset_graph: {}};
  assert.deepEqual(desk.placementItems().map(item => item.id), ["current", "review"], "A reduced projection without placement data must keep every research item visible");
  desk.state.data = {asset_graph: {card_view_consolidation: {placement: {commitments: [{id: "current"}, {id: "review"}]}}}};
  assert.deepEqual(desk.placementItems().map(item => item.id), ["current"], "A complete placement projection may apply the selected single-region filter");
  console.log("OK: missing placement projection fails open for task visibility");
}
checkPlacementProjectionFallback();
async function checkCurrentCalendarDate() {
  const { desk } = fixture("en", "en");
  await desk.init({fetcher: async () => ({ok: true, json: async () => ({generated_at: "2026-08-19T10:00:00", config: {content_language: "en"}})})});
  assert.equal(desk.state.today, "2026-09-06", "Today must use the current local date, not projection build time");
  assert.equal(desk.state.anchorDate, "2026-09-06");
  console.log("OK: Unified Desk preserves frozen language, copy-only effects and the current calendar date");
}
checkCurrentCalendarDate().catch((error) => { console.error(error); process.exitCode = 1; });

async function checkLifecycleControls() {
  for (const scope of ["private", "public_starter"]) {
    const {context, desk, nodes} = await interactionFixture(scope);
    desk.state.effectsEnabled = scope === "private";
    const item = desk.state.portfolioModel.items[0];
    Object.assign(item, {state:"waiting", lifecycleState:"waiting"});
    let calls = 0;
    context.ResearchOSWorkSessionClient.setPortfolioState = async (_, target) => {
      calls++;
      return {ok:true, rebuilt:true, result:{state:target}, undo:{kind:"portfolio_state",token:"fixture"}};
    };
    const root = nodes.get("drawer-what");
    desk.renderLifecycle(item, root);
    const elements = root.descendants();
    const select = elements.find(node => node.tag === "select");
    const confirm = elements.find(node => node.type === "checkbox");
    const save = elements.find(node => node.tag === "button");
    if (scope === "public_starter") {
      assert.equal(select.disabled, true, "A read-only preview shows the recorded state without letting it change");
      assert.equal(save, undefined, "A read-only preview renders no Save button that could never act");
      assert.equal(confirm, undefined, "A read-only preview renders no confirmation box");
      continue;
    }
    select.value = "closed";
    await save.listeners.click();
    assert.equal(calls, 0, "Selection or an unconfirmed save must never write");
    confirm.checked = true;
    await save.listeners.click();
    assert.equal(calls, scope === "private" ? 1 : 0);
    if (scope === "private") {
      assert.equal(item.state, "closed");
      assert.equal(item.primaryRegion, "Archive");
      assert.equal(desk.state.lastUndo.previous.state, "waiting");
      root.replaceChildren();
      desk.renderLifecycle(item, root);
      const reopenedElements = root.descendants();
      const target = reopenedElements.find(node => node.tag === "select" && "lifecycleState" in node.dataset);
      const confirmation = reopenedElements.find(node => node.type === "checkbox");
      const button = reopenedElements.find(node => node.tag === "button");
      target.value = "mainline";
      confirmation.checked = true;
      await button.listeners.click();
      assert.equal(calls, 1, "Reopening without a new plan must not write");
      for (const node of reopenedElements.filter(node => node.dataset.reopenField)) {
        node.value = {next_step:"Review a new request", success_gate:"New request reviewed", priority:"P2"}[node.dataset.reopenField];
        node.listeners.input();
        assert.equal(confirmation.checked, false, "Editing a reopen plan invalidates earlier confirmation");
      }
      confirmation.checked = true;
      await button.listeners.click();
      assert.equal(calls, 2);
      assert.equal(item.nextStep, "Review a new request");
      assert.equal(item.priority, "P2");
    } else assert.equal(select.disabled, true);
  }
  const {context, desk, nodes} = await interactionFixture("private");
  const item = desk.state.portfolioModel.items[0];
  desk.state.data.preview_documents = [{path:item.sourcePath}];
  let reads = 0;
  context.ResearchOSPreviewContentClient = {loadPreviewContent: async () => {reads++; return "Complete source";}};
  context.ResearchOSPreviewMarkdownService = {markdownToHtml: text => `<p>${text}</p>`};
  desk.renderItemLens();
  const source = nodes.get("drawer-what").children.find(node => node.tag === "details" && node.listeners.toggle);
  assert.ok(source, "The item drawer must expose its source directly");
  assert.equal(reads, 0, "Collapsed source must not be read");
  source.open = true;
  await source.listeners.toggle();
  assert.equal(reads, 1);
  assert.match(source.children[1].innerHTML, /Complete source/);
  desk.state.data.preview_documents = [];
  desk.renderItemLens();
  const blocked = nodes.get("drawer-what").children.find(node => node.tag === "details" && node.listeners.toggle);
  blocked.open = true;
  await blocked.listeners.toggle();
  assert.equal(reads, 1, "An excluded source must never be fetched");
  console.log("OK: lifecycle confirmation/private-only save, archive placement and manifest-bound item Markdown");
}
checkLifecycleControls().catch(error => {console.error(error);process.exitCode=1;});

// Exercise the registered calendar callbacks, not a second date implementation.
async function interactionFixture(scope = "public_starter") {
  const {context, desk} = fixture("en", "en", scope);
  const nodes = new Map();
  class Node {
    constructor(tag = "div") { this.tag = tag; this.dataset = {}; this.children = []; this.listeners = {}; this.classList = {add(){}, toggle(){}}; }
    append(...nodes) { this.children.push(...nodes); }
    replaceChildren(...nodes) { this.children = nodes; }
    setAttribute(key, value) { this[key] = value; }
    addEventListener(key, callback) { this.listeners[key] = callback; }
    cloneNode() { return new Node(); }
    replaceWith(node) { nodes.set("desk-calendar", node); }
    querySelectorAll() { return []; }
    querySelector(selector) {
      const key = selector === "[data-drawer-attention-date]" ? "drawerAttentionDate" : "attentionConfirm";
      return this.descendants().find(node => key in node.dataset) || null;
    }
    descendants() { return this.children.flatMap(node => [node, ...(node.descendants?.() || [])]); }
    focus() { context.document.activeElement = this; }
    contains(node) { return this.descendants().includes(node); }
    showModal() { this.open = true; }
    close() { this.open = false; }
  }
  for (const id of ids) nodes.set(id, new Node());
  nodes.get("item-drawer").append(nodes.get("drawer-when"));
  nodes.delete("resource-card-boxes"); // The independent library renderer is outside this scheduling fixture.
  const rootNode = new Node();
  let callbacks;
  let writes = 0;
  Object.assign(context.document, {
    createElement: tag => new Node(tag), createDocumentFragment: () => new Node(),
    createTextNode: value => Object.assign(new Node(), {textContent: value}),
    getElementById: id => nodes.get(id) || null,
    querySelector: selector => selector === "[data-unified-desk]" ? rootNode : null,
  });
  context.ResearchOSResearchPortfolioWorkbench = {...context.ResearchOSResearchPortfolioWorkbench, bind: (_, value) => {callbacks = value;}};
  context.ResearchOSItemCompositionModel.build = () => ({components: [], compositionForItem: () => null});
  context.ResearchOSWorkSessionClient = {applyAttentionAction: () => {writes++;}, undoMutation: () => {writes++;}};
  await desk.init({fetcher: async () => ({ok:true,json:async()=>({config:{content_language:"en"}})})});
  assert.ok(callbacks, "Calendar must register its actual callbacks");
  return {context, desk, nodes, callbacks, writes: () => writes};
}

async function checkPreviewRecovery() {
  const {context, desk, nodes, callbacks, writes} = await interactionFixture();
  for (const invalid of ["2026-02-29", "2026-02-30", "2026-04-31", "2026-13-01", "invalid"]) {
    callbacks.onCalendarMove({itemId:"demo-item", targetDate:invalid});
    assert.equal(desk.state.previewAttentionDates["demo-item"], undefined, `Reject nonexistent date ${invalid}`);
  }
  desk.state.previewAttentionDates.other = "2026-10-01";
  callbacks.onCalendarMove({itemId:"demo-item", targetDate:"2028-02-29"});
  assert.equal(desk.state.previewAttentionDates["demo-item"], "2028-02-29", "Accept a real leap day");
  const buttons = nodes.get("drawer-when").descendants();
  const cancel = buttons.find(node => node.textContent === "Cancel date preview");
  assert.ok(cancel && !cancel.disabled, "A preview must expose a usable cancel action");
  assert.equal(buttons.some(node => node.textContent === "Undo last write"), false, "Public must not advertise a write action");
  cancel.listeners.click();
  assert.equal(desk.state.previewAttentionDates["demo-item"], undefined);
  assert.equal(desk.state.previewAttentionDates.other, "2026-10-01", "Cancel affects only the current item");
  assert.equal(writes(), 0, "Public preview and cancel never call mutation clients");
  assert.equal(context.document.activeElement?.dataset.drawerAttentionDate, "", "Rerender retains a useful focus target");
  console.log("OK: real dates, per-item preview recovery and Public no-write behavior");
}
checkPreviewRecovery().catch(error => { console.error(error); process.exitCode = 1; });

async function checkPlacementBadgeFallback() {
  const {desk} = await interactionFixture();
  desk.state.data = {asset_graph: {}};
  const fallbackCard = desk.titleCard({id: "review", title: "Review item", primaryRegion: "Review"});
  assert.equal(fallbackCard.children.some(node => String(node.className || "").includes("placement-region-badge")), false, "Reduced projections must not show an ungrounded placement badge");
  desk.state.data = {asset_graph: {card_view_consolidation: {placement: {commitments: [{id: "review"}]}}}};
  const projectedCard = desk.titleCard({id: "review", title: "Review item", primaryRegion: "Review"});
  assert.equal(projectedCard.children.some(node => String(node.className || "").includes("placement-region-badge")), true, "Complete projections keep the single-region badge");
  console.log("OK: placement badges appear only when their projection exists");
}
checkPlacementBadgeFallback().catch(error => { console.error(error); process.exitCode = 1; });


async function checkAsyncOwnership() {
  for (const scope of ["public_starter", "private"]) {
    const {context, desk, nodes} = await interactionFixture(scope);
    const items = [{id:"a", title:"Alpha", sourcePath:"demo/a.md", attentionDate:"2026-09-01", attentionState:"upcoming"}, {id:"b", title:"Beta", sourcePath:"demo/b.md"}];
    desk.state.portfolioModel.items = items;
    context.ResearchOSCodexThreadRouter = {decide: () => ({recommended_route:"copy_only", intended_route:"copy_only", reason_codes:[]})};
    const pending = [];
    context.ResearchOSHandoffComposer = {compose: () => new Promise(resolve => pending.push(resolve))};
    desk.state.selectedTaskId = "a";
    const a = desk.prepareHandoff();
    desk.state.selectedTaskId = "b";
    const b = desk.prepareHandoff();
    pending[1]({markdown:"Beta"}); await b;
    pending[0]({markdown:"Alpha"}); await a;
    assert.equal(desk.state.lastHandoff.markdown, "Beta", "Late A cannot replace B");
    const closing = desk.prepareHandoff();
    desk.closeDrawer();
    pending[2]({markdown:"Closed"}); await closing;
    assert.equal(desk.state.lastHandoff, null, "Closing invalidates an in-flight packet");
    assert.equal(nodes.get("handoff-dialog").open, false);
    if (scope === "public_starter") continue;
    desk.state.selectedTaskId = "a";
    const drawer = nodes.get("item-drawer"); drawer.hidden = false; drawer.dataset.exactItemId = "a";
    drawer.querySelector = () => ({checked:true, focus(){}});
    let calls = 0, finish;
    context.ResearchOSWorkSessionClient.applyAttentionAction = () => {calls++; return new Promise(resolve => {finish=resolve;});};
    const save = desk.saveAttention("a", "2026-09-10");
    await desk.saveAttention("a", "2026-09-10");
    assert.equal(calls, 1, "Double click must not submit twice");
    desk.state.selectedTaskId = "b";
    finish({ok:true,undo:{kind:"attention",token:"fixture"}}); await save;
    assert.equal(items[0].attentionDate, "2026-09-10");
    assert.equal(desk.state.mutationPending, false);
    let undos = 0;
    context.ResearchOSWorkSessionClient.undoMutation = async () => {undos++;return {ok:true};};
    await desk.undoAttention();
    assert.equal(undos, 0, "B cannot undo A's receipt");
    desk.state.selectedTaskId = "a"; await desk.undoAttention();
    assert.equal(undos, 1); assert.equal(items[0].attentionDate, "2026-09-01");
    assert.equal(desk.state.lastUndo, null);
    for (const fail of [async()=>({ok:false,message:"offline"}),async()=>{throw Error("offline");}]) {
      context.ResearchOSWorkSessionClient.applyAttentionAction = fail;
      await desk.saveAttention("a", "2026-09-12");
      assert.equal(desk.state.mutationPending, false, "Failure allows retry");
      assert.match(nodes.get("prototype-status").textContent, /offline/);
      assert.equal(items[0].attentionDate, "2026-09-01", "Failure leaves the recorded date unchanged");
    }
  }
  console.log("OK: async packet ownership, close cancellation, single-flight save, item-bound undo and failure recovery");
}
checkAsyncOwnership().catch(error => {console.error(error);process.exitCode=1;});


async function checkResourceExploration() {
  const {context, desk, nodes, writes} = await interactionFixture();
  const material = {id:"paper", title:"Example material", path:"demo/paper.md", type:"paper"};
  desk.state.selectedTaskId = "";
  desk.state.compositionModel = {
    componentForId: id => id === material.id ? material : null,
    compositionForItem: () => null,
    reverseForComponent: () => ({rootItems:[], confirmedItems:[], candidateItems:[]}),
  };
  desk.toggleHandoffComponent(material.id);
  assert.equal(desk.state.explorationAssets.size, 1);
  assert.equal(desk.buildSession().portfolioBinding, null, "Exploration must not fabricate an item");
  assert.deepEqual([...desk.buildSession().sourceHints], [], "Unbound exploration must not pull in the portfolio source");
  await desk.prepareHandoff();
  assert.equal(desk.state.lastHandoff, null, "Material alone does not specify a bounded intent");
  nodes.get("exploration-intent").listeners.input({target:{value:"Compare the assumptions; return questions, not accepted claims."}});
  assert.equal(nodes.get("prepare-exploration").disabled, false);
  assert.equal(desk.buildSession().goal, desk.state.explorationIntent);
  let composed;
  context.ResearchOSCodexThreadRouter = {decide: input => {
    assert.equal(input.routeReceipt, null, "Unbound exploration cannot inherit an unrelated thread receipt");
    return {recommended_route:"copy_only", intended_route:"new", reason_codes:[]};
  }};
  context.ResearchOSHandoffComposer = {compose: async input => {composed=input; return {markdown:"Exploration candidate"};}};
  await desk.prepareHandoff();
  assert.equal(composed.selection.primaryProject, null);
  assert.equal(composed.handoffReceipt, null);
  assert.equal(composed.session.cards[0].path, material.path);
  assert.equal(desk.state.lastHandoff.markdown, "Exploration candidate");
  assert.equal(writes(), 0, "Selecting and preparing exploration must not invoke mutation");
  desk.state.selectedTaskId = "demo-item";
  assert.equal(desk.buildSession().cards.length, 0, "Exploration material must not silently enter another item");
  desk.state.selectedTaskId = "";
  let finish;
  context.ResearchOSHandoffComposer.compose = () => new Promise(resolve => {finish=resolve;});
  const pending=desk.prepareHandoff();
  nodes.get("exploration-intent").listeners.input({target:{value:"A changed question"}});
  finish({markdown:"Stale exploration"});
  await pending;
  assert.equal(desk.state.lastHandoff, null, "Editing intent invalidates an in-flight handoff");
  desk.toggleHandoffComponent(material.id);
  assert.equal(desk.buildSession().cards.length, 0, "Selection is reversible");
  console.log("OK: unbound exploration is intentional, copy-only, isolated and revision guarded");
}
checkResourceExploration().catch(error => {console.error(error);process.exitCode=1;});

function checkResourceFilterComposition() {
  const {desk}=fixture("en","en");
  desk.state.selectedTaskId="";
  desk.state.compositionModel={compositionForItem:()=>null};
  const cards=Array.from({length:9},(_,i)=>({dataset:{assetCardId:`c${i}`,assetCardSearchText:`material ${i}`,assetCardDisplayLimit:"6"}, hidden:false}));
  const box={querySelectorAll:()=>cards,classList:{contains:()=>false},open:false};
  const root={querySelectorAll:()=>[box],querySelector:()=>null};
  desk.handoffAssetIds().add("c8");
  desk.state.resourceFilter="selected";
  desk.applyResourceCardBoxSearch(root,"");
  assert.deepEqual(cards.filter(c=>!c.hidden).map(c=>c.dataset.assetCardId),["c8"],"A matching selection beyond the default display limit must remain reachable");
  desk.state.resourceFilter="all";
  desk.applyResourceCardBoxSearch(root,"material 8");
  assert.equal(cards[8].hidden,false);
  assert.equal(box.open,true,"Searching must reveal a result in a collapsed category");
  desk.applyResourceCardBoxSearch(root,"missing");
  assert.equal(box.hidden,true);
  desk.applyResourceCardBoxSearch(root,"");
  assert.equal(box.hidden,false,"Clearing search restores browsing");
  console.log("OK: resource search and scope compose without losing off-screen matches");
}
checkResourceFilterComposition();

async function checkCardContentAndEnhancement() {
  const {context, desk, nodes, writes} = await interactionFixture();
  const unresolved = {id:"reference-person",title:"Evaluation Partner",type:"person",path:"",identity_state:"unresolved_reference"};
  const itemSource = {id:"item-source",title:"Research Agenda",type:"material",path:"demo/source.md",identity_state:"identified"};
  desk.state.selectedTaskId = "demo-item";
  desk.state.compositionModel = {
    componentForId: id => ({[unresolved.id]:unresolved,[itemSource.id]:itemSource})[id] || null,
    compositionForItem: () => ({
      rootComponentId:itemSource.id,
      confirmedComponents:[{componentId:unresolved.id}],
      candidateComponents:[],
    }),
    reverseForComponent: () => ({rootItems:[],confirmedItems:[],candidateItems:[]}),
  };
  desk.state.data.preview_documents = [{path:itemSource.path}];
  desk.state.focusedAssetId = unresolved.id;
  await desk.renderCardContent(unresolved);
  const unresolvedContent = nodes.get("component-content").children[0];
  assert.match(unresolvedContent.children.map(node => node.textContent).join(" "), /not an independent Markdown card/);
  const sourceButton = unresolvedContent.children.find(node => node.tag === "button");
  assert.equal(sourceButton.textContent, "View item source Markdown");
  sourceButton.listeners.click();
  assert.equal(desk.state.focusedAssetId, itemSource.id, "An unresolved reference must open its exact item source, never a name-matched card");

  const blocked = {id:"blocked",title:"Blocked source",type:"material",path:"demo/private.md",preview:"Summary"};
  desk.state.data.preview_documents = [];
  desk.state.focusedAssetId = blocked.id;
  await desk.renderCardContent(blocked);
  const blockedContent = nodes.get("component-content").children[0];
  assert.match(blockedContent.children.map(node => node.textContent).join(" "), /not included in this runtime's text-preview manifest/);

  const a = {id:"card-a",title:"Example",type:"paper",path:"demo/a.md",preview:"Summary"};
  desk.state.data.preview_documents = [{path:a.path}];
  desk.state.focusedAssetId = a.id;
  nodes.get("item-drawer").hidden = false;
  let finish;
  context.ResearchOSPreviewContentClient = {loadPreviewContent: () => new Promise(resolve => {finish=resolve;})};
  context.ResearchOSPreviewMarkdownService = {markdownToHtml: content => `<p>${content}</p>`};
  const pending = desk.renderCardContent(a);
  desk.state.focusedAssetId = "card-b";
  finish("Old content"); await pending;
  assert.equal(nodes.get("component-content").children[0].textContent,"Summary", "Late source cannot replace another card");
  desk.state.focusedAssetId = a.id;
  context.ResearchOSPreviewContentClient.loadPreviewContent = async () => "Complete registered source";
  await desk.renderCardContent(a);
  assert.match(nodes.get("component-content").children[0].innerHTML,/Complete registered source/);
  desk.state.selectedTaskId = "unrelated-item";
  desk.state.items = [{id:"unrelated-item"}];
  context.document.querySelectorAll = () => [{dataset:{assetCardId:a.id}}];
  context.ResearchOSAssetOverviewWorkbenchService = {assetTaskPayloadFromCard: () => ({enhancement:{},candidate:{proposed_writeback:{save_target:a.path}}})};
  context.ResearchOSCodexThreadRouter = {decide: input => {
    assert.equal(input.routeReceipt,null);
    return {recommended_route:"copy_only",intended_route:"new",reason_codes:[]};
  }};
  let packet;
  context.ResearchOSHandoffComposer = {compose: async input => {packet=input; return {markdown:"Candidate"};}};
  await desk.prepareCardEnhancement(a,{axis:"M",level:"M1",target_level:"M2"},"enhance");
  assert.equal(packet.session.portfolioBinding,null);
  assert.equal(packet.handoffReceipt,null);
  assert.equal(packet.session.candidate.required_confirmation,"handoff_only");
  assert.equal(packet.session.candidate.proposed_writeback.save_target,"");
  assert.equal(writes(),0);
  console.log("OK: registered full source, late preview isolation and unbound Public enhancement handoff");
}
checkCardContentAndEnhancement().catch(error => {console.error(error);process.exitCode=1;});

// Navigation must reuse the exact-item review owner; a visual change must not hide copy recovery.
async function checkReviewNavigationAndCopyRecovery() {
  const {context, desk, nodes, writes} = await interactionFixture();
  const calls = [];
  context.openItemExecutionDrawer = (...args) => { calls.push(args); return true; };
  desk.state.selectedTaskId = "demo-item";
  nodes.get("open-item-review").listeners.click();
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0], "demo-item");
  assert.equal(calls[0][1], "review");
  assert.equal(nodes.get("item-drawer").hidden, true);
  nodes.get("open-item-review").listeners.click();
  assert.equal(calls.length, 1, "No selected item must not open a guessed review");
  assert.equal(writes(), 0, "Review navigation must not trigger an effect");
  const details = {open:false};
  nodes.get("handoff-preview").closest = () => details;
  desk.state.lastHandoff = {markdown:"Retained packet"};
  context.navigator = {clipboard:{writeText:async()=>{throw new Error("denied");}}};
  await nodes.get("copy-handoff").listeners.click();
  assert.equal(details.open, true, "Clipboard failure must reveal the retained text");
  assert.equal(context.document.activeElement, nodes.get("handoff-preview"));
  assert.equal(desk.state.lastHandoff.markdown, "Retained packet");
  console.log("OK: exact-item review navigation and visible copy-failure recovery");
}
checkReviewNavigationAndCopyRecovery().catch(error => { console.error(error); process.exitCode = 1; });

async function checkBoundaryOverview() {
  const {context,desk,nodes,writes}=await interactionFixture('public_starter');
  const source={id:'local:synthetic',title:'Synthetic reference',identity_state:'unresolved_reference',identity_scope:'synthetic:item',type:'person'};
  desk.state.selectedTaskId='demo-item';
  desk.state.compositionModel={componentForId:()=>source};
  desk.handoffAssetIds().add(source.id);
  context.ResearchOSCodexThreadRouter={decide:()=>({recommended_route:'copy_only'})};
  context.ResearchOSHandoffComposer={compose:async()=>({markdown:'Full packet',envelope:{context_pack:{included:[{id:source.id,preview_state:'needs_confirmation'}]}}})};
  await desk.prepareHandoff();
  const text=nodes.get('handoff-overview').descendants().map(node=>node.textContent||'').join(' ');
  assert.ok(text.includes('Identity unresolved'));
  assert.ok(text.includes('Source location unverified'));
  assert.equal(writes(),0);
  console.log('OK: handoff overview exposes identity and source uncertainty without effects');
}
checkBoundaryOverview().catch(error=>{console.error(error);process.exitCode=1;});

async function checkReviewFindings2026() {
  // Focus after a date preview goes to `[data-drawer-attention-date]`; only the date input may carry it.
  assert.doesNotMatch(html, /id="drawer-when"[^>]*data-drawer-attention-date/, "The drawer wrapper must not take focus from the date input");
  // A page without a runtime-scope attribute must stay read-only, not fall back to private writes.
  assert.equal(fixture("en", "en", "").desk.state.effectsEnabled, false, "A missing runtime scope fails closed to the public starter");

  const {context, desk, nodes, writes} = await interactionFixture("public_starter");
  // An item scheduled outside the visible week: the range line says where it is instead of looking empty.
  Object.assign(desk.state.portfolioModel.items[0], {attentionDate: "2026-08-10"});
  desk.renderDesk();
  assert.match(nodes.get("calendar-range").textContent, /nothing scheduled in this period; 1 outside it/);

  // With no selected cards, the handoff summary lists the packet's session sources rather than "see full text".
  desk.state.selectedTaskId = "demo-item";
  context.ResearchOSCodexThreadRouter = {decide: () => ({recommended_route: "copy_only"})};
  context.ResearchOSHandoffComposer = {compose: async () => ({markdown: "Full packet", envelope: {context_pack: {included: []}}})};
  await desk.prepareHandoff();
  const overview = nodes.get("handoff-overview").descendants().map(node => node.textContent || "").join(" ");
  assert.ok(overview.includes("demo/source.md"), "The summary names the session source");
  assert.ok(!overview.includes("Check sources and scope in the full text."));
  assert.equal(writes(), 0);
  console.log("OK: fail-closed scope default, empty-period hint and handoff source summary");
}
checkReviewFindings2026().catch(error=>{console.error(error);process.exitCode=1;});

function checkCalendarArithmetic() {
  const {context} = fixture("en", "en");
  const calendar = context.ResearchOSUnifiedDeskCalendar;
  assert.equal(calendar.parseIso("2028-02-29")?.getDate(), 29, "a real leap day parses");
  for (const invalid of ["2026-02-29", "2026-04-31", "2026-13-01", "26-01-01"]) assert.equal(calendar.parseIso(invalid), null, `reject ${invalid}`);
  assert.deepEqual([...calendar.weekDates("2026-09-06")], ["2026-08-31", "2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04", "2026-09-05", "2026-09-06"], "weeks start on Monday");
  const month = calendar.monthDates("2026-09-15");
  assert.equal(month.length, 42);
  assert.equal(month[0], "2026-08-31", "the month grid starts on the Monday on or before the first");
  assert.equal(calendar.shiftAnchor("month", "2026-01-31", 1), "2026-02-01", "month navigation moves from the first of the month");
  assert.equal(calendar.shiftAnchor("week", "2026-09-06", -1), "2026-08-30");
  assert.equal(calendar.shiftAnchor("day", "2026-12-31", 1), "2027-01-01");
  assert.equal(calendar.periodLabel("week", "2026-09-06"), "2026-08-31 — 2026-09-06");
  assert.equal(calendar.periodLabel("month", "2026-09-06", [], (year, monthNumber) => `${year}/${monthNumber}`), "2026/09");
  console.log("OK: calendar arithmetic is pure and Monday-first");
}
checkCalendarArithmetic();
