'use strict';
// Development-only, dependency-free measurements. None of these establish musical quality.
const crypto=require('node:crypto');
const digest=value=>crypto.createHash('sha256').update(typeof value==='string'||Buffer.isBuffer(value)?value:JSON.stringify(value)).digest('hex');
const VERSION='awen-score-lab-1';
const LIMITS=Object.freeze({peak:.140001,minRms:.0005,maxStateStep:.11,minPhrasePatterns:2,maxOnsetsPerSecond:4});
function signalMetrics(samples,sampleRate){
 let peak=0,sum=0,finite=true;const windows=[];
 for(let start=0;start<samples.length;start+=sampleRate/2){let energy=0,count=0;for(let i=start;i<Math.min(samples.length,start+sampleRate/2);i++){const v=samples[i];if(!Number.isFinite(v)){finite=false;continue;}peak=Math.max(peak,Math.abs(v));energy+=v*v;count++;}sum+=energy;windows.push(Math.sqrt(energy/Math.max(1,count)));}
 return {finite,peak,rms:Math.sqrt(sum/Math.max(1,samples.length)),windows};
}
function traceMetrics(trace,events,steps){
 let resets=0,regimeBreaks=0,maxStateStep=0;const regimes=[];
 for(let i=1;i<trace.length;i++){const a=trace[i-1],b=trace[i];if(a.chapter===b.chapter){if(b.tick!==a.tick+1)resets++;if(b.regime!==a.regime)regimeBreaks++;for(const k of Object.keys(a.state))maxStateStep=Math.max(maxStateStep,Math.abs(b.state[k]-a.state[k]));}}
 const phrases=Array.from({length:Math.floor(steps/32)},(_,i)=>events.filter(e=>Math.floor(e.step/32)===i).map(e=>[e.step%32,e.layer,e.midi,+e.duration.toFixed(3),e.instrument]));
 for(const t of trace)if(!regimes.includes(t.regime))regimes.push(t.regime);
 return {resets,regimeBreaks,maxStateStep,phrasePatterns:new Set(phrases.map(p=>JSON.stringify(p))).size,phrases:phrases.length,onsetsPerSecond:events.length/(steps*5/12),regimes:regimes.length};
}
function assess(signal,structure,limits=LIMITS){
 const reasons=[];
 if(!['resets','regimeBreaks','maxStateStep','phrasePatterns','onsetsPerSecond'].every(k=>Number.isFinite(structure[k])&&structure[k]>=0))reasons.push('invalid structural measurements');
 if(!signal.finite||![signal.peak,signal.rms].every(Number.isFinite))reasons.push('non-finite audio');
 if(signal.peak>limits.peak)reasons.push('output ceiling exceeded');
 if(signal.rms<limits.minRms)reasons.push('silent or near-silent');
 if(structure.resets)reasons.push('score reset inside chapter');
 if(structure.regimeBreaks)reasons.push('sudden palette/recipe/key/seed change inside chapter');
 if(structure.maxStateStep>limits.maxStateStep)reasons.push('expression changes too quickly');
 if(structure.phrasePatterns<limits.minPhrasePatterns)reasons.push('insufficient symbolic variation');
 if(structure.onsetsPerSecond>limits.maxOnsetsPerSecond)reasons.push('excessive onset density');
 return {eligible:!reasons.length,reasons};
}
function pcmWav(samples,sampleRate,gain=1){
 if(!(gain>0&&gain<=1))throw Error('WAV gain must attenuate only');
 const b=Buffer.alloc(44+samples.length*2);b.write('RIFF');b.writeUInt32LE(b.length-8,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);b.writeUInt16LE(1,20);b.writeUInt16LE(1,22);b.writeUInt32LE(sampleRate,24);b.writeUInt32LE(sampleRate*2,28);b.writeUInt16LE(2,32);b.writeUInt16LE(16,34);b.write('data',36);b.writeUInt32LE(samples.length*2,40);
 for(let i=0;i<samples.length;i++){if(!Number.isFinite(samples[i]))throw Error('Non-finite sample');b.writeInt16LE(Math.round(Math.max(-1,Math.min(1,samples[i]*gain))*32767),44+i*2);}return b;
}
const DIMENSIONS=['fit','coherence','unobtrusiveness'];
function judgePacket(run){
 const requests=[];const eligible=run.candidates.filter(c=>c.eligible);
 const make=(id,caseId,clips,control=null)=>({id,caseId,control,audioAvailable:control!=='no-audio',timeline:run.cases.find(c=>c.id===caseId).timeline,clips:clips.map((c,i)=>({slot:i?'B':'A',...(control==='no-audio'?{}:{file:c.file,sha256:c.sha256,seconds:c.seconds})}))});
 const baseline=eligible.find(c=>c.id===run.baseline);
 if(baseline)for(const candidate of eligible.filter(c=>c!==baseline))for(const fixture of run.cases){const pair=[baseline.clips.find(c=>c.caseId===fixture.id),candidate.clips.find(c=>c.caseId===fixture.id)],swap=parseInt(digest(candidate.id+fixture.id)[0],16)%2;if(swap)pair.reverse();for(let order=0;order<2;order++){const r=make(`${candidate.id}/${fixture.id}/${order}`,fixture.id,order?[...pair].reverse():pair);r.mapping=(order?[...pair].reverse():pair).map(c=>c.candidateId);requests.push(r);}}
 if(baseline){const clip=baseline.clips[0];requests.push(make('probe-'+digest(run.id+'identical').slice(0,12),clip.caseId,[clip,clip],'identical'));requests.push(make('probe-'+digest(run.id+'no-audio').slice(0,12),clip.caseId,[clip,clip],'no-audio'));}
 const privateRequests=requests.map(r=>({...r}));
 // The adapter receives only opaque slots/files, never config names, rule features or expected verdicts.
 return {version:VERSION,runId:run.id,rubricVersion:1,requests:requests.map(({mapping,control,...r})=>r),privateRequests};
}
function evaluateJudgments(run,packet,response){
 if(response?.version!==VERSION||response.runId!==run.id||typeof response.model!=='string'||!response.model.trim()||typeof response.modelVersion!=='string'||!response.modelVersion.trim()||!Array.isArray(response.verdicts))throw Error('Judge provenance/run ID missing');
 const byId=new Map();for(const v of response.verdicts){if(byId.has(v.id))throw Error('Duplicate judge verdict');byId.set(v.id,v);}if(byId.size!==packet.requests.length)throw Error('Incomplete or extra judge verdicts');
 const issues=[],usable=[];
 for(const r of packet.privateRequests){const v=byId.get(r.id);if(!v)throw Error('Missing judge request '+r.id);
  if(!Number.isFinite(v.confidence)||v.confidence<0||v.confidence>1||!DIMENSIONS.every(k=>['A','B','tie','abstain'].includes(v[k])))throw Error('Invalid judge values');
  if(r.control==='no-audio'){if(v.audioHeard!==false||!DIMENSIONS.every(k=>v[k]==='abstain'))issues.push('judge did not abstain without audio');continue;}
  if(v.audioHeard!==true||JSON.stringify(v.audioSha256)!==JSON.stringify(r.clips.map(c=>c.sha256)))throw Error('Judge must attest to the exact audio attachments');
  if(!Array.isArray(v.evidence)||!['A','B'].every(slot=>v.evidence.some(e=>e.slot===slot&&Number.isFinite(e.start)&&Number.isFinite(e.end)&&e.start>=0&&e.end>e.start&&e.end<=r.clips[slot==='A'?0:1].seconds&&typeof e.observation==='string'&&e.observation.trim())))throw Error('Timestamped evidence for both clips required');
  if(r.control==='identical'){if(!DIMENSIONS.every(k=>v[k]==='tie'))issues.push('judge disagrees on identical audio');continue;}
  usable.push({request:r,verdict:v});
 }
 const decisions=[];
 for(const candidate of run.candidates.filter(c=>c.eligible&&c.id!==run.baseline)){
  let fitWins=0,coherenceWins=0,failures=0;const reasons=[];
  for(const fixture of run.cases){const pair=usable.filter(x=>x.request.id.startsWith(candidate.id+'/'+fixture.id+'/'));if(pair.length!==2)throw Error('Missing swapped comparison');
   for(const dimension of DIMENSIONS){const outcomes=pair.map(({request:r,verdict:v})=>v[dimension]==='A'||v[dimension]==='B'?r.mapping[v[dimension]==='A'?0:1]:v[dimension]);
    if(outcomes[0]!==outcomes[1]){failures++;reasons.push(fixture.id+': order-sensitive '+dimension);}else if(outcomes[0]==='abstain'||pair.some(x=>x.verdict.confidence<.7)){failures++;reasons.push(fixture.id+': uncertain '+dimension);}else if(outcomes[0]===run.baseline){failures++;reasons.push(fixture.id+': baseline preferred for '+dimension);}else if(outcomes[0]===candidate.id){if(dimension==='fit')fitWins++;if(dimension==='coherence')coherenceWins++;}
   }
  }
  decisions.push({id:candidate.id,fitWins,coherenceWins,advance:!issues.length&&!failures&&(fitWins>0||coherenceWins>0),reasons});
 }
 const advances=decisions.filter(d=>d.advance).sort((a,b)=>b.fitWins-a.fitWins||b.coherenceWins-a.coherenceWins||a.id.localeCompare(b.id));
 return {model:response.model,modelVersion:response.modelVersion,issues,decisions,selected:advances[0]?.id||run.baseline,status:issues.length?'judge-controls-failed':advances.length?'development-proposal':'no-supported-improvement'};
}
module.exports={VERSION,LIMITS,DIMENSIONS,digest,signalMetrics,traceMetrics,assess,pcmWav,judgePacket,evaluateJudgments};
