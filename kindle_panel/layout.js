/* One height choice per document; never write measured widths into the page. */
(function () {
    var root=document.getElementById('dashboard-root');
    if (!root || root.getAttribute('data-layout-ready')) { return; }
    function height(node) { var r=node.getBoundingClientRect();return r.bottom-r.top; }
    function fit() {
        if (root.getAttribute('data-layout-ready')) { return; }
        var rows=Number(root.getAttribute('data-grid-rows'))||0;
        var visible=window.innerHeight || document.documentElement.clientHeight;
        var width=window.innerWidth || document.documentElement.clientWidth;
        var fixed=4, nodes=root.querySelectorAll('.masthead,.dashboard-badges,.tile-heading-card,.view-tabs,.bottom'), i, unit=52;
        for (i=0;i<nodes.length;i+=1) { fixed+=height(nodes[i]); }
        var choices=[80,68,60,52],preferred=Number(root.getAttribute('data-layout-preferred'));
        root.setAttribute('data-layout-fixed',String(fixed));
        for (i=0;i<choices.length;i+=1) {
            if (rows*choices[i]+fixed+4<=visible) { unit=choices[i];break; }
        }
        if (preferred===52 || preferred===60 || preferred===68 || preferred===80) { unit=preferred; }
        root.className='panel dashboard layout-u'+unit+(width>=700?' layout-wide':'');
        root.setAttribute('data-layout-unit',String(unit));
        root.setAttribute('data-layout-ready','1');
    }
    fit();
    window.KindlePanelLayout={metrics:function () {
        var doc=document.documentElement,screen=window.screen||{},button=root.querySelector('.light-button');
        return {inner_w:window.innerWidth||0,inner_h:window.innerHeight||0,doc_w:doc.clientWidth||0,doc_h:doc.clientHeight||0,
            screen_w:screen.width||0,screen_h:screen.height||0,dpr:window.devicePixelRatio||1,
            button_h:button?height(button):0,unit:Number(root.getAttribute('data-layout-unit'))||52,rows:Number(root.getAttribute('data-grid-rows'))||0,fixed_h:Number(root.getAttribute('data-layout-fixed'))||0};
    }};
}());
