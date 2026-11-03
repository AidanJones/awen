'use strict';
// Authored experimental arrangements, rendered through the production graph.
const fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {loadRuntime}=require('./score-lab.cjs');
const {digest,signalMetrics,pcmWav}=require('./score-lab-metrics.cjs');
const ROOT=path.resolve(__dirname,'..');
function plan(){
 const {books}=loadRuntime();
 return [['rat',2,'baroque'],['riders',1,'romantic']].map(([id,index,palette])=>{
  const b=books.find(b=>b.id===id),c=b.chapters[0];
  return {id,book:Object.fromEntries(['id','title','author','url','revision','license'].map(k=>[k,b[k]])),chapter:{id:c.id,title:c.title},text:c.paragraphs.slice(index,index+3).join('\n\n'),context:c.paragraphs.slice(Math.max(0,index-1),index).join('\n'),palette};
 });
}
function score(treatment,transpose=0,seed='recurrence-pilot-20261103'){
 if(!['cell','ostinato','varied','sustained'].includes(treatment))throw Error('Unknown treatment');
 transpose+=(parseInt(digest(seed).slice(0,4),16)%3)*2;
 const notes=[],harmony=[48,55,64,72].map(n=>n+transpose);
 for(let step=0;step<192;step++){
  let midi=null,duration=.65;
  if(treatment==='cell'&&step%2===0)midi=60;
  if(treatment==='ostinato'&&step%2===0)midi=[60,64,67,64,62,65,69,65,60,64,67,71,62,65,67,64][(step%32)/2];
  if(treatment==='varied'&&step%2===0){
   const base=[60,64,67,64,62,65,69,65,60,64,67,71,62,65,67,64],phrase=Math.floor(step/32),slot=(step%32)/2;
   midi=base[(slot+(phrase%3)*4)%16]+(phrase%2&&slot>=12?-12:0);
  }
  if(treatment==='sustained'&&step%16===0){midi=[60,64,67,64][Math.floor(step/16)%4];duration=5.4;}
  if(midi!==null)notes.push({step,midi:midi+transpose,duration,layer:2,instrument:'felt',level:.13});
 }
 return {notes,harmony,steps:192};
}
async function nativeRender({notation,palette}){
 const sampleRate=24000,seconds=notation.steps*STEP_SECONDS+6,ctx=new OfflineAudioContext(1,Math.ceil(seconds*sampleRate),sampleRate),a=new AudioAdapter();
 a.resetScore('RECURRENCE-CONTROL','control');a.setPalette(palette);a.initialize(ctx);a.running=true;a.volume=.35;a.background=.3;a.mix=[1,1,1,1];a.setMasterVolume(.35);a.applyMix(0);
 a.changeHarmony(notation.harmony,.12);
 for(const e of notation.notes)a.note(440*2**((e.midi-69)/12),.12+e.step*STEP_SECONDS,e.duration,e.layer,e.level,a.layers[e.layer],e.instrument);
 a.master.gain.setValueAtTime(.35*MASTER_GAIN,seconds-2);a.master.gain.linearRampToValueAtTime(0,seconds-.1);
 const buffer=await ctx.startRendering();return {samples:Array.from(buffer.getChannelData(0)),sampleRate,seconds,cap:OUTPUT_CEILING};
}
async function main(){
 const [command,inputFile,outFile]=process.argv.slice(2),raw=fs.readFileSync(inputFile),input=JSON.parse(raw);let result;
 if(command==='plan')result=plan();
 else if(command==='render'){
  const {chromium}=require('playwright'),browser=await chromium.launch({headless:true,channel:process.env.AWEN_BROWSER_CHANNEL||'msedge'});
  try{const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(pathToFileURL(path.join(ROOT,'index.html')).href);
   const notation=score(input.treatment,input.transpose,input.seed),data=await page.evaluate(nativeRender,{notation,palette:input.palette});if(errors.length)throw Error(errors.join('; '));
   const samples=Float32Array.from(data.samples),signal=signalMetrics(samples,data.sampleRate);
   if(!signal.finite||signal.peak>data.cap+1e-6||signal.rms<.0001)throw Error('Physical signal check failed');
   const gain=Math.min(1,.018/signal.rms),wav=pcmWav(samples,data.sampleRate,gain),trace=Buffer.from(JSON.stringify(notation)+'\n');
   fs.writeFileSync(path.join(path.dirname(outFile),'audio.wav'),wav,{flag:'wx'});fs.writeFileSync(path.join(path.dirname(outFile),'trace.json'),trace,{flag:'wx'});
   result={file:'audio.wav',sha256:digest(wav),traceFile:'trace.json',traceSha256:digest(trace),seconds:data.seconds,gain,signal,cap:data.cap,renderer:{browser:browser.version(),playwright:require('playwright/package.json').version,node:process.version}};
  }finally{await browser.close();}
 }else throw Error('Expected plan or render');
 const temp=outFile+'.tmp';fs.writeFileSync(temp,JSON.stringify({requestSha256:digest(raw),result})+'\n',{flag:'wx'});fs.renameSync(temp,outFile);
}
if(require.main===module)main().catch(e=>{console.error(e.stack);process.exitCode=1;});
module.exports={score,plan};
