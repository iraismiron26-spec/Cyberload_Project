# ╔══════════════════════════════════════════════════════════════════╗
# ║  buildozer.spec — CYBERLOAD MSTL v2.0                          ║
# ║                                                                  ║
# ║  Cambios v2.0:                                                  ║
# ║  · package.domain = org.test                                    ║
# ║    → ruta interna: /Android/data/org.test.cyberload/files/      ║
# ║  · version bump → 2.0 (cookie auto-download feature)           ║
# ╚══════════════════════════════════════════════════════════════════╝

[app]

title = Cyberload MSTL
package.name = cyberload

# ── CRÍTICO: org.test genera la ruta interna ──────────────────────
# /storage/emulated/0/Android/data/org.test.cyberload/files/
# Ahí es donde main.py guardará cookies.txt descargado de GitHub.
package.domain = org.test

version = 2.0

source.dir = .
source.include_exts = py,png,jpg,json,txt
source.include_patterns = assets/*,fonts/*,icon.png

entrypoint = main.py

icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png
presplash.lottie = False

orientation = portrait

android.archs = arm64-v8a, armeabi-v7a

# ──────────────────────────────────────────────────────────────────
#  REQUIREMENTS v2.0
#
#  · python3            → intérprete base.
#  · kivy==2.2.1        → framework UI estable con p4a.
#  · kivymd==1.2.0      → Material Design.
#  · openssl            → receta NATIVA. Va antes de requests/yt-dlp.
#  · yt-dlp             → motor YouTube/TikTok/Facebook/+.
#  · instaloader        → motor Instagram.
#  · pillow             → conversión webp→jpg.
#  · certifi            → certificados CA. Requerido por requests
#                         para descargar cookies.txt de GitHub HTTPS.
#  · urllib3            → cliente HTTP bajo nivel.
#  · charset-normalizer → encoding detection (dep. de requests).
#  · requests           → cliente HTTP. Usado para descargar cookies
#                         desde GitHub y por instaloader.
#  · setuptools         → instalación de paquetes en p4a.
# ──────────────────────────────────────────────────────────────────
requirements = python3,\
               kivy==2.2.1,\
               kivymd==1.2.0,\
               openssl,\
               yt-dlp,\
               instaloader,\
               pillow,\
               certifi,\
               urllib3,\
               charset-normalizer,\
               requests,\
               setuptools


[buildozer]

log_level = 2
warn_on_root = 1


[android]

android.minapi = 26
android.api = 33
android.ndk = 25b
android.build_tools_version = 33.0.2

# ── Permisos ──────────────────────────────────────────────────────
#  INTERNET                : descargar cookies de GitHub + yt-dlp
#  READ_EXTERNAL_STORAGE   : leer archivos en /sdcard/
#  WRITE_EXTERNAL_STORAGE  : escribir cookies.txt en /Android/data/
#  MANAGE_EXTERNAL_STORAGE : acceso completo en Android 11+
# ──────────────────────────────────────────────────────────────────
android.permissions = INTERNET,\
                      READ_EXTERNAL_STORAGE,\
                      WRITE_EXTERNAL_STORAGE,\
                      MANAGE_EXTERNAL_STORAGE

android.accept_sdk_license = True

android.gradle_dependencies =
android.enable_androidx = True

p4a.bootstrap = sdl2

android.release_artifact = apk
android.debug = True

android.activity_class_name = org.kivy.android.PythonActivity
android.manifest.android_windowSoftInputMode = adjustResize


[ios]
# iOS no aplica.
