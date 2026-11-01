const assert=require('assert'),fs=require('fs'),vm=require('vm');
const source=fs.readFileSync(__dirname+'/../../kindle/HAKiosk/web/kiosk.js','utf8');
function setup(){
 const events={},callbacks={},calls=[],timers=[];
 const context={String,Kindle:{use(fn){fn({applicationManager:{addEventListener(name,fn){events[name]=fn;}}});}},
  kindle:{messaging:{sendMessage(app,name,payload){calls.push(['bar',payload.function]);},receiveMessage(key,fn){callbacks[key]=fn;}},
   chrome:{setTitleBar(){calls.push(['title']);},createContentWindow(url){calls.push(['open',url]);}}},KIOSK_URL:'http://example.test:8098',
  setTimeout(fn,delay){const t={fn,delay,active:true};timers.push(t);return t;},clearTimeout(t){t.active=false;}};
 vm.runInNewContext(source,context);
 return {context,events,callbacks,calls,fire(delay){const t=timers.find(t=>t.active&&t.delay===delay);assert(t,'Missing timer '+delay);t.active=false;t.fn();}};
}
let a=setup();a.events.go();assert.equal(a.calls[0][0],'title');assert(a.calls[1][1].includes('hideMe()'));assert.equal(a.calls.filter(c=>c[0]==='open').length,0);
a.callbacks.haKioskBarReady('', 'old');assert.equal(a.calls.filter(c=>c[0]==='open').length,0);
a.callbacks.haKioskBarReady('', '1');a.fire(400);assert.equal(a.calls.filter(c=>c[0]==='open').length,1);
a.callbacks.haKioskBarReady('', '1');assert.equal(a.calls.filter(c=>c[0]==='open').length,1);a.events.pause();assert(a.calls.at(-1)[1].includes('showMe()'));
a=setup();a.events.go();a.callbacks.haKioskBarReady('','1');a.events.pause();assert.equal(a.calls.filter(c=>c[0]==='open').length,0);
a=setup();a.events.go();a.fire(1800);a.callbacks.haKioskBarReady('','1');assert.equal(a.calls.filter(c=>c[0]==='open').length,1);
a=setup();a.events.go();a.events.go();a.callbacks.haKioskBarReady('','1');a.callbacks.haKioskBarReady('','2');a.fire(400);assert.equal(a.calls.filter(c=>c[0]==='open').length,1);
a=setup();a.context.kindle.chrome.setTitleBar=function(){throw new Error('Early title not supported');};a.events.go();a.callbacks.haKioskBarReady('','1');a.fire(400);assert.equal(a.calls.filter(c=>c[0]==='open').length,1);
console.log('Native starter: hide acknowledgement before content, bounded fallback, one window, stale callbacks ignored, pause cancels launch.');
