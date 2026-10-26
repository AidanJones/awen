// Run with Node 18+: node --test tests/mvp.test.cjs. No dependencies.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const html=fs.readFileSync(require('node:path').join(__dirname,'../index.html'),'utf8');
const script=html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const books=JSON.parse(html.match(/<script id="books" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const ctx=vm.createContext({setInterval:()=>1,clearInterval:()=>{},setTimeout,clearTimeout});
vm.runInContext(script.split('const $=id=>')[0],ctx);
const api=vm.runInContext('({analyze,contextual,mapScore,smooth,neutral,AudioAdapter,dimensions,limiterCurve,OUTPUT_CEILING,MASTER_GAIN,directPassage,planStep,makeComposer,restoreComposer,voiceLead,scoreRandom,sfc32,hash32,normalSeed,STEP_SECONDS,COMPOSER_VERSION,normalGenome,mutateGenome,normalProfile,GENOME_DEFAULT,makeGallery,genomeDistance,genomeKey,describeGenome,cleanName,profileStamp,previewAttenuation,PREVIEW_RMS,SCORE_STYLES,starterGenome,makeStartingGallery,SKETCH_VERSION,validateScoringKnowledge,compileHarmonyRecipe,normalHarmonyRecipe,normalHarmonyChoice,makeHarmonyGallery,harmonicIdentity,canRestoreScoreSession})',ctx);
test('complete curated books retain spine order, stable IDs and nonempty paragraphs',()=>{
 assert.deepEqual(books.map(b=>b.chapters.length),[19,27,13]);
 for(const b of books){const ids=new Set();for(const c of b.chapters){assert(c.title);c.paragraphs.forEach((p,i)=>{assert(p.trim());const id=b.id+':'+c.id+':'+i;assert(!ids.has(id));ids.add(id);});}assert(b.license.includes('CC0'));assert(b.colophon);assert(b.url.startsWith('https://standardebooks.org/ebooks/'));}
 assert.equal(books[1].chapters[0].id,'chapter-1-1');assert.equal(books[1].chapters[9].id,'chapter-1-10');assert.equal(books[2].chapters.at(-1).id,'epilogue');
});
test('analysis is deterministic, bounded, and handles empty input',()=>{
 for(const t of ['',...books.flatMap(b=>b.chapters.flatMap(c=>c.paragraphs))]){const r=api.analyze(t).raw;for(const k of api.dimensions)assert(r[k]>=(k==='valence'?-1:0)&&r[k]<=1);}
 assert.equal(JSON.stringify(api.analyze('Unknown stars!')),JSON.stringify(api.analyze('Unknown stars!')));
 assert(Object.values(api.analyze('').raw).every(v=>v===0));
});
test('phrase evidence, negation, intensifiers and punctuation have limited scope',()=>{
 assert(api.analyze('death').raw.valence<0);assert(api.analyze('happy').raw.valence>0);
 assert(api.analyze('not happy').raw.valence<0);assert(api.analyze('not death').raw.valence>0);
 assert(api.analyze('very happy').raw.valence>api.analyze('happy').raw.valence);
 assert(api.analyze('not here. danger').raw.tension>0);assert(api.analyze('no escape').evidence.some(e=>e.phrase==='no escape'));
 assert(api.analyze('Danger!').raw.arousal>api.analyze('Danger').raw.arousal);
});
test('repeated words have capped contributions',()=>assert.equal(api.analyze('danger '.repeat(100)).raw.tension,api.analyze('danger danger').raw.tension));
test('context uses only the supplied previous paragraph, not future content',()=>{
 const a=api.analyze('stars').raw,b=api.analyze('danger').raw,c=api.contextual(a,b);
 assert.equal(c.wonder,a.wonder*.8);assert.equal(c.tension,b.tension*.2);
});
test('score mapping raises pulse and density for action and clamps targets',()=>{
 const calm=api.analyze('peace tranquil').raw,action=api.analyze('running fired explosion!').raw;
 assert(api.mapScore(action).pulse>api.mapScore(calm).pulse);assert(api.mapScore(action).density>api.mapScore(calm).density);
 for(const b of books)for(const p of b.chapters[0].paragraphs)for(const v of Object.values(api.mapScore(api.analyze(p).raw)))assert(v>=0&&v<=1);
});
test('smoothing converges, is time-based, and cancels superseded targets',()=>{
 let state={...api.neutral};const high=Object.fromEntries(Object.keys(state).map(k=>[k,1]));
 const once=api.smooth(state,high,1);let split={...state};for(let i=0;i<10;i++)split=api.smooth(split,high,.1);
 for(const k in state)assert(Math.abs(once[k]-split[k])<1e-10);
 for(let i=0;i<200;i++)state=api.smooth(state,high,.2);assert(state.pulse>.99);
 const lowered=api.smooth(state,api.neutral,.2);assert(lowered.pulse<state.pulse&&lowered.pulse>api.neutral.pulse);
});
class Param{constructor(){this.value=0;}setValueAtTime(v){this.value=v;}setTargetAtTime(v){this.value=v;}linearRampToValueAtTime(v){this.value=v;}exponentialRampToValueAtTime(v){this.value=v;}cancelScheduledValues(){}cancelAndHoldAtTime(){}}
class Node{constructor(){for(const k of ['gain','frequency','detune','Q','threshold','knee','ratio','attack','release'])this[k]=new Param();this.connections=[];}connect(n){this.connections.push(n);}disconnect(){}start(){}stop(){}setPeriodicWave(){}getFloatTimeDomainData(a){a.fill(0);}}
class FakeContext{constructor(){this.currentTime=0;this.sampleRate=1000;this.state='suspended';this.destination={};this.nodes=0;}createGain(){this.nodes++;return new Node();}createBiquadFilter(){this.nodes++;return new Node();}createOscillator(){this.nodes++;return new Node();}createWaveShaper(){return new Node();}createDynamicsCompressor(){return new Node();}createAnalyser(){return new Node();}createPeriodicWave(){return {};}createConvolver(){return new Node();}createBuffer(channels,length){const data=Array.from({length:channels},()=>new Float32Array(length));return {getChannelData:i=>data[i]};}async resume(){this.state='running';}async close(){this.state='closed';}}
ctx.AudioContext=FakeContext;
test('audio starts on demand, keeps graph/clock on navigation, and stops promptly',async()=>{
 const a=new api.AudioAdapter();assert.equal(a.ctx,null);await a.start();const graph=a.ctx,layers=a.layers;
 for(let i=0;i<20;i++)a.applyTarget(api.mapScore(api.analyze(i%2?'danger running!':'peace').raw));
 assert.equal(a.ctx,graph);assert.equal(a.layers,layers);assert.equal(a.running,true);
 a.ctx.currentTime=1;a.update();assert(a.tick>0);const tick=a.tick;
 a.applyTarget(api.neutral);assert.equal(a.tick,tick);a.setMasterVolume(10);assert(a.master.gain.value<=api.MASTER_GAIN);
 a.stop();assert.equal(a.running,false);assert.equal(a.master.gain.value,0);assert.equal(a.voices.size,0);
 await a.start();assert.equal(a.ctx,graph);await a.dispose();assert.equal(a.ctx,null);
});
test('background recovery skips missed beats instead of accumulating voices',async()=>{
 const a=new api.AudioAdapter();await a.start();const tick=a.tick;a.ctx.currentTime=600;a.update();assert(a.tick-tick<=1);assert(a.voices.size<=10);await a.dispose();
});
test('output curve is finite, symmetric, monotonic, and never exceeds the cap',()=>{
 const curve=api.limiterCurve();assert.equal(curve[4096],0);
 for(let i=0;i<curve.length;i++){assert(Number.isFinite(curve[i]));assert(Math.abs(curve[i])<=api.OUTPUT_CEILING);assert(Math.abs(curve[i]+curve[curve.length-1-i])<1e-7);if(i)assert(curve[i]>=curve[i-1]);}
});
test('every sound route passes through the limiter with no gain afterwards',async()=>{
 const a=new api.AudioAdapter();await a.start();assert.equal(a.bed.connections[0],a.filter);assert.equal(a.filter.connections[0],a.highpass);assert.equal(a.highpass.connections[0],a.compressor);assert.equal(a.compressor.connections[0],a.master);assert.equal(a.master.connections[0],a.limiter);assert.equal(a.limiter.connections[0],a.analyser);assert.equal(a.analyser.connections[0],a.ctx.destination);
 for(const v of [Infinity,NaN,-10]){a.setMasterVolume(v);assert.equal(a.master.gain.value,0);}
 a.applyTarget({pulse:Infinity});assert(Object.values(a.target).every(Number.isFinite));await a.dispose();
});
test('continuous background is adjustable, respects chord mute, and stays off during a check tone',async()=>{
 const a=new api.AudioAdapter();await a.start();assert(a.bed.gain.value>0);const sources=a.bedBanks;
 a.setBackground(0);assert.equal(a.bed.gain.value,0);a.setBackground(1);assert(a.bed.gain.value<=.07);assert.equal(a.bedBanks,sources);
 a.mix[1]=0;a.applyMix(0);assert.equal(a.bed.gain.value,0);a.stop();assert.equal(a.bed.gain.value,0);
 a.setBackground(.5);await a.checkSound();assert.equal(a.bed.gain.value,0);await a.dispose();
});
test('mute cancels an in-flight start or sound check',async()=>{
 for(const method of ['start','checkSound']){const a=new api.AudioAdapter();a.initialize();let resume;a.ctx.resume=()=>new Promise(resolve=>{resume=()=>{a.ctx.state='running';resolve();};});const pending=a[method]();a.stop();resume();await pending;assert.equal(a.running,false);assert.equal(a.checking,false);assert.equal(a.voices.size,0);assert.equal(a.master.gain.value,0);await a.dispose();}
});
test('palette changes reuse the graph and stopping silences the score layers',async()=>{
 const a=new api.AudioAdapter();await a.start();const nodes=a.ctx.nodes;
 for(const name of ['synth','ensemble','synth']){a.setPalette(name);assert.equal(a.ctx.nodes,nodes);assert.equal(a.running,true);}
 a.stop();assert(a.layers.every(g=>g.gain.value===0));await a.checkSound();assert(a.layers.every(g=>g.gain.value===0));await a.dispose();
});
test('Rat opening distinguishes caper, dialogue, action, calm and a precarious crossing',()=>{
 const p=books[0].chapters[0].paragraphs;
 for(const [i,kind] of [[0,'caper'],[1,'dialogue'],[2,'chase'],[7,'chase'],[20,'reflective'],[21,'suspense']]){
  const current=api.analyze(p[i]).raw,context=api.contextual(current,i?api.analyze(p[i-1]).raw:null);
  assert.equal(api.directPassage(p[i],context,'rat:'+i).kind,kind,'Rat paragraph '+(i+1));
 }
});
function trace(seed,steps=1440,events=[]){let state=api.makeComposer(seed,'rat');const notes=[],harmonies=[];for(let i=0;i<steps;i++){const intent=events.filter(e=>e.step<=i).at(-1)||{kind:'caper'};const r=api.planStep(state,intent);notes.push(r.events);if(r.harmony)harmonies.push(r.harmony);state=r.state;}return {state,notes,harmonies};}
test('specified hashing/PRNG vectors and Unicode seed normalisation are stable',()=>{
 assert.equal(api.hash32('hello'),0x4f9f2cab);const random=api.sfc32(1,2,3,4);assert.equal(random(),7/4294967296);assert.equal(random(),34/4294967296);
 assert.equal(api.normalSeed('  e\u0301  '),'é');assert.equal(api.normalSeed(''),'rat-001');assert.equal(api.normalSeed('x'.repeat(100)).length,64);
});
test('seeded score is reproducible, with independent random streams and different interpretations',()=>{
 const log=[{step:0,kind:'caper'},{step:70,kind:'chase'},{step:170,kind:'dialogue'}];
 assert.equal(JSON.stringify(trace('rat-001',256,log)),JSON.stringify(trace('rat-001',256,log)));
 assert.notEqual(JSON.stringify(trace('rat-001',128).notes),JSON.stringify(trace('rat-002',128).notes));
 const s=api.makeComposer();const before=api.scoreRandom(s,'melody',10);for(let i=0;i<500;i++)api.scoreRandom(s,'ornament',i);assert.equal(api.scoreRandom(s,'melody',10),before);
 const theme=trace('rat-001',32).notes.flat().filter(e=>e.layer===2&&e.instrument==='flute').map(e=>e.midi);assert.deepEqual(theme,[62,65,69,67,65,62],'default Rat theme should remain in its authored middle register');
});
test('paragraph IDs and rapid navigation do not restart or rewrite the current phrase',()=>{
 let a=api.makeComposer(),b=api.makeComposer();for(let step=0;step<128;step++){
  const first=api.planStep(a,{id:'fixed',kind:'caper'}),second=api.planStep(b,{id:'paragraph-'+step,kind:'caper'});
  assert.equal(second.state.step,step+1);assert.equal(JSON.stringify(first),JSON.stringify(second));a=first.state;b=second.state;
 }
});
test('scene changes have dwell and stability and only commit at a bar boundary',()=>{
 let s=api.makeComposer();for(let step=0;step<24;step++){s=api.planStep(s,{kind:step<2?'caper':'chase'}).state;assert.equal(s.scene,'caper');}
 s=api.planStep(s,{kind:'chase'}).state;assert.equal(s.scene,'chase');assert.equal(s.sceneSince,24);
 for(let i=0;i<48;i++)s=api.planStep(s,{kind:i%2?'dialogue':'chase'}).state;assert.equal(s.scene,'chase');
});
test('ten minutes across eight seeds obey register, voice-leading and polyphony bounds',()=>{
 for(const seed of ['a','b','c','d','e','f','g','h']){const result=trace(seed),active=[];let max=0,last=null;
  for(const chord of result.harmonies){assert.equal(new Set(chord.map(n=>n%12)).size,4);chord.forEach((n,i)=>{assert(n>=55&&n<=79);if(i)assert(n-chord[i-1]>=3);if(last)assert(Math.abs(n-last[i])<=12);});last=chord;}
  result.notes.forEach((events,step)=>{const time=step*api.STEP_SECONDS;while(active.length&&active[0]<=time)active.shift();for(const e of events){assert(e.midi>=48&&e.midi<=81);assert(e.duration>0&&e.duration<=3);assert(e.level>0&&e.level<=.4);active.push(time+e.duration);}active.sort((a,b)=>a-b);max=Math.max(max,active.length);});assert(max<=16);
 }
});
test('checkpoint round trip continues the same symbolic score and rejects incompatible/corrupt state',()=>{
 const first=trace('resume-seed',77).state,restored=api.restoreComposer(JSON.parse(JSON.stringify(first)),'resume-seed','rat');
 let a=first,b=restored;for(let i=0;i<100;i++){const x=api.planStep(a,{kind:'suspense'}),y=api.planStep(b,{kind:'suspense'});assert.equal(JSON.stringify(x),JSON.stringify(y));a=x.state;b=y.state;}
 for(const bad of [{...first,version:'old'},{...first,step:-1},{...first,voicing:[NaN,60,65,70]},{...first,seed:'different'}])assert.equal(api.restoreComposer(bad,'resume-seed','rat').step,0);
});
test('navigation keeps the playing graph and notes; applying a seed waits for a phrase boundary',async()=>{
 const a=new api.AudioAdapter();await a.start();const graph=a.ctx,voices=[...a.voices],step=a.tick;
 a.setPassage({id:'next',kind:'dialogue'});assert.equal(a.tick,step);assert(voices.every(v=>a.voices.has(v)));a.composeBeat(.5);assert.equal(a.tick,step+1);assert.equal(a.ctx,graph);
 let committed;a.onSeedApplied=()=>{committed=a.snapshot();};a.requestSeed('another');assert.equal(a.composer.seed,'rat-001');while(a.tick%32!==0)a.composeBeat(a.tick*api.STEP_SECONDS);a.composeBeat(20);assert.equal(a.composer.seed,'another');assert.equal(a.tick,1);assert.equal(committed.step,1);assert.equal(committed.seed,'another');
 a.stop();const paused=a.tick;a.update();assert.equal(a.tick,paused);await a.dispose();
});
test('saved-state parser tolerates unavailable/corrupt/wrong-version storage',()=>{
 let stored='';const local={getItem:()=>stored};const c=vm.createContext({localStorage:local,storageKey:'test'});
 vm.runInContext(script.match(/function readSaved\(\)\{[^\n]+/)[0],c);
 for(const v of ['not json','null','[]','{"version":2}']){stored=v;assert.equal(JSON.stringify(vm.runInContext('readSaved()',c)),'{}');}
 const payload={version:1,book:'rat',positions:{rat:'rat:chapter-1:2'},volume:.3};stored=JSON.stringify(payload);assert.equal(JSON.stringify(vm.runInContext('readSaved()',c)),stored);
 local.getItem=()=>{throw Error('denied');};assert.equal(JSON.stringify(vm.runInContext('readSaved()',c)),'{}');
});
test('single-file runtime has no external scripts, styles, fetch or eval',()=>{
 assert(!/<script[^>]+src=|<link[^>]+stylesheet/.test(html));assert(!/\bfetch\(|\beval\(|new Function\(/.test(script));new vm.Script(script);
});

test('personal genomes mutate deterministically within scope and validate imported profiles',()=>{
 const g=api.normalGenome();for(const scope of ['both','foreground','background'])for(let i=0;i<100;i++){const a=api.mutateGenome(g,scope,String(i));assert.equal(JSON.stringify(a),JSON.stringify(api.mutateGenome(g,scope,String(i))));assert(Object.keys(api.GENOME_DEFAULT).every(k=>a[k]>=0&&a[k]<=1));assert.notEqual(JSON.stringify(a),JSON.stringify(g));if(scope==='foreground')for(const k of ['warmth','space','bedPresence','bedMotion'])assert.equal(a[k],g[k]);if(scope==='background')for(const k of ['activity','softness'])assert.equal(a[k],g[k]);}
 assert.throws(()=>api.normalProfile({version:1,genome:{}}));assert.throws(()=>api.normalProfile({version:1,genomeVersion:'awen-genome-1',genome:{...g,warmth:Infinity}}));
 const p=api.normalProfile({version:1,genomeVersion:'awen-genome-1',genome:g,history:[]});assert.equal(p.history.length,0);
});
test('personal changes queue until a phrase and every evolved voice uses the same limiter',async()=>{
 const a=new api.AudioAdapter();await a.start();const original=JSON.stringify(a.genome);a.composer.step=1;a.setGenome({...api.normalGenome(),warmth:1},true);a.composeBeat(.2);assert.equal(JSON.stringify(a.genome),original);a.composer.step=32;a.composeBeat(.3);assert.equal(a.genome.warmth,1);assert.equal(a.pendingGenome,null);await a.dispose();
});

test('six-candidate galleries preserve parents/pins, reproduce and vary only the selected scope',()=>{
 for(const scope of ['both','foreground','background'])for(const strength of ['nearby','wide'])for(let n=0;n<80;n++){
  const base=api.normalGenome(Object.fromEntries(Object.keys(api.GENOME_DEFAULT).map((k,i)=>[k,n%3===0?0:n%3===1?1:(i+1)/7]))),other=api.normalGenome(),pins=[api.mutateGenome(base,scope,'pin'+n)];
  const gallery=api.makeGallery([base,other],scope,'batch'+n,pins,strength);
  assert.equal(gallery.length,6);assert.equal(JSON.stringify(gallery),JSON.stringify(api.makeGallery([base,other],scope,'batch'+n,pins,strength)));
  assert.equal(api.genomeKey(gallery[0].genome),api.genomeKey(base));assert(gallery.some(c=>api.genomeKey(c.genome)===api.genomeKey(pins[0])));
  assert.equal(new Set(gallery.map(c=>api.genomeKey(c.genome))).size,6);
  for(const c of gallery){assert(Object.keys(api.GENOME_DEFAULT).every(k=>Number.isFinite(c.genome[k])&&c.genome[k]>=0&&c.genome[k]<=1));if(c.kind==='variation'||c.kind==='explore'){
   for(const other of gallery.filter(x=>x!==c))assert(api.genomeDistance(c.genome,other.genome)>=.12);
   if(scope==='foreground')for(const k of ['warmth','space','bedPresence','bedMotion'])assert.equal(c.genome[k],base[k]);
   if(scope==='background')for(const k of ['activity','softness'])assert.equal(c.genome[k],base[k]);
  }}assert(api.genomeDistance(base,gallery[5].genome)>=.32);
 }
});
test('gallery profile migration preserves legacy choices and bounded favourites and generation data',()=>{
 const g=api.normalGenome(),legacy={version:1,genomeVersion:'awen-genome-1',genome:g,history:[{choice:'B',before:g,after:g}]};assert.equal(api.normalProfile(legacy).history[0].choice,'B');assert.equal(api.normalProfile(legacy).pins.length,0);
 const profile=api.normalProfile({...legacy,pins:Array(12).fill(g),history:[{choice:'gallery',before:g,after:g,candidates:Array(10).fill(g),parents:[g],selected:2,strength:'wide'}]});assert.equal(profile.pins.length,3);assert.equal(profile.history[0].candidates.length,6);assert.equal(profile.history[0].selected,2);assert.equal(profile.history[0].parents.length,1);assert.equal(profile.history[0].strength,'wide');assert.equal(JSON.stringify(api.normalProfile(JSON.parse(JSON.stringify(profile)))),JSON.stringify(profile));
 assert.equal(api.describeGenome({...g,warmth:1},g),'warmer');assert.equal(api.describeGenome(g,g),'Same musical settings');
});

test('preview balancing attenuates only and cannot bypass the master bound',async()=>{
 assert.equal(api.previewAttenuation(0),1);assert.equal(api.previewAttenuation(.001),1);assert.equal(api.previewAttenuation(NaN),1);assert.equal(api.previewAttenuation(api.PREVIEW_RMS*2),.5);
 const a=new api.AudioAdapter();await a.start();a.setMasterVolume(1);a.setPreviewGain(.25);assert.equal(a.master.gain.value,api.MASTER_GAIN*.25);a.setPreviewGain(20);assert.equal(a.master.gain.value,api.MASTER_GAIN);a.setPreviewGain(-5);assert.equal(a.master.gain.value,0);await a.dispose();
});
test('named favourites and profile fingerprints migrate and detect actual snapshot changes',()=>{
 const g=api.normalGenome(),key=api.genomeKey(g),p=api.normalProfile({version:1,genomeVersion:'awen-genome-1',genome:g,pins:[g],pinNames:{[key]:'  Quiet\u0000 frontier  ',unknown:'discard'},history:[]});assert.equal(p.pinNames[key],'Quiet frontier');assert.equal(Object.keys(p.pinNames).length,1);assert.equal(api.cleanName('x'.repeat(100)).length,40);
 const stamp=api.profileStamp(p);assert.equal(api.profileStamp(JSON.parse(JSON.stringify(p))),stamp);p.pinNames[key]='New name';assert.notEqual(api.profileStamp(p),stamp);p.pinNames[key]='Quiet frontier';assert.equal(api.profileStamp(p),stamp);p.genome.warmth=.9;assert.notEqual(api.profileStamp(p),stamp);
});

test('authored starting points change musical structure and preserve deterministic bounded planning',()=>{
 const logs={},counts={};for(const style of Object.keys(api.SCORE_STYLES)){
  let a=api.makeComposer(),b=api.makeComposer(),notes=[],harmonies=[];
  for(let step=0;step<192;step++){const x=api.planStep(a,{kind:'caper'},style),y=api.planStep(b,{kind:'caper'},style);assert.equal(JSON.stringify(x),JSON.stringify(y));a=x.state;b=y.state;notes.push(...x.events.map(e=>({...e,step})));if(x.harmony)harmonies.push(step);}
  assert(notes.every(e=>e.midi>=48&&e.midi<=81&&e.level>0&&e.level<=.4&&e.duration>0&&e.duration<=3));logs[style]=JSON.stringify(notes);counts[style]=notes.filter(e=>e.layer===2).length;assert.equal(harmonies[1],api.SCORE_STYLES[style].bars*8);
 }
 assert.equal(new Set(Object.values(logs)).size,5);assert(counts.frontier<counts.classic);assert(counts.dialogue<counts.classic);assert(counts.caper>counts.frontier);
 let s=api.makeComposer();for(let i=0;i<64;i++){const r=api.planStep(s,{kind:'dialogue'},'dialogue');if(i>=32)assert(r.events.every(e=>e.layer!==2),'dialogue recipe must leave a complete answer phrase open');s=r.state;}
});
test('starting-point gallery includes recipes and evolution retains the selected parent identity',()=>{
 const current=api.normalGenome(),gallery=api.makeStartingGallery(current,'small-proof');assert.equal(gallery.length,6);assert.equal(new Set(gallery.map(c=>api.genomeKey(c.genome))).size,6);for(const id of ['frontier','caper','unseen','dialogue'])assert(gallery.some(c=>c.genome.scoreStyle===id));
 const frontier=api.starterGenome('frontier');for(const c of api.makeGallery([frontier,api.starterGenome('caper')],'both','evolve'))assert.equal(c.genome.scoreStyle,'frontier');assert.equal(api.normalGenome({scoreStyle:'invalid'}).scoreStyle,'classic');
 const legacy=Object.fromEntries(Object.keys(api.GENOME_DEFAULT).map(k=>[k,current[k]])),oldKey=JSON.stringify(legacy),p=api.normalProfile({version:1,genomeVersion:'awen-genome-1',genome:legacy,pins:[legacy],pinNames:{[oldKey]:'Old favourite'},history:[]});assert.equal(p.genome.scoreStyle,'classic');assert.equal(p.pinNames[api.genomeKey(p.pins[0])],'Old favourite');
 const styled=api.normalProfile({...p,genome:frontier,pins:[frontier],pinNames:{[api.genomeKey(frontier)]:'Frontier'}});assert.equal(api.normalProfile(JSON.parse(JSON.stringify(styled))).genome.scoreStyle,'frontier');
});

const scoringKnowledge=JSON.parse(fs.readFileSync(require('node:path').join(__dirname,'../research/scoring-knowledge.json'),'utf8'));
test('versioned scoring library is embedded exactly, source-linked and structurally valid',()=>{
 assert.equal(JSON.stringify(JSON.parse(html.match(/<script id="scoring-knowledge" type="application\/json">([\s\S]*?)<\/script>/)[1])),JSON.stringify(scoringKnowledge));assert.equal(api.validateScoringKnowledge(scoringKnowledge),scoringKnowledge);
 const broken=JSON.parse(JSON.stringify(scoringKnowledge));broken.harmonicFamilies[0].sourceIds=['invented'];assert.throws(()=>api.validateScoringKnowledge(broken));broken.harmonicFamilies[0].sourceIds=['giacchino-2020'];broken.harmonicFamilies[0].chords[0].intervals=[0,0,7,9];assert.throws(()=>api.validateScoringKnowledge(broken));
});
test('genre and scene alternatives compile in every tonic to the four-voice engine',()=>{
 for(const genre of Object.keys(scoringKnowledge.genres))for(const scene of Object.keys(scoringKnowledge.sceneFunctions))for(let variant=0;variant<2;variant++)for(let tonicPc=0;tonicPc<12;tonicPc++){
  const recipe=api.compileHarmonyRecipe(scoringKnowledge,{genre,scene,variant,tonicPc});assert.equal(recipe.libraryVersion,scoringKnowledge.version);assert.equal(recipe.evidenceStatus,'awen-proposal');assert.equal(recipe.chords.length,4);assert(recipe.chords.every(c=>new Set(c).size===4&&c.every(n=>n>=0&&n<12)));assert(recipe.sourceIds.length);assert(recipe.advisory.function);
 }
 const western=api.compileHarmonyRecipe(scoringKnowledge,{genre:'frontier',scene:'suspense'}),science=api.compileHarmonyRecipe(scoringKnowledge,{genre:'unseen',scene:'suspense'});assert.notEqual(western.familyId,science.familyId);assert.equal(western.sceneFunction,science.sceneFunction);assert.equal(western.genre,'western');
 assert.throws(()=>api.compileHarmonyRecipe(scoringKnowledge,{genre:'unknown'}));assert.throws(()=>api.compileHarmonyRecipe(scoringKnowledge,{tonicPc:12}));assert.throws(()=>api.normalHarmonyRecipe({...western,bars:.01}));
});
test('compiled chord cycles produce deterministic chord-tone melodies with bounded notes',()=>{
 for(const genre of Object.keys(scoringKnowledge.genres))for(const scene of ['suspense','chase','discovery']){
  const recipe=api.compileHarmonyRecipe(scoringKnowledge,{genre,scene}),intent={kind:scene},first=[];let a=api.makeComposer(),b=api.makeComposer();
  for(let i=0;i<160;i++){const x=api.planStep(a,intent,'classic',recipe),y=api.planStep(b,intent,'classic',recipe);assert.equal(JSON.stringify(x),JSON.stringify(y));const chord=recipe.chords[recipe.form[Math.floor(i/8/recipe.bars)%recipe.form.length]];for(const e of x.events){assert(e.midi>=48&&e.midi<=81&&e.duration>0&&e.duration<=3);if(e.layer===2)assert(chord.includes(e.midi%12));}first.push(x.events);a=x.state;b=y.state;}
  assert(first.flat().length);
 }
});
test('experimental harmony queues at a phrase, clones input and restores the authored recipe',async()=>{
 const a=new api.AudioAdapter(),recipe=api.compileHarmonyRecipe(scoringKnowledge,{genre:'fantasy',scene:'discovery'});await a.start();a.composer.step=1;const graph=a.ctx;a.queueHarmonyRecipe(recipe);recipe.chords[0][0]=99;a.composeBeat(.5);assert.equal(a.harmonyRecipe,null);assert.equal(a.tick,2);a.composer.step=32;a.composeBeat(1);assert.equal(a.harmonyRecipe.genre,'fantasy');assert(a.harmonyRecipe.chords.every(c=>c.every(n=>n<12)));assert.equal(a.tick,33);assert.equal(a.ctx,graph);a.queueHarmonyRecipe(null);a.composer.step=64;a.composeBeat(2);assert.equal(a.harmonyRecipe,null);assert.equal(a.tick,65);await a.dispose();
});

test('saved harmony is a bounded, versioned snapshot that survives profile and pin round trips',()=>{
 const h=api.compileHarmonyRecipe(scoringKnowledge,{genre:'noir',scene:'anticipation',familyId:'major-third-colour',tonicPc:5});assert.equal(h.selectionMode,'manual');
 const g=api.normalGenome({...api.normalGenome(),harmony:h});assert.equal(g.harmony.tonicPc,5);assert.equal(g.harmony.libraryVersion,scoringKnowledge.version);assert.equal(g.harmony.familyId,'major-third-colour');
 const p=api.normalProfile({version:1,genomeVersion:'awen-genome-1',genome:g,pins:[g],pinNames:{[api.genomeKey(g)]:'Mystery'},history:[]}),restored=api.normalProfile(JSON.parse(JSON.stringify(p)));assert.equal(JSON.stringify(restored),JSON.stringify(p));assert.equal(restored.pinNames[api.genomeKey(restored.genome)],'Mystery');
 const archived=api.normalGenome({...g,harmony:{...g.harmony,libraryVersion:'9.0.0'}});assert.equal(archived.harmony.libraryVersion,'9.0.0');assert.equal(JSON.stringify(archived.harmony.chords),JSON.stringify(g.harmony.chords));
 for(const bad of [false,0,{...h,engineVersion:2},{...h,chords:[[99,2,4,7],...h.chords.slice(1)]},{...h,libraryVersion:'broken'},{...h,chords:[[0,1,2,3],...h.chords.slice(1)]}])assert.throws(()=>api.normalGenome({...g,harmony:bad}));
 for(const c of api.makeGallery([g,api.starterGenome('frontier')],'both','hold-direction'))assert.equal(api.genomeKey({...c.genome,...api.GENOME_DEFAULT}),api.genomeKey({...g,...api.GENOME_DEFAULT}));
});
test('harmony gallery supplies six different musical choices and an authored-harmony return',()=>{
 const base=api.normalGenome(),batch=api.makeHarmonyGallery(scoringKnowledge,base,{genre:'western',scene:'anticipation',tonicPc:2,seed:'proof'});assert.equal(batch.length,6);assert.equal(new Set(batch.map(c=>api.genomeKey(c.genome))).size,6);assert(batch.some(c=>!c.genome.harmony));assert(batch.some(c=>c.genome.harmony?.familyId==='static-suspension'));
 const manual=api.makeHarmonyGallery(scoringKnowledge,batch[1].genome,{genre:'fantasy',scene:'revelation',familyId:'minor-sixth-intrigue',tonicPc:7});assert(manual.some(c=>c.genome.harmony?.selectionMode==='manual'&&c.genome.harmony.familyId==='minor-sixth-intrigue'&&c.genome.harmony.tonicPc===7));assert(manual.some(c=>c.kind==='authored'&&!c.genome.harmony));
});
test('harmonic checkpoint identity prevents incompatible voicing restoration and supports legacy scores',()=>{
 const base=api.normalGenome(),g=api.normalGenome({...base,harmony:api.compileHarmonyRecipe(scoringKnowledge)}),session={harmonyIdentity:api.harmonicIdentity(g)};assert(api.canRestoreScoreSession(session,g));assert(!api.canRestoreScoreSession(session,base));assert(!api.canRestoreScoreSession({},g));assert(api.canRestoreScoreSession({},base));assert(!api.canRestoreScoreSession(undefined,base));
});
test('a saved harmonic preference becomes the live recipe at the next phrase without resetting time',async()=>{
 const a=new api.AudioAdapter(),g=api.normalGenome({...api.normalGenome(),harmony:api.compileHarmonyRecipe(scoringKnowledge,{genre:'fantasy',scene:'discovery'})});await a.start();a.composer.step=1;a.setGenome(g,true);a.composeBeat(.5);assert.equal(a.genome.harmony,undefined);a.composer.step=32;a.composeBeat(1);assert.equal(a.tick,33);assert.equal(a.genome.harmony.familyId,g.harmony.familyId);assert.equal(a.harmonyRecipe,null);const expected=api.planStep({...a.snapshot(),step:32,slot:-1},{kind:a.intent.kind},g.scoreStyle,g.harmony).state.voicing;assert.equal(JSON.stringify(a.composer.voicing),JSON.stringify(expected));await a.dispose();
});

test('the chosen tonal centre transposes the motif before chord-tone anchoring',()=>{
 const pitches=[];for(const tonicPc of [2,5]){const h=api.compileHarmonyRecipe(scoringKnowledge,{genre:'neutral',scene:'conversation',tonicPc});let s=api.makeComposer();for(let step=0;step<3;step++){const r=api.planStep(s,{kind:'caper'},'classic',h);for(const e of r.events)if(e.layer===2)pitches.push(e.midi);s=r.state;}}assert.deepEqual(pitches,[62,65]);
});
