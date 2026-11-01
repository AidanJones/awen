// Export harmonic context from the production DSL, without rendering or audio analysis.
'use strict';
const fs=require('node:fs'),crypto=require('node:crypto'),{loadRuntime}=require('./score-lab.cjs');
const [input,output]=process.argv.slice(2),api=loadRuntime().api,rows=JSON.parse(fs.readFileSync(input,'utf8'));
if(!Array.isArray(rows)||rows.length>100)throw Error('Bounded score batch required');
const result=rows.map(row=>{if(!Number.isInteger(row.steps)||row.steps<1||row.steps>4096)throw Error('Invalid score length');const g=api.normalGenome(row.genome);if(!g.scoreDSL||g.classical?.mode==='chapters')throw Error('This exporter needs a fixed DSL harmonic context; dynamic chapter state is unsupported');const p=api.compileScoreDSL(g.scoreDSL.source),h=g.harmony;return {id:row.id,style:p.texture==='line'?'figured':'lyric',chords:Array.from({length:row.steps},(_,step)=>h?h.chords[h.form[Math.floor(step/8/h.bars)%h.form.length]]:p.bars[Math.floor(step/8/p.hold)%p.bars.length].pcs)};});
const temp=output+'.'+crypto.randomUUID()+'.tmp';fs.writeFileSync(temp,JSON.stringify(result)+'\n',{flag:'wx'});fs.renameSync(temp,output);
