// Small, real-browser proof of the preference loop. No corpus or external service.
const assert=require('node:assert/strict');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.env.AWEN_BROWSER_CHANNEL||'msedge'});
 try{
  const page=await browser.newPage({viewport:{width:1180,height:1000}}),errors=[];
  page.setDefaultTimeout(10000);page.on('pageerror',e=>errors.push(e.message));
  await page.goto(pathToFileURL(path.join(__dirname,'../index.html')).href);
  await page.locator('#tuning summary').click();
  const initial=await page.evaluate(()=>audio.snapshot());
  const card=i=>page.locator('.candidate').nth(i),action=(i,name)=>card(i).locator('[data-action="'+name+'"]');
  await page.locator('#evolve-strength').selectOption('wide');await page.locator('#evolve-new').click();assert.equal(await page.locator('.candidate').count(),6);
  assert(await action(1,'keep').isDisabled());
  const firstBatch=await page.evaluate(()=>JSON.stringify(audition.candidates));
  await action(1,'play').focus();await page.keyboard.press('Enter');
  await page.waitForFunction(()=>audio.running&&audition.now===1);
  await page.waitForFunction(()=>audio.outputLevel().rms>.001);
  const graph=await page.evaluate(()=>{window.originalGraph=audio.ctx;return audio.tick;});assert(graph>0);
  await action(2,'play').click();await page.waitForFunction(()=>audition.now===2&&audio.running);
  assert(await page.evaluate(()=>audio.ctx===window.originalGraph));
  assert.equal(await page.locator('.candidate.is-playing').count(),1);
  await page.locator('#gallery-mute').click();assert.equal(await page.evaluate(()=>audio.running),false);
  assert.equal(await page.locator('.candidate.is-playing').count(),0);
  await action(1,'pin').click();assert.equal(await page.evaluate(()=>document.activeElement.dataset.action),'pin');const pinned=await page.evaluate(()=>JSON.stringify(profile.pins[0]));
  await card(1).locator('input').check();await card(2).locator('input').check();
  await page.locator('#explore-selected').click();assert.equal(await page.evaluate(()=>audition.parents.length),2);
  assert(await page.evaluate(()=>audition.candidates.some(c=>genomeKey(c.genome)===genomeKey(profile.pins[0]))));
  await page.locator('#gallery-back').click();assert.equal(await page.evaluate(()=>JSON.stringify(audition.candidates)),firstBatch);
  await page.locator('#gallery-next').click();assert.notEqual(await page.evaluate(()=>JSON.stringify(audition.candidates)),firstBatch);
  assert.equal(await page.evaluate(()=>profile.history.length),0,'skipping a batch must not record an invented preference');
  await page.locator('#gallery-back').click();await action(1,'play').click();await page.waitForFunction(()=>audition.now===1);
  await action(1,'keep').click();assert.equal(await page.evaluate(()=>profile.history.length),1);
  assert.equal(await page.evaluate(()=>audio.running),false);assert.equal(await page.evaluate(()=>audio.tick),initial.step);
  const chosen=await page.evaluate(()=>JSON.stringify(profile.genome));assert.notEqual(chosen,await page.evaluate(()=>JSON.stringify(GENOME_DEFAULT)));
  await page.reload();assert.equal(await page.evaluate(()=>JSON.stringify(profile.genome)),chosen);assert.equal(await page.evaluate(()=>audio.ctx),null);
  assert.equal(await page.evaluate(()=>JSON.stringify(profile.pins[0])),pinned);
  assert.equal(await page.evaluate(()=>profile.history[0].candidates.length),6);
  await page.locator('#tuning summary').click();await page.locator('#evolve-undo').click();assert.equal(await page.evaluate(()=>profile.history.length),0);
  await page.locator('#evolve-new').click();await action(2,'explore').click();assert.equal(await page.evaluate(()=>audition.round),2);
  await action(0,'play').click();await page.waitForFunction(()=>audio.running);
  await page.evaluate(()=>move(1));assert.equal(await page.evaluate(()=>audition),null);assert.equal(await page.evaluate(()=>audio.running),false);
  // Unfinished previews must not replace the saved reading-score cursor on reload.
  const checkpoint=await page.evaluate(()=>audio.snapshot());await page.locator('#evolve-new').click();await action(1,'play').click();await page.waitForFunction(()=>audio.running);await page.reload();assert.equal(await page.evaluate(()=>audio.tick),checkpoint.step);
  await page.locator('#tuning summary').click();
  await page.locator('#evolve-new').click();await action(0,'play').click();await page.waitForFunction(()=>audio.running);await page.keyboard.press('Escape');assert.equal(await page.evaluate(()=>audition),null);assert.equal(await page.evaluate(()=>audio.running),false);assert.equal(await page.locator('#gallery-dialog').evaluate(d=>d.open),false);assert.equal(await page.evaluate(()=>document.activeElement.id),'evolve-new');
  // Legacy import, invalid import and the production file writer.
  const imported={version:1,genomeVersion:'awen-genome-1',genome:{activity:.2,softness:1,warmth:1,space:1,bedPresence:1,bedMotion:1},history:[]};
  await page.locator('#profile-file').setInputFiles({name:'personal.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(imported))});
  await page.waitForFunction(()=>profile.genome.activity===.2);
  await page.locator('#profile-file').setInputFiles({name:'bad.json',mimeType:'application/json',buffer:Buffer.from('{"version":42}')});
  await page.waitForFunction(()=>document.querySelector('#profile-state').textContent.includes('Import failed'));assert.equal(await page.evaluate(()=>profile.genome.activity),.2);
  await page.evaluate(()=>{window.showSaveFilePicker=async()=>({name:'personal.json',createWritable:async()=>({write:async data=>window.writtenProfile=data,close:async()=>{}})});});
  await page.locator('#profile-save').click();await page.waitForFunction(()=>window.writtenProfile);assert.equal(JSON.parse(await page.evaluate(()=>window.writtenProfile)).genome.activity,.2);
  // Six short native renders demonstrate different bounded signals, not listener preference.
  const signals=await page.evaluate(async()=>{
   const candidates=makeGallery([normalGenome()],'both','proof-001',[],'wide'),samples=[],metrics=[];
   for(const candidate of candidates){const c=new OfflineAudioContext(1,24000*16,24000),a=new AudioAdapter();a.setGenome(candidate.genome);a.initialize(c);a.volume=.35;a.running=true;a.setMasterVolume(.35);a.applyMix(0);
    for(let i=0;i<38;i++)a.composeBeat(.1+i*STEP_SECONDS);const b=await c.startRendering(),data=b.getChannelData(0);let peak=0,sum=0;for(const v of data){if(!Number.isFinite(v))throw Error('Invalid output');peak=Math.max(peak,Math.abs(v));sum+=v*v;}samples.push(data);metrics.push({peak,rms:Math.sqrt(sum/data.length)});
   }
   return metrics.map((m,i)=>({...m,minDifference:Math.min(...samples.map((other,j)=>{if(i===j)return Infinity;let sum=0;for(let k=24000;k<other.length;k++)sum+=(other[k]-samples[i][k])**2;return Math.sqrt(sum/(other.length-24000));}))}));
  });
  for(const signal of signals){assert(signal.peak>.01&&signal.peak<=.140001);assert(signal.minDifference>.0003,'candidates must change the actual rendered signal');}
  console.log('Six-candidate native audio proof:',JSON.stringify(signals));
  // Actual preview duration, mobile wrapping and explicit cancellation.
  await page.setViewportSize({width:390,height:844});await page.locator('#evolve-new').click();
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  if(process.env.AWEN_SCREENSHOT){await page.setViewportSize({width:1180,height:1000});await page.screenshot({path:process.env.AWEN_SCREENSHOT});await page.setViewportSize({width:390,height:844});}
  await action(0,'play').click();await page.waitForFunction(()=>audio.running);await page.waitForFunction(()=>!audio.running,{},{timeout:19000});assert.equal(await page.evaluate(()=>audition.now),null);
  await page.locator('#evolve-cancel').click();assert.equal(await page.evaluate(()=>audition),null);
  assert.deepEqual(errors,[]);console.log('PASS six choices, one preview graph, keyboard, pin, multi-parent evolution, new batch/undo, keep/undo, reload/checkpoints, legacy import, file writer, 16-second stop and mobile layout');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
