const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync(require('node:path').resolve(__dirname,'../index.html'),'utf8'),ctx=vm.createContext({setInterval,clearInterval,setTimeout,clearTimeout});
vm.runInContext(html.match(/<script>\s*([\s\S]*?)<\/script>/)[1].split('const $=id=>')[0],ctx);
const a=vm.runInContext('({CLASSICAL_LIBRARY,classicalCue,classicalGenome,compileScoreDSL,SCORE_DSL_PRESETS,planStep,makeComposer,restoreComposer,normalGenome,normalProfile,mutateGenome,makeClassicalGallery,genomeKey,directPassage,neutral})',ctx);
const plain=x=>JSON.parse(JSON.stringify(x));
function intent(text,chapterIndex=0){return {...a.directPassage(text,{},'rat:chapter-'+(chapterIndex+1)+':1'),chapterIndex,chapterId:'chapter-'+(chapterIndex+1)};}
function step(s,g,i){return a.planStep(s,i,g.scoreStyle,g.harmony,g.scoreDSL,g.classical);}

test('nine source-linked families have distinct structures; legacy DSL defaults still parse',()=>{
 assert.deepEqual(plain(a.CLASSICAL_LIBRARY),JSON.parse(fs.readFileSync('research/classical-knowledge.json','utf8')));
 const signatures=[];for(const p of a.CLASSICAL_LIBRARY.presets){const g=a.classicalGenome(p.id,'fixed'),program=a.compileScoreDSL(g.scoreDSL.source);let s=a.makeComposer(),events=[];for(let n=0;n<256;n++){const r=step(s,g,intent('Quiet landscape.'));events.push(...r.events.map(e=>({...e,step:n})));s=r.state;}assert(events.every(e=>e.midi>=36&&e.midi<=76&&e.duration>0&&e.duration<=2.2&&e.level<=.3));signatures.push(JSON.stringify(events.map(e=>[e.step,e.midi,e.duration,e.layer])));assert(program.hold<=4);}
 assert.equal(new Set(signatures).size,9);const legacy=a.SCORE_DSL_PRESETS.flowing.replace(/\n(texture|hold|shape) .+/g,'');assert.equal(a.compileScoreDSL(legacy).id,a.compileScoreDSL(a.SCORE_DSL_PRESETS.flowing).id);
 for(const suffix of ['texture execute','hold 99','shape random'])assert.throws(()=>a.compileScoreDSL(legacy+'\n'+suffix));
});

test('text mappings expose evidence, respect simple negation, and distinguish cold from shelter',()=>{
 assert.equal(a.classicalCue('Thunder, lightning and an explosion!').id,'storm');
 assert.equal(a.classicalCue('Frozen snow and shivering.').id,'cold');
 assert.equal(a.classicalCue('Warmth by the fireside.').id,'shelter');
 assert.equal(a.classicalCue('No thunder. Without grief.').id,'neutral');
 assert.equal(a.classicalCue('Snow. Thunder and lightning.').id,'storm');
 assert(a.classicalCue('The chase began.').matches.includes('chase'));
});

test('a closing bass does not replace a required upper-neighbour resolution',()=>{
 const source=a.SCORE_DSL_PRESETS.flowing.replace('b 1 2 n2 2 1 2 1','b 1 2 1 2 1 n2 2').replace('neighbor 0.4','neighbor 1'),g=a.normalGenome({scoreStyle:'figured',scoreDSL:{version:1,source}});let s=a.makeComposer(),events=[];for(let n=0;n<64;n++){const r=step(s,g,intent('Quiet.'));events.push(...r.events.map(e=>({...e,step:n})));s=r.state;}for(const e of events.filter(e=>e.role==='neighbour'))assert(events.some(n=>n.step===e.step+1&&n.role==='upper'&&n.midi>e.midi&&n.midi-e.midi<=3));assert(events.some(e=>e.role==='cadence'&&e.step===31));
});

test('chapter development waits for a phrase; paragraph cues cannot switch recipe or tonal region',()=>{
 const g=a.classicalGenome('flowing'),start=intent('The birds filled the meadow.',0),next=intent('Thunder and lightning.',1);let s=a.makeComposer();
 const activatedLater=step(a.makeComposer(),g,intent('Thunder and lightning.',2)).state;assert.equal(activatedLater.classical.preset,'flowing');assert.equal(activatedLater.classical.transpose,7);
 for(let n=0;n<11;n++)s=step(s,g,start).state;assert.equal(s.classical.preset,'flowing');
 for(let n=11;n<32;n++){s=step(s,g,next).state;assert.equal(s.classical.preset,'flowing');assert.equal(s.classical.transpose,0);}
 s=step(s,g,next).state;assert.equal(s.step,33);assert.equal(s.classical.preset,'storm');assert.equal(s.classical.epoch,32);assert.equal(s.classical.transpose,5);
 const epoch=s.classical.epoch;for(let n=0;n<100;n++){const old=s;s=step(s,g,intent('Warmth by the fireside.',1)).state;assert.equal(s.classical.preset,'storm');assert.equal(s.classical.epoch,epoch);assert(Math.abs(s.classical.gate-old.classical.gate)<.05);}
 const snap=plain(s),restored=a.restoreComposer(snap,s.seed,s.bookId);assert.equal(JSON.stringify(step(s,g,next)),JSON.stringify(step(restored,g,next)));assert.equal(snap.step,s.step);
 for(const bad of [{...snap,classical:{...snap.classical,epoch:snap.step+1}},{...snap,classical:{...snap.classical,preset:'unknown'}},{...snap,classical:{...snap.classical,policy:{version:99}}}])assert.equal(a.restoreComposer(bad,s.seed,s.bookId).step,0);
});

test('held and expressive modes keep structure; profiles, names, history and mutations preserve policy',()=>{
 for(const mode of ['fixed','expression']){const g=a.classicalGenome('hearth',mode);let s=a.makeComposer();for(let n=0;n<100;n++)s=step(s,g,intent('Thunder and lightning.',Math.floor(n/20))).state;assert.equal(s.classical.preset,'hearth');assert.equal(s.classical.epoch,0);assert.equal(s.classical.transpose,0);if(mode==='fixed')assert.equal(s.classical.gate,1);else assert(s.classical.gate<.8);}
 const g=a.classicalGenome('elegy'),profile=a.normalProfile({version:1,genomeVersion:'awen-genome-1',genome:g,pins:[g],pinNames:{[a.genomeKey(g)]:'Quiet evening'},history:[{choice:'classical',before:a.normalGenome(),after:g}]});assert.equal(profile.history[0].after.classical.home,'elegy');assert.equal(profile.pinNames[a.genomeKey(g)],'Quiet evening');assert.equal(a.mutateGenome(g,'both','test').classical.home,'elegy');assert.equal(a.makeClassicalGallery(g,'frost').length,6);
 assert.throws(()=>a.normalGenome({...g,classical:{...g.classical,home:'storm'}}));assert.throws(()=>a.normalGenome({...g,classical:{...g.classical,libraryVersion:'99'}}));
});
