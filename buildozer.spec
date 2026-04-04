# ╔══════════════════════════════════════════════════════════════════╗
# ║  buildozer.spec — CYBERLOAD MSTL v1.5                          ║
# ║  Generado para: KivyMD + yt-dlp + Instaloader + Pillow         ║
# ║  Target: Android 8+ (API 26+) · Sin FFmpeg · APK lista         ║
# ║                                                                  ║
# ║  Cambios v1.5:                                                  ║
# ║  · version bump 1.4 → 1.5 (fuerza reinstalación limpia)        ║
# ║  · requirements verificados: python3, kivy, kivymd, yt-dlp,    ║
# ║    instaloader, requests, urllib3, certifi, openssl todos OK    ║
# ║  · permisos verificados: INTERNET, READ/WRITE_EXTERNAL,        ║
# ║    MANAGE_EXTERNAL_STORAGE todos presentes                     ║
# ╚══════════════════════════════════════════════════════════════════╝

[app]

# ── Identidad de la App ────────────────────────────────────────────
title = Cyberload MSTL
package.name = cyberload
package.domain = org.mstl

# ── Versión ────────────────────────────────────────────────────────
# IMPORTANTE: Subir la versión fuerza a Android a aceptar
# la instalación sobre la APK anterior sin necesidad de desinstalar.
version = 1.5

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
#  REQUIREMENTS v1.5
#
#  Lista completa verificada — NINGÚN paquete crítico falta:
#
#  · python3          → intérprete base. OBLIGATORIO como primer ítem.
#  · kivy==2.2.1      → framework UI. Versión más estable con p4a.
#  · kivymd==1.2.0    → widgets Material Design. Compatible con kivy 2.2.1.
#  · openssl          → receta NATIVA de p4a. Compila OpenSSL para ARM.
#                       DEBE ir antes de requests/yt-dlp en el orden,
#                       ya que urllib3 y certifi dependen de él en Android.
#  · yt-dlp           → motor de descarga YouTube/TikTok/Facebook/+.
#  · instaloader      → motor de descarga Instagram.
#  · pillow           → conversión webp→jpg y procesamiento de imágenes.
#  · certifi          → certificados CA para HTTPS. Requerido por requests.
#  · urllib3          → cliente HTTP de bajo nivel. Dependencia de requests.
#  · charset-normalizer → detección de encoding. Dependencia de requests.
#  · requests         → cliente HTTP de alto nivel. Usado por instaloader.
#  · setuptools       → necesario para que p4a instale paquetes correctamente.
#
#  NOTAS TÉCNICAS:
#  · Cython 0.29.x (NO 3.x) requerido por p4a — se controla en el
#    workflow de GitHub Actions, no aquí.
#  · ffmpeg NO incluido intencionalmente: yt-dlp opera sin él usando
#    formatos pre-combinados (diseño de mstl_logic.py).
#  · No especificar versión en yt-dlp, instaloader, pillow, certifi,
#    urllib3, requests → p4a usará la última versión compatible.
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
#  MANAGE_EXTERNAL_STORAGE  : acceso completo al almacenamiento en
#                             Android 11+ (API 30+). Necesario para
#                             acceder a /storage/emulated/0/Download/
#                             sin las restricciones de Scoped Storage.
#                             El usuario debe concederlo manualmente en:
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
