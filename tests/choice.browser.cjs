'use strict';
// Synthetic test choices in an isolated context, never actual listener labels.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {pathToFileURL}=require('node:url'),{chromium}=require('playwright');
(async()=>{
 const file=process.env.AWEN_CHOICE_PAGE;if(!file)throw Error('Set AWEN_CHOICE_PAGE');
 const browser=await chromium.launch({headless:true,channel:process.env.AWEN_BROWSER_CHANNEL||'msedge'});
 try{
  const context=await browser.newContext({acceptDownloads:true}),page=await context.newPage({viewport:{width:1150,height:950}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));await page.goto(/^http/.test(file)?file:pathToFileURL(path.resolve(file)).href);
  assert.equal(await page.locator('#progress').textContent(),'Passage 1 of 2');assert.equal(await page.locator('textarea,select').count(),0);
  assert.equal(await page.locator('[data-choice][aria-pressed="true"]').count(),0);
  assert(await page.evaluate(()=>[...document.querySelectorAll('audio')].every(a=>a.paused)));
  await page.locator('#play-A').click();await page.waitForFunction(()=>document.getElementById('audio-A').currentTime>.4);
  assert(Math.abs(await page.locator('#audio-A').evaluate(a=>a.duration)-165)<.01);
  const mediaURL=await page.locator('#audio-A').evaluate(a=>a.src);
  const range=await page.request.get(mediaURL,{headers:{Range:'bytes=0-15'}});
  assert.equal(range.status(),206);assert.equal((await range.body()).length,16);
  await page.locator('#audio-A').evaluate(a=>a.currentTime=60);
  await page.waitForFunction(()=>{const a=document.getElementById('audio-A');return !a.seeking&&a.currentTime>60.3&&a.currentTime<64;});
  await page.locator('#audio-A').evaluate(a=>a.currentTime=5);
  await page.waitForFunction(()=>{const a=document.getElementById('audio-A');return !a.seeking&&a.currentTime>5.3&&a.currentTime<9;});
  await page.locator('#play-B').click();await page.waitForFunction(()=>!document.getElementById('audio-B').paused&&document.getElementById('audio-A').paused);
  await page.keyboard.press('Escape');assert(await page.locator('#audio-B').evaluate(a=>a.paused));
  await page.locator('[data-choice="A"]').click();assert.equal(await page.locator('#saved').textContent(),'1 of 2 choices saved');
  await page.reload();assert.equal(await page.locator('[data-choice="A"]').getAttribute('aria-pressed'),'true');
  await page.locator('#next').click();assert.equal(await page.locator('#progress').textContent(),'Passage 2 of 2');
  await page.locator('[data-choice="neither"]').click();assert.equal(await page.locator('#saved').textContent(),'2 of 2 choices saved');
  const event=page.waitForEvent('download');await page.locator('#next').click();const download=await event;
  const dest=path.resolve('.score-lab/tests/choices-TEST-ONLY-'+crypto.randomUUID()+'.json');await download.saveAs(dest);
  const data=JSON.parse(fs.readFileSync(dest));assert.equal(data.version,'awen-choice-labels-1');assert.deepEqual(data.responses.map(r=>r.choice),['A','neither']);assert(!('enjoyment' in data.responses[0]));
  await page.locator('#clear').click();assert.equal(await page.locator('#saved').textContent(),'1 of 2 choices saved');
  await page.getByText('Restore choices',{exact:true}).click();await page.locator('#restore').setInputFiles(dest);
  await page.waitForFunction(()=>document.getElementById('status').textContent.includes('Choices restored'));assert.equal(await page.locator('[data-choice="neither"]').getAttribute('aria-pressed'),'true');
  const wrong=path.resolve('.score-lab/tests/choices-WRONG-'+crypto.randomUUID()+'.json');fs.writeFileSync(wrong,JSON.stringify({...data,packetSha256:'wrong'}));await page.locator('#restore').setInputFiles(wrong);
  await page.waitForFunction(()=>document.getElementById('status').textContent.includes('another comparison'));assert.equal(await page.locator('[data-choice="neither"]').getAttribute('aria-pressed'),'true');
  await page.locator('[data-choice="tie"]').focus();await page.keyboard.press('Enter');assert.equal(await page.locator('[data-choice="tie"]').getAttribute('aria-pressed'),'true');
  await page.emulateMedia({colorScheme:'dark'});await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  const shot=path.resolve('.score-lab/tests/choices-dark-'+crypto.randomUUID()+'.png');await page.screenshot({path:shot,fullPage:true});assert.deepEqual(errors,[]);
  console.log(JSON.stringify({testOnly:true,trials:2,oneClickPreference:true,neitherTieClear:true,backupRestore:true,noDescriptionRequired:true,exclusivePlayback:true,byteRanges:true,forwardAndBackwardSeeking:true,screenshot:shot,errors}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
