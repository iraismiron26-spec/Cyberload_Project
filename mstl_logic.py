#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════╗
# ║  MSTL LOGIC — Módulo de Descarga                        ║
# ║  Basado en MSTL UNIFIED v1.3                            ║
# ║  Instagram · TikTok · YouTube · Facebook · +            ║
# ║  Motor: Instaloader + yt-dlp | Sin FFmpeg | Pydroid 3   ║
# ║  API pública: descargar(url, callback=None)             ║
# ╚══════════════════════════════════════════════════════════╝

import yt_dlp
import os
import re
import json
import random
import string
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path


# ══════════════════════════════════════════════════════════
#   CONFIGURACIÓN Y RUTAS FIJAS
#   CRÍTICO: /storage/emulated/0/ es la ruta real en Android.
#   /sdcard/ es un symlink que Pydroid 3 no siempre resuelve
#   con permisos de escritura correctos → archivos "fantasma".
# ══════════════════════════════════════════════════════════
RUTA_DOWNLOADS = '/storage/emulated/0/Download/'
COOKIES_PATH   = '/sdcard/cookies.txt'
HISTORIAL_PATH = '/storage/emulated/0/Download/mstl_historial.json'

# Garantizar carpeta destino antes de cualquier operación
os.makedirs(RUTA_DOWNLOADS, exist_ok=True)

# ── Colores ANSI (terminal) ───────────────────────────────
R, BOLD, GREEN, GOLD, RED, YELLOW, CYAN, GRAY = (
    "\033[0m", "\033[1m", "\033[92m", "\033[38;5;220m",
    "\033[91m", "\033[93m", "\033[96m", "\033[90m"
)

def c(texto, *estilos):
    return "".join(estilos) + str(texto) + R

# Extensiones de imagen para detección en entradas yt-dlp
IMAGE_EXTS = {'jpg', 'jpeg', 'png', 'webp'}

# outtmpl canónica — Regla de Oro:
# yt-dlp resuelve %(title)s y %(id)s desde los metadatos reales.
# NUNCA construir el nombre manualmente con f-strings de Python.
OUTTMPL_GOLD = os.path.join(RUTA_DOWNLOADS, '%(title).100s [%(id)s].%(ext)s')


# ══════════════════════════════════════════════════════════
#   HELPER CENTRAL: NOTIFICACIÓN DUAL — Terminal + GUI
#
#   _notify() emite mensajes a DOS destinos simultáneamente:
#     1. Terminal → msg_raw  (con colores ANSI)
#     2. GUI      → clean_msg (texto limpio, sin ANSI)
#
#   Si clean_msg es None, se extrae automáticamente de
#   msg_raw eliminando todos los códigos ANSI con regex.
#
#   TODOS los motores usan esta función para no duplicar
#   la lógica de notificación.
# ══════════════════════════════════════════════════════════

def _notify(msg_raw, clean_msg=None, callback=None):
    """
    Imprime en terminal y envía mensaje limpio a la GUI.

    Parámetros:
        msg_raw   (str)            : Mensaje para terminal (puede contener ANSI)
        clean_msg (str | None)     : Mensaje para GUI. Si None, se extrae de msg_raw.
        callback  (callable | None): función(str) para actualizar la interfaz Kivy
    """
    print(msg_raw)
    if callback:
        if clean_msg is None:
            clean_msg = re.sub(r'\033\[[0-9;]*m', '', msg_raw).strip()
        if clean_msg:
            callback(clean_msg)


# ══════════════════════════════════════════════════════════
#   UTILIDADES
# ══════════════════════════════════════════════════════════

def gen_id(n=4):
    """Genera un ID aleatorio de N caracteres alfanuméricos."""
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def sanitizar_nombre(nombre):
    """Elimina caracteres ilegales en rutas de archivo Android."""
    nombre = re.sub(r'[\\/*?"<>|\n\r\t]', "", str(nombre))
    return nombre.strip()[:100]


def obtener_espacio_libre():
    try:
        stat = os.statvfs(RUTA_DOWNLOADS)
        return f"{(stat.f_bavail * stat.f_frsize) / (1024**3):.2f} GB"
    except:
        return "---"


