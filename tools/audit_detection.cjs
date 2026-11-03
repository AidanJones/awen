'use strict';
// Development-only coverage audit. Counts are not independent classification accuracy.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto'),{execFileSync}=require('node:child_process');
const sha=x=>crypto.createHash('sha256').update(x).digest('hex'),encode=x=>JSON.stringify(x,null,2)+'\n';
const atomic=(file,bytes)=>{const temp=file+'.'+crypto.randomUUID()+'.tmp';fs.writeFileSync(temp,bytes,{flag:'wx'});fs.renameSync(temp,file);};
function runtime(html){const c=vm.createContext({setInterval:()=>0,clearInterval:()=>{},setTimeout,clearTimeout});vm.runInContext(html.match(/<script>\s*([\s\S]*?)<\/script>/)[1].split('const $=id=>')[0],c);return {api:vm.runInContext('({analyze,contextual,directPassage})',c),books:JSON.parse(html.match(/<script id="books" type="application\/json">([\s\S]*?)<\/script>/)[1])};}
const args=process.argv.slice(2),resume=args[0]==='--resume',requested=resume?args[1]:args[0];
if(!requested)throw Error('Usage: node tools/audit_detection.cjs NEW_DIRECTORY | --resume DIRECTORY');
const root=path.resolve(__dirname,'..'),directory=path.resolve(requested),current=fs.readFileSync(path.join(root,'index.html')),
 baseline=execFileSync('git',['show','b02e461:index.html'],{cwd:root,maxBuffer:8*1024*1024}),
 identity={version:'awen-detection-audit-1',indexSha256:sha(current),baselineRevision:'b02e461',baselineSha256:sha(baseline),workerSha256:sha(fs.readFileSync(__filename)),dictionarySha256:sha(fs.readFileSync(path.join(root,'research/narrative-dictionary.json')))};
if(!resume){fs.mkdirSync(directory,{recursive:false});atomic(path.join(directory,'experiment.json'),encode(identity));atomic(path.join(directory,'state.json'),encode({jobs:{},status:'created'}));}
if(JSON.stringify(JSON.parse(fs.readFileSync(path.join(directory,'experiment.json'))))!==JSON.stringify(identity))throw Error('Audit source identity changed; start a new directory');
const lock=path.join(directory,'writer.lock');
if(fs.existsSync(lock)){const owner=JSON.parse(fs.readFileSync(lock));let alive=true;try{process.kill(owner.pid,0);}catch(e){if(e.code==='ESRCH')alive=false;}if(!resume||alive)throw Error('Audit writer lock is active; do not run concurrently');fs.unlinkSync(lock);}
fs.writeFileSync(lock,encode({pid:process.pid}),{flag:'wx'});
const invocation=new Date().toISOString().replace(/[:.]/g,'')+'-'+crypto.randomUUID(),log=path.join(directory,'invocation-'+invocation+'.jsonl'),event=(name,fields={})=>fs.appendFileSync(log,JSON.stringify({time:new Date().toISOString(),event:name,...fields})+'\n');
try{
 const old=runtime(baseline.toString('utf8')),now=runtime(current.toString('utf8')),state=JSON.parse(fs.readFileSync(path.join(directory,'state.json'))),rows=[];
 for(const book of now.books){
  if(!/^[a-z-]+$/.test(book.id))throw Error('Invalid book ID');
  const prior=old.books.find(b=>b.id===book.id);if(sha(JSON.stringify(prior))!==sha(JSON.stringify(book)))throw Error('Book edition changed; this is not a matched coverage audit');
  const requestSha256=sha(JSON.stringify([identity,book.id])),file=path.join(directory,book.id+'.json');
  let row;
  if(fs.existsSync(file)){
   const bytes=fs.readFileSync(file),saved=JSON.parse(bytes);if(saved.requestSha256!==requestSha256||saved.resultSha256!==sha(JSON.stringify(saved.result))||(state.jobs[book.id]&&state.jobs[book.id]!==sha(bytes)))throw Error('Cached audit artifact changed');row=saved.result;event('recovered-or-cached',{book:book.id});
  }else{
   row={book:book.id,revision:book.revision,paragraphs:0,baseline:{},current:{},currentLabels:{},opening:[],independentlyValidated:false};let previous=null;
   for(const [ci,chapter] of book.chapters.entries())for(const [pi,text] of chapter.paragraphs.entries()){
    const raw=now.api.analyze(text).raw,features=now.api.contextual(raw,previous),id=book.id+':'+chapter.id+':'+pi;
    const before=old.api.directPassage(text,features,id),after=now.api.directPassage(text,features,id,{chapterId:chapter.id,chapterIndex:ci,isChapterStart:pi===0,sameChapter:pi>0});previous=raw;
    row.paragraphs++;row.baseline[before.kind]=(row.baseline[before.kind]||0)+1;row.current[after.kind]=(row.current[after.kind]||0)+1;
    for(const label of after.narrative.musicLabels)row.currentLabels[label]=(row.currentLabels[label]||0)+1;
    if(book.id==='rat'&&ci===0&&pi<24)row.opening.push({paragraph:pi+1,kind:after.kind,labels:after.narrative.musicLabels,optionId:after.narrative.optionId});
   }
   atomic(file,encode({requestSha256,resultSha256:sha(JSON.stringify(row)),result:row}));event('scanned',{book:book.id,paragraphs:row.paragraphs});
  }
  state.jobs[book.id]=sha(fs.readFileSync(file));atomic(path.join(directory,'state.json'),encode(state));rows.push(row);
 }
 const report={...identity,contextPolicy:'Sequential book reading; previous raw feature vector only. New dictionary matching uses current text and explicit metadata.',classifierAccuracyMeasured:false,humanAnnotations:0,newAudioRenders:0,rows};
 atomic(path.join(directory,'report.json'),encode(report));state.status='complete';atomic(path.join(directory,'state.json'),encode(state));event('complete',{reportSha256:sha(fs.readFileSync(path.join(directory,'report.json')))});console.log('Complete:',directory);
}catch(error){event('failed',{message:error.message});throw error;}finally{fs.unlinkSync(lock);}
