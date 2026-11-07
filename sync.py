#!/usr/bin/env python3
"""Build www/index.html for the Android app from the Streamlit app.py.

Usage:  python3 sync.py            (looks for app.py next to this file, then one folder up)
        python3 sync.py path/to/app.py

Run it again whenever app.py changes, then:  npx cap sync android
If app.py is not found, the existing www/index.html is kept (so a plain repo still builds).
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "www" / "index.html"

cands = [pathlib.Path(sys.argv[1])] if len(sys.argv) > 1 else [ROOT / "app.py", ROOT.parent / "app.py"]
src = next((c for c in cands if c.is_file()), None)
if not src:
    print("sync.py: app.py not found - keeping existing www/index.html")
    sys.exit(0)

code = src.read_text(encoding="utf-8")

def const(name):
    m = re.search(r'^%s\s*=\s*"([^"]*)"' % name, code, re.M)
    return m.group(1) if m else ""

APP_URL, SPOTIFY_ID, YT_KEY = const("APP_URL"), const("SPOTIFY_CLIENT_ID"), const("YOUTUBE_API_KEY")

a = code.index("HTML = r'''") + len("HTML = r'''")
b = code.index("</html>'''", a) + len("</html>")
html = code[a:b]

SCHEME_REDIRECT = "socialhub://callback"   # add this as a Redirect URI in the Spotify dashboard
problems = []

def patch(old, new, label, count=1):
    global html
    if old not in html:
        problems.append(label)
        return
    html = html.replace(old, new) if count == 0 else html.replace(old, new, count)

# Spotify: redirect back into the app through a deep link instead of the Streamlit URL
patch("const SPID='__SPOTIFY_ID__',SPRED='__APP_URL__';",
      "const SPID='__SPOTIFY_ID__',SPRED='%s';" % SCHEME_REDIRECT, "Spotify redirect constant")
patch("new URLSearchParams(window.parent.location.search)",
      "new URLSearchParams(window.__spQuery||'')", "Spotify exchange(): read code")
patch("try{window.parent.history.replaceState({},'',window.parent.location.pathname)}catch(e){}try{window.close()}catch(e){}",
      "window.__spQuery='';try{window.dispatchEvent(new StorageEvent('storage',{key:'sp_tok'}))}catch(e){}",
      "Spotify exchange(): cleanup")
# YouTube player wants a real https referrer, not the deep link
patch("widget_referrer:(SPRED&&!SPRED.startsWith('__'))?SPRED:undefined",
      "widget_referrer:window.APP_URL||undefined", "YouTube widget_referrer")

# Fill the Streamlit placeholders
for k, v in {"__SPOTIFY_ID__": SPOTIFY_ID, "__APP_URL__": APP_URL, "__YT_KEY__": YT_KEY, "__OPEN_USER__": ""}.items():
    html = html.replace(k, v)

# Safe-area insets for the Android status/navigation bars
patch("</head>",
      '<style id="android-insets">:root{padding-top:max(env(safe-area-inset-top,0px),var(--safe-area-inset-top,0px));'
      'padding-bottom:max(env(safe-area-inset-bottom,0px),var(--safe-area-inset-bottom,0px))}</style></head>',
      "</head> for inset style")
# Native bridge (loaded last so Capacitor + the app's own scripts already exist)
patch("</body>", '<script src="bridge.js"></script></body>', "</body> for bridge.js")

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(html, encoding="utf-8")
print("sync.py: wrote %s (%d KB) from %s" % (OUT, len(html) // 1024, src))
for p in problems:
    print("  WARNING: patch not applied ->", p, "(app.py changed? check)")
