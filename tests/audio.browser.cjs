// Optional browser checks: npm install --no-save playwright && npx playwright install chromium
// Then: node tests/audio.browser.cjs (AWEN_BROWSER_CHANNEL=msedge also supported).
const assert=require('node:assert/strict');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require('playwright');

(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.env.AWEN_BROWSER_CHANNEL||undefined,args:['--autoplay-policy=user-gesture-required']});
 try{
  const page=await browser.newPage({viewport:{width:1180,height:1000}}),errors=[];
  page.setDefaultTimeout(10000);
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(pathToFileURL(path.join(__dirname,'../index.html')).href);
  assert.equal(await page.evaluate(()=>audio.ctx),null,'audio must remain off before a gesture');
  const idleWave=await page.locator('#visualizer').screenshot();

  // Real browser DSP, not fake AudioNodes: render the production graph offline.
  const renders=await page.evaluate(async()=>{
   async function render(volume,stress=false,mix=[1,1,1,1],palette='ensemble',kind='reflective',background=.3,seconds=12){
    const offline=new OfflineAudioContext(2,48000*seconds,48000),adapter=new AudioAdapter();adapter.background=background;adapter.setPalette(palette);adapter.setPassage({id:kind,kind});adapter.initialize(offline);adapter.volume=volume;adapter.mix=mix;adapter.running=true;adapter.setMasterVolume(volume);adapter.applyMix(0);
    for(let step=0;step<Math.floor((seconds-.2)/STEP_SECONDS);step++)adapter.composeBeat(.15+step*STEP_SECONDS);
    if(stress)for(let i=0;i<40;i++)adapter.note(440,.1,3.5,2,100,adapter.highpass);
    const buffer=await offline.startRendering();let peak=0,sum=0,count=0,restPeak=0,finite=true;
    for(let channel=0;channel<buffer.numberOfChannels;channel++){const data=buffer.getChannelData(channel);for(let i=0;i<data.length;i++){const value=data[i];finite&&=Number.isFinite(value);peak=Math.max(peak,Math.abs(value));if(i>24000){sum+=value*value;count++;}if(i>48000*4.2&&i<48000*7.9)restPeak=Math.max(restPeak,Math.abs(value));}}
    return {peak,rms:Math.sqrt(sum/count),restPeak,finite};
   }
   return {longForm:await render(.35,false,[1,1,1,1],'ensemble','caper',.3,80),backgroundOnly:await render(.35,false,[0,1,0,0]),noBackground:await render(.35,false,[0,1,0,0],'ensemble','reflective',0),muted:await render(0),default:await render(.35),sparse:await render(.35,false,[1,1,1,1],'ensemble','reflective',0),fullBackground:await render(1,false,[1,1,1,1],'ensemble','reflective',1),synth:await render(.35,false,[1,1,1,1],'synth'),bassOnly:await render(.35,false,[1,0,0,0]),chase:await render(.35,false,[1,1,1,1],'ensemble','chase'),dialogue:await render(.35,false,[1,1,1,1],'ensemble','dialogue'),maximum:await render(1),overloaded:await render(1,true),layersMuted:await render(1,false,[0,0,0,0]),cap:OUTPUT_CEILING};
  });
  console.log('Native rendering measurements:',JSON.stringify(renders));
  for(const [name,result] of Object.entries(renders)){if(name==='cap')continue;assert(result.finite,name+' must have finite samples');assert(result.peak<=renders.cap+1e-6,name+' exceeded final limiter');}
  assert.equal(renders.muted.peak,0);assert.equal(renders.layersMuted.peak,0);
  assert(renders.default.peak>.02,'phrases should produce a usable signal');
  assert(renders.synth.peak>.02);assert(renders.bassOnly.peak>.02,'bass notes must remain audible on their own');
  assert(renders.default.restPeak>.0001,'continuous harmony should connect foreground phrases');
  assert(renders.backgroundOnly.peak>.001,'isolated background must produce audio');assert.equal(renders.noBackground.peak,0,'background zero must silence its isolated path');
  assert(renders.chase.restPeak>.001&&renders.chase.rms>renders.dialogue.rms,'chase arrangement must have a different rhythmic activity');
  assert(renders.maximum.rms>renders.default.rms,'volume control must work');
  assert(renders.overloaded.peak>.13,'stress signal must exercise the limiter');
  console.log('PASS native OfflineAudioContext rendering and limiter, including an 80-second score');

  await page.locator('#check-sound').click();
  await page.waitForFunction(()=>audio.checking&&audio.outputLevel().rms>.001);
  assert.equal(await page.evaluate(()=>audio.running),false,'check tone must not start the soundtrack');
  await page.waitForFunction(()=>!audio.checking&&audio.outputLevel().peak<.00001);
  console.log('PASS check tone produces signal, then stops');

  await page.locator('#play').click();
  await page.waitForFunction(()=>audio.running&&audio.outputLevel().rms>.005);
  await page.waitForFunction(()=>document.getElementById('signal').textContent.includes('signal detected'));
  await page.waitForFunction(()=>audio.outputLevel().rms>.005);
  const playingWave=await page.locator('#visualizer').screenshot();assert(!playingWave.equals(idleWave),'waveform should respond to actual audio');
  const graph=await page.evaluate(()=>{window.testAudioContext=audio.ctx;return audio.tick;});
  for(let i=0;i<20;i++)await page.locator('#next').click();
  assert(await page.evaluate(()=>audio.ctx===window.testAudioContext&&audio.running&&audio.voices.size<=12));
  assert((await page.evaluate(()=>audio.tick))>=graph);
  console.log('PASS real playback, signal meter and 20 paragraph changes');
  await page.locator('#chapter').selectOption('0');
  const phrasePosition=await page.evaluate(()=>audio.tick);
  await page.locator('#next').click();assert.equal(await page.evaluate(()=>audio.intent.kind),'dialogue');
  assert((await page.evaluate(()=>audio.tick))>=phrasePosition,'navigation must not rewind musical time');
  await page.locator('#next').click();assert.equal(await page.evaluate(()=>audio.intent.kind),'chase');
  await page.waitForFunction(()=>audio.plan.kind==='chase',null,{timeout:20000});
  assert.equal(await page.evaluate(()=>audio.composer.sceneSince%8),0,'scene changes must land at a bar boundary');
  await page.locator('#mode').selectOption('fixed');assert.equal(await page.evaluate(()=>audio.intent.id),'fixed');
  const fixedPosition=await page.evaluate(()=>audio.tick);await page.locator('#next').click();
  assert((await page.evaluate(()=>audio.tick))>=fixedPosition);assert.equal(await page.evaluate(()=>audio.intent.id),'fixed');
  await page.locator('#mode').selectOption('adaptive');
  console.log('PASS continuous musical position, scene dwell/bar-boundary transition and fixed comparison mode');

  for(const palette of ['synth','ensemble']){await page.locator('#palette').selectOption(palette);assert(await page.evaluate(()=>audio.ctx===window.testAudioContext&&audio.running));}
  console.log('PASS both palettes switch without rebuilding the playing graph');
  await page.locator('#background').fill('50');assert.equal(await page.evaluate(()=>audio.background),.5);
  await page.locator('#background').fill('0');assert.equal(await page.evaluate(()=>audio.background),0);
  await page.locator('#background').fill('30');
  console.log('PASS independent continuous-background control');

  await page.locator('#volume').fill('100');
  await page.waitForFunction(()=>audio.volume===1);
  const maximum=await page.evaluate(()=>audio.outputLevel());assert(maximum.peak<=renders.cap+1e-6);
  await page.locator('#volume').fill('0');
  await page.waitForFunction(()=>audio.outputLevel().peak<.00001);
  assert((await page.locator('#audio-status').innerText()).includes('Muted'));
  await page.locator('#volume').fill('35');
  await page.waitForFunction(()=>audio.outputLevel().rms>.005);
  await page.locator('#mute').click();
  await page.waitForFunction(()=>!audio.running&&!audio.checking&&audio.outputLevel().peak<.00001);
  console.log('PASS maximum volume cap, volume zero and emergency mute');

  await page.locator('#check-sound').click();await page.waitForFunction(()=>audio.checking);
  await page.keyboard.press('Escape');
  await page.waitForFunction(()=>!audio.checking&&audio.outputLevel().peak<.00001);
  await page.locator('#play').click();await page.waitForFunction(()=>audio.running);
  await page.locator('#play').click();await page.waitForFunction(()=>!audio.running&&audio.outputLevel().peak<.00001);
  console.log('PASS Escape stops test tone; Pause stops soundtrack');
  await page.locator('#check-sound').click();await page.waitForFunction(()=>audio.checking&&audio.outputLevel().rms>.001);
  await page.waitForFunction(()=>!audio.checking&&audio.outputLevel().peak<.00001);
  assert.equal(await page.evaluate(()=>audio.running),false,'checking sound must not restart a paused soundtrack');
  await page.waitForFunction(()=>waveFrame===0);assert((await page.locator('#visualizer').screenshot()).equals(idleWave),'paused waveform should return to its baseline');
  await page.emulateMedia({reducedMotion:'reduce'});await page.locator('#play').click();await page.waitForFunction(()=>audio.running&&audio.outputLevel().rms>.005);
  assert.equal(await page.evaluate(()=>waveFrame),0,'reduced-motion preference must disable animation');
  await page.locator('#mute').click();await page.emulateMedia({reducedMotion:'no-preference'});
  console.log('PASS audio-driven waveform, idle baseline and reduced-motion preference');

  await page.getByText('Score seed',{exact:true}).click();await page.locator('#seed').fill('repeatable-rat');
  await page.getByRole('button',{name:'Apply seed',exact:true}).click();
  assert.equal(await page.evaluate(()=>audio.composer.seed),'repeatable-rat');assert.equal(await page.evaluate(()=>audio.tick),0);
  await page.locator('#play').click();await page.waitForFunction(()=>audio.tick>=3);
  await page.locator('#seed').fill('queued-rat');await page.getByRole('button',{name:'Apply seed',exact:true}).click();
  assert.equal(await page.evaluate(()=>audio.composer.seed),'repeatable-rat');assert.equal(await page.evaluate(()=>audio.pendingSeed),'queued-rat');
  await page.waitForFunction(()=>audio.composer.seed==='queued-rat'&&scoreSeeds.rat==='queued-rat',null,{timeout:20000});
  assert.equal(await page.evaluate(()=>audio.pendingSeed),null);await page.locator('#mute').click();
  const checkpoint=await page.evaluate(()=>audio.snapshot());await page.reload();
  assert.deepEqual(await page.evaluate(()=>audio.snapshot()),checkpoint);assert.equal(await page.evaluate(()=>audio.ctx),null);
  await page.locator('.book').filter({hasText:'The Time Machine'}).click();assert.equal(await page.evaluate(()=>audio.composer.seed),'time-001');
  await page.locator('.book').filter({hasText:'The Stainless Steel Rat'}).click();assert.equal(await page.evaluate(()=>audio.composer.seed),'queued-rat');
  await page.getByText('Score seed',{exact:true}).click();await page.getByRole('button',{name:'New interpretation',exact:true}).click();
  const generatedSeed=await page.evaluate(()=>audio.composer.seed);assert.match(generatedSeed,/^rat-[0-9a-f]{8}$/);await page.reload();assert.equal(await page.evaluate(()=>audio.composer.seed),generatedSeed);
  console.log('PASS explicit/generated seeds, per-book independence, checkpoints, reload and no autoplay');

  const paragraphCount=await page.evaluate(()=>nodes.length);
  await page.locator('#jump').fill('78');await page.locator('#jump-form button').click();
  assert((await page.locator('#position').innerText()).startsWith('78 / '));
  const jumpedChapter=await page.locator('#chapter').inputValue();assert.notEqual(jumpedChapter,'0','book-wide jump should cross chapter boundaries');
  await page.locator('#jump').fill(String(paragraphCount+1));await page.locator('#jump-form button').click();
  assert((await page.locator('#position').innerText()).startsWith('78 / '),'invalid jump must leave position unchanged');
  await page.locator('#jump').fill('1.5');await page.locator('#jump-form button').click();assert((await page.locator('#position').innerText()).startsWith('78 / '));
  await page.locator('#jump').fill(String(paragraphCount));await page.locator('#jump').press('Enter');
  assert.equal(await page.locator('#next').isEnabled(),false);
  await page.reload();assert((await page.locator('#position').innerText()).startsWith(paragraphCount+' / '));
  const volume=await page.locator('#volume').inputValue(),background=await page.locator('#background').inputValue();
  await page.locator('#restart').click();assert((await page.locator('#position').innerText()).startsWith('1 / '));
  assert.equal(await page.locator('#previous').isEnabled(),false);assert.equal(await page.locator('#chapter').inputValue(),'0');
  assert.equal(await page.locator('#volume').inputValue(),volume);assert.equal(await page.locator('#background').inputValue(),background);
  assert.equal(await page.evaluate(()=>preceding),null,'restart must clear prior passage context');assert.equal(await page.evaluate(()=>audio.tick),0);assert.equal(await page.evaluate(()=>audio.composer.seed),generatedSeed);
  await page.reload();assert((await page.locator('#position').innerText()).startsWith('1 / '));
  console.log('PASS restart, book-wide paragraph jump, validation, settings preservation and persistence');

  await page.setViewportSize({width:390,height:844});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'mobile must not overflow horizontally');
  await page.locator('#check-sound').scrollIntoViewIfNeeded();
  assert(await page.locator('#check-sound').isVisible());assert(await page.locator('#mute').isVisible());
  assert(await page.locator('#restart').isVisible());assert(await page.locator('#jump').isVisible());
  const position=await page.locator('#position').innerText();await page.reload();assert.equal(await page.locator('#position').innerText(),position);assert.equal(await page.evaluate(()=>audio.ctx),null);
  console.log('PASS mobile controls, progress restoration and no autoplay');
  assert.deepEqual(errors,[],'browser should not emit runtime errors');
  if(process.env.AWEN_SCREENSHOT){await page.setViewportSize({width:1180,height:1000});await page.locator('#play').scrollIntoViewIfNeeded();await page.screenshot({path:process.env.AWEN_SCREENSHOT});}
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
