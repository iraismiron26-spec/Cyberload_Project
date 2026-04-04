# ╔══════════════════════════════════════════════════════════════════╗
# ║  buildozer.spec — CYBERLOAD MSTL v1.9                          ║
# ║  Generado para: KivyMD + yt-dlp + Instaloader + Pillow         ║
# ║  Target: Android 8+ (API 26+) · Sin FFmpeg · APK lista         ║
# ║                                                                  ║
# ║  Cambios v1.9:                                                  ║
# ║  · version bump 1.8 → 1.9 (fuerza reinstalación limpia)        ║
# ║  · Sin otros cambios — spec correcto desde V9                   ║
# ╚══════════════════════════════════════════════════════════════════╝

[app]

title = Cyberload MSTL
package.name = cyberload
package.domain = org.mstl

version = 1.9

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
#  REQUIREMENTS v1.9
#
#  · python3            → intérprete base. OBLIGATORIO primer ítem.
#  · kivy==2.2.1        → framework UI estable con p4a.
#  · kivymd==1.2.0      → Material Design. Compatible con kivy 2.2.1.
#  · openssl            → receta NATIVA p4a. Va antes de requests/yt-dlp.
#  · yt-dlp             → motor YouTube/TikTok/Facebook/+.
#  · instaloader        → motor Instagram.
#  · pillow             → conversión webp→jpg.
#  · certifi            → certificados CA para HTTPS.
#  · urllib3            → cliente HTTP de bajo nivel.
#  · charset-normalizer → dep. interna de requests.
#  · requests           → cliente HTTP. Usado por instaloader.
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
#  INTERNET                : red para yt-dlp e instaloader
#  READ_EXTERNAL_STORAGE   : leer cookies.txt desde /sdcard/
#  WRITE_EXTERNAL_STORAGE  : escribir en /Download/
#  MANAGE_EXTERNAL_STORAGE : acceso completo en Android 11+
# ──────────────────────────────────────────────────────────────────
android.permissions = INTERNET,\
                      READ_EXTERNAL_STORAGE,\
                      WRITE_EXTERNAL_STORAGE,\
                      MANAGE_EXTERNAL_STORAGE

# CRÍTICO: Sin esta línea buildozer se detiene esperando confirmación.
android.accept_sdk_license = True

android.gradle_dependencies =

android.enable_androidx = True

p4a.bootstrap = sdl2

android.release_artifact = apk
android.debug = True

android.activity_class_name = org.kivy.android.PythonActivity

android.manifest.android_windowSoftInputMode = adjustResize


[ios]
# iOS no aplica a este proyecto.
