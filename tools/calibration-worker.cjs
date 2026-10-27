#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {loadRuntime}=require('./score-lab.cjs');
const {digest}=require('./score-lab-metrics.cjs');
const ROOT=path.resolve(__dirname,'..');
function plan(input){
 const {html,api,books}=loadRuntime(),suite=JSON.parse(fs.readFileSync(path.join(ROOT,'research/calibration-scenes.json'),'utf8'));
 if(suite.version!==1||suite.scenes.length!==6||!input.experimentId||typeof input.seed!=='string')throw Error('Invalid calibration plan');
 const scenes=suite.scenes.map(s=>{
  if(suite.holdoutBooks.includes(s.book))throw Error('Holdout book selected for calibration');
  const b=books.find(b=>b.id===s.book),c=b?.chapters.find(c=>c.id===s.chapter),text=c?.paragraphs[s.paragraph-1];
  if(!text||s.variants.length!==3||s.preceding&&s.paragraph<2)throw Error('Invalid scene');
  const position=pi=>({chapterId:c.id,paragraphId:`${b.id}:${c.id}:${pi}`,text:c.paragraphs[pi]});
  const current=position(s.paragraph-1),previous=s.preceding?position(s.paragraph-2):null;
  const timeline=previous?[{...previous,step:0},{...current,step:32}]:[{...current,step:0}];
  const candidates=s.variants.map(([style,palette])=>{if(!Object.hasOwn(api.SCORE_STYLES,style)||!Object.hasOwn(api.SOUND_PALETTES,palette))throw Error('Unknown variant');const genome=api.starterGenome(style);return {id:'c-'+digest({genome,palette}).slice(0,12),genome,palette};});
  if(new Set(candidates.map(c=>c.id)).size!==3)throw Error('Duplicate alternatives');
  return {id:s.id,selectionNote:s.selectionNote,book:{id:b.id,title:b.title,author:b.author,url:b.url,revision:b.revision,license:b.license},chapter:{id:c.id,title:c.title},current,previous,candidates,
    fixture:{id:s.id,book:b.id,seed:input.seed+'|'+s.id,timeline},
    crop:{startFrame:Math.round((.12+suite.cropStartStep*api.STEP_SECONDS)*24000),frameCount:Math.round(suite.cropSteps*api.STEP_SECONDS*24000)}};
 });
 return {version:'awen-calibration-1',id:digest({html:digest(html),suite,...input}),suite,scenes,
  versions:{composer:api.COMPOSER_VERSION,sketch:api.SKETCH_VERSION,node:process.version,htmlSha256:digest(html),playwright:require('playwright/package.json').version}};
}
function main(){const [command,input,output]=process.argv.slice(2);if(command!=='plan')throw Error('Expected plan');const bytes=fs.readFileSync(input),data={requestSha256:digest(bytes),result:plan(JSON.parse(bytes))};if(fs.existsSync(output))throw Error('Refusing overwrite');const temp=output+'.'+crypto.randomUUID()+'.tmp',fd=fs.openSync(temp,'wx');try{fs.writeFileSync(fd,JSON.stringify(data,null,2)+'\n');fs.fsyncSync(fd);}finally{fs.closeSync(fd);}fs.renameSync(temp,output);}
if(require.main===module)try{main();}catch(e){console.error(e.stack);process.exitCode=1;}
module.exports={plan};
