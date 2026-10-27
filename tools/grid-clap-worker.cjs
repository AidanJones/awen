'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),{pathToFileURL}=require('node:url');
const {signalMetrics,traceMetrics,assess,pcmWav,digest}=require('./score-lab-metrics.cjs');
function atomic(file,bytes){const temp=file+'.'+crypto.randomUUID()+'.tmp';fs.writeFileSync(temp,bytes,{flag:'wx'});fs.renameSync(temp,file);}
(async()=>{const [command,inputFile,outputFile]=process.argv.slice(2),bytes=fs.readFileSync(inputFile),input=JSON.parse(bytes),{chromium}=require('playwright'),browser=await chromium.launch({headless:true,channel:process.env.AWEN_BROWSER_CHANNEL||'msedge'});try{
 const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(pathToFileURL(input.page).href);let result;
 if(command==='grid-plan')result=await page.evaluate(()=>({cards:startingCards(),scenes:data.scenes,composer:COMPOSER_VERSION,engineSha256:data.engineSha256}));
 else if(command==='grid-children')result=await page.evaluate(({parents,generation,seed,count})=>Array.from({length:count},(_,i)=>{const p=parents[i%parents.length],g=mutateGenome(p.genome,'both',seed+'|grid-clap|'+generation+'|'+i);return {id:'g'+generation+'-'+i+'-'+hash32(JSON.stringify([p.id,g])).toString(36),name:p.name+' · G'+generation+'.'+(i+1),description:describeGenome(g,p.genome),palette:p.palette,genome:g,parentId:p.id};}),input);
 else if(command==='render'){
  const rendered=await page.evaluate(async input=>{
   const trace=[],events=[],note=AudioAdapter.prototype.note,compose=AudioAdapter.prototype.composeBeat;
   AudioAdapter.prototype.note=function(hz,time,duration,layer,level,destination,instrument){events.push({step:this.tick-1,layer,midi:Math.round(69+12*Math.log2(hz/440)),duration,instrument:paletteInstrument(this.palette,instrument,(this.tick+31)%32)});return note.call(this,hz,time,duration,layer,level,destination,instrument);};
   AudioAdapter.prototype.composeBeat=function(time){compose.call(this,time);trace.push({tick:this.tick,chapter:'fixed-scene',state:{...this.state},regime:JSON.stringify([this.palette,this.genome.scoreStyle,harmonicIdentity(this.genome),this.composer.seed])});};
   const r=await renderPreview(input.card,data.scenes[input.scene],input.seed,input.seconds);return {samples:Array.from(r.buffer.getChannelData(0)),gain:r.gain,trace,events};
  },input),samples=Float32Array.from(rendered.samples),signal=signalMetrics(samples,24000),structure=traceMetrics(rendered.trace,rendered.events,rendered.trace.length),wav=pcmWav(samples,24000),trace=JSON.stringify({trace:rendered.trace,events:rendered.events})+'\n',out=path.dirname(outputFile);
  atomic(path.join(out,'audio.wav'),wav);atomic(path.join(out,'trace.json'),trace);result={file:'audio.wav',sha256:digest(wav),traceFile:'trace.json',traceSha256:digest(trace),signal,structure,gate:assess(signal,structure),gain:rendered.gain,seconds:input.seconds,renderer:{browser:browser.version(),playwright:require('playwright/package.json').version,node:process.version}};
 }else throw Error('Unknown grid worker command');
 if(errors.length)throw Error(errors.join('; '));atomic(outputFile,JSON.stringify({requestSha256:digest(bytes),result})+'\n');
}finally{await browser.close();}})().catch(e=>{console.error(e.stack);process.exitCode=1;});
