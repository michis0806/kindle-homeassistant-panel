/* Run with node test_live.js: incremental rendering and reconnect behavior. */
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
let mutations = 0, requests = [], timers = [];
function node() {
    return {children: [], className: '', get firstChild() { return this.children[0]; },
        appendChild(child) { this.children.push(child); mutations++; },
        removeChild(child) { this.children.splice(this.children.indexOf(child), 1); mutations++; }};
}
const host = node(), status = node();
const context = {document: {getElementById(id) { return id === 'live-status' ? status : host; },
    createElement: node, createTextNode(value) { return {value}; }}, window: {}, JSON,
    setTimeout(fn, delay) { const timer = {fn, delay}; timers.push(timer); return timer; },
    clearTimeout(timer) { timers = timers.filter(t => t !== timer); },
    XMLHttpRequest: function () {
        requests.push(this); this.status = 0; this.readyState = 0;
        this.open = function () {}; this.send = function () {}; this.abort = function () {};
    }};
vm.runInNewContext(fs.readFileSync(__dirname + '/live.js', 'utf8'), context);
function reply(code, data) {
    const xhr = requests[requests.length - 1];
    xhr.status = code; xhr.readyState = 4; xhr.responseText = JSON.stringify(data);
    xhr.onreadystatechange();
}
function next(delay) {
    const timer = timers.find(t => t.delay === delay); assert(timer);
    timers = timers.filter(t => t !== timer); timer.fn();
}
const data = {readings: [{entity: 'sensor.power', label: '<Power>', value: '245', unit: 'W'}]};
reply(200, data);
assert.equal(host.children.length, 1);
assert.equal(host.children[0].children[0].firstChild.value, '<Power>');
const firstMutations = mutations;
next(2000); reply(200, data);
assert.equal(mutations, firstMutations, 'Unchanged payload must not redraw DOM');
const sameCard = host.firstChild;
data.readings[0].value = '250';
next(2000); reply(200, data);
assert.strictEqual(host.firstChild, sameCard);
assert.equal(mutations - firstMutations, 2, 'Only the changed value text is replaced');
next(2000); reply(503, {});
assert.strictEqual(host.firstChild, sameCard);
assert(status.firstChild.value.includes('veraltet'));
next(5000); reply(200, data);
assert(status.firstChild.value.includes('Live'));
next(2000); reply(403, {});
assert.equal(timers.length, 0, 'Revoked devices stop polling');
assert(status.firstChild.value.includes('Freigabe fehlt'));
console.log('Live DOM tests passed: unchanged values, partial update, reconnect, revocation.');
