const assert=require('assert'),fs=require('fs'),vm=require('vm');
const source=fs.readFileSync(__dirname+'/layout.js','utf8');
for(const [width,height,expected] of [[758,1024,80],[600,800,68],[600,713,60]]){
 const attrs={'data-grid-rows':'9'},fixed=[57,52,28,26].map(h=>({getBoundingClientRect(){return {top:0,bottom:h};}}));
 const root={className:'panel dashboard layout-u52',style:{},getAttribute(k){return attrs[k]||null;},setAttribute(k,v){attrs[k]=v;},querySelectorAll(){return fixed;},querySelector(){return {getBoundingClientRect(){return {top:0,bottom:Number(attrs['data-layout-unit'])-8};}};}};
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
console.log('Layout helper: actual viewport chooses 60/68/80px rows without media queries, width writes or repeated resizing.');