def verificar_limite_espacio(callback=None):
    """
    Barrera de seguridad: al menos 500 MB libres antes de descargar.
    Usa RUTA_DOWNLOADS real para que statvfs lea el filesystem correcto.
    """
    try:
        stat = os.statvfs(RUTA_DOWNLOADS)
        mb = (stat.f_bavail * stat.f_frsize) / (1024 ** 2)
        if mb < 500:
            msg = f"🚨 ¡ESPACIO INSUFICIENTE! Solo {mb:.1f} MB libres (mínimo 500 MB)."
            _notify(f"\n  {c(msg, RED, BOLD)}", msg, callback)
            return False
        return True
    except Exception as e:
        _notify(
            f"  {c(f'⚠️  No se pudo verificar espacio: {e}', YELLOW)}",
            f"⚠️ No se pudo verificar espacio: {e}",
            callback
        )
        return True  # En caso de error, dejar continuar


def guardar_historial(titulo, url):
    """Guarda la entrada en el historial JSON. Conserva las últimas 20."""
    historial = []
    try:
        if os.path.exists(HISTORIAL_PATH):
            with open(HISTORIAL_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    historial = data
        historial.append({
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "titulo": str(titulo)[:80],
            "url": url
        })
        with open(HISTORIAL_PATH, 'w', encoding='utf-8') as f:
            json.dump(historial[-20:], f, indent=4, ensure_ascii=False)
    except:
        pass


def detectar_plataforma(url):
    """
    Retorna: 'instagram' | 'tiktok' | 'general'
    """
    u = url.lower()
    if 'instagram.com' in u:
        return 'instagram'
    if 'tiktok.com' in u or 'vm.tiktok.com' in u:
        return 'tiktok'
    return 'general'


def _ruta_segura(directorio, filename):
    """
    Construye la ruta completa. Si el archivo ya existe,
    añade sufijo de 4 chars para evitar sobreescritura.
    """
    ruta = os.path.join(directorio, filename)
    if os.path.exists(ruta):
        base, ext = os.path.splitext(ruta)
        ruta = f"{base}_{gen_id(4)}{ext}"
    return ruta


def _convertir_webp_a_jpg(filepath, callback=None):
    """
    Convierte .webp → .jpg con Pillow si está instalado.
    Sin Pillow, conserva el .webp original sin error.
    """
    if not filepath.lower().endswith('.webp'):
        return filepath
    try:
        from PIL import Image
        jpg_path = filepath[:-5] + '.jpg'
        Image.open(filepath).convert('RGB').save(jpg_path, 'JPEG', quality=95)
        os.remove(filepath)
        _notify(
            f"  {c('🔄 .webp convertido a .jpg con Pillow.', CYAN)}",
            "🔄 .webp convertido a .jpg",
            callback
        )
        return jpg_path
    except Exception:
        return filepath


def _cookies_ok(callback=None):
    """
    Verifica que el archivo de cookies exista y lo devuelve (o None).
    Notifica aviso tanto en terminal como en GUI.
    """
    if os.path.exists(COOKIES_PATH):
        return COOKIES_PATH
    _notify(
        f"  {c('⚠️  cookies.txt no encontrado en /sdcard/ — posible bloqueo.', YELLOW)}",
        "⚠️ cookies.txt no encontrado — posible bloqueo.",
        callback
    )
    return None


# ══════════════════════════════════════════════════════════
#   FIX v1.3 — ACTUALIZADOR DE FECHAS
#
#   Problema: Instaloader y yt-dlp preservan la fecha de
#   publicación original del post vía os.utime interno.
#   Esto hace que las fotos aparezcan "enterradas" al final
#   de la galería de Android (ordenada por fecha).
#
#   Solución: Después de cada descarga, actualizar atime y
#   mtime de todos los archivos de la sesión al momento
#   presente con os.utime(ruta, None).
#
#   La sesión se identifica por session_id en el nombre
#   del archivo → solo se tocan los archivos recién
#   descargados, nunca archivos preexistentes.
# ══════════════════════════════════════════════════════════

def actualizar_fechas_archivos(session_id, callback=None):
    """
    Recorre RUTA_DOWNLOADS y actualiza atime+mtime al tiempo
    actual en todos los archivos de esta sesión.

    Parámetros:
        session_id (str)           : ID de 4 chars de la sesión activa.
        callback   (callable|None) : función(str) para notificar a la GUI.
    """
    actualizados = 0
    try:
        for f in os.listdir(RUTA_DOWNLOADS):
            if session_id not in f:
                continue
            ruta_f = os.path.join(RUTA_DOWNLOADS, f)
            if not os.path.isfile(ruta_f):
                continue
            os.utime(ruta_f, None)  # None → atime y mtime = AHORA
            actualizados += 1

        if actualizados:
            msg = f"🕐 Fechas actualizadas: {actualizados} archivo(s) → timestamp = AHORA"
            _notify(
                f"  {c(msg, GREEN)}",
                msg,
                callback
            )
    except Exception as e:
        _notify(
            f"  {c(f'⚠️  No se pudo actualizar fechas ({e})', YELLOW)}",
            f"⚠️ No se pudo actualizar fechas: {e}",
            callback
        )


# ══════════════════════════════════════════════════════════
#   DESCARGA HTTP DIRECTA — urllib puro, sin requests
#   Para fotos CDN de TikTok e Instagram.
# ══════════════════════════════════════════════════════════

def _descargar_http(src_url, filepath, referer=""):
    """
    Descarga directa con User-Agent de Chrome Android.
    """
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Linux; Android 12; SM-A525F) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/124.0.0.0 Mobile Safari/537.36'
        ),
        'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
    }
    if referer:
        headers['Referer'] = referer
    try:
        req = urllib.request.Request(src_url, headers=headers)
        with urllib.request.urlopen(req, timeout=90) as resp:
            with open(filepath, 'wb') as f:
                f.write(resp.read())
        return True
    except Exception as e:
        print(f"  {c(f'⚠️  Descarga HTTP directa falló: {e}', YELLOW)}")
        return False


