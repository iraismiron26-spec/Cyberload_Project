# ╔══════════════════════════════════════════════════════════════════╗
# ║  buildozer.spec — CYBERLOAD MSTL v13.0                         ║
# ║                                                                  ║
# ║  Cambios V13:                                                   ║
# ║  · ELIMINADO openssl de requirements → era PyPI inválido        ║
# ║    p4a lo compila automáticamente como receta nativa.           ║
# ║    ERA EL ORIGEN DEL ERROR: "No matching distribution for       ║
# ║    openssl" → pip no puede instalarlo, solo p4a lo compila.     ║
# ║  · Añadido pyjnius → captura Intent SEND (ventana flotante)     ║
# ║  · Añadido plyer   → notificaciones Android al bajar contenido  ║
# ║  · android.manifest.intent_filters → app aparece al compartir  ║
# ║  · POST_NOTIFICATIONS → Android 13+ requiere este permiso       ║
# ║  · Cache key → v13 para bustar caché corrupta de V12           ║
# ╚══════════════════════════════════════════════════════════════════╝

[app]

title = Cyberload MSTL
package.name = cyberload

# ── CRÍTICO: org.test genera la ruta interna ──────────────────────
# /storage/emulated/0/Android/data/org.test.cyberload/files/
# Ahí es donde main.py guarda cookies.txt descargado de GitHub.
package.domain = org.test

version = 13.0

source.dir = .
source.include_exts = py,png,jpg,json,txt,xml
source.include_patterns = assets/*,fonts/*,icon.png

entrypoint = main.py

icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png
presplash.lottie = False

orientation = portrait

android.archs = arm64-v8a, armeabi-v7a


# ──────────────────────────────────────────────────────────────────
#  REQUIREMENTS V13
#
#  CAMBIO CRÍTICO — ELIMINADO openssl:
#    openssl NO existe en PyPI como paquete pip instalable.
#    Buildozer intentaba "pip install openssl" → falla con:
#    "ERROR: No matching distribution found for openssl"
#    p4a compila OpenSSL automáticamente como receta nativa.
#    No necesitas declararlo: kivy, requests y yt-dlp lo jalan.
#
#  NUEVOS EN V13:
#    · pyjnius   → acceso a la API de Android (capturar Intent)
#    · plyer     → notificaciones cruzadas (Android/Desktop)
#
#  RECETAS NATIVAS p4a (no son paquetes pip):
#    · python3, kivy, kivymd, pyjnius → compilados por p4a
#    · pillow (Pillow) → receta nativa p4a
#    · setuptools → receta nativa p4a
#
#  PAQUETES PyPI (instalados por pip dentro del APK):
#    · yt-dlp, instaloader, certifi, urllib3,
#      charset-normalizer, requests, plyer
# ──────────────────────────────────────────────────────────────────
requirements = python3,\
               kivy==2.2.1,\
               kivymd==1.2.0,\
               pyjnius,\
               plyer,\
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

# ── Permisos V13 ──────────────────────────────────────────────────
#  INTERNET                : descargar contenido + cookies de GitHub
#  READ_EXTERNAL_STORAGE   : leer archivos en /sdcard/
#  WRITE_EXTERNAL_STORAGE  : escribir en /storage/emulated/0/Download/
#  MANAGE_EXTERNAL_STORAGE : acceso completo en Android 11+
#  POST_NOTIFICATIONS      : NUEVO — Android 13+ (API 33) requiere
#                            este permiso para mostrar notificaciones
# ──────────────────────────────────────────────────────────────────
android.permissions = INTERNET,\
                      READ_EXTERNAL_STORAGE,\
                      WRITE_EXTERNAL_STORAGE,\
                      MANAGE_EXTERNAL_STORAGE,\
                      POST_NOTIFICATIONS

android.accept_sdk_license = True

android.gradle_dependencies =
android.enable_androidx = True

p4a.bootstrap = sdl2

android.release_artifact = apk
android.debug = True

android.activity_class_name = org.kivy.android.PythonActivity
android.manifest.android_windowSoftInputMode = adjustResize

# ── Intent Filter V13 — Receptor de enlaces compartidos ───────────
#  Hace que CyberLoad aparezca en el menú "Compartir" de Android.
#  Cuando el usuario comparte una URL desde Instagram, TikTok,
#  Facebook, YouTube → la app captura el texto y muestra el panel
#  flotante de descarga rápida (PantallaFlotante en main.py).
#
#  Formato: XML compacto (una línea) para evitar errores de parsing
#  en el parser INI de buildozer con valores multilínea.
# ──────────────────────────────────────────────────────────────────
android.manifest.intent_filters = <intent-filter><action android:name="android.intent.action.SEND" /><category android:name="android.intent.category.DEFAULT" /><data android:mimeType="text/plain" /></intent-filter>


[ios]
# iOS no aplica.
