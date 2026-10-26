const assert=require('node:assert/strict');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.env.AWEN_BROWSER_CHANNEL||'msedge'});
 try{
  const page=await browser.newPage({viewport:{width:1180,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(12000);
  await page.goto(pathToFileURL(path.join(__dirname,'../index.html')).href);await page.locator('#tuning > summary').click();
  const position=await page.locator('#position').textContent(),tick=await page.evaluate(()=>audio.tick);
  await page.locator('#starter-new').click();assert.equal(await page.locator('.candidate').count(),6);
  for(const id of ['frontier','caper','unseen','dialogue'])assert.equal(await page.locator('.candidate[data-style="'+id+'"]').count(),1);
  const card=id=>page.locator('.candidate[data-style="'+id+'"]').first(),button=(id,action)=>card(id).locator('[data-action="'+action+'"]');
  // Explore from a recipe first, then adopt a previewed variation.
  await button('frontier','explore').click();assert(await page.evaluate(()=>audition.candidates.every(c=>c.genome.scoreStyle==='frontier')));
  await page.locator('#gallery-back').click();assert.equal(await page.locator('.candidate[data-style="caper"]').count(),1);
  await button('frontier','pin').click();await card('frontier').locator('input[type=text]').fill('Open spaces');await card('frontier').locator('input[type=text]').press('Tab');
  await button('frontier','play').click();await page.waitForFunction(()=>audio.running&&audio.genome.scoreStyle==='frontier');await page.waitForFunction(()=>audio.outputLevel().rms>.0005);
  await button('frontier','keep').click();assert.equal(await page.evaluate(()=>profile.genome.scoreStyle),'frontier');assert.equal(await page.evaluate(()=>audio.tick),tick);assert.equal(await page.locator('#position').textContent(),position);
  await page.reload();await page.locator('#tuning > summary').click();assert.equal(await page.evaluate(()=>profile.genome.scoreStyle),'frontier');assert.equal(await page.evaluate(()=>audio.ctx),null);assert.match(await page.locator('#active-style').textContent(),/Spacious frontier/);
  await page.locator('#evolve-new').click();assert(await page.evaluate(()=>audition.candidates.every(c=>c.genome.scoreStyle==='frontier')));await page.keyboard.press('Escape');
  await page.locator('#shelf .book').nth(1).click();assert.equal(await page.evaluate(()=>audio.genome.scoreStyle),'frontier');await page.locator('#shelf .book').nth(0).click();assert.equal(await page.evaluate(()=>audio.genome.scoreStyle),'frontier');assert.equal(await page.locator('#position').textContent(),position);
  // A named favourite keeps both the recipe and six traits through an actual JSON import.
  const exported=await page.evaluate(()=>JSON.stringify(profile));await page.locator('#profile-file').setInputFiles({name:'frontier.json',mimeType:'application/json',buffer:Buffer.from(exported)});await page.waitForFunction(()=>profileFileState.method==='import');assert.equal(await page.evaluate(()=>profile.genome.scoreStyle),'frontier');assert.equal(await page.evaluate(()=>Object.values(profile.pinNames)[0]),'Open spaces');
  await page.locator('#starter-new').click();await page.locator('.candidate[data-style="frontier"]').first().locator('input[type=checkbox]').check();await card('caper').locator('input[type=checkbox]').check();await page.locator('#explore-selected').click();assert.equal(await page.evaluate(()=>audition.parents.length),2);assert(await page.evaluate(()=>audition.candidates.every(c=>c.genome.scoreStyle==='frontier')));await page.keyboard.press('Escape');
  // Tiny comparison: four original recipes on the same three Rat passages. No audio corpus retained.
  const report=await page.evaluate(async()=>{
   const results=[];const book=books.find(b=>b.id==='rat');let previous=null;
   for(let i=0;i<3;i++){const text=book.chapters[0].paragraphs[i],raw=analyze(text).raw,features=contextual(raw,previous);previous=raw;const intent=directPassage(text,features,'proof-'+i),target=mapScore(features),context={seed:'rat-001',book:'rat',snapshot:makeComposer(),target,intent,palette:'ensemble',background:.3,mix:[1,1,1,1]};
    for(const style of ['frontier','caper','unseen','dialogue']){const metrics=await measurePreview(starterGenome(style),context);results.push({paragraph:i+1,scene:intent.kind,style,...metrics});}
   }
   return results;
  });
  for(const r of report){assert(r.rms>.001,r.style+' must have usable signal');assert(r.peak<=.140001);assert(Number.isFinite(r.rms));}
  console.log('Three-passage starting-point proof:',JSON.stringify(report));
  // Render a later dialogue phrase to verify breathing room still has continuous background.
  const rest=await page.evaluate(async()=>{let state=makeComposer();for(let i=0;i<32;i++)state=planStep(state,{kind:'dialogue'},'dialogue').state;return measurePreview(starterGenome('dialogue'),{seed:'rat-001',book:'rat',snapshot:state,target:neutral,intent:{id:'rest',kind:'dialogue'},palette:'ensemble',background:.3,mix:[1,1,1,1]});});assert(rest.rms>.0001);assert(rest.peak<=.140001);
  await page.locator('#starter-new').click();if(process.env.AWEN_SCREENSHOT)await page.screenshot({path:process.env.AWEN_SCREENSHOT});await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.keyboard.press('Escape');assert.deepEqual(errors,[]);
  console.log('PASS original recipes, persistent/evolvable choice, named-pin migration, multi-parent identity, matched passage/seed/context, native signal cap, dialogue rests and mobile controls');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
