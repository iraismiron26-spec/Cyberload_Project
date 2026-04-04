# ╔══════════════════════════════════════════════════════════════════╗
# ║  buildozer.spec — CYBERLOAD MSTL v1.4                          ║
# ║  Generado para: KivyMD + yt-dlp + Instaloader + Pillow         ║
# ║  Target: Android 8+ (API 26+) · Sin FFmpeg · APK lista         ║
# ║                                                                  ║
# ║  Cambios v1.4:                                                  ║
# ║  · MANAGE_EXTERNAL_STORAGE añadido a permisos                  ║
# ║  · openssl añadido a requirements (receta nativa p4a)           ║
# ║  · version bump 1.3 → 1.4 para forzar reinstalación limpia     ║
# ╚══════════════════════════════════════════════════════════════════╝

[app]

# ── Identidad de la App ────────────────────────────────────────────
title = Cyberload MSTL
package.name = cyberload
package.domain = org.mstl

# ── Versión ────────────────────────────────────────────────────────
# IMPORTANTE: Subir la versión fuerza a Android a aceptar
# la instalación sobre la APK anterior sin necesidad de desinstalar.
version = 1.4

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
# arm64-v8a  : dispositivos modernos (Android 8+)
# armeabi-v7a: compatibilidad con dispositivos de 32-bit más viejos
android.archs = arm64-v8a, armeabi-v7a

# ──────────────────────────────────────────────────────────────────
#  REQUIREMENTS v1.4
#
#  Cambios respecto a v1.3:
#  · openssl  → NUEVO. Receta nativa de p4a que compila OpenSSL
#               para ARM. Sin ella, requests/urllib3/certifi fallan
#               silenciosamente en Android al intentar conexiones
#               HTTPS (yt-dlp e instaloader dependen de HTTPS).
#
#  Notas:
#  · kivy==2.2.1 y kivymd==1.2.0 son las versiones más estables
#    con p4a en 2024-2026. No actualizar sin pruebas.
#  · Cython 0.29.x (no 3.x) requerido por p4a — se controla
#    en el workflow de GitHub Actions, no aquí.
#  · ffmpeg NO incluido intencionalmente: yt-dlp opera sin él
#    usando formatos pre-combinados (diseño de mstl_logic.py).
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

# ── Log ───────────────────────────────────────────────────────────
# 2 = verbose (recomendado para depurar en GitHub Actions / Colab)
log_level = 2

warn_on_root = 1


[android]

# ── APIs Android ──────────────────────────────────────────────────
# minapi 26 = Android 8.0 Oreo  (requisito mínimo)
# api     33 = Android 13        (target estable)
# ndk     25b = versión estable recomendada para Python/Kivy builds
android.minapi = 26
android.api = 33
android.ndk = 25b

# ── Build tools ───────────────────────────────────────────────────
android.build_tools_version = 33.0.2

# ── Permisos ──────────────────────────────────────────────────────
#
#  INTERNET                 : conexión de red para yt-dlp e instaloader
#  READ_EXTERNAL_STORAGE    : leer cookies.txt desde /sdcard/
#  WRITE_EXTERNAL_STORAGE   : escribir archivos en /Download/
#  MANAGE_EXTERNAL_STORAGE  : NUEVO en v1.4
#                             Necesario en Android 11+ (API 30+) para
#                             acceder a /storage/emulated/0/Download/
#                             sin las restricciones de Scoped Storage.
#                             Se declara en el Manifest pero el usuario
#                             debe concederlo manualmente en:
#                             Ajustes → Apps → Cyberload → Permisos
#                             → Archivos y medios → Permitir gestión
#
#  NOTA: main.py solicita estos permisos dinámicamente en on_start()
#        usando android.permissions.request_permissions().
# ──────────────────────────────────────────────────────────────────
android.permissions = INTERNET,\
                      READ_EXTERNAL_STORAGE,\
                      WRITE_EXTERNAL_STORAGE,\
                      MANAGE_EXTERNAL_STORAGE

# ── Accept SDK License ────────────────────────────────────────────
android.accept_sdk_license = True

# ── Gradle ────────────────────────────────────────────────────────
android.gradle_dependencies =

# Habilitar AndroidX (requerido por KivyMD 1.x)
android.enable_androidx = True

# ── Python for Android (p4a) ──────────────────────────────────────
# Bootstrap SDL2 = soporte oficial de Kivy en Android.
p4a.bootstrap = sdl2

# ── Release / Debug ───────────────────────────────────────────────
android.release_artifact = apk
android.debug = True

# ── Orientación de la actividad ───────────────────────────────────
android.activity_class_name = org.kivy.android.PythonActivity

# ── Opciones adicionales del manifest ─────────────────────────────
android.manifest.android_windowSoftInputMode = adjustResize


[ios]
# iOS no aplica a este proyecto.
