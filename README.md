# Social Hub - Android app (no Streamlit)

The web app (`www/index.html`) talks straight to your Supabase project, so all existing
posts, reels, stories, chats, notes and accounts show up in the Android app after login.
Capacitor just wraps that page in a native Android app. `bridge.js` replaces what the
Streamlit iframe used to provide (links, Spotify login, notifications, share, back button).

## Way 1 - build the APK in the cloud (no PC, no Android Studio)
1. Create a GitHub repo and upload **all files of this folder** (keep `.github/workflows/`).
   - Tip: you can also copy these files into your existing Streamlit repo root. Then every
     push re-builds `www/index.html` from your latest `app.py` automatically.
2. GitHub -> **Actions** -> *Build Android APK* -> **Run workflow**. Takes about 5-10 minutes.
3. Open the finished run -> **Artifacts** -> download `SocialHub-debug-apk` -> unzip -> install
   `app-debug.apk` on the phone (allow "install unknown apps").

## Way 2 - build on your PC
Needs Node 22+, JDK 21, Android Studio.
```
npm install
npx cap add android
npx @capacitor/assets generate --android     # icon + splash from /assets
python3 patch_android.py                      # permissions + socialhub:// deep link
npx cap sync android
npx cap open android                          # Android Studio -> Build > Build APK(s)
```

## After you change app.py
```
python3 sync.py path/to/app.py     # regenerates www/index.html (reads APP_URL, Spotify id, YouTube key)
npx cap sync android
```
(`sync.py` prints a WARNING if one of its patches no longer matches your code.)

## One-time setup for Spotify login
Spotify dashboard -> your app -> Redirect URIs -> add:  `socialhub://callback`

## Not included yet
- **Background push** (notifications when the app is closed). Right now notifications appear while the app is open/recent (local notifications). Real push needs Firebase (FCM) + a server/Supabase edge function.
- **Play Store release**: this builds a debug-signed APK for installing directly. Play Store needs a release keystore + AAB.
- Replace `assets/icon-only.png` with your 1024x1024 logo for a sharper icon (current one is upscaled from the 192px favicon).

## Security note
`YOUTUBE_API_KEY` ends up inside the APK. Restrict that key in Google Cloud Console (Android app restriction / API restriction to YouTube Data API v3 only) or move YouTube calls behind a Supabase edge function.
