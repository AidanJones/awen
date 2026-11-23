'use strict';
// Development-only bounded arrangement language; original material, not a game transcription.
const {digest}=require('./score-lab-metrics.cjs');
const VERSION='awen-adventure-arrangement-1',STEPS=128,REPEATS=3;
const FAMILY={version:VERSION,form:['A','answer','B','return'],
 sections:{
  A:{chords:['i','VI','iv','V'],figure:[0,-1,1,2,-1,1,0,-1]},
  answer:{chords:['i','VI','iv','V'],figure:[0,1,-1,2,1,-1,0,-1]},
  B:{chords:['III','VI','ii_dim','V'],figure:[2,-1,1,-1,0,1,-1,2]},
  return:{chords:['iv','i','V7','i'],figure:[0,-1,2,1,-1,0,1,-1]}
 }};
const CHORDS={i:[0,3,7],VI:[-4,0,3],iv:[-7,-4,0],V:[-5,-1,2],III:[-9,-5,-2],ii_dim:[-10,-7,-4],V7:[-5,-1,2,5]};
function compile(family=FAMILY,{seed='adventure-pilot-1',quiet=false}={}){
 if(!family||family.version!==VERSION||!Array.isArray(family.form)||family.form.length!==4||!family.sections||typeof seed!=='string'||seed.length>128||typeof quiet!=='boolean')throw Error('Invalid arrangement header');
 const root=60+(parseInt(digest(seed).slice(0,4),16)%3)*2,notes=[],bars=[];
 for(const [sectionIndex,name] of family.form.entries()){
  const section=Object.hasOwn(family.sections,name)&&family.sections[name];
  if(!section||!Array.isArray(section.chords)||section.chords.length!==4||!section.chords.every(c=>Object.hasOwn(CHORDS,c))||!Array.isArray(section.figure)||section.figure.length!==8||!section.figure.every(n=>Number.isInteger(n)&&n>=-1&&n<=2))throw Error('Invalid four-bar section');
  for(let b=0;b<4;b++){
   const bar=sectionIndex*4+b,chord=section.chords[b],pitches=CHORDS[chord].map(n=>n+root),step=bar*8;
   bars.push({step,section:name,chord,harmony:[pitches[0]-12,...pitches.slice(0,3)],exit:b===3});
   notes.push({step,midi:pitches[0]-12,durationSteps:quiet?5.5:3,layer:0,level:.15});
   for(let slot=0;slot<8;slot++){
    const degree=section.figure[slot];
    // Quiet relative preserves theme pitches/harmony, with fewer, longer attacks.
    if(degree<0||(quiet&&slot%2))continue;
    // Leave a full closing beat at every section boundary.
    if(b===3&&slot>=6)continue;
    notes.push({step:step+slot,midi:pitches[degree]+12,durationSteps:quiet?1.6:.8,layer:2,level:quiet?.11:.14});
   }
   if(!quiet&&sectionIndex===1&&b%2===0)notes.push({step:step+5,midi:pitches[1],durationSteps:1.5,layer:3,level:.08});
  }
 }
 if(notes.some(e=>e.midi<36||e.midi>88||e.step+e.durationSteps>STEPS))throw Error('Arrangement exceeds pitch/time bounds');
 if(!bars[0].harmony.some(n=>bars.at(-1).harmony.includes(n)))throw Error('Loop needs a common-tone seam');
 return {version:VERSION,steps:STEPS,root,quiet,bars,notes,seed,sourceSha256:digest(family)};
}
function window(plan,start=0,count=STEPS*REPEATS-start){
 if(!Number.isInteger(start)||!Number.isInteger(count)||start<0||count<0||start+count>STEPS*REPEATS)throw Error('Invalid replay window');
 const expand=rows=>Array.from({length:REPEATS},(_,cycle)=>rows.map(e=>({...e,step:e.step+cycle*STEPS,cycle}))).flat().filter(e=>e.step>=start&&e.step<start+count);
 return {notes:expand(plan.notes),bars:expand(plan.bars),nextStep:start+count};
}
module.exports={VERSION,STEPS,REPEATS,FAMILY,compile,window};
