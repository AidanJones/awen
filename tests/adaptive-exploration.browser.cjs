'use strict';
// Synthetic selections only. Native sample differences do not establish artistic quality.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {pathToFileURL}=require('node:url'),{chromium}=require('playwright');
(async()=>{
 const file=process.env.AWEN_EXPLORATION_PAGE;if(!file)throw Error('Set AWEN_EXPLORATION_PAGE');
 const browser=await chromium.launch({headless:true,channel:process.env.AWEN_BROWSER_CHANNEL||'msedge'});
 try{
  const context=await browser.newContext({acceptDownloads:true}),page=await context.newPage({viewport:{width:1250,height:1000}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));await page.goto(/^http/.test(file)?file:pathToFileURL(path.resolve(file)).href);
  assert(await page.locator('#widen').isDisabled());
  await page.locator('.card').first().getByRole('button',{name:'Select for next round',exact:true}).click();
  const favourite=await page.evaluate(()=>round().cards[0]);await page.locator('#evolve').click();
  const mixed=await page.evaluate(()=>round());assert.deepEqual(mixed.cards[0],favourite);
  assert.deepEqual(mixed.branch.offspring.reduce((a,c)=>(a[c.tier]=(a[c.tier]||0)+1,a),{}),{near:2,medium:3,broad:3});
  await page.locator('#widen').click();const wide=await page.evaluate(()=>round());assert.deepEqual(wide.cards[0],favourite);
  assert.equal(wide.branch.action,'widen');assert.equal(wide.branch.breadth,2);assert.equal(wide.branch.offspring.filter(c=>c.tier==='broad').length,5);
  assert.equal(wide.selected.length,0);assert(await page.locator('#widen').isEnabled());
  const audio=await page.evaluate(async()=>{const out=[];for(const c of round().cards){const r=await renderPreview(c,data.scenes[0],'ADAPTIVE-TEST-ONLY',32),samples=r.buffer.getChannelData(0);let hash=2166136261;for(let i=0;i<samples.length;i+=17)hash=Math.imul(hash^Math.round(samples[i]*1e7),16777619);out.push({id:c.id,tier:c.lineage?.tier||'parent',hash,peak:r.peak,rms:r.rms,gain:r.gain});normalProfile({version:1,genomeVersion:'awen-genome-1',genome:c.genome});}return out;});
  assert.equal(new Set(audio.map(c=>c.hash)).size,9);assert(audio.every(c=>c.peak<=.14001&&c.rms>.0005&&c.rms<=.018001&&c.gain<=1));
  await page.reload();assert.deepEqual(await page.evaluate(()=>round().cards),wide.cards);
  await page.locator('#undo').click();await page.locator('#widen').click();assert.deepEqual(await page.evaluate(()=>round().cards),wide.cards);
  await page.locator('#widen').click();assert.equal(await page.evaluate(()=>round().branch.breadth),3);
  const broader=await page.evaluate(()=>round());assert.equal(broader.branch.offspring.filter(c=>c.tier==='broad').length,6);assert.deepEqual(broader.cards[0],favourite);
  const selected=broader.cards.at(-1);await page.locator('.card').last().getByRole('button',{name:'Select for next round',exact:true}).click();await page.locator('#refine').click();
  const refined=await page.evaluate(()=>round());assert.deepEqual(refined.cards[0],selected);assert.equal(refined.branch.breadth,0);assert(refined.branch.offspring.every(c=>c.tier==='near'));
  await page.locator('.listen').first().click();await page.waitForFunction(()=>playing!==null);await page.keyboard.press('Escape');assert.equal(await page.evaluate(()=>source),null);
  const event=page.waitForEvent('download');await page.locator('#export').click();const download=await event,dest=path.resolve('.score-lab/tests/adaptive-TEST-ONLY-'+crypto.randomUUID()+'.json');await download.saveAs(dest);
  const backup=JSON.parse(fs.readFileSync(dest));assert.equal(backup.branchingVersion,'awen-branching-1');assert.equal(backup.rounds.length,5);
  await page.locator('#reset').click();await page.getByText('Restore exploration backup',{exact:true}).click();await page.locator('#restore').setInputFiles(dest);await page.waitForFunction(()=>document.getElementById('status').textContent.includes('restored'));assert.deepEqual(await page.evaluate(()=>round().cards),refined.cards);
  const bad=structuredClone(backup);bad.rounds.at(-1).branch.parents=['missing'];await page.locator('#restore').setInputFiles({name:'bad.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(bad))});await page.waitForFunction(()=>document.getElementById('status').textContent.includes('Invalid branch'));assert.deepEqual(await page.evaluate(()=>round().cards),refined.cards);
  const legacy=structuredClone(backup);delete legacy.branchingVersion;delete legacy.branchingSha256;legacy.rounds=legacy.rounds.slice(0,1);legacy.position=0;await page.locator('#restore').setInputFiles({name:'legacy.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(legacy))});await page.waitForFunction(()=>document.getElementById('status').textContent.includes('restored'));assert.equal(await page.evaluate(()=>state.position),0);
  await page.emulateMedia({colorScheme:'dark'});await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  const screenshot=path.resolve('.score-lab/tests/adaptive-dark-'+crypto.randomUUID()+'.png');await page.screenshot({path:screenshot,fullPage:true});assert.deepEqual(errors,[]);
  const proof={testOnly:true,mixed:true,adaptiveWidening:[2,3],refinement:true,favouriteUnchanged:true,deterministicReplay:true,backupRestore:true,legacyRestore:true,invalidLineageRejected:true,nativeAudio:audio,screenshot,errors};
  const proofFile=path.resolve('.score-lab/tests/adaptive-proof-'+crypto.randomUUID()+'.json');fs.writeFileSync(proofFile,JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify({...proof,proofFile}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
