'use strict';
// Produce the small notation-only pilot. Refuse to replace an archived export.
const fs=require('node:fs'),path=require('node:path'),{loadRuntime}=require('./score-lab.cjs'),{exportScore}=require('./symbolic-score.cjs');
const [output]=process.argv.slice(2);
if(!output)throw Error('Usage: node tools/symbolic-score-fixtures.cjs NEW_EXPORT_JSON');
const fixture=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../research/symbolic-score-fixtures.json'),'utf8')),api=loadRuntime().api;
const rows=fixture.presets.map(preset=>exportScore({id:preset,steps:fixture.steps,seed:fixture.seed,book:'rat',
 genome:api.classicalGenome(preset,'chapters'),timeline:fixture.timeline},api));
fs.writeFileSync(output,JSON.stringify(rows)+'\n',{flag:'wx'});
console.log('Exported',rows.length,'scores');
