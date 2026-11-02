// Export harmonic context from the production DSL, without rendering or audio analysis.
'use strict';
const fs=require('node:fs'),crypto=require('node:crypto'),{loadRuntime}=require('./score-lab.cjs');
const [input,output]=process.argv.slice(2),api=loadRuntime().api,rows=JSON.parse(fs.readFileSync(input,'utf8'));
if(!Array.isArray(rows)||rows.length>100)throw Error('Bounded score batch required');
const {exportScore}=require('./symbolic-score.cjs');
const result=rows.map(row=>exportScore(row,api));
const temp=output+'.'+crypto.randomUUID()+'.tmp';fs.writeFileSync(temp,JSON.stringify(result)+'\n',{flag:'wx'});fs.renameSync(temp,output);