# ══════════════════════════════════════════════════════════
#   MOTOR INSTAGRAM  (Instaloader primario + yt-dlp fallback)
#
#   NOMBRES:
#     filename_pattern = '{profile}_{shortcode}_{session_id}'
#     Instaloader añade _1, _2... automáticamente en carruseles.
#
#   RUTA:
#     dirname_pattern  = RUTA_DOWNLOADS  → sin subcarpetas
#     target           = Path(RUTA_DOWNLOADS) → fuerza directorio
#
#   POST-DESCARGA:
#     → actualizar_fechas_archivos(session_id, callback) [v1.3 FIX]
#     → Verificación física con session_id en os.listdir()
#     → Limpieza de .json.xz, .txt, .xz y JPGs < 50 KB
# ══════════════════════════════════════════════════════════

def motor_instagram(url, callback=None):
    if not verificar_limite_espacio(callback):
        return

    _notify(
        f"\n  {c('📷 Motor Instagram activado (Instaloader)...', CYAN)}",
        "📷 Motor Instagram activado...",
        callback
    )

    cookies_path = _cookies_ok(callback)

    try:
        import instaloader

        session_id = gen_id(4)

        # ── Instaloader configurado ────────────────────────────
        # dirname_pattern: directorio destino sin subcarpetas.
        # filename_pattern: {profile}_{shortcode}_{session_id}
        #   → carrusel IG añade automáticamente _1, _2, _3
        # download_videos=True: CRÍTICO para carruseles mixtos
        # ──────────────────────────────────────────────────────
        L = instaloader.Instaloader(
            dirname_pattern              = RUTA_DOWNLOADS,
            filename_pattern             = '{profile}_{shortcode}_' + session_id,
            download_videos              = True,
            download_video_thumbnails    = False,
            save_metadata                = False,
            post_metadata_txt_pattern    = "",
            quiet                        = True,
        )

        # ── Inyectar cookies Netscape ──────────────────────────
        if cookies_path:
            try:
                import http.cookiejar
                jar = http.cookiejar.MozillaCookieJar()
                jar.load(cookies_path, ignore_discard=True, ignore_expires=True)
                L.context._session.cookies.update(jar)
                print(f"  {c('🍪 Cookies inyectadas en Instaloader.', GREEN)}")
            except Exception as ce:
                print(f"  {c(f'⚠️  No se pudieron cargar cookies: {ce}', YELLOW)}")

        # ── Extraer shortcode ──────────────────────────────────
        match = re.search(r'/(?:p|reel|reels)/([A-Za-z0-9_-]+)', url)
        if not match:
            raise ValueError("No se pudo extraer el shortcode de la URL de Instagram.")
        shortcode = match.group(1)

        print(f"  {c('🔍 Shortcode:', GOLD)} {shortcode}")
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        _notify(
            f"  {c(f'📥 Descargando post de @{post.owner_username} ({post.typename})...', CYAN)}",
            f"📥 Descargando @{post.owner_username} ({post.typename})...",
            callback
        )

        # ── Descarga con target como Path absoluto ─────────────
        # Path() es necesario: string → Instaloader crea subcarpeta.
        L.download_post(post, target=Path(RUTA_DOWNLOADS))

        # ── v1.3 FIX: Actualizar timestamps al tiempo presente ─
        # Sobreescribe la fecha de publicación original que
        # Instaloader aplica, para que los archivos aparezcan
        # primero en la galería de Android (orden por fecha desc).
        actualizar_fechas_archivos(session_id, callback)

        # ── Verificación física ────────────────────────────────
        archivos_sesion = [
            f for f in os.listdir(RUTA_DOWNLOADS)
            if session_id in f
        ]

        if not archivos_sesion:
            _notify(
                f"\n  {c('⚠️  Verificación física: 0 archivos. Activando respaldo yt-dlp...', YELLOW)}",
                "⚠️ 0 archivos encontrados → activando yt-dlp...",
                callback
            )
            motor_general(url, callback=callback)
            return

        # ── Limpieza post-descarga ─────────────────────────────
        # Solo toca archivos de ESTA sesión (contienen session_id).
        # Elimina: metadatos .json.xz / .xz / .txt
        #          miniaturas basura < 50 KB
        eliminados = 0
        for f in os.listdir(RUTA_DOWNLOADS):
            if session_id not in f:
                continue
            ruta_f = os.path.join(RUTA_DOWNLOADS, f)
            if not os.path.isfile(ruta_f):
                continue
            if f.endswith((".json.xz", ".xz", ".txt")):
                os.remove(ruta_f)
                eliminados += 1
            elif f.endswith(".jpg") and os.path.getsize(ruta_f) < 50000:
                os.remove(ruta_f)
                eliminados += 1

        guardados = [
            f for f in os.listdir(RUTA_DOWNLOADS)
            if session_id in f
        ]

        msg_ok = f"✅ Instagram: {len(guardados)} archivo(s) guardado(s), {eliminados} temporales eliminados"
        _notify(
            f"\n  {c(msg_ok, GREEN, BOLD)}\n  {c('📂 Ruta:', GOLD)} {RUTA_DOWNLOADS}",
            msg_ok,
            callback
        )
        for nombre in guardados:
            print(f"  {c('  ✔', GREEN)} {nombre}")

        guardar_historial(f"IG @{post.owner_username} [{shortcode}]", url)
        print(f"\n  {c('✅ Motor Instagram finalizado.', GREEN, BOLD)}")

    except ImportError:
        _notify(
            f"\n  {c('❌ Instaloader no instalado → pip install instaloader', RED)}\n"
            f"  {c('🔄 Activando respaldo yt-dlp...', CYAN)}",
            "❌ Instaloader no instalado. Usando yt-dlp como respaldo...",
            callback
        )
        motor_general(url, callback=callback)

    except Exception as e:
        _notify(
            f"\n  {c(f'⚠️  Instaloader falló ({type(e).__name__}): {e}', YELLOW)}\n"
            f"  {c('🔄 Activando respaldo yt-dlp...', CYAN)}",
            f"⚠️ Instaloader falló ({type(e).__name__}) → usando yt-dlp...",
            callback
        )
        motor_general(url, callback=callback)


