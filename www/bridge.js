/* Social Hub - Android bridge.
   Replaces the things Streamlit's iframe used to give the page:
   external links, Spotify login redirect, notifications, share, back button. */
(function () {
  var C = window.Capacitor;
  if (!C || !C.isNativePlatform || !C.isNativePlatform()) return; // plain browser: do nothing
  var P = C.Plugins || {};

  /* 0) Hide the (empty) notification banner properly. On Android its slide-away
        offset is too small once the status-bar inset is added, so it showed as an empty pill. */
  try {
    var st = document.createElement('style');
    st.textContent = '#nb:not(.show){opacity:0!important;visibility:hidden!important;pointer-events:none!important}';
    document.head.appendChild(st);
  } catch (e) {}

  /* 1) http(s) links / window.open -> system browser (Custom Tab) */
  var _open = window.open;
  window.open = function (u) {
    if (u && /^https?:/i.test(String(u)) && P.Browser) {
      try { P.Browser.open({ url: String(u) }); } catch (e) {}
      return null;
    }
    return _open.apply(window, arguments);
  };

  /* 2) Spotify login comes back as  socialhub://callback?code=..&state=sphub */
  if (P.App) {
    P.App.addListener('appUrlOpen', function (e) {
      try {
        var u = (e && e.url) || '';
        if (u.indexOf('socialhub://callback') !== 0) return;
        window.__spQuery = (u.split('?')[1] || '').split('#')[0];
        try { var r = P.Browser && P.Browser.close(); r && r.catch && r.catch(function () {}); } catch (x) {}
        if (typeof SP !== 'undefined') SP.exchange();
      } catch (x) {}
    });
    /* Android back button: go back inside the app, minimise at the root */
    P.App.addListener('backButton', function (e) {
      if (e && e.canGoBack) history.back();
      else P.App.minimizeApp();
    });
  }

  /* 3) Notifications: WebView has no Notification API -> use local notifications */
  var LN = P.LocalNotifications;
  if (LN) {
    var perm = 'default';
    var hash = function (s) { var h = 7; for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return Math.abs(h) % 2147483000 + 1; };
    var Nt = function (title, opts) {
      opts = opts || {};
      this.title = title; this.onclick = null;
      var id = opts.tag ? hash(String(opts.tag)) : Math.floor(Math.random() * 2147483000) + 1;
      try { LN.schedule({ notifications: [{ id: id, title: String(title), body: String(opts.body || '') }] }); } catch (e) {}
    };
    Nt.prototype.close = function () {};
    Object.defineProperty(Nt, 'permission', { get: function () { return perm; } });
    Nt.requestPermission = function (cb) {
      return LN.requestPermissions().then(function (r) {
        perm = r && r.display === 'granted' ? 'granted' : 'denied';
        if (cb) cb(perm);
        return perm;
      });
    };
    try {
      LN.checkPermissions().then(function (r) {
        if (r && r.display === 'granted') perm = 'granted';
        else if (r && r.display === 'denied') perm = 'denied';
      }).catch(function () {});
    } catch (e) {}
    window.Notification = Nt;
  }

  /* 4) Share sheet */
  if (P.Share) {
    navigator.share = function (d) {
      d = d || {};
      return P.Share.share({ title: d.title, text: d.text, url: d.url, dialogTitle: d.title }).then(function () {}, function (err) {
        if (/cancel/i.test((err && err.message) || '')) { var x = new Error('cancel'); x.name = 'AbortError'; throw x; }
        throw err;
      });
    };
    navigator.canShare = function () { return true; };
  }
})();
