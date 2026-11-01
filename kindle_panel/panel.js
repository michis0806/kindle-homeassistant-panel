/* Old-WebKit client: selected state patches, no framework, no automatic reload. */
(function () {
    var stopped = false, online = false, polling = false, pollTimer = null;
    var pending = null, pendingTimer = null, clicked = null;
    var status = document.getElementById('panel-status');
    function text(node, value) {
        value = String(value);
        if (!node) { return; }
        if (node.firstChild && node.childNodes.length === 1 && node.firstChild.nodeType === 3) {
            if (node.firstChild.nodeValue !== value) { node.firstChild.nodeValue = value; }
        } else if (node.firstChild || value) {
            while (node.firstChild) { node.removeChild(node.firstChild); }
            if (value) { node.appendChild(document.createTextNode(value)); }
        }
    }
    function actionForm(form) { return form && form.getAttribute('action') === 'action'; }
    function lockButtons() {
        var i, j, control, form;
        for (i = 0; i < document.forms.length; i += 1) {
            form = document.forms[i];
            if (!actionForm(form)) { continue; }
            for (j = 0; j < form.elements.length; j += 1) {
                control = form.elements[j];
                if (control.tagName.toLowerCase() !== 'button') { continue; }
                if (typeof control._serverDisabled === 'undefined') { control._serverDisabled = !!control.disabled; }
                var disabled = control._serverDisabled || !online || !!pending;
                if (control.disabled !== disabled) { control.disabled = disabled; }
            }
        }
    }
    function patch(item) {
        var node = document.getElementById(item.id), key, option, i;
        if (!node) { return; }
        if (typeof item.text !== 'undefined') { text(node, item.text); }
        if (typeof item.disabled !== 'undefined') {
            node._serverDisabled = item.disabled;
            var disabled = item.disabled || (node.tagName.toLowerCase() === 'button' && (!online || !!pending));
            if (node.disabled !== disabled) { node.disabled = disabled; }
        }
        if (typeof item.pressed !== 'undefined' && node.getAttribute('aria-pressed') !== String(item.pressed)) { node.setAttribute('aria-pressed', String(item.pressed)); }
        if (typeof item.className !== 'undefined' && node.className !== item.className) { node.className = item.className; }
        if (item.options && !node._dirty && document.activeElement !== node) {
            key = JSON.stringify(item.options);
            if (key !== node._optionsKey) {
                while (node.firstChild) { node.removeChild(node.firstChild); }
                for (i = 0; i < item.options.length; i += 1) {
                    option = document.createElement('option');
                    option.value = item.options[i].value;
                    option.appendChild(document.createTextNode(item.options[i].label));
                    node.appendChild(option);
                }
                node._optionsKey = key;
            }
        }
        if (typeof item.value !== 'undefined' && !node._dirty && (node.tagName.toLowerCase() !== 'select' || document.activeElement !== node) && node.value !== item.value) {
            node.value = item.value;
        }
    }
    function clearPending() {
        pending = null;
        if (pendingTimer !== null) { clearTimeout(pendingTimer); pendingTimer = null; }
    }
    function confirmed(data) {
        var item = pending && data.entities[pending.entity], action = pending && pending.action;
        if (!item || !pending.ack) { return false; }
        if (action === 'climate_temperature') { return item.temperature !== null && typeof item.temperature !== 'undefined' && Number(item.temperature) === Number(pending.value.replace(',', '.')); }
        if (action === 'climate_hvac') { return item.state === pending.value; }
        if (action === 'climate_fan') { return item.fan_mode === pending.value; }
        return (action === 'turn_on' && item.state === 'on') || (action === 'turn_off' && item.state === 'off');
    }
    function render(data) {
        var i, root=document.getElementById('dashboard-root');
        if (!pending && root && data.revision && root.getAttribute('data-revision')!==data.revision) {
            window.location.reload(); return;
        }
        if (confirmed(data)) {
            for (i = 0; i < pending.form.elements.length; i += 1) { pending.form.elements[i]._dirty = false; }
            clearPending();
        }
        online = true;
        for (i = 0; i < data.patches.length; i += 1) { patch(data.patches[i]); }
         lockButtons();
        text(status, pending ? 'Wird von Home Assistant übernommen …' : 'Live');
    }
    function request(method, url, body, callback) {
        var xhr = new XMLHttpRequest(), done = false, timer;
        function finish(code, data) {
            if (done) { return; }
            done = true; clearTimeout(timer);
            if (!stopped) { callback(code, data); }
        }
        xhr.onreadystatechange = function () {
            if (xhr.readyState !== 4 || done) { return; }
            var data = null;
            try { data = JSON.parse(xhr.responseText); } catch (ignore) {}
            finish(xhr.status, data);
        };
        try {
            xhr.open(method, url, true);
            if (body !== null) { xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded'); }
            timer = setTimeout(function () { finish(0, null); xhr.abort(); }, 12000);
            xhr.send(body);
        } catch (error) { finish(0, null); }
    }
    function schedule(delay) {
        if (pollTimer !== null) { clearTimeout(pollTimer); }
        if (!stopped) { pollTimer = setTimeout(poll, delay); }
    }
    function poll() {
        pollTimer = null;
        if (stopped || polling) { return; }
        polling = true;
        request('GET', '/updates.json' + (window.location ? window.location.search : ''), null, function (code, data) {
            polling = false;
            if (code === 200 && data && data.patches && data.entities) {
                render(data); schedule(2000);
            } else {
                online = false; lockButtons();
                text(status, code === 403 ? 'Freigabe fehlt · Bitte aktualisieren' : 'Verbindung unterbrochen · Werte sind veraltet');
                if (code !== 403) { schedule(5000); }
            }
        });
    }
    document.addEventListener('click', function (event) {
        var node = event.target;
        while (node && node.tagName && node.tagName.toLowerCase() !== 'button') { node = node.parentNode; }
        clicked = node && node.tagName && node.tagName.toLowerCase() === 'button' ? node : null;
    }, true);
    document.addEventListener('change', function (event) {
        if (event.target.tagName.toLowerCase() === 'select') { event.target._dirty = true; }
    }, true);
    document.addEventListener('submit', function (event) {
        var form = event.target, fields = [], values = {}, i, control, button = clicked;
        if (!actionForm(form)) { return; }
        event.preventDefault();
        if (pending || !online) { return; }
        if (!button || button.form !== form) {
            button = null;
            for (i = 0; i < form.elements.length; i += 1) {
                if (form.elements[i].tagName.toLowerCase() === 'button') { button = form.elements[i]; break; }
            }
        }
        for (i = 0; i < form.elements.length; i += 1) {
            control = form.elements[i];
            if (!control.name || control.disabled || (control.tagName.toLowerCase() === 'button' && control !== button)) { continue; }
            fields.push(encodeURIComponent(control.name) + '=' + encodeURIComponent(control.value));
            values[control.name] = control.value;
        }
        clicked = null;
        pending = {entity: values.entity, action: values.action, value: values.value || '', form: form, ack: false};
        lockButtons(); text(status, 'Befehl wird gesendet …');
        request('POST', '/action.json', fields.join('&'), function (code, data) {
            if (code === 202 && data && data.accepted) {
                pending.ack = true;
                if (pending.action === 'activate') {
                    clearPending(); lockButtons(); text(status, 'Befehl gesendet');
                } else {
                    text(status, 'Wird von Home Assistant übernommen …');
                    pendingTimer = setTimeout(function () {
                        clearPending(); lockButtons(); text(status, 'Änderung noch nicht bestätigt · Bitte Zustand prüfen');
                    }, 12000);
                }
                schedule(0);
            } else {
                clearPending(); lockButtons();
                text(status, code === 400 ? 'Aktion nicht möglich · Bitte aktuellen Zustand prüfen' :
                    code === 403 ? 'Aktion nicht freigegeben' : 'Antwort fehlt · Bitte Zustand prüfen, bevor du erneut bedienst');
            }
        });
    }, false);
    window.onunload = function () { stopped = true; clearTimeout(pollTimer); clearTimeout(pendingTimer); };
    lockButtons(); poll();
}());
