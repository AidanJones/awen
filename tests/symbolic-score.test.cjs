'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {loadRuntime}=require('../tools/score-lab.cjs'),{exportScore}=require('../tools/symbolic-score.cjs');
const api=loadRuntime().api,plain=x=>JSON.parse(JSON.stringify(x));
function intent(chapter,cue='neutral'){return {kind:'reflective',chapterId:'chapter-'+chapter,chapterIndex:chapter,musicCue:{id:cue}};}
function row(extra={}){return {id:'chapter-proof',seed:'symbolic-proof-001',book:'rat',steps:96,
 genome:plain(api.classicalGenome('flowing','chapters')),
 timeline:[{step:0,intent:intent(0)},{step:11,intent:intent(1,'storm')},{step:59,intent:intent(0,'reflection')}],...extra};}

test('actual planner and export agree across forward/back chapter boundaries',()=>{
 const input=row(),s=exportScore(input,api);let state=api.makeComposer(input.seed,input.book),cursor=0;
 for(let step=0;step<input.steps;step++){
  if(input.timeline[cursor+1]?.step===step)cursor++;
  const r=api.planStep(state,input.timeline[cursor].intent,input.genome.scoreStyle,input.genome.harmony,input.genome.scoreDSL,input.genome.classical);
  const events=s.events.filter(e=>e.step===step).map(({step,absoluteStep,voice,...e})=>e);
  assert.deepEqual(events,plain(r.events));assert.deepEqual(s.contexts[step].bedHarmony,plain(r.state.voicing));state=r.state;
 }
 assert.equal(s.contexts[11].requestedChapter,'chapter-1');assert.equal(s.contexts[31].activeChapter,'chapter-0');
 assert.equal(s.contexts[32].activeChapter,'chapter-1');assert.equal(s.contexts[32].transpose,5);
 assert.equal(s.contexts[63].activeChapter,'chapter-1');assert.equal(s.contexts[64].activeChapter,'chapter-0');
 assert.equal(s.contexts[64].transpose,0);assert.equal(s.coverage.bed,'harmonic-target-only');
 assert(s.events.every(e=>s.voices.some(v=>v.id===e.voice)));
});

test('snapshot continuation is identical including mid-phrase clock, density and harmony',()=>{
 const input=row(),whole=exportScore(input,api),first=exportScore(row({steps:48,timeline:input.timeline.slice(0,2)}),api);
 const second=exportScore(row({steps:48,snapshot:first.snapshot,timeline:[{step:0,intent:input.timeline[1].intent},{step:11,intent:input.timeline[2].intent}]}),api);
 assert.deepEqual(second.contexts.map(c=>({...c,step:c.step+48})),whole.contexts.slice(48));
 assert.deepEqual(second.events.map(e=>({...e,step:e.step+48})),whole.events.filter(e=>e.step>=48));
 assert.deepEqual(second.snapshot,whole.snapshot);
 assert.throws(()=>exportScore(row({snapshot:{...first.snapshot,classical:{...first.snapshot.classical,epoch:999}}}),api),/snapshot/);
});

test('fixed-context compatibility uses exact held-chord plan',()=>{
 const genome=plain(api.classicalGenome('elegy','fixed')),s=exportScore({id:'fixed',steps:64,genome},api),p=api.compileScoreDSL(genome.scoreDSL.source);
 assert.deepEqual(s.chords,plain(Array.from({length:64},(_,step)=>p.bars[Math.floor(step/8/p.hold)%p.bars.length].pcs)));
 assert.equal(s.coverage.scheduledNotes,false);assert.equal(s.coverage.physicalOscillatorIdentity,false);
});

test('missing chapter state, unsupported planners and malformed timeline fail explicitly',()=>{
 assert.throws(()=>exportScore(row({timeline:undefined}),api),/timeline/);
 assert.throws(()=>exportScore(row({genome:plain(api.normalGenome())}),api),/DSL/);
 for(const timeline of [[],[{step:1,intent:intent(0)}],[{step:0,intent:intent(0)},{step:0,intent:intent(1)}], [{step:0,intent:{chapterId:'missing-index'}}]])
  assert.throws(()=>exportScore(row({timeline}),api));
});
