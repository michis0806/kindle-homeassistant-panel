const fs = require('fs'), vm = require('vm'), assert = require('assert');
let mutations=0, timers=[], requests=[], handlers={}, windowHandlers={}, reloads=0;
function textNode(value) {
    let stored=value;
    return {nodeType:3, get nodeValue(){return stored;}, set nodeValue(v){stored=v;mutations++;}};
}
function node(tag,id,value) {
    return {attributes:{},getAttribute(name){return this.attributes[name]||null;},setAttribute(name,value){this.attributes[name]=value;mutations++;},tagName:tag.toUpperCase(),id,children:[],className:'',value:value||'',disabled:false,
        get childNodes(){return this.children;},get firstChild(){return this.children[0];},
        appendChild(n){this.children.push(n);mutations++;},removeChild(n){this.children.splice(this.children.indexOf(n),1);mutations++;}};
}
const nodes={};
function add(tag,id,value,text){const n=node(tag,id,value);nodes[id]=n;if(text!==undefined)n.children.push(textNode(text));return n;}
const status=add('span','panel-status','','Starting');
const target=add('span','e-climate-test-target','','24,5');
const plus=add('button','e-climate-test-plus','25.0','+');plus.name='value';
const modeButton=add('button','e-climate-test-mode-cool','cool');modeButton.name='value';modeButton.className='mode-button';
const select=add('select','e-climate-test-climate_hvac','off');select.name='value';
const apply=add('button','e-climate-test-climate_hvac-apply','','Setzen');
function form(button,action,extra){
    const fields=[{tagName:'INPUT',name:'csrf',value:'csrf-test'},{tagName:'INPUT',name:'entity',value:'climate.test'},
        {tagName:'INPUT',name:'action',value:action}];
    if(extra)fields.push(extra);fields.push(button);
    const f={elements:fields,getAttribute(){return 'action';}};button.form=f;return f;
}
const tempForm=form(plus,'climate_temperature'), modeForm=form(apply,'climate_hvac',select), directModeForm=form(modeButton,'climate_hvac');
const light=add('button','e-light-test-toggle','turn_on');light.name='action';light.className='light-button is-off';light.attributes['aria-pressed']='false';
const lightForm=form(light,'turn_on');lightForm.elements=lightForm.elements.filter(c=>c.name!=='action'||c===light);lightForm.elements.find(c=>c.name==='entity').value='light.test';
const root=add('div','dashboard-root');root.style={};
const scriptButton=add('button','e-script-test-run');
const scriptForm=form(scriptButton,'activate');scriptForm.elements.find(c=>c.name==='entity').value='script.test';
const document={documentElement:{clientWidth:600,clientHeight:800},forms:[tempForm,modeForm,directModeForm,lightForm,scriptForm],activeElement:null,getElementById(id){return nodes[id]||null;},
    createElement(tag){return node(tag,'');},createTextNode:textNode,
    addEventListener(name,fn){handlers[name]=fn;}};
const context={document,window:{innerHeight:800,addEventListener(name,fn){windowHandlers[name]=fn;},location:{search:"",reload(){reloads++;}}},JSON,Number,String,
    setTimeout(fn,delay){const t={fn,delay};timers.push(t);return t;},
    clearTimeout(t){timers=timers.filter(x=>x!==t);},
    XMLHttpRequest:function(){requests.push(this);this.readyState=0;this.status=0;
        this.open=function(method,url){this.method=method;this.url=url;};this.setRequestHeader=function(){};
        this.send=function(body){this.body=body;};this.abort=function(){};}};
vm.runInNewContext(fs.readFileSync(__dirname+'/panel.js','utf8'),context);
assert.equal(root.style.width,undefined,'The client must not write measured viewport widths back into layout');
assert.equal(root.style.minHeight,undefined);
const initialRequests=requests.length;document.documentElement.clientWidth=758;context.window.innerHeight=1024;
assert.equal(root.style.width,undefined);assert.equal(reloads,0);assert.equal(requests.length,initialRequests);
function respond(method,code,data){
    const r=requests.find(r=>r.method===method&&!r.replied);assert(r,'Expected '+method);
    r.replied=true;r.status=code;r.readyState=4;r.responseText=JSON.stringify(data);r.onreadystatechange();return r;
}
function next(delay){const t=timers.find(t=>t.delay===delay);assert(t,'Expected timer '+delay);timers=timers.filter(x=>x!==t);t.fn();}
function snapshot(temperature,mode){return {entities:{'climate.test':{state:mode,temperature,fan_mode:'auto'}},patches:[
    {id:target.id,text:String(temperature).replace('.',',')},
    {id:plus.id,value:(temperature+0.5).toFixed(1),disabled:false},
    {id:select.id,value:mode,disabled:false,options:[{value:'off',label:'Aus'},{value:'cool',label:'Kühlen'}]},
    {id:modeButton.id,disabled:false,className:'mode-button'+(mode==='cool'?' active':'')},{id:apply.id,disabled:false}]};}