# ══════════════════════════════════════════════════════════
#   MOTOR TIKTOK
#
#   Carrusel de fotos:
#     Nombre: {id}_{session_id}_{num:03d}.{ext}
#     Descarga HTTP directa con urllib (sin yt-dlp para imágenes)
#     v1.3 FIX: os.utime(fpath, None) post-descarga HTTP
#
#   Video único / entries de video:
#     outtmpl: OUTTMPL_GOLD → %(title).100s [%(id)s].%(ext)s
#     v1.3 FIX: 'updatetime': False en todos los opts yt-dlp
# ══════════════════════════════════════════════════════════

def motor_tiktok(url, callback=None):
    if not verificar_limite_espacio(callback):
        return

    _notify(
        f"\n  {c('🎵 Motor TikTok activado (yt-dlp)...', CYAN)}",
        "🎵 Motor TikTok activado...",
        callback
    )
    session_id = gen_id(4)
    cookies    = _cookies_ok(callback)

    try:
        opts_info = {
            'quiet':              True,
            'no_warnings':        True,
            'nocheckcertificate': True,
            'cookiefile':         cookies,
        }
        with yt_dlp.YoutubeDL(opts_info) as ydl:
            info = ydl.extract_info(url, download=False)

        entries = info.get('entries')

        # ══════════════════════════════════════════════════
        # CASO A: CARRUSEL / SLIDESHOW
        # ══════════════════════════════════════════════════
        if entries:
            entries_list = list(entries)
            total = len(entries_list)
            _notify(
                f"\n  📦 TikTok: {total} elemento(s) detectados. Descargando en {RUTA_DOWNLOADS}...",
                f"📦 TikTok: {total} elemento(s) detectados. Descargando...",
                callback
            )

            ok = fail = 0
            for i, entry in enumerate(entries_list, 1):
                try:
                    eid     = sanitizar_nombre(entry.get('id', f"{session_id}_{i:03d}"))
                    ext_raw = (entry.get('ext') or 'bin').lower()
                    eurl    = (
                        entry.get('url') or
                        entry.get('webpage_url') or
                        entry.get('original_url') or ''
                    )

                    # ── Foto directa desde CDN de TikTok ──────
                    if ext_raw in IMAGE_EXTS and eurl.startswith('http'):
                        fname = f"{eid}_{session_id}_{i:03d}.{ext_raw}"
                        fpath = _ruta_segura(RUTA_DOWNLOADS, fname)

                        _notify(
                            f"  {c(f'🖼️  [{i}/{total}] {os.path.basename(fpath)}', YELLOW)}",
                            f"🖼️ [{i}/{total}] Descargando imagen...",
                            callback
                        )
                        if _descargar_http(eurl, fpath, referer="https://www.tiktok.com/"):
                            fpath = _convertir_webp_a_jpg(fpath, callback)
                            # v1.3 FIX: Timestamp al tiempo presente
                            os.utime(fpath, None)
                            print(c("  ✅ OK", GREEN))
                            ok += 1
                        else:
                            print(c("  ❌ Falló", RED))
                            fail += 1

                    # ── Entry de video → yt-dlp con outtmpl Gold ─
                    else:
                        opts_item = {
                            'format':             'best[ext=mp4]/best',
                            'outtmpl':            OUTTMPL_GOLD,
                            'quiet':              True,
                            'no_warnings':        True,
                            'nocheckcertificate': True,
                            'cookiefile':         cookies,
                            'noplaylist':         True,
                            'updatetime':         False,  # v1.3 FIX: no usar fecha del servidor
                        }
                        etit = sanitizar_nombre(entry.get('title', eid))
                        _notify(
                            f"  {c(f'🎬 [{i}/{total}] {etit[:45]}', YELLOW)}",
                            f"🎬 [{i}/{total}] {etit[:40]}...",
                            callback
                        )
                        with yt_dlp.YoutubeDL(opts_item) as ydl2:
                            ydl2.download([eurl or url])
                        print(c("  ✅ OK", GREEN))
                        ok += 1

                except Exception as ei:
                    print(f"\n  {c(f'⚠️  Error en item {i}: {ei}', YELLOW)}")
                    if callback:
                        callback(f"⚠️ Error en item {i}/{total}: {type(ei).__name__}")
                    fail += 1

            msg_ok = f"🎉 TikTok: {ok} guardado(s), {fail} error(es)"
            _notify(f"\n  {c(msg_ok, GREEN, BOLD)}", msg_ok, callback)
            guardar_historial(f"TikTok Carrusel ({ok}/{total})", url)

        # ══════════════════════════════════════════════════
        # CASO B: VIDEO ÚNICO
        # ══════════════════════════════════════════════════
        else:
            titulo = info.get('title', 'TikTok_Video')
            _notify(
                f"\n  📦 1 video TikTok. Descargando en {RUTA_DOWNLOADS}...",
                "📦 1 video TikTok detectado. Descargando...",
                callback
            )

            opts_video = {
                'format':             'best[ext=mp4]/best',
                'outtmpl':            OUTTMPL_GOLD,
                'quiet':              False,
                'no_warnings':        True,
                'nocheckcertificate': True,
                'cookiefile':         cookies,
                'noplaylist':         True,
                'updatetime':         False,  # v1.3 FIX
            }
            with yt_dlp.YoutubeDL(opts_video) as ydl:
                ydl.download([url])

            msg_ok = "✅ Video TikTok guardado."
            _notify(
                f"\n  {c(msg_ok, GREEN, BOLD)}\n  {c('📂 Ruta:', GOLD)} {RUTA_DOWNLOADS}",
                msg_ok,
                callback
            )
            guardar_historial(sanitizar_nombre(titulo), url)

    except Exception as e:
        msg_err = f"❌ Error en motor TikTok ({type(e).__name__}): {e}"
        _notify(f"\n  {c(msg_err, RED)}", msg_err[:70], callback)


