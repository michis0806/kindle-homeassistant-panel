const assert=require('assert'),fs=require('fs'),vm=require('vm');
const source=fs.readFileSync(__dirname+'/layout.js','utf8');
for(const [width,height,expected] of [[758,1024,88],[600,800,68],[600,713,60]]){
 const attrs={'data-grid-rows':'9'},fixed=[57,52,28,26].map(h=>({getBoundingClientRect(){return {top:0,bottom:h};}}));
 const root={className:'panel dashboard layout-u52',style:{},getAttribute(k){return attrs[k]||null;},setAttribute(k,v){attrs[k]=v;},getBoundingClientRect(){return {left:0,right:width};},querySelectorAll(){return fixed;},querySelector(){return {getBoundingClientRect(){return {top:0,bottom:Number(attrs['data-layout-unit'])-8};}};}};
 const window={innerWidth:width,innerHeight:height,screen:{width,height},devicePixelRatio:1};
 const document={documentElement:{clientWidth:width,clientHeight:height},getElementById(){return root;}};
 vm.runInNewContext(source,{document,window,Number,String});
 assert.equal(Number(attrs['data-layout-unit']),expected);
 assert.equal(window.KindlePanelLayout.metrics().button_h,expected-8);
 assert.equal(root.style.width,undefined,'No width mutation');
 const before=root.className;window.innerHeight=500;
 vm.runInNewContext(source,{document,window,Number,String});
 assert.equal(root.className,before,'Height is chosen once per document, never during a command');
}
const attrs={'data-grid-rows':'2','data-fit-rows':'11','data-layout-preferred':'80'};
const root={className:'',getAttribute(k){return attrs[k]||null;},setAttribute(k,v){attrs[k]=v;},querySelectorAll(){return [{getBoundingClientRect(){return {top:0,bottom:100};}}];}};
vm.runInNewContext(source,{document:{getElementById(){return root;},documentElement:{}},window:{innerWidth:758,innerHeight:897},Number,String});
assert.equal(attrs['data-layout-unit'],'68','Page uses largest-page budget; oversized preview preference cannot overflow');
const roomyAttrs={'data-grid-rows':'6','data-fit-rows':'6','data-fit-headings':'0'};
const roomyRoot={className:'',getAttribute(k){return Object.prototype.hasOwnProperty.call(roomyAttrs,k)?roomyAttrs[k]:null;},setAttribute(k,v){roomyAttrs[k]=v;},querySelectorAll(){return [{getBoundingClientRect(){return {top:0,bottom:100};}}];},querySelector(selector){return selector==='.layout-badge-measure'?{getBoundingClientRect(){return {top:0,bottom:52};}}:null;}};
vm.runInNewContext(source,{document:{getElementById(){return roomyRoot;},documentElement:{}},window:{innerWidth:758,innerHeight:897},Number,String});
assert.equal(roomyAttrs['data-layout-unit'],'112','Fixed-height badges do not consume enlarged grid rows');
console.log('Layout helper: actual viewport chooses fitting shared rows up to 112px without media queries, width writes or repeated resizing.');
