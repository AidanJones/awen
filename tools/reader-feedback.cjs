'use strict';
// One shared schema: development imports execute the reader's pure validator.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
function validate(data){const html=fs.readFileSync(path.resolve(__dirname,'../index.html'),'utf8'),script=html.match(/<script>\s*([\s\S]*?)<\/script>/)[1],context=vm.createContext({setInterval:()=>1,clearInterval:()=>{},setTimeout,clearTimeout});vm.runInContext(script.split('const $=id=>')[0],context);context.feedbackInput=data;return JSON.parse(vm.runInContext('JSON.stringify(validateReaderFeedback(feedbackInput))',context));}
if(require.main===module){try{const raw=fs.readFileSync(0);if(raw.length>2097152)throw Error('Feedback exceeds 2 MB');process.stdout.write(JSON.stringify(validate(JSON.parse(raw)))+'\n');}catch(e){process.stderr.write(e.message+'\n');process.exitCode=1;}}
module.exports={validate};
