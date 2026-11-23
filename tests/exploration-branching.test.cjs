'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const branching=require('../tools/exploration-branching.cjs');
const context=vm.createContext({setInterval:()=>1,clearInterval:()=>{}});
const html=fs.readFileSync('index.html','utf8'),runtime=html.match(/<script>\s*([\s\S]*?)<\/script>/)[1].split('const $=id=>')[0];
vm.runInContext(runtime,context);
context.data={library:JSON.parse(fs.readFileSync('research/scoring-knowledge.json','utf8'))};
const template=fs.readFileSync('tools/exploration-review.html','utf8');
vm.runInContext(template.slice(template.indexOf('const directions='),template.indexOf('const uid=')),context);
const api=vm.runInContext('({normalGenome,mutateGenome,compileScoreDSL})',context);
const pool=JSON.parse(JSON.stringify(vm.runInContext("['broad','bach','classical'].flatMap(startingCards)",context)));
const plain=x=>JSON.parse(JSON.stringify(x));
const request=(parents,breadth=1)=>({parents,pool,seed:'TEST-ONLY-PARENTS-'+JSON.stringify(parents),breadth,generation:1,action:breadth===0?'refine':breadth>=2?'widen':'explore'});

test('nine-card branches preserve each parent and obey tier guarantees across starting families',()=>{
 for(const parent of [pool[0],pool[4],pool[9],pool.at(-1)])for(const breadth of [0,1,2,3]){
  const input=request([parent],breadth),before=JSON.stringify(input),result=branching.build(api,input);
  assert.equal(result.cards.length,9);assert.equal(JSON.stringify(input),before);
  assert.deepEqual(result.cards[0],parent);assert.equal(new Set(result.cards.map(c=>branching.key(c,api))).size,9);
  for(const child of result.cards.slice(1)){
   const count=branching.structural(child,parent,api).length;
   assert(child.lineage.tier==='near'?count===0:child.lineage.tier==='medium'?count===1:count>=2);
   assert.deepEqual(child.lineage.changes,branching.changes(child,parent,api));
   assert(child.name.length<=100&&child.description.length<=700);
   api.normalGenome(child.genome);
  }
  assert.deepEqual(plain(branching.build(api,input)),plain(result));
 }
});
test('default one-parent mix is two near, three medium, three broad; widening offers more broad choices',()=>{
 const counts=b=>branching.build(api,request([pool[0]],b)).branch.offspring.reduce((a,c)=>(a[c.tier]=(a[c.tier]||0)+1,a),{});
 assert.deepEqual(counts(1),{near:2,medium:3,broad:3});
 assert.deepEqual(counts(2),{near:1,medium:2,broad:5});
 assert.deepEqual(counts(3),{medium:2,broad:6});
 assert.deepEqual(counts(0),{near:8});
});
test('multi-parent generations retain snapshots, track ancestry and do not average parents',()=>{
 const parents=[pool[0],pool[1],pool[4]],result=branching.build(api,request(parents,2));
 assert.deepEqual(result.cards.slice(0,3),parents);
 assert.deepEqual(result.branch.parents,parents.map(p=>p.id));
 assert(result.cards.slice(3).every(c=>parents.some(p=>p.id===c.lineage.parentId)));
 assert(new Set(result.cards.slice(3).map(c=>c.lineage.parentId)).size===3);
});
test('a chosen wider direction can be refined with its structure intact',()=>{
 const broad=branching.build(api,request([pool[0]],3)).cards.at(-1);
 const refined=branching.build(api,{...request([broad],0),generation:2});
 assert.deepEqual(plain(refined.cards[0]),plain(broad));
 assert(refined.cards.every(c=>branching.structural(c,broad,api).length===0));
});
test('invalid requests and exhausted structural pools fail without changing favourites',()=>{
 const p=pool[0],before=JSON.stringify(p);
 assert.throws(()=>branching.build(api,{...request([p]),breadth:4}));
 assert.throws(()=>branching.build(api,{...request([p]),parents:[]}));
 assert.throws(()=>branching.build(api,{...request([p]),pool:[p]}));
 assert.equal(JSON.stringify(p),before);
});
