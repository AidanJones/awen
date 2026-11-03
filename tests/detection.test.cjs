'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync('index.html','utf8'),ctx=vm.createContext({setInterval,clearInterval,setTimeout,clearTimeout});
vm.runInContext(html.match(/<script>\s*([\s\S]*?)<\/script>/)[1].split('const $=id=>')[0],ctx);
const a=vm.runInContext('({detectNarrative,directPassage,analyze,contextual,narrativeTarget,automaticMusicDirection,classicalGenome,makeComposer,planStep,normalGenome})',ctx),plain=x=>JSON.parse(JSON.stringify(x));
const positive=(text,metadata={})=>a.detectNarrative(text,metadata).annotations.filter(x=>x.state==='supported');
const current=text=>positive(text).filter(x=>x.eventScope==='current').map(x=>x.id);
const intent=text=>a.directPassage(text,a.analyze(text).raw,'test');

test('all 28 categories have a reachable supported rule, with chapter/continuation requiring metadata',()=>{
 const cases=[['pursuit','She fled and dodged the guards.'],['anticipation','They waited for the door.'],['confrontation','The explosion struck the gate.'],['revelation','Only then she realised who sent the letter.'],['conversation','He asked and she replied.'],['reflection','She considered what the promise meant.'],['aftermath','Afterwards they counted the missing.'],['intrigue','He concealed the secret.'],['high-activation','She raced for the exit.'],['low-activation','They rested peacefully.'],['threat','A dangerous weapon blocked the way.'],['wonder','The marvellous sight astonished her.'],['grief','He mourned his friend.'],['humour','He joked about the absurd situation.'],['tenderness','She embraced and comforted him.'],['release','They were relieved and safe at last.'],['ironic-framing','The crash wrecked the car very nicely, thank you.'],['character-interior','To her it seemed threatening.'],['recalled-action','Years ago he had fled.'],['hypothetical-action','If they followed he would flee.'],['current-action','Now she ran.'],['cold-exposure','Snow stung their shivering hands.'],['shelter','They sat by the fireplace.'],['open-landscape','Birdsong filled the meadow.'],['severe-weather','Thunder shook the windows.'],['chapter-boundary','Unrelated prose.',{isChapterStart:true}],['situation-change','Hours later they arrived elsewhere.'],['continuation','The conversation continued.',{sameChapter:true}]];
 assert.equal(cases.length,28);for(const [label,text,metadata] of cases)assert(positive(text,metadata).some(x=>x.id===label),label);
 assert(!positive('The chapter was too long.').some(x=>x.id==='chapter-boundary'));
 assert(!positive('It continued.').some(x=>x.id==='continuation'));
});

test('negation, remembered/conditional action and current dialogue are kept separate',()=>{
 assert(!current('There was no danger.').includes('threat'));
 assert(!current('He never fled.').includes('pursuit'));
 const remembered=positive('She asked how he had escaped years ago.');
 assert(remembered.some(x=>x.id==='conversation'&&x.eventScope==='current'));
 assert(remembered.some(x=>x.id==='pursuit'&&x.eventScope==='recalled'));
 assert.equal(intent('She asked how he had escaped years ago.').kind,'dialogue');
 assert.notEqual(intent('Years ago he ran. He fired at the guards.').kind,'chase');
 assert.notEqual(intent('If the guards followed, he would flee.').kind,'chase');
 assert.equal(intent('If the guards followed he would flee, but now she ran.').kind,'chase');
 assert.equal(a.narrativeTarget({action:.8,arousal:.2},intent('Yesterday he ran.').narrative).action,0);
});

test('ambiguous tone/setting cues abstain and comic danger remains multi-label',()=>{
 for(const [text,label] of [['I wonder whether the kettle is ready.','wonder'],['A storm of applause greeted them.','severe-weather'],['They were searching for shelter.','shelter'],['He wept with joy.','grief'],['Excellent, she said.','ironic-framing'],['Her cold reply ended it.','cold-exposure']])assert(!current(text).includes(label),text);
 const result=intent('The safe dropped and squashed the officer very nicely, thank you.');
 assert(result.narrative.musicLabels.includes('confrontation'));assert(result.narrative.musicLabels.includes('humour'));
 assert.equal(result.kind,'chase');assert.equal(result.musicDirection.preset,'concertino');
 assert(!current('No one said anything as she ran.').includes('conversation'));
 assert(current('There was no danger, he said.').includes('conversation'));
});

test('evidence spans are exact and results deterministic/bounded, including Unicode',()=>{
 const text='😀 She fled, but there was no danger. He replied.';
 const result=a.detectNarrative(text);assert.deepEqual(plain(result),plain(a.detectNarrative(text)));
 for(const hit of result.annotations)if(hit.evidence.source==='text')assert.equal(text.slice(hit.evidence.start,hit.evidence.end),hit.evidence.quote);
 assert(a.detectNarrative('fled '.repeat(20000)).annotations.length<=84);
 assert.equal(a.detectNarrative('').labels.length,0);
});

test('dictionary direction uses existing smoothing and only commits recipes at chapter phrase boundaries',()=>{
 const g=a.classicalGenome('flowing','chapters'),first={...intent('Quiet thoughts.'),chapterId:'one',chapterIndex:0},next={...intent('He mourned his friend.'),chapterId:'two',chapterIndex:1};let s=a.makeComposer();
 for(let n=0;n<32;n++)s=a.planStep(s,n<11?first:next,g.scoreStyle,g.harmony,g.scoreDSL,g.classical).state;
 assert.equal(s.classical.preset,'flowing');s=a.planStep(s,next,g.scoreStyle,g.harmony,g.scoreDSL,g.classical).state;
 assert.equal(s.classical.preset,'elegy');assert.equal(s.step,33);assert.equal(s.classical.epoch,32);
 const sameChapter={...intent('The guards fired and she fled.'),chapterId:'two',chapterIndex:1};
 for(let n=0;n<64;n++)s=a.planStep(s,sameChapter,g.scoreStyle,g.harmony,g.scoreDSL,g.classical).state;
 assert.equal(s.classical.preset,'elegy');
 for(const mode of ['fixed','expression']){const held=a.classicalGenome('hearth',mode);let state=a.makeComposer();for(let n=0;n<80;n++)state=a.planStep(state,next,held.scoreStyle,held.harmony,held.scoreDSL,held.classical).state;assert.equal(state.classical.preset,'hearth');if(mode==='fixed')assert.equal(state.classical.gate,1);}
});

test('Rat opening automatic cues include comic danger, conversation, reflection and suspense',()=>{
 const book=JSON.parse(html.match(/<script id="books" type="application\/json">([\s\S]*?)<\/script>/)[1]).find(b=>b.id==='rat'),paragraphs=book.chapters[0].paragraphs;
 const third=intent(paragraphs[2]);assert(third.narrative.musicLabels.includes('humour'));assert(third.narrative.musicLabels.includes('confrontation'));assert.equal(third.musicDirection.preset,'concertino');
 assert.equal(intent(paragraphs[1]).kind,'dialogue');assert.equal(intent(paragraphs[21]).kind,'suspense');
});
