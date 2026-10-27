// Native signal evidence, not a claim of acoustic realism or artistic quality.
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),crypto=require('node:crypto');
const {pathToFileURL}=require('node:url'),{chromium}=require('playwright');
(async()=>{const browser=await chromium.launch({headless:true,channel:process.env.AWEN_BROWSER_CHANNEL||'msedge'});try{
 const page=await browser.newPage();await page.goto(pathToFileURL(path.resolve(__dirname,'../index.html')).href);
 const proof=await page.evaluate(async()=>{
  const results=[],waves={};const rms=(samples,start,end)=>{let sum=0;for(let i=Math.round(start*24000);i<end*24000;i++)sum+=samples[i]**2;return Math.sqrt(sum/Math.round((end-start)*24000));};
  for(const instrument of ['guitar','pizzicato','flute','reed','bow','softBrass','felt','woodTap']){
   const c=new OfflineAudioContext(1,24000*3,24000),a=new AudioAdapter();a.initialize(c);a.background=0;a.mix=[0,0,1,0];a.running=true;a.setMasterVolume(.35);a.applyMix(0);a.note(220,.2,2,2,.3,a.layers[2],instrument);const buffer=await c.startRendering(),samples=buffer.getChannelData(0);let peak=0;for(const v of samples){if(!Number.isFinite(v))throw Error('Nonfinite '+instrument);peak=Math.max(peak,Math.abs(v));}
   const early=instrument==='woodTap'?rms(samples,.205,.28):rms(samples,.3,.55),middle=rms(samples,.8,1.05),tail=rms(samples,1.35,1.6),after=rms(samples,2.65,2.9);waves[instrument]=Array.from(samples.subarray(7200,26400));results.push({instrument,early,middle,tail,after,tailRatio:tail/early,peak});
  }
  // Equal-energy signal distance: differences cannot pass solely by changing volume.
  const distances=[];for(const [one,two] of [['guitar','flute'],['guitar','bow'],['flute','reed'],['felt','flute'],['bow','softBrass']]){const a=waves[one],b=waves[two],ra=Math.sqrt(a.reduce((s,v)=>s+v*v,0)/a.length),rb=Math.sqrt(b.reduce((s,v)=>s+v*v,0)/b.length);distances.push({one,two,distance:Math.sqrt(a.reduce((s,v,i)=>s+(v/ra-b[i]/rb)**2,0)/a.length)});}
  const source=pluckedSamples(24000,220,1,'pitch-check'),start=2400;let best=-Infinity,lag=0;for(let n=100;n<=118;n++){let correlation=0;for(let i=start;i<start+6000;i++)correlation+=source[i]*source[i+n];if(correlation>best){best=correlation;lag=n;}}
  return {composer:COMPOSER_VERSION,results,distances,pluckHz:24000/lag};
 });
 console.log(JSON.stringify(proof,null,2));for(const r of proof.results){assert(r.peak<=.140001);assert(r.early>.0001,r.instrument);assert(r.after<.0005,r.instrument+' must end');}const get=id=>proof.results.find(r=>r.instrument===id);assert(get('guitar').tailRatio<.5);assert(get('pizzicato').tailRatio<.1);assert(get('felt').tailRatio<.2);assert(get('flute').tailRatio>get('guitar').tailRatio*2);assert(get('bow').tailRatio>get('guitar').tailRatio*2);assert(Math.abs(proof.pluckHz-220)<4);for(const r of proof.distances)assert(r.distance>.2,r.one+'/'+r.two);
 const folder=path.resolve('.score-lab/tests/instruments');fs.mkdirSync(folder,{recursive:true});fs.writeFileSync(path.join(folder,new Date().toISOString().replace(/[:.]/g,'-')+'-'+crypto.randomUUID()+'.json'),JSON.stringify(proof,null,2)+'\n',{flag:'wx'});console.log('PASS pluck tuning/decay, wind and bow sustain, spectral/waveform contrasts at matched energy, finite bounded output and release tails.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
