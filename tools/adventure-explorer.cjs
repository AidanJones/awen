'use strict';
const AwenAdventure=(()=>{
 function normal(value){if(value?.version!==1||!['original','contrast-middle','answer-first'].includes(value.form)||!['full','spacious','lyric'].includes(value.texture))throw Error('Invalid adventure score');return {version:1,form:value.form,texture:value.texture};}
 function plan(seed,descriptor,quiet=false){
  const d=normal(descriptor),base=seed.plans[quiet?'reflection':'caper'],order={original:[0,1,2,3],'contrast-middle':[0,2,1,3],'answer-first':[1,0,2,3]}[d.form];
  const notes=[],bars=[];
  for(const [dest,source] of order.entries()){
   for(const row of base.bars.filter(e=>Math.floor(e[0]/32)===source))bars.push({step:dest*32+row[0]%32,harmony:row[1]});
   for(const row of base.notes.filter(e=>Math.floor(e[0]/32)===source)){
    const [at,midi,length,layer,level]=row,step=dest*32+at%32;
    if(d.texture==='spacious'&&(layer===3||layer===2&&at%2))continue;
    if(d.texture==='lyric'&&(layer===3||layer===2&&![0,3].includes(at%8)))continue;
    notes.push({step,midi,durationSteps:Math.min(length*(d.texture==='full'?1:1.6),128-step),layer,level});
   }
  }
  return {steps:128,notes,bars};
 }
 return {normal,plan};
})();
if(typeof module!=='undefined'&&module.exports)module.exports=AwenAdventure;
