# ╔══════════════════════════════════════════════════════════════════╗
# ║  buildozer.spec — CYBERLOAD MSTL v1.8                          ║
# ║  Generado para: KivyMD + yt-dlp + Instaloader + Pillow         ║
# ║  Target: Android 8+ (API 26+) · Sin FFmpeg · APK lista         ║
# ║                                                                  ║
# ║  Cambios v1.8:                                                  ║
# ║  · version bump 1.7 → 1.8 (fuerza reinstalación limpia)        ║
# ║  · Sin otros cambios — spec estaba correcto desde V9            ║
# ╚══════════════════════════════════════════════════════════════════╝

[app]

# ── Identidad de la App ────────────────────────────────────────────
title = Cyberload MSTL
package.name = cyberload
package.domain = org.mstl

# ── Versión ────────────────────────────────────────────────────────
version = 1.8

# ── Fuentes de código ─────────────────────────────────────────────
source.dir = .
source.include_exts = py,png,jpg,json,txt
source.include_patterns = assets/*,fonts/*,icon.png

# ── Punto de entrada ──────────────────────────────────────────────
entrypoint = main.py

# ── Icono y Presentación ──────────────────────────────────────────
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png
presplash.lottie = False

# ── Orientación ───────────────────────────────────────────────────
orientation = portrait

# ── Arquitecturas objetivo ────────────────────────────────────────
android.archs = arm64-v8a, armeabi-v7a

# ──────────────────────────────────────────────────────────────────
#  REQUIREMENTS v1.8
#
#  · python3            → intérprete base. OBLIGATORIO primer ítem.
#  · kivy==2.2.1        → framework UI estable con p4a.
#  · kivymd==1.2.0      → Material Design. Compatible con kivy 2.2.1.
#  · openssl            → receta NATIVA p4a. Compila OpenSSL para ARM.
#                         Va antes de requests/yt-dlp (dependencia).
#  · yt-dlp             → motor YouTube/TikTok/Facebook/+.
#  · instaloader        → motor Instagram.
#  · pillow             → conversión webp→jpg.
#  · certifi            → certificados CA para HTTPS.
#  · urllib3            → cliente HTTP de bajo nivel.
#  · charset-normalizer → detección de encoding (dep. de requests).
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

# ── APIs Android ──────────────────────────────────────────────────
android.minapi = 26
android.api = 33
android.ndk = 25b

# ── Build tools ───────────────────────────────────────────────────
android.build_tools_version = 33.0.2

# ── Permisos ──────────────────────────────────────────────────────
#
#  INTERNET                : red para yt-dlp e instaloader
#  READ_EXTERNAL_STORAGE   : leer cookies.txt desde /sdcard/
#  WRITE_EXTERNAL_STORAGE  : escribir en /Download/
#  MANAGE_EXTERNAL_STORAGE : acceso completo en Android 11+
#                            (necesario para Scoped Storage)
# ──────────────────────────────────────────────────────────────────
android.permissions = INTERNET,\
                      READ_EXTERNAL_STORAGE,\
                      WRITE_EXTERNAL_STORAGE,\
                      MANAGE_EXTERNAL_STORAGE

# ── Accept SDK License ────────────────────────────────────────────
android.accept_sdk_license = True

# ── Gradle ────────────────────────────────────────────────────────
android.gradle_dependencies =

# AndroidX requerido por KivyMD 1.x
android.enable_androidx = True

# ── Python for Android ────────────────────────────────────────────
p4a.bootstrap = sdl2

# ── Release / Debug ───────────────────────────────────────────────
android.release_artifact = apk
android.debug = True

# ── Orientación de la actividad ───────────────────────────────────
android.activity_class_name = org.kivy.android.PythonActivity

# ── Manifest ──────────────────────────────────────────────────────
android.manifest.android_windowSoftInputMode = adjustResize


[ios]
# iOS no aplica a este proyecto.
