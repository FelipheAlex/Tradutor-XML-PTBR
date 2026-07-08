[app]
title = Tradutor XML PT-BR
package.name = tradutorxmlptbr
package.domain = org.feliphealex
source.dir = .
source.include_exts = py,kv,txt,xml,png,jpg,jpeg
version = 1.0
requirements = python3,kivy,requests,certifi,deep-translator
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 35
android.minapi = 23
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a,armeabi-v7a
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
