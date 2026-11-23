'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {compile,FAMILY,window}=require('../tools/adventure-arrangement.cjs');
test('original family has bounded form, common-tone seam and phrase breaths',()=>{
 for(const seed of ['one','two','three','adventure-pilot-1']){
  const p=compile(FAMILY,{seed});assert.equal(p.steps,128);assert.equal(p.bars.length,16);
  assert.deepEqual(p,compile(FAMILY,{seed}));assert(p.notes.every(e=>e.midi>=36&&e.midi<=88&&e.durationSteps>0&&e.step+e.durationSteps<=128));
  assert(p.bars[0].harmony.some(n=>p.bars.at(-1).harmony.includes(n)));
  for(const end of [32,64,96,128])assert(!p.notes.some(e=>e.layer===2&&e.step>=end-2&&e.step<end));
 }
});
test('quiet relative retains pitches/harmony, with fewer longer melody notes',()=>{
 const full=compile(),quiet=compile(FAMILY,{quiet:true});
 assert.deepEqual(full.bars,quiet.bars);assert(quiet.notes.length<full.notes.length);
 assert(quiet.notes.filter(e=>e.layer===2).every(e=>full.notes.some(n=>n.step===e.step&&n.midi===e.midi&&n.layer===e.layer)));
 assert(quiet.notes.filter(e=>e.layer===2).every(e=>e.durationSteps===1.6));
});
test('checkpoint windows concatenate exactly, without dropping or duplicating attacks',()=>{
 const p=compile(),whole=window(p),before=window(p,0,173),after=window(p,before.nextStep,384-before.nextStep);
 assert.deepEqual([...before.notes,...after.notes],whole.notes);assert.deepEqual([...before.bars,...after.bars],whole.bars);
 assert.equal(whole.nextStep,384);assert.equal(whole.bars.length,48);
 assert.deepEqual(window(p,384,0).notes,[]);assert.throws(()=>window(p,380,5));
});
test('invalid grammar fails before scheduling',()=>{
 for(const mutate of [p=>p.form.push('A'),p=>p.form[0]='__proto__',p=>p.sections.A.chords[0]='unknown',p=>p.sections.A.figure[0]=3,p=>p.sections.A.figure.pop(),p=>p.version='wrong']){
  const p=structuredClone(FAMILY);mutate(p);assert.throws(()=>compile(p));
 }
 assert.throws(()=>compile(FAMILY,{quiet:'yes'}));assert.throws(()=>compile(FAMILY,{seed:'x'.repeat(129)}));
});
test('form ablation preserves harmony, note inventory and phrase-local timing',()=>{
 const {formScore}=require('../tools/form-arrangement.cjs');
 for(const quiet of [false,true]){
  const a=formScore('alternating',{quiet}),b=formScore('grouped',{quiet});
  assert.deepEqual(a.bars.map(({step,chord,harmony})=>({step,chord,harmony})),b.bars.map(({step,chord,harmony})=>({step,chord,harmony})));
  const inventory=p=>p.notes.map(e=>JSON.stringify([e.step%32,e.midi,e.durationSteps,e.layer,e.level])).sort();
  assert.deepEqual(inventory(a),inventory(b));assert.equal(a.notes.length,b.notes.length);
  assert.deepEqual(a.notes.filter(e=>e.step<32),b.notes.filter(e=>e.step<32));
  assert.notDeepEqual(a.notes,b.notes);
  assert.deepEqual(a.bars.map(b=>b.section),['A','B','A','B'].flatMap(s=>Array(4).fill(s)));
  assert.deepEqual(b.bars.map(b=>b.section),['A','A','B','B'].flatMap(s=>Array(4).fill(s)));
 }
 assert.throws(()=>formScore('unknown'));
});
