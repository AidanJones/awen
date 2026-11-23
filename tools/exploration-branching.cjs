'use strict';
// Pure browser-compatible branching. This is preference exploration, not a reward model.
const AwenBranching=(()=>{
 const VERSION='awen-branching-1',TRAITS=['activity','softness','warmth','space','bedPresence','bedMotion'];
 const hash=s=>{let n=2166136261;for(const c of s)n=Math.imul(n^c.codePointAt(0),16777619);return n>>>0;};
 const recipe=(c,api)=>JSON.stringify([c.genome.scoreStyle,c.genome.scoreDSL?api.compileScoreDSL(c.genome.scoreDSL.source).id:null,c.genome.classical||null,c.adventure||null]);
 const harmony=c=>{const h=c.genome.harmony;return JSON.stringify(h?[h.tonicPc,h.bars,h.chords,h.form]:null);};
 function key(c,api){return JSON.stringify([c.palette,recipe(c,api),harmony(c),TRAITS.map(k=>c.genome[k])]);}
 function changes(a,b,api){return [...(recipe(a,api)!==recipe(b,api)?['composition']:[]),...(harmony(a)!==harmony(b)?['harmony']:[]),...(a.palette!==b.palette?['instruments']:[]),...TRAITS.filter(k=>a.genome[k]!==b.genome[k])];}
 function structural(a,b,api){return changes(a,b,api).filter(k=>['composition','harmony','instruments'].includes(k));}
 function build(api,{parents,pool,seed,breadth=1,generation=1,action='explore'}){
  if(!Array.isArray(parents)||parents.length<1||parents.length>3||new Set(parents.map(p=>p.id)).size!==parents.length||!Array.isArray(pool)||!pool.length||typeof seed!=='string'||seed.length>200000||!Number.isInteger(breadth)||breadth<0||breadth>3||!Number.isInteger(generation)||generation<1||!['explore','widen','refine'].includes(action))throw Error('Invalid branch request');
  const cards=parents.map(p=>JSON.parse(JSON.stringify(p))),seen=new Set(cards.map(c=>key(c,api)));
  const schedules=[Array(8).fill('near'),['near','near','medium','medium','medium','broad','broad','broad'],['near','medium','medium','broad','broad','broad','broad','broad'],['medium','medium','broad','broad','broad','broad','broad','broad']];
  const offspring=[];let retries=0;
  while(cards.length<9){
   const i=offspring.length,parent=parents[i%parents.length],tier=schedules[breadth][i];let child=null,donorId=null;
   for(let attempt=0;attempt<500&&!child;attempt++){
    const token=seed+'|'+breadth+'|'+i+'|'+attempt,eligible=pool.filter(d=>!!d.adventure===!!parent.adventure),donor=eligible[hash(token)%eligible.length];let c;
    if(!donor)throw Error('No compatible score-family donors');
    if(tier==='near')c={palette:parent.palette,genome:api.mutateGenome(parent.genome,'both',token),...(parent.adventure?{adventure:{...parent.adventure}}:{})};
    else if(tier==='medium'){
     const axis=['composition','harmony','instruments'][i%3];c={palette:parent.palette,genome:{...parent.genome},...(parent.adventure?{adventure:{...parent.adventure}}:{})};
     if(axis==='instruments')c.palette=donor.palette;
     if(axis==='harmony'){delete c.genome.harmony;if(donor.genome.harmony)c.genome.harmony=donor.genome.harmony;}
     if(axis==='composition'){
      if(donor.adventure)c.adventure={...donor.adventure};else delete c.adventure;
      delete c.genome.scoreDSL;delete c.genome.classical;c.genome.scoreStyle=donor.genome.scoreStyle;
      if(donor.genome.scoreDSL)c.genome.scoreDSL=donor.genome.scoreDSL;
      if(donor.genome.classical)c.genome.classical=donor.genome.classical;
     }
     c.genome=api.normalGenome(c.genome);
     if(structural(c,parent,api).length!==1)continue;
    }else{
     c={palette:donor.palette,genome:api.normalGenome({...donor.genome,warmth:parent.genome.warmth,softness:parent.genome.softness}),...(donor.adventure?{adventure:{...donor.adventure}}:{})};
     if(structural(c,parent,api).length<2)continue;
    }
    if(seen.has(key(c,api))){retries++;continue;}
    donorId=tier==='near'?null:donor.id;child=c;
   }
   if(!child)throw Error('Could not create a distinct bounded branch; retained the current round.');
   const changed=changes(child,parent,api),id='branch-'+generation+'-'+i+'-'+hash(seed+'|'+breadth).toString(36);
   child={id,name:(tier==='near'?parent.name:pool.find(p=>p.id===donorId).name).slice(0,65)+' · '+tier+' '+(i+1),description:(tier==='near'?'Close relative; composition, harmony and instruments retained.':tier==='medium'?'One authored component changed: '+changed.filter(k=>['composition','harmony','instruments'].includes(k)).join(', ')+'.':'Broader alternative; changed '+structural(child,parent,api).join(', ')+'.')+' Parent: '+parent.name.slice(0,70)+'.',...child,lineage:{version:VERSION,parentId:parent.id,tier,donorId,changes:changed}};
   seen.add(key(child,api));cards.push(child);offspring.push({id,parentId:parent.id,tier,donorId,changes:changed});
  }
  return {cards,branch:{version:VERSION,action,breadth,seedHash:hash(seed).toString(16),parents:parents.map(p=>p.id),offspring,duplicateRetries:retries}};
 }
 return {VERSION,key,changes,structural,build};
})();
if(typeof module!=='undefined'&&module.exports)module.exports=AwenBranching;
