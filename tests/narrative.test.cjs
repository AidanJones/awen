'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync('index.html','utf8'),ctx=vm.createContext({setInterval,clearInterval,setTimeout,clearTimeout});
vm.runInContext(html.match(/<script>\s*([\s\S]*?)<\/script>/)[1].split('const $=id=>')[0],ctx);
const a=vm.runInContext('({NARRATIVE_LIBRARY,narrativeOptions,narrativeGallery,normalNarrativeChoice,normalGenome,normalProfile,compileHarmonyRecipe,compileScoreDSL})',ctx);
const plain=x=>JSON.parse(JSON.stringify(x)),knowledge=JSON.parse(fs.readFileSync('research/scoring-knowledge.json','utf8'));

test('reader embeds exact current dictionary and does not claim an automatic classifier',()=>{
 assert.deepEqual(plain(a.NARRATIVE_LIBRARY),JSON.parse(fs.readFileSync('research/narrative-dictionary.json','utf8')));
 assert.equal(a.NARRATIVE_LIBRARY.runtimeScope,'manual-interpretation-and-audition-only');
 assert.equal(a.NARRATIVE_LIBRARY.entries.length,28);
});
test('labels give alternatives with explicit event scope and no forced winner',()=>{
 assert.deepEqual(plain(a.narrativeOptions(['pursuit','humour']).map(o=>o.id)),['driving-motion','light-motion','quiet-intrigue']);
 assert.equal(a.narrativeOptions(['pursuit'],'recalled').length,0);
 assert.equal(a.narrativeOptions(['threat'],'unknown').length,0);
 assert.equal(a.narrativeOptions([]).length,0);
 assert.throws(()=>a.narrativeOptions(['MISSING']));
});
test('gallery preserves personal traits and optional chosen chords; all target recipes compile',()=>{
 const parent=plain(a.normalGenome()),harmony=a.compileHarmonyRecipe(knowledge,{familyId:'open-modal'});
 parent.harmony=plain(harmony);
 for(const entry of a.NARRATIVE_LIBRARY.entries){
  const choice={labels:[entry.id],scope:'current'};
  for(const o of a.narrativeOptions(choice.labels)){
   const held=a.narrativeGallery(knowledge,parent,choice,o.id,true,'fixed');
   assert.deepEqual(plain(held[1].genome.harmony),plain(a.normalGenome(parent).harmony));
   const changed=a.narrativeGallery(knowledge,parent,choice,o.id,false,'chapters');
   assert.equal(changed[1].genome.harmony.familyId,o.targets.harmonyFamily);
   assert.equal(changed[1].genome.classical.home,o.targets.classicalPreset);
   assert.equal(changed[1].genome.activity,parent.activity);
   assert.equal(changed[1].genome.softness,parent.softness);
   a.compileScoreDSL(changed[1].genome.scoreDSL.source);
   assert(changed.length<=6);
  }
 }
});
test('profile history retains bounded interpretation provenance separately from choice',()=>{
 const g=a.normalGenome(),value={labels:['pursuit','humour','pursuit'],scope:'current',note:'x'.repeat(500),basis:'accepted-rule-estimate',optionId:'light-motion'};
 const p=a.normalProfile({version:1,genomeVersion:'awen-genome-1',genome:g,history:[{choice:'gallery',before:g,after:g,narrativeChoice:value}]});
 const n=plain(p.history[0].narrativeChoice);assert.equal(n.note.length,240);assert.deepEqual(n.labels,['pursuit','humour']);
 assert.equal(n.basis,'accepted-rule-estimate');assert.equal(n.optionId,'light-motion');
 assert.equal(a.normalNarrativeChoice({...value,labels:['MISSING']}),null);
 assert.equal(a.normalNarrativeChoice({...value,scope:'MISSING'}),null);
 assert.equal(a.normalProfile({version:1,genomeVersion:'awen-genome-1',genome:g}).history.length,0);
});
