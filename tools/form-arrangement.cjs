'use strict';
const {FAMILY,compile}=require('./adventure-arrangement.cjs');
// Same two phrase materials and four-bar harmonic plan, different phrase ordering.
function formScore(treatment,options={}){
 if(!['alternating','grouped'].includes(treatment))throw Error('Unknown form treatment');
 const chords=['i','VI','V7','i'];
 const family={version:FAMILY.version,form:treatment==='alternating'?['A','B','A','B']:['A','A','B','B'],sections:{
  A:{chords,figure:FAMILY.sections.A.figure},B:{chords,figure:FAMILY.sections.answer.figure}
 }};
 return {...compile(family,options),treatment};
}
module.exports={formScore};
