#!/usr/bin/env node
'use strict';
// Optional development tool. The shipped HTML imports none of this code.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {pathToFileURL}=require('node:url');
const {VERSION,LIMITS,digest,signalMetrics,traceMetrics,assess,pcmWav,judgePacket,evaluateJudgments}=require('./score-lab-metrics.cjs');
const ROOT=path.resolve(__dirname,'..');
function loadRuntime(){const html=fs.readFileSync(path.join(ROOT,'index.html'),'utf8'),script=html.match(/<script>\s*([\s\S]*?)<\/script>/)[1],ctx=vm.createContext({setInterval:()=>1,clearInterval:()=>{},setTimeout,clearTimeout});vm.runInContext(script.split('const $=id=>')[0],ctx);return {html,api:vm.runInContext('({normalGenome,starterGenome,mutateGenome,SCORE_STYLES,SOUND_PALETTES,compileScoreDSL,normalScoreDSL,SCORE_DSL_PRESETS,COMPOSER_VERSION,SKETCH_VERSION,STEP_SECONDS})',ctx),books:JSON.parse(html.match(/<script id="books" type="application\/json">([\s\S]*?)<\/script>/)[1])};}
function candidates(api,parent,seed,round,count){
 const first=parent?{genome:parent.genome,palette:parent.palette}:{genome:api.starterGenome('classic'),palette:'ensemble'},pool=[first];
 for(let i=1;i<count;i++){let base=first;if(round===0&&!parent){const style=['frontier','dialogue','caper'][i-1];base={genome:api.starterGenome(style),palette:{frontier:'frontier',dialogue:'chamber',caper:'noir'}[style]};}pool.push({genome:api.mutateGenome(base.genome,'whole',seed+'|'+round+'|'+i),palette:base.palette});}
 return pool.map(c=>({...c,genome:JSON.parse(JSON.stringify(api.normalGenome(c.genome))),id:'c-'+digest(c).slice(0,12)}));
}
function resolveCases(fixtures,books,split){return fixtures.cases.filter(c=>c.split===split).map(c=>{const book=books.find(b=>b.id===c.book);if(!book)throw Error('Fixture book missing');let last=-1;const timeline=c.passages.map(p=>{const chapter=book.chapters[p.chapter],text=chapter?.paragraphs[p.paragraph-1];if(!text||!Number.isInteger(p.step)||p.step<=last||p.step>=fixtures.steps||p.step%8)throw Error('Invalid fixture passage');last=p.step;return {...p,chapterId:chapter.id,paragraphId:book.id+':'+chapter.id+':'+(p.paragraph-1),text,seconds:+(.12+p.step*5/12).toFixed(4)};});if(timeline[0]?.step!==0)throw Error('Fixture must start at step zero');return {...c,revision:book.revision,timeline};});}
// Runs against the real production AudioAdapter, including smoothing, scene dwell and output cap.
async function renderCase({candidate,fixture,steps}){
 const sampleRate=24000,seconds=steps*STEP_SECONDS+5,offline=new OfflineAudioContext(1,Math.ceil(seconds*sampleRate),sampleRate),adapter=new AudioAdapter();
 adapter.resetScore(fixture.seed,fixture.book);adapter.setGenome(candidate.genome);adapter.setPalette(candidate.palette);adapter.initialize(offline);adapter.running=true;adapter.volume=.35;adapter.background=.3;adapter.mix=[1,1,1,1];adapter.setMasterVolume(.35);
 const trace=[],events=[],boundaries=[];let previous=null,current=null;
 const originalNote=adapter.note.bind(adapter);adapter.note=(hz,time,duration,layer,level,destination,instrument)=>{events.push({step:adapter.tick-1,layer,midi:Math.round(69+12*Math.log2(hz/440)),duration,instrument:paletteInstrument(adapter.palette,instrument,(adapter.tick+31)%32)});return originalNote(hz,time,duration,layer,level,destination,instrument);};
 for(let step=0;step<steps;step++){
  const time=.12+step*STEP_SECONDS,next=fixture.timeline.find(p=>p.step===step);
  if(next){const raw=analyze(next.text).raw,features=contextual(raw,previous);previous=raw;current=next;adapter.applyTarget(mapScore(features));adapter.setPassage(directPassage(next.text,features,next.paragraphId));boundaries.push({seconds:time,chapter:next.chapterId});}
  adapter.state=smooth(adapter.state,adapter.target,STEP_SECONDS);adapter.applyMix(time);adapter.composeBeat(time);
  trace.push({tick:adapter.tick,chapter:current.chapterId,state:{...adapter.state},regime:JSON.stringify([adapter.palette,adapter.genome.scoreStyle,harmonicIdentity(adapter.genome),adapter.composer.seed]),scene:adapter.composer.scene});
 }
 adapter.master.gain.setValueAtTime(.35*MASTER_GAIN,seconds-1);adapter.master.gain.linearRampToValueAtTime(0,seconds);
 const buffer=await offline.startRendering();return {samples:Array.from(buffer.getChannelData(0)),sampleRate,seconds,trace,events,boundaries};
}
function writeJson(file,value){fs.writeFileSync(file,JSON.stringify(value,null,2)+'\n');}
function publicPacket(packet){const {privateRequests,...result}=packet;return result;}
async function main(argv){
 const command=argv.shift()||'help',options={};while(argv.length){const key=argv.shift();if(!/^--[a-z-]+$/.test(key)||!argv.length)throw Error('Expected --option value');options[key.slice(2)]=argv.shift();}
 if(command==='help'){console.log('node tools/score-lab.cjs search --out <new-dir> [--seed lab-001] [--budget 4] [--rounds 1] [--judge-module <adapter.cjs>]\nnode tools/score-lab.cjs judge --run <round-dir> --responses <json-file>\nnode tools/score-lab.cjs holdout --out <new-dir> --proposal <proposal.json>');return;}
 if(command==='judge'){
  if(!options.run||!options.responses)throw Error('--run and --responses required');const dir=path.resolve(options.run),run=JSON.parse(fs.readFileSync(path.join(dir,'run.json'))),packet=judgePacket(run),response=JSON.parse(fs.readFileSync(options.responses)),old=path.join(dir,'judgment.json');if(fs.existsSync(old)&&!['awaiting-audio-judge'].includes(JSON.parse(fs.readFileSync(old)).status))throw Error('Run already judged; archive a fresh experiment instead of overwriting decisions');verifyClips(dir,run);const decision=evaluateJudgments(run,packet,response);if(run.split==='holdout'){decision.status='holdout-review';decision.selected=null;}writeJson(path.join(dir,'judge-responses.json'),response);writeJson(path.join(dir,'judgment.json'),decision);writeProposal(dir,run,decision);console.log(JSON.stringify(decision));return;
 }
 if(!['search','holdout'].includes(command)||!options.out)throw Error('Use help for commands; --out required');
 const budget=Number(options.budget||4),rounds=Number(options.rounds||1),seed=options.seed||'lab-001';if(!Number.isInteger(budget)||budget<2||budget>4||!Number.isInteger(rounds)||rounds<1||rounds>3)throw Error('Budget 2..4 and rounds 1..3 only');if(rounds>1&&!options['judge-module'])throw Error('Multiple rounds require an actual audio judge adapter');
 const runtime=loadRuntime(),fixtures=JSON.parse(fs.readFileSync(path.join(ROOT,'research/score-lab-fixtures.json'))),split=command==='holdout'?'holdout':'development',cases=resolveCases(fixtures,runtime.books,split),out=path.resolve(options.out);
 let parent=null;if(command==='holdout'){if(!options.proposal)throw Error('Holdout requires --proposal');const proposal=JSON.parse(fs.readFileSync(options.proposal));if(proposal.version!==VERSION||proposal.status!=='development-proposal')throw Error('A supported development proposal is required');parent=proposal.candidate;validateCandidate(parent,runtime.api);if(rounds!==1||options['judge-module'])throw Error('Holdout is a one-shot report, not a tuning loop');}
 // Never overwrite an archived run, and never write to the app or its saved user profile.
 if(fs.existsSync(out))throw Error('Output directory already exists; choose a new archive directory');fs.mkdirSync(out,{recursive:true});
 const judge=options['judge-module']?require(path.resolve(options['judge-module'])):null;if(judge&&typeof judge!=='function')throw Error('Judge module must export an async function(packet, {directory})');
 const {chromium}=require('playwright'),browser=await chromium.launch({headless:true,channel:process.env.AWEN_BROWSER_CHANNEL||'msedge'});
 try{const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(pathToFileURL(path.join(ROOT,'index.html')).href);
  for(let round=0;round<rounds;round++){
   const dir=path.join(out,'round-'+round);fs.mkdirSync(dir);const pool=command==='holdout'?[{genome:runtime.api.starterGenome('classic'),palette:'ensemble'},parent].map(c=>({...c,id:'c-'+digest(c).slice(0,12)})):candidates(runtime.api,parent,seed,round,budget);
   const versions={composer:runtime.api.COMPOSER_VERSION,sketch:runtime.api.SKETCH_VERSION,htmlSha256:digest(runtime.html),fixturesSha256:digest(fixtures),toolSha256:digest(fs.readFileSync(__filename)),metricsSha256:digest(fs.readFileSync(path.join(__dirname,'score-lab-metrics.cjs'))),rubricSha256:digest(fs.readFileSync(path.join(ROOT,'research/score-lab-judge.md'))),browser:browser.version(),playwright:require('playwright/package.json').version};
   const run={version:VERSION,id:digest({versions,seed,round,pool,split}),createdAt:new Date().toISOString(),split,seed,round,versions,settings:{volume:.35,background:.3,mix:[1,1,1,1],sampleRate:24000,steps:fixtures.steps},limits:LIMITS,baseline:pool[0].id,cases,candidates:[]};
   for(const candidate of pool){const clips=[];for(const fixture of cases){const rendered=await page.evaluate(renderCase,{candidate,fixture,steps:fixtures.steps}),samples=Float32Array.from(rendered.samples),signal=signalMetrics(samples,rendered.sampleRate),structure=traceMetrics(rendered.trace,rendered.events,fixtures.steps),gate=assess(signal,structure);const gain=signal.rms>0?Math.min(1,.018/signal.rms):1,file=candidate.id+'-'+fixture.id+'.wav',wav=pcmWav(samples,rendered.sampleRate,gain),traceFile=candidate.id+'-'+fixture.id+'-trace.json';fs.writeFileSync(path.join(dir,file),wav);writeJson(path.join(dir,traceFile),{trace:rendered.trace,events:rendered.events,boundaries:rendered.boundaries});clips.push({candidateId:candidate.id,caseId:fixture.id,file,sha256:digest(wav),traceFile,traceSha256:digest(fs.readFileSync(path.join(dir,traceFile))),seconds:rendered.seconds,gain,signal,structure,gate});console.log('Rendered',round,candidate.id,fixture.id,gate.eligible?'eligible':gate.reasons.join('; '));}run.candidates.push({...candidate,eligible:clips.every(c=>c.gate.eligible),clips});}
   if(errors.length)throw Error('Page errors: '+errors.join('; '));writeJson(path.join(dir,'run.json'),run);const packet=judgePacket(run);writeJson(path.join(dir,'judge-packet.json'),publicPacket(packet));fs.copyFileSync(path.join(ROOT,'research/score-lab-judge.md'),path.join(dir,'judge-instructions.md'));
   if(command==='holdout'){writeJson(path.join(dir,'holdout.json'),{status:'unjudged-holdout',candidate:parent.id,eligible:run.candidates[1].eligible,note:'Independent judgement/listening required; never use this report to tune this fixture.'});break;}
   if(!run.candidates[0].eligible){writeJson(path.join(dir,'judgment.json'),{status:'baseline-failed-gates',selected:null});break;}
   if(!judge){writeJson(path.join(dir,'judgment.json'),{status:'awaiting-audio-judge',selected:null,note:'Signal/structure checks cannot select the best music.'});break;}
   verifyClips(dir,run);const response=await judge(publicPacket(packet),{directory:dir}),decision=evaluateJudgments(run,packet,response);writeJson(path.join(dir,'judge-responses.json'),response);writeJson(path.join(dir,'judgment.json'),decision);writeProposal(dir,run,decision);console.log('Judge:',decision.status);if(decision.status!=='development-proposal')break;parent=run.candidates.find(c=>c.id===decision.selected);
  }
 }finally{await browser.close();}
}
function validateCandidate(c,api){const canonical=value=>Array.isArray(value)?value.map(canonical):value&&typeof value==='object'?Object.fromEntries(Object.keys(value).sort().map(k=>[k,canonical(value[k])])):value;if(!c||!Object.hasOwn(api.SOUND_PALETTES,c.palette)||JSON.stringify(canonical(api.normalGenome(c.genome)))!==JSON.stringify(canonical(c.genome)))throw Error('Invalid proposal candidate');}
function verifyClips(dir,run){for(const c of run.candidates)for(const clip of c.clips){if(path.basename(clip.file)!==clip.file||digest(fs.readFileSync(path.join(dir,clip.file)))!==clip.sha256)throw Error('Audio hash mismatch');}}
function writeProposal(dir,run,decision){if(decision.status==='development-proposal')writeJson(path.join(dir,'proposal.json'),{version:VERSION,status:decision.status,runId:run.id,judge:{model:decision.model,modelVersion:decision.modelVersion},candidate:run.candidates.find(c=>c.id===decision.selected),deploymentApproved:false,requires:['unseen book/chapter evaluation','reader listening/calibration','runtime regression tests']});}
if(require.main===module)main(process.argv.slice(2)).catch(e=>{console.error(e.message);process.exitCode=1;});
module.exports={loadRuntime,candidates,resolveCases,renderCase,publicPacket,verifyClips,writeProposal,validateCandidate};
