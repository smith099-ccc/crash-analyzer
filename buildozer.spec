[app]
title = Crash Analyzer
package.name = crashanalyzer
package.domain = org.crashanalyzer
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json
version = 1.0.2
requirements = python3==3.11.9,hostpython3==3.11.9,kivy
orientation = portrait
fullscreen = 0
android.api = 35
android.minapi = 23
android.archs = arm64-v8a, armeabi-v7a
android.permissions = INTERNET, ACCESS_NETWORK_STATE
android.allow_backup = True
android.copy_libs = 1
android.ndk = 28c

[buildozer]
log_level = 2
warn_on_root = 1
p4a.branch = develop
