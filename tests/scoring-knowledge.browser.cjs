const assert=require('node:assert/strict');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.env.AWEN_BROWSER_CHANNEL||'msedge'});
 try{
  const page=await browser.newPage(),errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url());});await page.goto(pathToFileURL(path.join(__dirname,'../index.html')).href);
  const metrics=await page.evaluate(async()=>{
   const choices=new Map();for(const genre of Object.keys(scoringKnowledge.genres))for(const scene of Object.keys(scoringKnowledge.sceneFunctions))for(let variant=0;variant<2;variant++){const recipe=proposeHarmony(genre,scene,variant);if(!choices.has(recipe.familyId))choices.set(recipe.familyId,recipe);}
   const context={seed:'rat-001',book:'rat',snapshot:makeComposer(),target:neutral,intent:{id:'proof',kind:'suspense'},palette:'ensemble',background:.3,mix:[1,1,1,1]},result=[];
   for(const recipe of choices.values()){const rendered=await measurePreview(normalGenome(),{...context,harmonyRecipe:recipe});result.push({id:recipe.familyId,...rendered});}return result;
  });
  assert.equal(metrics.length,9);for(const m of metrics){assert(Number.isFinite(m.rms)&&m.rms>.001);assert(m.peak<=.140001);}
  console.log('Nine-family native render check:',JSON.stringify(metrics));
  const profileBefore=await page.evaluate(()=>profileStamp(profile));await page.locator('#play').click();await page.waitForFunction(()=>audio.running);
  const transition=await page.evaluate(()=>{const savedCheckpoint=JSON.stringify(JSON.parse(localStorage.getItem(storageKey)).scoreSessions.rat.state),graph=audio.ctx,recipe=proposeHarmony('unseen','discovery',0);audio.composer.step=31;audio.queueHarmonyRecipe(recipe);audio.composeBeat(audio.ctx.currentTime+.2);const before=audio.harmonyRecipe;audio.composeBeat(audio.ctx.currentTime+.3);const applied={id:audio.harmonyRecipe.familyId,step:audio.tick};persist();const checkpointPreserved=JSON.stringify(JSON.parse(localStorage.getItem(storageKey)).scoreSessions.rat.state)===savedCheckpoint;audio.queueHarmonyRecipe(null);audio.composer.step=64;audio.composeBeat(audio.ctx.currentTime+.4);return {before,applied,cleared:audio.harmonyRecipe,sameGraph:audio.ctx===graph,checkpointPreserved,step:audio.tick};});
  assert.equal(transition.before,null);assert.equal(transition.applied.id,'tritone-distance');assert.equal(transition.applied.step,33);assert.equal(transition.cleared,null);assert.equal(transition.step,65);assert(transition.sameGraph);assert(transition.checkpointPreserved);assert.equal(await page.evaluate(()=>profileStamp(profile)),profileBefore);await page.keyboard.press('Escape');assert.equal(await page.evaluate(()=>audio.running),false);
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);console.log('PASS embedded research data, nine native harmonic families, phrase-boundary application/removal, unchanged preference profile, shared audio graph and no runtime network requests');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
