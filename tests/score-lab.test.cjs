'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {VERSION,signalMetrics,traceMetrics,assess,pcmWav,judgePacket,evaluateJudgments}=require('../tools/score-lab-metrics.cjs');
const {loadRuntime,candidates,resolveCases,publicPacket,validateCandidate}=require('../tools/score-lab.cjs');
const goodSignal={finite:true,peak:.08,rms:.018},goodStructure={resets:0,regimeBreaks:0,maxStateStep:.05,phrasePatterns:3,onsetsPerSecond:.5};
test('hard gates reject silence, nonfinite/overlevel audio, monotony and excessive activity',()=>{
 assert(assess(goodSignal,goodStructure).eligible);
 for(const change of [{rms:0},{finite:false},{peak:.3},{rms:NaN}])assert(!assess({...goodSignal,...change},goodStructure).eligible);
 for(const change of [{resets:1},{regimeBreaks:1},{maxStateStep:.5},{phrasePatterns:1},{onsetsPerSecond:20},{onsetsPerSecond:NaN}])assert(!assess(goodSignal,{...goodStructure,...change}).eligible);
});
test('trace continuity permits larger chapter changes while rejecting inside-chapter resets/regime jumps',()=>{
 const row=(tick,chapter,regime)=>({tick,chapter,regime,state:{pulse:.2}}),same=[row(1,'one','a'),row(1,'one','b')],chapter=[row(1,'one','a'),row(1,'two','b')];
 const a=traceMetrics(same,[],64),b=traceMetrics(chapter,[],64);assert.equal(a.resets,1);assert.equal(a.regimeBreaks,1);assert.equal(b.resets,0);assert.equal(b.regimeBreaks,0);
 const jump=traceMetrics([row(1,'one','a'),{...row(2,'one','a'),state:{pulse:1}}],[],64);assert(jump.maxStateStep>.11);
 const chapterJump=traceMetrics([row(1,'one','a'),{...row(2,'two','b'),state:{pulse:1}}],[],64);assert.equal(chapterJump.maxStateStep,0);
});
test('signal measurement and WAV encoding preserve bounds, attenuation and finite checks',()=>{
 const s=Float32Array.from({length:24000},(_,i)=>Math.sin(i)*.1),m=signalMetrics(s,24000);assert(m.finite&&m.peak<=.100001&&m.rms>.05);const a=pcmWav(s,24000),b=pcmWav(s,24000,.5);assert.equal(a.toString('ascii',0,4),'RIFF');assert.equal(a.readUInt32LE(24),24000);assert.equal(a.length,48044);assert(Math.abs(b.readInt16LE(100))<=Math.abs(a.readInt16LE(100)));assert.throws(()=>pcmWav(s,24000,2));assert.throws(()=>pcmWav([NaN],24000));
});
const runtime=loadRuntime(),fixtures=require('../research/score-lab-fixtures.json');
test('Python-sorted proposal keys remain compatible with the existing holdout CLI',()=>{
 const source=candidates(runtime.api,null,'python',0,2)[1],sorted={...source,genome:Object.fromEntries(Object.entries(source.genome).sort(([a],[b])=>a.localeCompare(b)))};assert.doesNotThrow(()=>validateCandidate(sorted,runtime.api));assert.throws(()=>validateCandidate({...sorted,genome:{...sorted.genome,activity:100}},runtime.api));assert.throws(()=>validateCandidate({...sorted,genome:{...sorted.genome,unexpected:1}},runtime.api));
});
test('seeded candidates are reproducible bounded configs, with separate book holdout and valid passages',()=>{
 const a=candidates(runtime.api,null,'same',0,4),b=candidates(runtime.api,null,'same',0,4);assert.deepEqual(a,b);assert.equal(new Set(a.map(c=>c.id)).size,4);assert.notDeepEqual(a,candidates(runtime.api,null,'other',0,4));
 for(const c of a)assert(Object.hasOwn(runtime.api.SOUND_PALETTES,c.palette));const dev=resolveCases(fixtures,runtime.books,'development'),hold=resolveCases(fixtures,runtime.books,'holdout');assert(dev.length===2&&hold.length===1);assert(!dev.some(d=>hold.some(h=>h.book===d.book)));for(const c of [...dev,...hold]){assert(c.timeline.every(t=>t.text&&t.paragraphId));assert.equal(c.timeline[2].chapterId,c.timeline[0].chapterId);assert.notEqual(c.timeline[3].chapterId,c.timeline[0].chapterId);}
});
function sampleRun(){const clips=id=>['x','y'].map(caseId=>({candidateId:id,caseId,file:id+'-'+caseId+'.wav',sha256:id+caseId,seconds:58}));return {id:'unit-test-only-run',baseline:'base',cases:[{id:'x',timeline:[]},{id:'y',timeline:[]}],candidates:[{id:'base',eligible:true,clips:clips('base')},{id:'challenger',eligible:true,clips:clips('challenger')}]};}
function mockResponse(run,packet){return {version:VERSION,runId:run.id,model:'TEST-ONLY-MOCK',modelVersion:'not-a-real-judge',verdicts:packet.privateRequests.map(r=>({id:r.id,audioHeard:r.audioAvailable,audioSha256:r.clips.map(c=>c.sha256),fit:r.control==='no-audio'?'abstain':r.control==='identical'?'tie':r.mapping.indexOf('challenger')===0?'A':'B',coherence:r.control==='no-audio'?'abstain':'tie',unobtrusiveness:r.control==='no-audio'?'abstain':'tie',confidence:.9,evidence:r.audioAvailable?['A','B'].map(slot=>({slot,start:1,end:2,observation:'TEST ONLY'})):[]}))};}
test('blinded judge packet contains reversed pairs and identical/no-audio probes without config or answer keys',()=>{
 const run=sampleRun(),p=judgePacket(run),pub=publicPacket(p);assert.equal(p.requests.length,6);assert(!JSON.stringify(pub).includes('mapping'));assert(!JSON.stringify(pub).includes('control"'));assert.equal(p.requests.filter(r=>!r.audioAvailable).length,1);const first=p.privateRequests[0],second=p.privateRequests[1];assert.deepEqual(first.mapping,[...second.mapping].reverse());
});
test('order-consistent, non-regressing actual-audio attested votes can produce only a development proposal',()=>{
 const run=sampleRun(),p=judgePacket(run),result=evaluateJudgments(run,p,mockResponse(run,p));assert.equal(result.status,'development-proposal');assert.equal(result.selected,'challenger');
});
test('judge order bias, missing audio, low confidence and regressions cannot advance a candidate',()=>{
 const run=sampleRun(),p=judgePacket(run);
 const biased=mockResponse(run,p);biased.verdicts.filter(v=>!v.id.startsWith('probe-')).forEach(v=>v.fit='A');assert.equal(evaluateJudgments(run,p,biased).status,'no-supported-improvement');
 const noAudio=mockResponse(run,p);noAudio.verdicts.at(-1).fit='A';assert.equal(evaluateJudgments(run,p,noAudio).status,'judge-controls-failed');
 const identical=mockResponse(run,p);identical.verdicts.at(-2).fit='B';assert.equal(evaluateJudgments(run,p,identical).status,'judge-controls-failed');
 const uncertain=mockResponse(run,p);uncertain.verdicts[0].confidence=.2;assert.equal(evaluateJudgments(run,p,uncertain).status,'no-supported-improvement');
 const worse=mockResponse(run,p);for(const v of worse.verdicts.filter(v=>!v.id.startsWith('probe-'))){const r=p.privateRequests.find(r=>r.id===v.id);v.unobtrusiveness=r.mapping[0]==='base'?'A':'B';}assert.equal(evaluateJudgments(run,p,worse).status,'no-supported-improvement');
});
test('strict judge exchange rejects missing/duplicate verdicts, wrong hashes and impossible evidence',()=>{
 const run=sampleRun(),p=judgePacket(run);for(const mutate of [r=>r.verdicts.pop(),r=>r.verdicts[0].audioSha256=['wrong'],r=>r.verdicts[0].evidence[0].end=100,r=>r.verdicts[0].audioHeard=false,r=>r.verdicts[1]=r.verdicts[0],r=>r.runId='wrong']){const r=mockResponse(run,p);mutate(r);assert.throws(()=>evaluateJudgments(run,p,r));}
});
