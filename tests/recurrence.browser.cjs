'use strict';
// Synthetic interactions in an isolated profile; never actual listener ratings.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {pathToFileURL}=require('node:url'),{chromium}=require('playwright');
(async()=>{
 const file=process.env.AWEN_RECURRENCE_PAGE;if(!file)throw Error('Set AWEN_RECURRENCE_PAGE');
 const browser=await chromium.launch({headless:true,channel:process.env.AWEN_BROWSER_CHANNEL||'msedge'});
 try{const context=await browser.newContext({acceptDownloads:true}),page=await context.newPage({viewport:{width:1100,height:950}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));await page.goto(pathToFileURL(path.resolve(file)).href);
  assert.equal(await page.locator('#trial-progress').textContent(),'Comparison 1 of 14');
  assert.equal(await page.evaluate(()=>document.querySelectorAll('audio[autoplay]').length),0);
  assert(await page.evaluate(()=>[...document.querySelectorAll('audio')].every(a=>a.paused)));
  assert.equal(await page.locator('#recurrence').inputValue(),'');
  await page.locator('#play-A').click();await page.waitForFunction(()=>document.getElementById('audio-A').currentTime>.4);
  await page.locator('#play-B').click();await page.waitForFunction(()=>!document.getElementById('audio-B').paused);
  assert(await page.locator('#audio-A').evaluate(a=>a.paused));await page.keyboard.press('Escape');assert(await page.locator('#audio-B').evaluate(a=>a.paused));
  await page.locator('#recurrence').selectOption('tie');await page.locator('#fit').selectOption('A');await page.locator('#enjoyment').selectOption('B');await page.locator('#lessDistracting').selectOption('unsure');await page.locator('#notes').fill('SYNTHETIC AUTOMATION TEST ONLY');
  await page.reload();assert.equal(await page.locator('#recurrence').inputValue(),'tie');assert.equal(await page.locator('#fit').inputValue(),'A');
  assert(await page.locator('#audio-A').evaluate(a=>a.paused));
  const event=page.waitForEvent('download');await page.locator('#export').click();const download=await event,dest=path.resolve('.score-lab/tests/recurrence-TEST-ONLY-'+crypto.randomUUID()+'.json');await download.saveAs(dest);
  const data=JSON.parse(fs.readFileSync(dest));assert.equal(data.version,'awen-recurrence-labels-1');assert.equal(data.responses.length,1);assert.equal(data.responses[0].enjoyment,'B');assert.equal(data.responses[0].lessDistracting,'unsure');
  await page.locator('#recurrence').selectOption('A');await page.getByText('Restore an exported backup').click();await page.locator('#load-backup').setInputFiles(dest);await page.waitForFunction(()=>document.getElementById('status').textContent.includes('Backup restored'));assert.equal(await page.locator('#recurrence').inputValue(),'tie');
  const wrong=path.resolve('.score-lab/tests/recurrence-WRONG-'+crypto.randomUUID()+'.json');fs.writeFileSync(wrong,JSON.stringify({...data,packetSha256:'wrong'}));await page.locator('#load-backup').setInputFiles(wrong);await page.waitForFunction(()=>document.getElementById('status').textContent.includes('another packet'));assert.equal(await page.locator('#recurrence').inputValue(),'tie');
  await page.locator('#next').click();assert.equal(await page.locator('#recurrence').inputValue(),'');await page.locator('#previous').click();assert.equal(await page.locator('#recurrence').inputValue(),'tie');
  await page.emulateMedia({colorScheme:'dark'});await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  const shot=path.resolve('.score-lab/tests/recurrence-dark-'+crypto.randomUUID()+'.png');await page.screenshot({path:shot,fullPage:true});assert.deepEqual(errors,[]);
  console.log(JSON.stringify({testOnly:true,trials:14,exportRestore:true,exclusivePlayback:true,darkMobile:true,screenshot:shot,errors}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
