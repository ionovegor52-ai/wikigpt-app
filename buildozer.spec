[app]
title = WikiGPT
package.name = wikigpt
package.domain = org.yourname.wikigpt
source.dir = .
version = 1.0
requirements = python3,kivy,wikipedia,openssl,requests,urllib3
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2

[android]
api = 33
minapi = 21
private = True
permissions = INTERNET

[android:meta-data]
android.app.uses_cleartext_traffic = true

[android:activity]
android:launchMode = singleTop

[app:source.exclude_patterns]
.git
.gitignore
.buildozer
bin
.venv
