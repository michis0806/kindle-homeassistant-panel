/* Fullscreen content only; exit is handled by the shell observer. */
Kindle.use(function (app) {
    function bar(visible) {
        kindle.messaging.sendMessage('com.lab126.pillow', 'interrogatePillow', {
            pillowId:'default_status_bar', 'function':"if(document.body.haKioskExitWatch){nativeBridge.registerEventsWatchCallback(StatusBar.eventsCallback);document.body.haKioskExitWatch=null;}" + (visible?'nativeBridge.showMe();':'nativeBridge.hideMe();')
        });
    }
    function open() {
        kindle.chrome.createContentWindow(KIOSK_URL);
        kindle.chrome.setTitleBar('', 'Home Assistant');
        bar(false);
    }
    app.applicationManager.addEventListener('go',open);
    app.applicationManager.addEventListener('pause',function(){bar(true);});
    app.applicationManager.addEventListener('unload',function(){bar(true);});
});
