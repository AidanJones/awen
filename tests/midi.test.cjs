'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync(require('node:path').resolve(__dirname,'../index.html'),'utf8'),script=html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const context=vm.createContext({setInterval:()=>1,clearInterval:()=>{},setTimeout,clearTimeout});vm.runInContext(script.split('const $=id=>')[0],context);
const {MidiScoreOutput,AudioAdapter}=vm.runInContext('({MidiScoreOutput,AudioAdapter})',context);
async function setup(){let time=1000;const messages=[],port={state:'connected',async open(){},async close(){},clear(){messages.push({clear:true});},send(bytes,at){messages.push({bytes:Array.from(bytes),at});}},midi=new MidiScoreOutput(()=>time);await midi.arm(port);return {midi,port,messages,setTime:t=>time=t};}
const on=messages=>messages.filter(m=>m.bytes?.[0]>>4===9),off=messages=>messages.filter(m=>m.bytes?.[0]>>4===8);
test('explicit arm, bounded channel/pitch/velocity, timed note off and no SysEx/program/clock',async()=>{
 const s=await setup();assert.equal(s.messages.length,0);s.midi.configure({channel:3,limit:999,parts:'foreground'});s.midi.tone(10,1020,300,127);s.midi.flush();assert.deepEqual(on(s.messages)[0],{bytes:[0x93,36,80],at:1020});s.setTime(1310);s.midi.flush();assert.deepEqual(off(s.messages)[0],{bytes:[0x83,36,0],at:1320});assert(s.messages.every(m=>m.bytes.length===3));
});
test('overlapping identical pitches release only after the last owner',async()=>{
 const s=await setup();s.midi.tone(60,1000,400,40);s.midi.tone(60,1100,800,40);s.midi.flush();s.setTime(1100);s.midi.flush();assert.equal(on(s.messages).length,1);s.setTime(1400);s.midi.flush();assert.equal(off(s.messages).length,0);s.setTime(1900);s.midi.flush();assert.equal(off(s.messages).length,1);assert.equal(s.midi.voices.size,0);
});
test('ambient harmony holds common tones, renews leases and releases when frames stop',async()=>{
 const s=await setup(),frame=(h,time=1)=>s.midi.frame({time,audioTime:1,harmony:h,events:[{midi:76,duration:1,layer:2,level:.3}],volume:.35,background:.3,mix:[1,1,1,1]});frame([48,55,64,72]);assert.equal(on(s.messages).length,4);s.setTime(1400);frame([48,55,65,72]);assert.equal(on(s.messages).length,5);assert.equal(off(s.messages).filter(m=>m.bytes[1]===64).length,1);assert.equal(on(s.messages).filter(m=>m.bytes[1]===48).length,1);s.setTime(3000);s.midi.flush();assert.equal(s.midi.voices.size,0);
});
test('polyphony and queue limits, stale starts, mute and panic cancel future and held notes',async()=>{
 const s=await setup();for(let n=36;n<76;n++)s.midi.tone(n,1000,2000,100);s.midi.flush();assert.equal(on(s.messages).length,8);s.midi.tone(80,1200,1000,20);s.midi.panic();assert(s.messages.some(m=>m.clear));assert.equal(s.midi.queue.length,0);assert.equal(s.midi.voices.size,0);const count=on(s.messages).length;s.setTime(5000);s.midi.flush();assert.equal(on(s.messages).length,count);assert(s.messages.some(m=>m.bytes?.[1]===123));assert(s.messages.some(m=>m.bytes?.[1]===120));
 s.midi.tone(60,1000,100,20);s.midi.flush();assert.equal(on(s.messages).length,count);
 s.midi.tone(60,5100,1000,20);s.midi.frame({volume:0});assert.equal(s.midi.queue.length,0);
});
test('suppressed previews, disconnect and send errors stop output without reconnecting',async()=>{
 const s=await setup();s.midi.suppressed=true;assert.equal(s.midi.tone(60,1000,100,20),null);s.midi.suppressed=false;s.midi.tone(60,1000,200,20);s.port.state='disconnected';let error='';s.midi.onFailure=e=>error=e;s.midi.flush();assert(!s.midi.enabled);assert(error.includes('disconnected'));s.port.state='connected';s.midi.flush();assert.equal(on(s.messages).length,0);
 await s.midi.arm(s.port);s.port.send=()=>{throw Error('unplug');};s.midi.tone(60,1000,200,20);s.midi.flush();assert(!s.midi.enabled);assert.equal(s.midi.voices.size,0);assert.equal(s.midi.queue.length,0);
});
test('pending device opens are cancelled by panic, and offline adapters have no MIDI sink',async()=>{
 let finish;const midi=new MidiScoreOutput(()=>0),port={state:'connected',open:()=>new Promise(resolve=>finish=resolve),close:async()=>{},clear(){},send(){}};
 const opening=midi.arm(port);midi.panic();finish();assert.equal(await opening,false);assert(!midi.enabled);assert.equal(midi.port,null);assert.equal(new AudioAdapter().midi,undefined);
});
