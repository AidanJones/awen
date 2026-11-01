// Audio/UI engineering checks only. This page intentionally collects no listener labels.
const assert=require('node:assert/strict'),path=require('node:path');
const {pathToFileURL}=require('node:url'),{chromium}=require('playwright');
(async()=>{const file=process.env.AWEN_MULTIOBJECTIVE_PAGE;if(!file)throw Error('Set AWEN_MULTIOBJECTIVE_PAGE');const b=await chromium.launch({headless:true,channel:process.env.AWEN_BROWSER_CHANNEL||'msedge'});try{
 const page=await b.newPage(),errors=[],external=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))external.push(r.url());});await page.goto(pathToFileURL(path.resolve(file)).href);
 assert.equal(await page.locator('h2').count(),3);assert.equal(await page.locator('audio').count(),27);assert.match(await page.locator('body').textContent(),/synthetic-label fitted test models/);assert.match(await page.locator('body').textContent(),/No validated reward/);assert(await page.evaluate(()=>[...document.querySelectorAll('audio')].every(a=>a.paused)));
 await page.locator('#stop').click();await page.locator('audio').nth(0).evaluate(a=>a.play());await page.waitForFunction(()=>document.querySelectorAll('audio')[0].currentTime>.05);
 await page.locator('audio').nth(1).evaluate(a=>a.play());assert(await page.locator('audio').nth(0).evaluate(a=>a.paused));await page.locator('#stop').click();assert(await page.evaluate(()=>[...document.querySelectorAll('audio')].every(a=>a.paused)));
 await page.locator('audio').nth(2).evaluate(a=>a.play());await page.keyboard.press('Escape');assert(await page.locator('audio').nth(2).evaluate(a=>a.paused));await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 console.log('PASS real prototype WAV playback, no autoplay, exclusive playback, Stop/Escape, test-model disclosures, three scene tables and mobile layout.');
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
