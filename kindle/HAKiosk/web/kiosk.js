/* Wait for native chrome to settle before creating the content window. */
Kindle.use(function (app) {
    var active=false, opened=false, generation=0, launchTimer=null, fallbackTimer=null;
    function clearTimers() {
        if (launchTimer!==null) { clearTimeout(launchTimer); launchTimer=null; }
        if (fallbackTimer!==null) { clearTimeout(fallbackTimer); fallbackTimer=null; }
    }
    function bar(visible, ticket) {
        var code="if(document.body.haKioskExitWatch){nativeBridge.registerEventsWatchCallback(StatusBar.eventsCallback);document.body.haKioskExitWatch=null;}" + (visible?'nativeBridge.showMe();':'nativeBridge.hideMe();');
        if (!visible) {
            code+="try{nativeBridge.setLipcProperty('com.schmid.kindlekiosk','haKioskBarReady','"+ticket+"');}catch(ignore){}";
        }
        kindle.messaging.sendMessage('com.lab126.pillow','interrogatePillow',{pillowId:'default_status_bar','function':code});
    }
    function launch(ticket) {
        if (!active || opened || ticket!==generation) { return; }
        clearTimers();opened=true;
        kindle.chrome.createContentWindow(KIOSK_URL);
    }
    if (typeof kindle.messaging.receiveMessage==='function') { kindle.messaging.receiveMessage('haKioskBarReady',function (message,value) {
        if (!active || opened || String(value)!==String(generation) || launchTimer!==null) { return; }
        var ticket=generation;
        // The reply confirms hideMe ran; allow its window-manager change to settle.
        launchTimer=setTimeout(function () { launch(ticket); },400);
    }); }
    function open() {
        clearTimers();active=true;opened=false;generation+=1;
        var ticket=generation;
        try { kindle.chrome.setTitleBar('','Home Assistant'); } catch (ignoreTitle) {}
        bar(false,ticket);
        // Older builds can omit the reply. Still create exactly one window.
        fallbackTimer=setTimeout(function () { launch(ticket); },1800);
    }
    function close() {
        active=false;generation+=1;clearTimers();bar(true);
    }
    app.applicationManager.addEventListener('go',open);
    app.applicationManager.addEventListener('pause',close);
    app.applicationManager.addEventListener('unload',close);
});