# ══════════════════════════════════════════════════════════
#   MOTOR GENERAL
#   YouTube, Facebook, Twitter/X, Reddit, Vimeo, etc.
#
#   outtmpl = OUTTMPL_GOLD en todos los casos.
#   v1.3 FIX: 'updatetime': False en opts_item y opts_video
# ══════════════════════════════════════════════════════════

def motor_general(url, callback=None):
    if not verificar_limite_espacio(callback):
        return

    _notify(
        f"\n  {c('🌐 Motor General activado (yt-dlp)...', CYAN)}",
        "🌐 Motor General activado (yt-dlp)...",
        callback
    )
    cookies = _cookies_ok(callback)

    try:
        opts_info = {
            'quiet':              True,
            'no_warnings':        True,
            'nocheckcertificate': True,
            'cookiefile':         cookies,
        }
        with yt_dlp.YoutubeDL(opts_info) as ydl:
            info = ydl.extract_info(url, download=False)

        entries = info.get('entries')

        # ══════════════════════════════════════════════════
        # CASO A: PLAYLIST / COLECCIÓN MÚLTIPLE
        # ══════════════════════════════════════════════════
        if entries:
            entries_list = list(entries)
            total = len(entries_list)
            _notify(
                f"\n  📦 {total} elemento(s) en playlist. Descargando en {RUTA_DOWNLOADS}...",
                f"📦 {total} elemento(s) en playlist. Descargando...",
                callback
            )

            ok = fail = 0
            for i, entry in enumerate(entries_list, 1):
                try:
                    etit = sanitizar_nombre(entry.get('title', f'item_{i:03d}'))
                    eurl = (
                        entry.get('webpage_url') or
                        entry.get('url') or
                        url
                    )
                    opts_item = {
                        'format':             'best[ext=mp4]/best',
                        'outtmpl':            OUTTMPL_GOLD,
                        'quiet':              True,
                        'no_warnings':        True,
                        'nocheckcertificate': True,
                        'cookiefile':         cookies,
                        'noplaylist':         True,
                        'updatetime':         False,  # v1.3 FIX
                    }
                    _notify(
                        f"  {c(f'⬇️  [{i}/{total}] {etit[:45]}', YELLOW)}",
                        f"⬇️ [{i}/{total}] {etit[:40]}...",
                        callback
                    )
                    with yt_dlp.YoutubeDL(opts_item) as ydl2:
                        ydl2.download([eurl])
                    print(c("  ✅ OK", GREEN))
                    ok += 1

                except Exception as ei:
                    print(f"\n  {c(f'⚠️  Error en item {i}: {ei}', YELLOW)}")
                    if callback:
                        callback(f"⚠️ Error en item {i}/{total}: {type(ei).__name__}")
                    fail += 1

            msg_ok = f"🎉 Playlist: {ok} guardado(s), {fail} error(es)"
            _notify(f"\n  {c(msg_ok, GREEN, BOLD)}", msg_ok, callback)
            guardar_historial(f"Playlist ({ok}/{total} items)", url)

        # ══════════════════════════════════════════════════
        # CASO B: VIDEO / MEDIA ÚNICO
        # ══════════════════════════════════════════════════
        else:
            titulo   = info.get('title', 'Sin_Titulo')
            uploader = info.get('uploader', '')
            vistas   = info.get('view_count')

            _notify(
                f"\n  📦 1 elemento detectado. Descargando en {RUTA_DOWNLOADS}...",
                "📦 1 elemento detectado. Descargando...",
                callback
            )

            opts_video = {
                'format':             'best[ext=mp4]/best',
                'outtmpl':            OUTTMPL_GOLD,
                'quiet':              False,
                'no_warnings':        True,
                'nocheckcertificate': True,
                'cookiefile':         cookies,
                'noplaylist':         True,
                'updatetime':         False,  # v1.3 FIX
            }
            with yt_dlp.YoutubeDL(opts_video) as ydl:
                ydl.download([url])

            # Nombre para historial
            if isinstance(vistas, int):
                nombre_display = f"{vistas} views - {titulo} ({uploader})"
            else:
                nombre_display = f"{titulo} - {uploader}"

            msg_ok = f"✅ ¡DESCARGA EXITOSA! — {nombre_display[:50]}"
            _notify(
                f"\n  {c('✅ ¡DESCARGA EXITOSA!', GREEN, BOLD)}\n"
                f"  {c('📂 Guardado en:', GOLD)} {RUTA_DOWNLOADS}\n"
                f"  {c('🎬 Archivo:', GOLD)} {nombre_display[:65]}",
                msg_ok,
                callback
            )
            guardar_historial(nombre_display, url)

    except Exception as e:
        msg_err = f"❌ Error en motor general ({type(e).__name__}): {e}"
        _notify(f"\n  {c(msg_err, RED)}", msg_err[:70], callback)


# ══════════════════════════════════════════════════════════
#   ROUTER PRINCIPAL
#
#   Única función que main.py necesita importar.
#   Detecta la plataforma y despacha al motor correcto.
#
#   Parámetros:
#     url      (str)          : URL a descargar
#     callback (callable|None): función(str) invocada en tiempo
#                               real con mensajes de progreso.
#                               Thread-safe: puede llamarse desde
#                               un hilo secundario sin problemas.
# ══════════════════════════════════════════════════════════

def descargar(url, callback=None):
    """
    Punto de entrada principal del módulo.

    Uso desde main.py:
        from mstl_logic import descargar
        descargar(url, callback=mi_funcion_de_estado)
    """
    plataforma = detectar_plataforma(url)
    iconos = {'instagram': '📷', 'tiktok': '🎵', 'general': '🌐'}

    msg = f"{iconos.get(plataforma, '🔗')} Plataforma detectada: {plataforma.upper()}"
    _notify(f"\n  {c(msg, GOLD, BOLD)}", msg, callback)

    if plataforma == 'instagram':
        motor_instagram(url, callback=callback)
    elif plataforma == 'tiktok':
        motor_tiktok(url, callback=callback)
    else:
        motor_general(url, callback=callback)
