/* Regression: source references must not become invented global identities. Synthetic data only. */
"use strict";
const assert = require('node:assert/strict');
global.window = global;
require('../dashboard/src/core/contracts.js');
require('../dashboard/src/plugins/research-portfolio-model.js');
require('../dashboard/src/services/item-composition-model.js');
const input = [
  {id:'a',title:'First item',related_people:[{name:'Methods Collaborator'}, {name:'A-B'}, {name:'A B'}]},
  {id:'b',title:'Second item',related_people:[{name:'Corresponding Author'}, {name:'Methods Collaborator'}]},
  {id:'c',title:'Explicit identity',related_people:[{id:'person:exact',name:'Alias'}]},
  {id:'d',title:'Identifier only',related_people:[{id:'person:exact'}]},
];
const projected = ResearchOSResearchPortfolioModel.build({items:input}).items;
const options = {portfolioItems:projected, assetBoxes:[{cards:[{id:'person:exact',type:'person',title:'Sourced Person',path:'04_people/exact.md'}]}]};
const model=ResearchOSItemCompositionModel.build(options);
const refs=id=>model.compositionForItem(id).confirmedComponents;
for(const id of ['a','b']) for(const ref of refs(id)) {
  assert.equal(model.componentForId(ref.componentId).title,ref.title,'Opened title must match the reference');
  assert.equal(ref.identityState,'unresolved_reference');
  assert.deepEqual(model.reverseForComponent(ref.componentId).confirmedItems.map(i=>i.id),[id]);
}
assert.equal(new Set([...refs('a'),...refs('b')].map(r=>r.componentId)).size,5,'Same name across items and punctuation differences must not merge');
assert.equal(refs('c')[0].componentId,'person:exact');
assert.equal(refs('d')[0].componentId,'person:exact');
assert.equal(refs('c')[0].title,'Sourced Person');
assert.deepEqual(model.reverseForComponent('person:exact').confirmedItems.map(i=>i.id),['c','d']);
const reversed=ResearchOSItemCompositionModel.build({...options,portfolioItems:[...projected].reverse()});
assert.deepEqual(refs('a').map(r=>r.componentId),reversed.compositionForItem('a').confirmedComponents.map(r=>r.componentId),'Item reordering must preserve local reference IDs');
const prefix='04_people/'+ 'long-name-'.repeat(20);
const paths=['04_people/A-B.md','04_people/A B.md',prefix+'one.md',prefix+'two.md'];
const exact=ResearchOSItemCompositionModel.build({portfolioItems:[{id:'paths',title:'Paths',relatedPeople:paths.map(path=>({path,name:path}))}]});
assert.equal(new Set(exact.compositionForItem('paths').confirmedComponents.map(r=>r.componentId)).size,4,'Exact paths must not collide after slug folding or truncation');
console.log('OK: unresolved references are item-scoped; exact identifiers, full paths and reverse relations remain intact');
