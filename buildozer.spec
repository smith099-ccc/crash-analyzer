[app]
title = Crash Analyzer
package.name = crashanalyzer
package.domain = org.crashanalyzer
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json
version = 1.0.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0
android.api = 35
android.minapi = 23
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.copy_libs = 1

[buildozer]
log_level = 2
warn_on_root = 1
