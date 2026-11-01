/* ES3-compatible DOM/XHR client for the Kindle PW1. No HTML injection. */
(function () {
    var stopped = false, rows = {}, order = '', request = null;
    var host = document.getElementById('live-readings');
    var status = document.getElementById('live-status');
    function text(node, value) {
        value = String(value);
        if (node._liveText === value) { return; }
        while (node.firstChild) { node.removeChild(node.firstChild); }
        node.appendChild(document.createTextNode(value));
        node._liveText = value;
    }
    function element(tag, className, parent) {
        var node = document.createElement(tag);
        node.className = className;
        parent.appendChild(node);
        return node;
    }
    function render(data) {
        var i, item, key = '', row, card;
        for (i = 0; i < data.readings.length; i += 1) {
            key += data.readings[i].entity + '|';
        }
        if (key !== order) {
            while (host.firstChild) { host.removeChild(host.firstChild); }
            rows = {}; order = key;
        }
        for (i = 0; i < data.readings.length; i += 1) {
            item = data.readings[i]; row = rows[item.entity];
            if (!row) {
                card = element('div', 'setting-row', host);
                row = {label: element('h2', '', card), value: element('div', 'measure', card),
                    unit: element('div', 'current', card)};
                rows[item.entity] = row;
            }
            text(row.label, item.label);
            text(row.value, item.value);
            text(row.unit, item.unit);
        }
        text(status, data.readings.length ? 'Live · Abfrage alle 2 Sekunden' :
            'Keine Sensoren ausgewählt. Bitte in Kindle Panel auswählen.');
    }
    function poll() {
        if (stopped) { return; }
        var xhr = new XMLHttpRequest(), done = false, watchdog;
        request = xhr;
        function finish(ok, message) {
            if (done) { return; }
            done = true; clearTimeout(watchdog); request = null;
            if (stopped) { return; }
            if (!ok) { text(status, message || 'Verbindung unterbrochen · Werte sind veraltet'); }
            if (xhr.status !== 403) { setTimeout(poll, ok ? 2000 : 5000); }
        }
        xhr.onreadystatechange = function () {
            if (xhr.readyState !== 4 || done) { return; }
            if (xhr.status === 200) {
                try { render(JSON.parse(xhr.responseText)); finish(true); }
                catch (error) { finish(false); }
            } else {
                finish(false, xhr.status === 403 ?
                    'Freigabe fehlt · Bitte zur Übersicht zurückkehren' : null);
            }
        };
        try {
            xhr.open('GET', '/live.json', true);
            watchdog = setTimeout(function () {
                finish(false); xhr.abort();
            }, 12000);
            xhr.send(null);
        } catch (error) { finish(false); }
    }
    window.onunload = function () {
        stopped = true;
        if (request) { request.abort(); }
    };
    poll();
}());
