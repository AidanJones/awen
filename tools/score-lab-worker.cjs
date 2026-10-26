#!/usr/bin/env node
'use strict';
// JSON-file bridge for Python orchestration; reuse the shipped engine and shared metrics.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {pathToFileURL}=require('node:url');
const {loadRuntime,candidates,resolveCases,renderCase,publicPacket}=require('./score-lab.cjs');
const {VERSION,LIMITS,digest,signalMetrics,traceMetrics,assess,pcmWav,judgePacket,evaluateJudgments}=require('./score-lab-metrics.cjs');
const ROOT=path.resolve(__dirname,'..');
const canonical=value=>Array.isArray(value)?value.map(canonical):value&&typeof value==='object'?Object.fromEntries(Object.keys(value).sort().map(k=>[k,canonical(value[k])])):value;
function atomic(file,data){if(fs.existsSync(file))throw Error('Refusing to replace worker artifact');const temp=file+'.'+crypto.randomUUID()+'.tmp';const fd=fs.openSync(temp,'wx');try{fs.writeFileSync(fd,data);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}fs.renameSync(temp,file);}
function json(file,data){atomic(file,JSON.stringify(data,null,2)+'\n');}
function inside(root,name){const base=fs.realpathSync(root),target=fs.realpathSync(path.resolve(base,name));if(!target.startsWith(base+path.sep))throw Error('Artifact outside experiment');return target;}
function verify(run,root){for(const c of run.candidates)for(const clip of c.clips){if(digest(fs.readFileSync(inside(root,clip.file)))!==clip.sha256||digest(fs.readFileSync(inside(root,clip.traceFile)))!==clip.traceSha256)throw Error('Artifact hash mismatch');}}
function plan(input){
 const {html,api,books}=loadRuntime(),fixtures=JSON.parse(fs.readFileSync(path.join(ROOT,'research/score-lab-fixtures.json'),'utf8'));
 if(!Number.isInteger(input.budget)||input.budget<2||input.budget>4||!Number.isInteger(input.round)||input.round<0||input.round>2||!['development','holdout'].includes(input.split)||typeof input.experimentId!=='string'||typeof input.seed!=='string')throw Error('Invalid plan limits');
 if(input.parent&&(!Object.hasOwn(api.SOUND_PALETTES,input.parent.palette)||digest(canonical(api.normalGenome(input.parent.genome)))!==digest(canonical(input.parent.genome))))throw Error('Invalid parent');
 if(input.split==='holdout'&&!input.parent)throw Error('Holdout requires a proposal parent');
 const pool=input.split==='holdout'?[{genome:api.starterGenome('classic'),palette:'ensemble'},input.parent].map(c=>({genome:c.genome,palette:c.palette,id:'c-'+digest({genome:c.genome,palette:c.palette}).slice(0,12)})):candidates(api,input.parent,input.seed,input.round,input.budget);
 const versions={composer:api.COMPOSER_VERSION,sketch:api.SKETCH_VERSION,node:process.version,playwright:require('playwright/package.json').version,htmlSha256:digest(html),fixturesSha256:digest(fixtures),coreSha256:digest(fs.readFileSync(path.join(__dirname,'score-lab.cjs'))),workerSha256:digest(fs.readFileSync(__filename)),metricsSha256:digest(fs.readFileSync(path.join(__dirname,'score-lab-metrics.cjs'))),rubricSha256:digest(fs.readFileSync(path.join(ROOT,'research/score-lab-judge.md')))};
 return {version:VERSION,id:digest({versions,...input,pool}),experimentId:input.experimentId,split:input.split,seed:input.seed,round:input.round,versions,settings:{volume:.35,background:.3,mix:[1,1,1,1],sampleRate:24000,steps:fixtures.steps},limits:LIMITS,baseline:pool[0].id,cases:resolveCases(fixtures,books,input.split),candidates:pool};
}
async function render(input,out){
 const {chromium}=require('playwright'),browser=await chromium.launch({headless:true,channel:process.env.AWEN_BROWSER_CHANNEL||'msedge'});
 try{const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(pathToFileURL(path.join(ROOT,'index.html')).href);const data=await page.evaluate(renderCase,input);if(errors.length)throw Error('Page error: '+errors.join('; '));
  const samples=Float32Array.from(data.samples),signal=signalMetrics(samples,data.sampleRate),structure=traceMetrics(data.trace,data.events,input.steps),gain=signal.rms>0?Math.min(1,.018/signal.rms):1,wav=pcmWav(samples,data.sampleRate,gain),trace=JSON.stringify({trace:data.trace,events:data.events,boundaries:data.boundaries},null,2)+'\n';
  atomic(path.join(out,'audio.wav'),wav);atomic(path.join(out,'trace.json'),trace);
  return {candidateId:input.candidate.id,caseId:input.fixture.id,file:'audio.wav',sha256:digest(wav),traceFile:'trace.json',traceSha256:digest(trace),seconds:data.seconds,gain,signal,structure,gate:assess(signal,structure),renderer:{browser:browser.version(),playwright:require('playwright/package.json').version,node:process.version}};
 }finally{await browser.close();}
}
async function main(){
 const [command,inputPath,outputPath]=process.argv.slice(2);if(!command||!inputPath||!outputPath)throw Error('Usage: worker <plan|render|assemble|validate-verdict|judge> input.json output.json');
 const bytes=fs.readFileSync(inputPath),input=JSON.parse(bytes),out=path.dirname(path.resolve(outputPath));let result;
 if(command==='plan')result=plan(input);
 else if(command==='render')result=await render(input,out);
 else if(command==='assemble'){
  const run={...input.plan,candidates:input.plan.candidates.map(c=>{const clips=input.clips.filter(x=>x.candidateId===c.id);if(clips.length!==input.plan.cases.length||new Set(clips.map(x=>x.caseId)).size!==clips.length||!input.plan.cases.every(f=>clips.some(x=>x.caseId===f.id)))throw Error('Incomplete candidate');return {...c,clips,eligible:clips.every(x=>x.gate.eligible)};})};verify(run,process.cwd());result={run,packet:publicPacket(judgePacket(run))};
 }else if(command==='validate-verdict'){
  const packet=judgePacket(input.run),request=packet.privateRequests.find(r=>r.id===input.requestId);if(!request)throw Error('Unknown judge request');
  // Reuse the exact shared validator on one request, without ranking a partial round.
  const minimal={...input.run,candidates:input.run.candidates.filter(c=>c.id===input.run.baseline)},single={...packet,requests:[request],privateRequests:[request]};evaluateJudgments(minimal,single,{...input.response,verdicts:[input.response.verdict]});result=input.response;
 }else if(command==='judge'){
  verify(input.run,process.cwd());const packet=judgePacket(input.run),decision=evaluateJudgments(input.run,packet,input.responses);if(input.run.split==='holdout'){decision.status='holdout-review';decision.selected=null;}
  const proposal=decision.status==='development-proposal'?{version:VERSION,status:decision.status,runId:input.run.id,judge:{model:decision.model,modelVersion:decision.modelVersion},candidate:input.run.candidates.find(c=>c.id===decision.selected),deploymentApproved:false,requires:['unseen book/chapter evaluation','reader listening/calibration','runtime regression tests']}:null;result={decision,proposal};
 }else throw Error('Unknown worker command');
 json(outputPath,{requestSha256:digest(bytes),result});console.log(JSON.stringify({command,status:'complete'}));
}
if(require.main===module)main().catch(e=>{console.error(e.stack);process.exitCode=1;});
module.exports={plan,verify,inside};
