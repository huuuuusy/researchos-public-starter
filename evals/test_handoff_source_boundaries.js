/* Synthetic integration: composition -> Desk selection -> ContextPack -> copy-only handoff. */
"use strict";
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
async function check(language, runtimeScope) {
  const c = {console, URLSearchParams, TextEncoder, crypto:crypto.webcrypto,
    document:{readyState:'loading',addEventListener(){},documentElement:{lang:language},
      querySelector:()=>({dataset:{runtimeScope}})}};
  c.window=c; vm.createContext(c);
  for (const file of ['core/ui','core/contracts','services/item-composition-model','services/task-intent',
    'services/context-pack-projection','services/work-session-router','services/handoff-composer',
    'plugins/research-portfolio-copy','plugins/unified-desk-calendar','plugins/unified-desk-handoff',
    'plugins/unified-research-desk','views/work-session']) {
    vm.runInContext(fs.readFileSync(path.join(root,`dashboard/src/${file}.js`),'utf8'),c);
  }
  const items=[{id:'a',title:'Compare evidence',nextStep:'Explain the conflict; return a candidate only',relatedPeople:[{name:'Collaborator'}]},
    {id:'b',title:'Another question',relatedPeople:[{name:'Collaborator'}]}];
  const longPath=`projects/${'研究'.repeat(20)}.md`;
  const model=c.ResearchOSItemCompositionModel.build({portfolioItems:items,assetBoxes:[{cards:[
    {title:'Long project',path:longPath,type:'project'},
    {id:'paper:one',title:'Selected paper',path:'old/example.md',type:'paper'}]}]});
  const a=model.componentForId(model.compositionForItem('a').confirmedComponents[0].componentId);
  const b=model.componentForId(model.compositionForItem('b').confirmedComponents[0].componentId);
  assert.notEqual(a.id,b.id); assert.notEqual(a.identity_scope,b.identity_scope);
  const project=model.components.find(x=>x.path===longPath);
  const desk=c.ResearchOSUnifiedResearchDesk;
  Object.assign(desk.state,{portfolioModel:{items},compositionModel:model,selectedTaskId:'a',data:{config:{content_language:language}}});
  // Use the VM's Set so the production scoped-selection contract is exercised.
  c.selectionIds=[a.id,project.id,'paper:one'];
  vm.runInContext('ResearchOSUnifiedResearchDesk.state.handoffAssetsByTask.a = new Set(selectionIds)',c);
  const session=desk.buildSession();
  assert.equal(session.cards[0].identity_state,'unresolved_reference');
  assert.equal(session.cards[0].identity_scope,a.identity_scope);
  const input={session,selection:desk.selectionFor(session)};
  const options={language,displayLanguage:language,publicStarter:runtimeScope==='public_starter',
    previewDocuments:[{path:'different/example.md',title:'Unrelated same-name document'}]};
  const result=await c.ResearchOSHandoffComposer.compose(input,options);
  const sources=result.envelope.context_pack.included;
  const paper=sources.find(x=>x.id==='paper:one');
  assert.equal(paper.path,'old/example.md');assert.equal(paper.preview_path,'');
  assert.equal(paper.preview_state,'needs_confirmation');
  assert.equal(paper.candidate_preview_path,'different/example.md');
  const unresolved=language==='en'?'Identity unresolved':'身份待核对';
  const candidate=language==='en'?'not verified as the original source':'尚未证明是原来源';
  for(const text of [result.markdown,result.envelope.prompt]){
    assert.ok(text.includes(unresolved));assert.ok(text.includes(a.identity_scope));
    assert.ok(!text.includes(b.identity_scope));assert.ok(text.includes(candidate));
    assert.ok(text.includes('old/example.md'));assert.ok(text.includes('different/example.md'));
  }
  assert.equal(result.envelope.related_projects[0].id,project.id);
  assert.ok(project.id.length>240);
  if(runtimeScope==='public_starter')assert.equal(result.envelope.context_pack.egress.state,'copy_only_user_controlled');
  const projection=c.ResearchOSContextPackProjection;
  assert.equal(projection.previewResolution('old/example.md',[{path:'old/example.md'}]).state,'exact');
  const relocated=projection.includedSources(session,{previewDocuments:[{id:'paper:one',path:'archive/example.md'}]}).find(x=>x.id==='paper:one');
  assert.equal(relocated.preview_state,'relocated');assert.equal(relocated.path,'old/example.md');
  assert.equal(relocated.preview_path,'archive/example.md');
  assert.equal(projection.previewResolution('old/example.md',[{path:'a/example.md'},{path:'b/example.md'}]).state,'ambiguous');
  assert.equal(projection.previewResolution('old/example.md',[]).state,'unavailable');
  const html=c.ResearchOSWorkSessionView.renderLibraryContextPack({projection:result.envelope.context_pack});
  assert.ok(!html.includes('data-preview-path="different/example.md"'));
  assert.ok(html.includes(candidate));
  const composeProject=record=>c.ResearchOSHandoffComposer.compose({...input,selection:{relatedProjects:[record]}});
  await assert.rejects(()=>composeProject({id:'x'.repeat(241),path:'short.md'}),e=>e.code==='handoff_input_too_large'&&e.field==='project.id');
  await assert.rejects(()=>composeProject({id:project.id,path:'mismatch.md'}),e=>e.field==='project.id');
  const oversized='x'.repeat(2049);
  await assert.rejects(()=>composeProject({id:`reference:project:${encodeURIComponent(oversized)}`,path:oversized}),e=>e.field==='project.path');
  for (const suffix of ['A-B.md','A B.md','Case.md','case.md',`${'x'.repeat(250)}1.md`,`${'x'.repeat(250)}2.md`]) {
    const source=`projects/${suffix}`;
    const id=`reference:project:${encodeURIComponent(source)}`;
    const r=await composeProject({id,path:source,title:'Project'});
    assert.equal(r.envelope.related_projects[0].id,id);
  }
}
(async()=>{for(const language of ['en','zh-CN'])for(const mode of ['private','public_starter'])await check(language,mode);
console.log('OK: bilingual UI/headless source identity, candidate relocation, long-path handoff and fail-closed limits');})().catch(e=>{console.error(e);process.exitCode=1;});
