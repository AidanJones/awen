'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const {compile}=require('../tools/adventure-arrangement.cjs'),adventure=require('../tools/adventure-explorer.cjs');
const seed=JSON.parse(fs.readFileSync('research/adventure-starting-score.json','utf8'));
test('reference card plans exactly match the originally preferred arrangement for both passages',()=>{
 for(const quiet of [false,true]){
  const original=compile(undefined,{seed:seed.seed,quiet}),plan=adventure.plan(seed,{version:1,form:'original',texture:'full'},quiet);
  assert.deepEqual(plan.notes,original.notes);assert.deepEqual(plan.bars,original.bars.map(({step,harmony})=>({step,harmony})));
 }
 assert.equal(seed.reviewPacketSha256,JSON.parse(fs.readFileSync('research/adventure-listener-feedback.json')).packetSha256);
});
test('family variations change structure while keeping bounded original material',()=>{
 const original=adventure.plan(seed,{version:1,form:'original',texture:'full'});
 for(const form of ['original','contrast-middle','answer-first'])for(const texture of ['full','spacious','lyric']){
  const plan=adventure.plan(seed,{version:1,form,texture});
  assert(plan.notes.every(e=>e.step>=0&&e.step+e.durationSteps<=128&&e.midi>=36&&e.midi<=88));
  assert.equal(plan.bars.length,16);
  if(form!=='original'||texture!=='full')assert.notDeepEqual(plan.notes,original.notes);
 }
 assert.throws(()=>adventure.normal({version:1,form:'unknown',texture:'full'}));
});
