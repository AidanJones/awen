'use strict';
// Isolated synthetic interactions, never listener preference evidence.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {pathToFileURL}=require('node:url'),{chromium}=require('playwright');
(async()=>{
 const file=process.env.AWEN_ADVENTURE_PAGE;if(!file)throw Error('Set AWEN_ADVENTURE_PAGE');
 const browser=await chromium.launch({headless:true,channel:process.env.AWEN_BROWSER_CHANNEL||'msedge'});
 try{
  const context=await browser.newContext({acceptDownloads:true}),page=await context.newPage({viewport:{width:1100,height:950}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));await page.goto(/^https?:/.test(file)?file:pathToFileURL(path.resolve(file)).href);
  assert(!(await page.locator('body').textContent()).includes('86 seconds'));
  assert.equal(await page.locator('#trial-progress').textContent(),'Comparison 1 of 4');
  assert.equal(await page.locator('#fit').inputValue(),'');assert(await page.evaluate(()=>[...document.querySelectorAll('audio')].every(a=>a.paused)));
  await page.locator('#play-A').click();await page.waitForFunction(()=>document.getElementById('audio-A').currentTime>.4);
  assert(Math.abs(await page.locator('#audio-A').evaluate(a=>a.duration)-165)<.01);
  await page.locator('#play-B').click();await page.waitForFunction(()=>!document.getElementById('audio-B').paused&&document.getElementById('audio-A').paused);
  assert(await page.locator('#audio-A').evaluate(a=>a.paused));await page.keyboard.press('Escape');assert(await page.locator('#audio-B').evaluate(a=>a.paused));
  await page.locator('#fit').selectOption('A');await page.locator('#enjoyment').selectOption('B');await page.locator('#lessDistracting').selectOption('tie');await page.locator('#notes').fill('SYNTHETIC AUTOMATION TEST ONLY');
  await page.reload();assert.equal(await page.locator('#fit').inputValue(),'A');assert.equal(await page.locator('#enjoyment').inputValue(),'B');
  const event=page.waitForEvent('download');await page.locator('#export').click();const download=await event;
  const dest=path.resolve('.score-lab/tests/adventure-TEST-ONLY-'+crypto.randomUUID()+'.json');await download.saveAs(dest);
  const data=JSON.parse(fs.readFileSync(dest));assert.equal(data.responses.length,1);assert.equal(data.responses[0].lessDistracting,'tie');
  await page.locator('#fit').selectOption('B');await page.getByText('Restore an exported backup').click();await page.locator('#load-backup').setInputFiles(dest);
  await page.waitForFunction(()=>document.getElementById('status').textContent.includes('Backup restored'));assert.equal(await page.locator('#fit').inputValue(),'A');
  await page.locator('#next').click();assert.equal(await page.locator('#fit').inputValue(),'');
  await page.emulateMedia({colorScheme:'dark'});await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  const shot=path.resolve('.score-lab/tests/adventure-dark-'+crypto.randomUUID()+'.png');await page.screenshot({path:shot,fullPage:true});
  assert.deepEqual(errors,[]);console.log(JSON.stringify({testOnly:true,trials:4,exclusivePlayback:true,backupRestore:true,darkMobile:true,screenshot:shot,errors}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