respond('GET',200,snapshot(24.5,'off'));assert.equal(plus.disabled,false);
const before=mutations;next(2000);respond('GET',200,snapshot(24.5,'off'));
assert.equal(mutations,before,'Unchanged update must not alter text/option DOM');
select.value='cool';handlers.change({target:select});document.activeElement=select;
next(2000);respond('GET',200,snapshot(24.5,'off'));assert.equal(select.value,'cool','Preserve unsaved selection');
function submit(f,button){if(button)handlers.click({target:button});let prevented=false;handlers.submit({target:f,preventDefault(){prevented=true;}});assert(prevented);}
document.activeElement=plus;submit(tempForm,plus);assert(plus.disabled);
const count=requests.length;submit(tempForm,plus);assert.equal(requests.length,count,'No duplicate command while pending');
const post=respond('POST',202,{accepted:true});assert(post.body.includes('value=25.0'));assert(post.body.includes('csrf=csrf-test'));
assert.equal(target.firstChild.nodeValue,'24,5','Do not show optimistic unconfirmed temperature');
next(0);respond('GET',200,snapshot(25,'off'));
assert.equal(target.firstChild.nodeValue,'25');assert.equal(plus.value,'25.5','Focused plus button must advance its next value');assert(!plus.disabled);
assert.equal(select.value,'cool','Temperature response must not overwrite dirty HVAC select');
submit(directModeForm,modeButton);assert.equal(modeButton.className,'mode-button');
respond('POST',202,{accepted:true});assert.equal(modeButton.className,'mode-button');next(0);respond('GET',200,snapshot(25,'cool'));assert.equal(modeButton.className,'mode-button active');
submit(modeForm,apply);respond('POST',202,{accepted:true});next(0);respond('GET',200,snapshot(25,'cool'));
assert(!apply.disabled);assert.equal(select._dirty,false);assert.equal(status.firstChild.nodeValue,'Live');
next(2000);respond('GET',503,{error:'upstream_unavailable'});assert(plus.disabled);assert(status.firstChild.nodeValue.includes('veraltet'));
next(5000);respond('GET',200,snapshot(25,'cool'));assert(!plus.disabled);
submit(tempForm,plus);respond('POST',400,{error:'invalid_action'});assert(!plus.disabled);assert(status.firstChild.nodeValue.includes('Aktion nicht möglich'));
function lightSnapshot(state){const data=snapshot(25,'cool');data.entities['light.test']={state};data.patches.push({id:light.id,disabled:false,value:state==='on'?'turn_off':'turn_on',className:'light-button is-'+state,pressed:state==='on'});return data;}
next(2000);respond('GET',200,lightSnapshot('off'));
const unchanged=mutations;next(2000);respond('GET',200,lightSnapshot('off'));assert.equal(mutations,unchanged,'Unchanged light must not repaint');
submit(lightForm,light);assert(light.disabled);const lightPost=respond('POST',202,{accepted:true});assert(lightPost.body.includes('action=turn_on'));
assert.equal(light.className,'light-button is-off','No optimistic light icon change');
next(0);respond('GET',200,lightSnapshot('off'));assert(light.disabled,'Wait for confirmed light state');
next(2000);respond('GET',200,lightSnapshot('on'));assert(!light.disabled);assert.equal(light.value,'turn_off');assert.equal(light.className,'light-button is-on');assert.equal(light.getAttribute('aria-pressed'),'true');
submit(lightForm,light);assert(respond('POST',202,{accepted:true}).body.includes('action=turn_off'));next(0);respond('GET',200,lightSnapshot('off'));assert.equal(light.getAttribute('aria-pressed'),'false');
submit(scriptForm,scriptButton);const scriptRequests=requests.length;submit(scriptForm,scriptButton);assert.equal(requests.length,scriptRequests,'One script activation while request is pending');
const scriptPost=respond('POST',202,{accepted:true});assert(scriptPost.body.includes('action=activate'));assert(scriptPost.body.includes('entity=script.test'));
assert(!scriptButton.disabled,'Script activation does not wait for a short-lived on state');
const coverButton=add('button','e-cover-test-open_cover');const coverForm=form(coverButton,'open_cover');coverForm.elements.find(c=>c.name==='entity').value='cover.test';document.forms.push(coverForm);
submit(coverForm,coverButton);respond('POST',202,{accepted:true});assert(coverButton.disabled);next(0);const moving=lightSnapshot('off');moving.entities['cover.test']={state:'opening'};moving.patches.push({id:coverButton.id,disabled:false});respond('GET',200,moving);assert(!coverButton.disabled,'Cover command is confirmed when movement starts');
const stopButton=add('button','e-cover-test-stop_cover');const stopForm=form(stopButton,'stop_cover');stopForm.elements.find(c=>c.name==='entity').value='cover.test';document.forms.push(stopForm);
submit(stopForm,stopButton);assert(respond('POST',202,{accepted:true}).body.includes('action=stop_cover'));
next(0);const stopping=lightSnapshot('off');stopping.entities['cover.test']={state:'opening'};stopping.patches.push({id:stopButton.id,disabled:false});respond('GET',200,stopping);assert(stopButton.disabled,'Wait until HA confirms cover is no longer moving');
next(2000);stopping.entities['cover.test'].state='open';respond('GET',200,stopping);assert(!stopButton.disabled,'Stop completes when HA reports a stationary cover');
assert.equal(root.style.width,undefined,'Commands and state updates must never set pixel widths');
console.log('Panel tests passed: no viewport feedback writes, script activation, cover movement confirmation, no unchanged repaint, dirty selection, command confirmation, duplicate prevention, focused +/- values, reconnect.');
