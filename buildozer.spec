[app]

title = TestApp
package.name = testapp
package.domain = org.test

source.dir = .
source.include_exts = py,png,jpg,kv

version = 0.1

requirements = python3,kivy==2.2.1

orientation = portrait
fullsceeen = 1

android.permissions = INTERNET
android.api = 31
android.miniapi = 21
android.archs = arm64-v8a, armeabi-v7a

[buildozer]

log_level = 2
bin_dir = ./bin
