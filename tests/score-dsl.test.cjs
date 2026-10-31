const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync(require('node:path').resolve(__dirname,'../index.html'),'utf8'),context=vm.createContext({setInterval,clearInterval,setTimeout,clearTimeout});vm.runInContext(html.match(/<script>\s*([\s\S]*?)<\/script>/)[1].split('const $=id=>')[0],context);
const api=vm.runInContext('({compileScoreDSL,normalScoreDSL,SCORE_DSL_PRESETS,dslGenome,normalGenome,normalProfile,makeDSLGallery,mutateGenome,makeGallery,planStep,makeComposer,restoreComposer,STEP_SECONDS,compileHarmonyRecipe,harmonicIdentity,canRestoreScoreSession})',context);
const library=JSON.parse(fs.readFileSync(require('node:path').resolve(__dirname,'../research/scoring-knowledge.json'),'utf8'));
test('DSL rejects code, unknown/repeated fields, excessive work and unresolved ornaments',()=>{
 const good=api.SCORE_DSL_PRESETS.flowing;
 for(const source of [good+'\neval alert(1)',good+'\ngate 0.5',good.replace('score 1','score 2'),good.replace('n2 2','n2 1'),good.replace('gate 0.95','gate Infinity'),good.replace('cycle I IV V7 I vi ii V7 I','cycle I IV V7 ii'),good.replace('key G2 major','key G8 major'),'x'.repeat(6001)])assert.throws(()=>api.compileScoreDSL(source));
 assert.throws(()=>api.normalScoreDSL({version:2,source:good}));const p=api.compileScoreDSL(good);assert(Object.isFrozen(p)&&Object.isFrozen(p.bars)&&Object.isFrozen(p.bars[0].upper));
 assert.equal(api.compileScoreDSL('# a comment\n'+good).id,p.id);assert.equal(api.compileScoreDSL(good.replace('Flowing figured cello','A renamed figure')).id,p.id);
});
function trace(genome,seed='dsl-test',count=256,harmony=null){let state=api.makeComposer(seed),events=[],snapshots=[];for(let step=0;step<count;step++){const r=api.planStep(state,{id:'p'+step,kind:step<64?'reflective':step<128?'chase':'dialogue'},genome.scoreStyle,harmony,genome.scoreDSL);events.push(...r.events.map(e=>({...e,step})));snapshots.push(r.state);state=r.state;}return {events,state,snapshots};}
test('figures imply bass/upper voices, resolve neighbours, mark cadences and stay deterministic/bounded',()=>{
 for(const id of Object.keys(api.SCORE_DSL_PRESETS)){
  const g=api.dslGenome(id),a=trace(g),b=trace(g);assert.equal(JSON.stringify(a),JSON.stringify(b));assert.equal(a.state.step,256);assert(a.events.every(e=>e.midi>=36&&e.midi<=76&&e.duration>0&&e.duration<=(['flowing','sequence','dialogue'].includes(id)?1.4:2.2)&&e.level<=.3));assert(a.events.some(e=>e.layer===0)&&a.events.some(e=>e.layer===2));assert(a.events.some(e=>e.role==='cadence'));
  for(const e of a.events.filter(e=>e.role==='neighbour')){const next=a.events.find(n=>n.step===e.step+1);assert(next&&next.role==='upper'&&next.midi>e.midi&&next.midi-e.midi<=3);}
  const snapshot=a.snapshots[79],restored=api.restoreComposer(snapshot,'dsl-test','rat');assert.equal(restored.step,80);assert.equal(JSON.stringify(api.planStep(snapshot,{kind:'chase'},g.scoreStyle,null,g.scoreDSL)),JSON.stringify(api.planStep(restored,{kind:'chase'},g.scoreStyle,null,g.scoreDSL)));
 }
 const dialogue=trace(api.dslGenome('dialogue'));assert(!dialogue.events.some(e=>Math.floor(e.step/8)%4===3&&e.step%8>=5));
});
test('saved DSL survives profiles, pins, undo history and scoped/multi-parent evolution',()=>{
 const g=api.dslGenome(),other=api.dslGenome('sequence');const profile=api.normalProfile({version:1,genomeVersion:'awen-genome-1',genome:g,pins:[other],history:[{choice:'dsl',before:api.normalGenome(),after:g}]});assert.equal(profile.genome.scoreDSL.source,g.scoreDSL.source);assert.equal(profile.pins[0].scoreDSL.source,other.scoreDSL.source);assert.equal(profile.history[0].after.scoreDSL.source,g.scoreDSL.source);
 for(const child of api.makeGallery([g,other],'both','dsl-evolve'))assert.equal(child.genome.scoreDSL.source,g.scoreDSL.source);
 for(const scope of ['foreground','background','both'])assert.equal(api.mutateGenome(g,scope,'x').scoreDSL.source,g.scoreDSL.source);
 assert.equal(new Set(api.makeDSLGallery(g).map(c=>JSON.stringify(c.genome))).size,6);
 assert(!api.canRestoreScoreSession({state:api.makeComposer()},g));
 assert.notEqual(api.harmonicIdentity(g),api.harmonicIdentity(other));
});
test('existing harmonic directions override the cycle without dropping figuration or changing phase',()=>{
 const g=api.dslGenome(),h=api.compileHarmonyRecipe(library,{genre:'western',scene:'pursuit'}),result=trace(g,'h',96,h);assert.equal(result.state.step,96);assert(result.events.every(e=>e.midi>=36&&e.midi<=76));assert(result.events.every(e=>e.dslId));
 for(const event of result.events.filter(e=>e.role!=='neighbour')){const bar=Math.floor(event.step/8),chord=h.chords[h.form[Math.floor(bar/h.bars)%h.form.length]];assert(chord.includes(event.midi%12));}
});
