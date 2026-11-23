'use strict';
const fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {loadRuntime}=require('./score-lab.cjs');
const {digest,signalMetrics,pcmWav}=require('./score-lab-metrics.cjs');
const arrangement=require('./adventure-arrangement.cjs');
const ROOT=path.resolve(__dirname,'..');
function plan(){
 const {books,api}=loadRuntime(),book=books.find(b=>b.id==='rat');
 return [[0,2,'caper'],[1,0,'reflection']].map(([chapterIndex,index,id])=>{
  const chapter=book.chapters[chapterIndex];
  return {id,book:Object.fromEntries(['id','title','author','url','revision','license'].map(k=>[k,book[k]])),chapter:{id:chapter.id,title:chapter.title},chapterIndex,paragraph:index+1,text:chapter.paragraphs[index],context:chapter.paragraphs[index-1]||'',palette:'romantic',genome:JSON.parse(JSON.stringify(api.starterGenome('classic')))};
 });
}
// Both conditions use the production graph, scene analysis, mixer and limiter.
async function nativeRender({scene,treatment,notation,seed,steps}){
 const sampleRate=24000,seconds=steps*STEP_SECONDS+5,ctx=new OfflineAudioContext(1,Math.ceil(seconds*sampleRate),sampleRate),a=new AudioAdapter();
 a.resetScore(seed,scene.book.id);a.setGenome(scene.genome);a.setPalette(scene.palette);a.initialize(ctx);a.running=true;a.volume=.35;a.background=.3;a.mix=[1,1,1,1];a.setMasterVolume(.35);
 const features=contextual(analyze(scene.text).raw,null),id=scene.book.id+':'+scene.chapter.id+':'+(scene.paragraph-1),passage=directPassage(scene.text,features,id);
 a.applyTarget(mapScore(narrativeTarget(features,passage.narrative)));a.setPassage({...passage,chapterId:scene.chapter.id,chapterIndex:scene.chapterIndex});
 const notes=[],harmony=[],original=a.note.bind(a);
 a.note=(hz,time,duration,layer,level,dest,instrument)=>{notes.push({step:a.tick-1,midi:Math.round(69+12*Math.log2(hz/440)),duration,layer,instrument:paletteInstrument(a.palette,instrument,(a.tick+31)%32,layer)});return original(hz,time,duration,layer,level,dest,instrument);};
 const snapshots=[];
 for(let step=0;step<steps;step++){
  const time=.12+step*STEP_SECONDS;a.state=smooth(a.state,a.target,STEP_SECONDS);a.applyMix(time);
  if(treatment==='baseline')a.composeBeat(time);
  else{
   a.composer.step=step+1;
   const bar=notation.bars.find(e=>e.step===step);
   if(bar){a.changeHarmony(bar.harmony,time);harmony.push(bar);}
   for(const e of notation.notes.filter(e=>e.step===step))a.note(440*2**((e.midi-69)/12),time,e.durationSteps*STEP_SECONDS,e.layer,e.level,a.layers[e.layer],'felt');
  }
  if(step%128===0)snapshots.push({step,nextStep:step+1});
 }
 // Identical final fade and tail for both conditions. No Web MIDI is opened offline.
 a.master.gain.setValueAtTime(.35*MASTER_GAIN,seconds-1);a.master.gain.linearRampToValueAtTime(0,seconds);
 const buffer=await ctx.startRendering();return {samples:Array.from(buffer.getChannelData(0)),sampleRate,seconds,notes,harmony,snapshots,cap:OUTPUT_CEILING};
}
async function main(){
 const [command,inputFile,outFile]=process.argv.slice(2),raw=fs.readFileSync(inputFile),input=JSON.parse(raw);let result;
 if(command==='plan')result=plan();
 else if(command==='render'){
  if(!['baseline','arranged'].includes(input.treatment))throw Error('Unknown treatment');
  const score=arrangement.compile(undefined,{seed:input.seed,quiet:input.scene.id==='reflection'}),notation=arrangement.window(score),steps=arrangement.STEPS*arrangement.REPEATS;
  const {chromium}=require('playwright'),browser=await chromium.launch({headless:true,channel:process.env.AWEN_BROWSER_CHANNEL||'msedge'});
  try{
   const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(pathToFileURL(path.join(ROOT,'index.html')).href);
   const data=await page.evaluate(nativeRender,{...input,notation,steps});if(errors.length)throw Error(errors.join('; '));
   const samples=Float32Array.from(data.samples),signal=signalMetrics(samples,data.sampleRate);
   if(!signal.finite||signal.peak>data.cap+1e-6||signal.rms<.0001)throw Error('Physical signal check failed');
   // Save raw first; paired attenuation-only matching is performed by the orchestrator.
   const wav=pcmWav(samples,data.sampleRate,1),trace=Buffer.from(JSON.stringify({treatment:input.treatment,score:input.treatment==='arranged'?score:null,notes:data.notes,harmony:data.harmony,snapshots:data.snapshots})+'\n');
   fs.writeFileSync(path.join(path.dirname(outFile),'audio.wav'),wav,{flag:'wx'});fs.writeFileSync(path.join(path.dirname(outFile),'trace.json'),trace,{flag:'wx'});
   result={file:'audio.wav',sha256:digest(wav),traceFile:'trace.json',traceSha256:digest(trace),seconds:data.seconds,signal,cap:data.cap,noteCount:data.notes.length,renderer:{browser:browser.version(),playwright:require('playwright/package.json').version,node:process.version}};
  }finally{await browser.close();}
 }else throw Error('Expected plan or render');
 const temp=outFile+'.tmp';fs.writeFileSync(temp,JSON.stringify({requestSha256:digest(raw),result})+'\n',{flag:'wx'});fs.renameSync(temp,outFile);
}
if(require.main===module)main().catch(e=>{console.error(e.stack);process.exitCode=1;});
module.exports={plan,nativeRender};
