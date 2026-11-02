// Development-only symbolic export; no Web Audio or waveform access.
'use strict';
const {loadRuntime}=require('./score-lab.cjs');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const VERSION='awen-symbolic-score-1',plain=x=>JSON.parse(JSON.stringify(x));
function exportScore(row,api=loadRuntime().api){
 if(!Number.isInteger(row.steps)||row.steps<1||row.steps>4096)throw Error('Invalid score length');
 const g=api.normalGenome(row.genome);
 if(!g.scoreDSL)throw Error('Explicit DSL required; other planners have no declared voice identities yet');
 const seed=row.seed||'symbolic-001',book=row.book||'rat';let state=api.makeComposer(seed,book);
 if(row.snapshot){state=api.restoreComposer(row.snapshot,seed,book);if(JSON.stringify(plain(state))!==JSON.stringify({...plain(state),...row.snapshot}))throw Error('Invalid composer snapshot');}
 const timeline=row.timeline||[{step:0,intent:{kind:'reflective',chapterId:'fixed-scene',chapterIndex:0}}];
 if(g.classical?.mode==='chapters'&&!row.timeline)throw Error('Chapter policy requires an explicit intent timeline');
 if(!Array.isArray(timeline)||!timeline.length||timeline.length>128)throw Error('Bounded intent timeline required');
 let last=-1;
 for(const item of timeline){const i=item.intent;if(!Number.isInteger(item.step)||item.step<=last||item.step>=row.steps||!i||typeof i.chapterId!=='string'||i.chapterId.length>180||!Number.isInteger(i.chapterIndex)||i.chapterIndex<0||i.chapterIndex>=10000)throw Error('Invalid chapter timeline');last=item.step;}
 if(timeline[0].step!==0)throw Error('Timeline must establish initial context');
 const start=state.step,events=[],contexts=[],chords=[];let cursor=0;
 const voices=[{id:'dsl.bass',meaning:'Authored bass and cadential bass part'},
  {id:'dsl.figure',meaning:'Authored upper figure, including neighbour notes'},
  {id:'dsl.chord',meaning:'Authored supplementary chord part'}];
 for(let step=0;step<row.steps;step++){
  if(timeline[cursor+1]?.step===step)cursor++;
  const intent=timeline[cursor].intent,absoluteStep=state.step;
  const result=api.planStep(state,intent,g.scoreStyle,g.harmony,g.scoreDSL,g.classical),frame=result.state.classical;
  const program=api.compileScoreDSL(frame?api.SCORE_DSL_PRESETS[frame.preset]:g.scoreDSL.source);
  const bar=Math.floor((absoluteStep-(frame?.epoch||0))/8),h=g.harmony;
  const pcs=plain(h?h.chords[h.form[Math.floor(absoluteStep/8/h.bars)%h.form.length]]:
    program.bars[Math.floor(bar/program.hold)%program.bars.length].pcs.map(n=>(n+(frame?.transpose||0))%12));
  chords.push(pcs);
  contexts.push({step,absoluteStep,requestedChapter:intent.chapterId,requestedChapterIndex:intent.chapterIndex,
    activeChapter:frame?.chapter||null,preset:frame?.preset||null,epoch:frame?.epoch??0,
    transpose:frame?.transpose||0,style:program.texture==='line'?'figured':'lyric',
    chord:pcs,bedHarmony:plain(result.state.voicing)});
  for(const e of result.events){const voice=e.role==='bass'||e.role==='cadence'?'dsl.bass':
    e.role==='upper'||e.role==='neighbour'?'dsl.figure':e.role==='chord'?'dsl.chord':null;
   if(!voice)throw Error('Planner emitted an undeclared part');
   events.push({...plain(e),step,absoluteStep,voice});}
  state=result.state;
 }
 const sources=Object.fromEntries(['index.html','tools/score-lab.cjs','tools/symbolic-score.cjs'].map(p=>[p,crypto.createHash('sha256').update(fs.readFileSync(path.resolve(__dirname,'..',p))).digest('hex')]));
 return {version:VERSION,id:row.id,sources,request:plain(row),startStep:start,steps:row.steps,voices,events,contexts,chords,
  style:contexts[0].style,snapshot:plain(state),coverage:{plannedNotes:true,scheduledNotes:false,
   voiceIdentity:'explicit-dsl-part',physicalOscillatorIdentity:false,bed:'harmonic-target-only',
   acousticEnvelope:false,waveformRead:false},
  limitations:['Planned notes precede runtime mix/activity filtering.',
   'Bed harmony is a target; continuous oscillators, crossfades, timbre and level are not represented.',
   'Part identity is not a promise of strict contrapuntal independence.']};
}
module.exports={exportScore,VERSION};
