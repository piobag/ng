(function (o, c, t, a, d, e, s, k) {
    o.octadesk = o.octadesk || {};
    s = c.getElementsByTagName("body")[0];
    k = c.createElement("script");
    k.async = 1;
    k.src = t + '/' + a + '?showButton=' +  d + '&openOnMessage=' + e;
    s.appendChild(k);

    "use strict";
   
})(window, document, 'https://chat.octadesk.services/api/widget', 'ng',  true, true);
