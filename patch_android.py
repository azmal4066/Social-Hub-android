#!/usr/bin/env python3
"""Adds Android permissions + the socialhub:// deep link to android/app/src/main/AndroidManifest.xml.
Safe to run many times. Run after `npx cap add android`."""
import pathlib, sys

mf = pathlib.Path(__file__).resolve().parent / "android/app/src/main/AndroidManifest.xml"
if not mf.is_file():
    sys.exit("patch_android.py: run `npx cap add android` first")

x = mf.read_text(encoding="utf-8")
if "socialhub-patched" in x:
    print("patch_android.py: already patched")
    sys.exit(0)

perms = """
    <!-- socialhub-patched -->
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.RECORD_AUDIO" />
    <uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />
    <uses-permission android:name="android.permission.VIBRATE" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <uses-feature android:name="android.hardware.camera" android:required="false" />
    <uses-feature android:name="android.hardware.microphone" android:required="false" />
"""
deeplink = """
            <intent-filter>
                <action android:name="android.intent.action.VIEW" />
                <category android:name="android.intent.category.DEFAULT" />
                <category android:name="android.intent.category.BROWSABLE" />
                <data android:scheme="socialhub" />
            </intent-filter>
"""
if "android.permission.INTERNET" not in x:
    perms += '    <uses-permission android:name="android.permission.INTERNET" />\n'
x = x.replace("<application", perms + "\n    <application", 1)
x = x.replace("</activity>", deeplink + "        </activity>", 1)
if "windowSoftInputMode" not in x:
    x = x.replace("<activity", '<activity android:windowSoftInputMode="adjustResize"', 1)
mf.write_text(x, encoding="utf-8")
print("patch_android.py: manifest patched")
