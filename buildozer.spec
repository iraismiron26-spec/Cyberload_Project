# ╔══════════════════════════════════════════════════════════════════╗
# ║  buildozer.spec — CYBERLOAD MSTL v1.3                          ║
# ║  Generado para: KivyMD + yt-dlp + Instaloader + Pillow         ║
# ║  Target: Android 8+ (API 26+) · Sin FFmpeg · APK lista         ║
# ╚══════════════════════════════════════════════════════════════════╝

[app]

# ── Identidad de la App ────────────────────────────────────────────
title = Cyberload MSTL
package.name = cyberload
package.domain = org.mstl

# ── Versión ────────────────────────────────────────────────────────
version = 1.3

# ── Fuentes de código ─────────────────────────────────────────────
# Incluye main.py + mstl_logic.py + mstl_unified_v1_3.py
# y todos los assets necesarios desde la raíz del proyecto.
source.dir = .
source.include_exts = py,png,jpg,json,txt
source.include_patterns = assets/*,fonts/*,icon.png

# ── Punto de entrada ──────────────────────────────────────────────
# main.py es el entry point estándar de Kivy/KivyMD.
entrypoint = main.py

# ── Icono y Presentación ──────────────────────────────────────────
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png
presplash.lottie = False

# ── Orientación ───────────────────────────────────────────────────
# portrait: descargador → uso con una mano en móvil.
orientation = portrait

# ── Arquitecturas objetivo ────────────────────────────────────────
# arm64-v8a  : dispositivos modernos (Android 8+)
# armeabi-v7a: compatibilidad con dispositivos de 32-bit más viejos
android.archs = arm64-v8a, armeabi-v7a

# ──────────────────────────────────────────────────────────────────
#  REQUIREMENTS
#  Análisis de imports realizados en los 3 archivos del proyecto:
#
#  main.py         → kivy, kivymd, threading (stdlib)
#  mstl_logic.py   → yt_dlp, instaloader, PIL (pillow),
#                    os/re/json/random/string/urllib/
#                    datetime/pathlib/http.cookiejar (stdlib)
#  mstl_unified    → mismos que mstl_logic.py
#
#  Notas importantes:
#  · NO se incluye ffmpeg (el motor opera sin él — diseño intencional)
#  · requests no se importa directamente; urllib se usa en su lugar
#  · certifi y urllib3 son requeridos por yt-dlp/instaloader en Android
#  · setuptools necesario para que pip resuelva dependencias en build
# ──────────────────────────────────────────────────────────────────
requirements = python3,\
               kivy==2.2.1,\
               kivymd==1.2.0,\
               yt-dlp,\
               instaloader,\
               pillow,\
               certifi,\
               urllib3,\
               charset-normalizer,\
               requests,\
               setuptools

# ── Servicios en segundo plano ────────────────────────────────────
# Sin servicios de fondo declarados: la descarga usa threading
# nativo de Python dentro del proceso principal de la app.
# services =

# ── Garden ────────────────────────────────────────────────────────
# No se usa ningún módulo externo de Kivy Garden.
# garden_requirements =


[buildozer]

# ── Log ───────────────────────────────────────────────────────────
# 2 = verbose (recomendado para depurar en Google Colab)
log_level = 2

# ── Caché ─────────────────────────────────────────────────────────
warn_on_root = 1


[android]

# ── APIs Android ──────────────────────────────────────────────────
# minapi 26 = Android 8.0 Oreo  (requisito mínimo solicitado)
# api     33 = Android 13        (target estable y ampliamente soportado)
# ndk     25b = versión estable recomendada para Python/Kivy builds
android.minapi = 26
android.api = 33
android.ndk = 25b

# ── SDK ───────────────────────────────────────────────────────────
# Buildozer descarga automáticamente el SDK si no existe.
# android.sdk = 20
# android.sdk_path =
# android.ndk_path =
# android.ant_path =

# ── Build tools ───────────────────────────────────────────────────
android.build_tools_version = 33.0.2

# ── Permisos ──────────────────────────────────────────────────────
# INTERNET              : descargas en red (yt-dlp, instaloader)
# WRITE_EXTERNAL_STORAGE: guardar en /storage/emulated/0/Download/
# READ_EXTERNAL_STORAGE : leer cookies.txt en /sdcard/
#
# NOTA Android 10+ (API 29+): WRITE_EXTERNAL_STORAGE queda
# restringido en Android 11+. Si el APK se distribuye en Play
# Store para API >= 30, evaluar agregar:
#   MANAGE_EXTERNAL_STORAGE (requiere declaración especial)
android.permissions = INTERNET,\
                      WRITE_EXTERNAL_STORAGE,\
                      READ_EXTERNAL_STORAGE

# ── Accept SDK License ────────────────────────────────────────────
# Acepta automáticamente las licencias del Android SDK en Colab.
android.accept_sdk_license = True

# ── Gradle ────────────────────────────────────────────────────────
# Versión estable compatible con Buildozer moderno.
android.gradle_dependencies =

# Habilitar AndroidX (requerido por KivyMD 1.x)
android.enable_androidx = True

# ── Python for Android (p4a) ──────────────────────────────────────
# Bootstrap SDL2 = el único soporte oficial de Kivy en Android.
p4a.bootstrap = sdl2

# Branch estable de python-for-android.
# Descomenta si necesitas una revisión específica:
# p4a.branch = master

# ── Release / Debug ───────────────────────────────────────────────
# Para Colab/pruebas usar 'debug'. Para distribución usar 'release'.
android.release_artifact = apk
android.debug = True

# ── Orientación de la actividad ───────────────────────────────────
android.activity_class_name = org.kivy.android.PythonActivity

# ── Meta-datos del manifest ───────────────────────────────────────
# Fuerza portrait via manifest si orientation = portrait arriba
# android.manifest.orientation = portrait

# ── Opciones adicionales del manifest ─────────────────────────────
# Evita crash al rotar pantalla durante una descarga activa.
android.manifest.android_windowSoftInputMode = adjustResize


[ios]
# ── iOS (NO aplica a este proyecto) ──────────────────────────────
# ios.kivy_ios_url = https://github.com/kivy/kivy-ios
# ios.kivy_ios_branch = master
# ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
# ios.ios_deploy_branch = 1.7.0
# ios.codesign.allowed = false


# ──────────────────────────────────────────────────────────────────
#  INSTRUCCIONES PARA GOOGLE COLAB
#  ─────────────────────────────────────────────────────────────────
#  1. Sube a Colab: main.py, mstl_logic.py,
#                   mstl_unified_v1_3.py, icon.png, buildozer.spec
#
#  2. Instala buildozer:
#       !pip install buildozer
#       !pip install cython==0.29.33
#
#  3. Instala dependencias del sistema:
#       !apt-get install -y \
#           python3-pip build-essential git \
#           ffmpeg libsdl2-dev libsdl2-image-dev \
#           libsdl2-mixer-dev libsdl2-ttf-dev \
#           libportmidi-dev libswscale-dev \
#           libavformat-dev libavcodec-dev \
#           zlib1g-dev openjdk-17-jdk \
#           libgstreamer1.0 gstreamer1.0-plugins-base \
#           gstreamer1.0-plugins-good
#
#  4. Construye la APK (debug):
#       !buildozer -v android debug
#
#  5. La APK estará en:  ./bin/cyberload-1.3-armeabi-v7a-debug.apk
#                         ./bin/cyberload-1.3-arm64-v8a-debug.apk
#
#  6. Descárgala desde Colab:
#       from google.colab import files
#       import glob
#       for apk in glob.glob('bin/*.apk'):
#           files.download(apk)
#
#  NOTA: El primer build puede tardar 20-40 minutos en Colab
#        por la compilación de python-for-android desde cero.
#        Los builds siguientes usan caché y son más rápidos.
# ──────────────────────────────────────────────────────────────────
