'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),{pathToFileURL}=require('node:url'),{chromium}=require('playwright');
(async()=>{const browser=await chromium.launch({headless:true,channel:process.env.AWEN_BROWSER_CHANNEL||'msedge'});try{
 const context=await browser.newContext({acceptDownloads:true}),page=await context.newPage({viewport:{width:1200,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(path.resolve(process.env.AWEN_EXPLORATION_PAGE)).href);
 assert.match(await page.locator('h1').textContent(),/point-and-click/);assert.match(await page.locator('#passage').textContent(),/black powder/);assert.equal(await page.locator('#starting-set').inputValue(),'adventure');
 const initial=await page.evaluate(()=>round().cards);assert.equal(initial.length,9);assert(initial.every(c=>c.adventure));
 const reference=await page.evaluate(async()=>{
  const card=round().cards[0],events=[],original=AudioAdapter.prototype.note;
  AudioAdapter.prototype.note=function(hz,t,duration,layer,...rest){events.push({step:Math.round((t-.12)/STEP_SECONDS),midi:Math.round(69+12*Math.log2(hz/440)),duration,layer});return original.call(this,hz,t,duration,layer,...rest);};
  try{await renderPreview(card,data.scenes[state.scene],state.seed,64);}finally{AudioAdapter.prototype.note=original;}
  const expected=AwenAdventure.plan(data.adventure,card.adventure,false).notes.map(e=>({step:e.step,midi:e.midi,duration:e.durationSteps*STEP_SECONDS,layer:e.layer}));
  return {actual:events.filter(e=>e.step<128),expected:expected.sort((a,b)=>a.step-b.step)};
 });assert.deepEqual(reference.actual,reference.expected);
 const samples=await page.evaluate(async()=>{const result=[];for(const c of round().cards){const r=await renderPreview(c,data.scenes[state.scene],state.seed,32),values=r.buffer.getChannelData(0);let hash=2166136261;for(let i=0;i<values.length;i+=17)hash=Math.imul(hash^Math.round(values[i]*1e7),16777619);result.push({id:c.id,hash,peak:r.peak,rms:r.rms,gain:r.gain});}return result;});
 assert.equal(new Set(samples.map(r=>r.hash)).size,9);assert(samples.every(r=>r.peak<=.14001&&r.rms>.0005&&r.gain<=1));
 assert(await page.locator('.card').first().getByRole('button',{name:'Score saved in exploration backup'}).isDisabled());
 await page.locator('.card').first().getByRole('button',{name:'Select for next round',exact:true}).click();await page.locator('#widen').click();
 const wider=await page.evaluate(()=>round().cards);assert.deepEqual(wider[0],initial[0]);assert(wider.every(c=>c.adventure));
 await page.reload();assert.deepEqual(await page.evaluate(()=>round().cards),wider);
 const download=page.waitForEvent('download');await page.locator('#export').click();const file=path.resolve('.score-lab/tests/adventure-family-TEST-ONLY-'+crypto.randomUUID()+'.json');await(await download).saveAs(file);
 const backup=JSON.parse(fs.readFileSync(file));assert(backup.adventureSha256);assert(backup.rounds.at(-1).cards.every(c=>c.adventure));
 await page.locator('#reset').click();await page.getByText('Restore exploration backup',{exact:true}).click();await page.locator('#restore').setInputFiles(file);await page.waitForFunction(()=>document.getElementById('status').textContent.includes('restored'));assert.deepEqual(await page.evaluate(()=>round().cards),wider);
 assert.deepEqual(errors,[]);const proof={testOnly:true,originalScheduledNotesVerified:true,originalPassage:true,familyPreserved:true,favouriteUnchanged:true,backupRestore:true,readerExportGuarded:true,native:samples,errors},proofFile=path.resolve('.score-lab/tests/adventure-explorer-proof-'+crypto.randomUUID()+'.json');fs.writeFileSync(proofFile,JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify({...proof,proofFile}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
