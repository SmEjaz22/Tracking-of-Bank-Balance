[app]
title = Pocket
package.name = pocketapp
package.domain = org.pocketapp

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 0.1

requirements = python3,kivy,requests
p4a.branch = develop
#requirements = python3,kivy,requests

android.env_vars = P4A_sdl2_image_FORMATS=png,jpg

# Tell buildozer where your custom Java file lives
android.add_src = android/src

# SMS permissions
android.permissions = RECEIVE_SMS, READ_SMS, INTERNET, \
    POST_NOTIFICATIONS

android.api = 33
android.minapi = 26
android.ndk = 25b
android.sdk = 33

android.archs = arm64-v8a

# Keeps build cache between runs — speeds up rebuilds significantly
android.accept_sdk_license = True

orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
