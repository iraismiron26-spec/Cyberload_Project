#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════╗
# ║  MSTL LOGIC — Módulo de Descarga  V13                   ║
# ║  Instagram · TikTok · YouTube · Facebook · +            ║
# ║  Motor: Instaloader + yt-dlp | Sin FFmpeg | Pydroid 3   ║
# ║                                                          ║
# ║  API pública:                                           ║
# ║    descargar(url, callback)        → router principal   ║
# ║    descargar_solo_video(url, cb)   → MP4 directo [V13]  ║
# ║    descargar_solo_imagenes(url,cb) → fotos/carrusel[V13]║
# ║    detectar_plataforma(url)        → str de plataforma  ║
# ║                                                          ║
# ║  Cambios V13:                                           ║
# ║  · detectar_plataforma() → añadido 'facebook'          ║
# ║    Detecta: facebook.com / fb.com / fb.watch /          ║
# ║    m.facebook.com / fbwat.ch / web.facebook.com        ║
# ║  · descargar_solo_video() → nueva función para          ║
# ║    la ventana flotante. Descarga exclusivamente MP4     ║
# ║    con yt-dlp. Compatible con todas las plataformas.   ║
# ║  · descargar_solo_imagenes() → nueva función para       ║
# ║    la ventana flotante. Instagram → motor_instagram;    ║
# ║    TikTok → motor_tiktok (ya maneja carruseles);        ║
# ║    General → fallback a video si no hay imágenes.       ║
# ║  · Cambios en V12/V11/V10... heredados sin modificar.  ║
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
# ══════════════════════════════════════════════════════════
RUTA_DOWNLOADS = '/storage/emulated/0/Download/'
HISTORIAL_PATH = '/storage/emulated/0/Download/mstl_historial.json'

os.makedirs(RUTA_DOWNLOADS, exist_ok=True)


# ══════════════════════════════════════════════════════════
#   RUTA DINÁMICA DE COOKIES — v2.0 (sin cambios)
# ══════════════════════════════════════════════════════════

def _get_cookies_path():
    """
    Detecta dinámicamente la ruta de cookies.txt.

    Orden de prioridad:
        1. App external files dir (Android/data/org.test.cyberload/files/)
        2. /sdcard/cookies.txt (compatibilidad)
        3. None si no existe ninguna
    """
    app_cookies = None

    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        context = PythonActivity.mActivity
        ext_dir = context.getExternalFilesDir(None)
        if ext_dir is not None:
            app_cookies = os.path.join(ext_dir.getAbsolutePath(), 'cookies.txt')
    except Exception:
        pass

    if app_cookies is None:
        android_files = '/storage/emulated/0/Android/data/org.test.cyberload/files/cookies.txt'
        if os.path.exists(os.path.dirname(android_files)):
            app_cookies = android_files

    if app_cookies and os.path.exists(app_cookies):
        return app_cookies

    if os.path.exists('/sdcard/cookies.txt'):
        return '/sdcard/cookies.txt'

    return None


# ── Colores ANSI (terminal) ───────────────────────────────
R, BOLD, GREEN, GOLD, RED, YELLOW, CYAN, GRAY = (
    "\033[0m", "\033[1m", "\033[92m", "\033[38;5;220m",
    "\033[91m", "\033[93m", "\033[96m", "\033[90m"
)

def c(texto, *estilos):
    return "".join(estilos) + str(texto) + R

IMAGE_EXTS = {'jpg', 'jpeg', 'png', 'webp'}

OUTTMPL_GOLD = os.path.join(RUTA_DOWNLOADS, '%(title).100s [%(id)s].%(ext)s')


# ══════════════════════════════════════════════════════════
#   HELPER CENTRAL: NOTIFICACIÓN DUAL — Terminal + GUI
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
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def sanitizar_nombre(nombre):
    nombre = re.sub(r'[\\/*?"<>|\n\r\t]', "", str(nombre))
    return nombre.strip()[:100]


def obtener_espacio_libre():
    try:
        stat = os.statvfs(RUTA_DOWNLOADS)
        return f"{(stat.f_bavail * stat.f_frsize) / (1024**3):.2f} GB"
    except:
        return "---"


def verificar_limite_espacio(callback=None):
    """Barrera de seguridad: al menos 500 MB libres antes de descargar."""
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
        return True


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


# ══════════════════════════════════════════════════════════
#   DETECTOR DE PLATAFORMA — V13: añadido 'facebook'
#
#   Retorna: 'instagram' | 'tiktok' | 'facebook' | 'general'
#
#   NUEVA EN V13: detección de Facebook.
#   Dominios detectados:
#     facebook.com, m.facebook.com, web.facebook.com,
#     fb.com, fb.watch, fbwat.ch, l.facebook.com
#
#   IMPORTANTE: Facebook NO ofrece imágenes vía API pública.
#   Solo se permite descarga de video desde la PantallaFlotante.
#   El motor_general (yt-dlp) maneja el video de FB sin problemas.
# ══════════════════════════════════════════════════════════

def detectar_plataforma(url):
    """
    Detecta la plataforma de la URL.

    Retorna: 'instagram' | 'tiktok' | 'facebook' | 'general'
    """
    u = url.lower()

    if 'instagram.com' in u:
        return 'instagram'

    if 'tiktok.com' in u or 'vm.tiktok.com' in u:
        return 'tiktok'

    # ── Facebook — V13 ────────────────────────────────────────────
    dominios_facebook = (
        'facebook.com', 'fb.com', 'fb.watch',
        'fbwat.ch', 'm.facebook.com', 'web.facebook.com',
        'l.facebook.com',
    )
    if any(d in u for d in dominios_facebook):
        return 'facebook'

    return 'general'


def _ruta_segura(directorio, filename):
    ruta = os.path.join(directorio, filename)
    if os.path.exists(ruta):
        base, ext = os.path.splitext(ruta)
        ruta = f"{base}_{gen_id(4)}{ext}"
    return ruta


def _convertir_webp_a_jpg(filepath, callback=None):
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
    ruta = _get_cookies_path()
    if ruta:
        print(f"  {c(f'🍪 Cookies encontradas: {ruta}', GREEN)}")
        return ruta
    _notify(
        f"  {c('⚠️  cookies.txt no encontrado — posible bloqueo en Instagram/TikTok.', YELLOW)}",
        "⚠️ Sin cookies disponibles — posible bloqueo.",
        callback
    )
    return None


# ══════════════════════════════════════════════════════════
#   FIX v1.3 — ACTUALIZADOR DE FECHAS
# ══════════════════════════════════════════════════════════

def actualizar_fechas_archivos(session_id, callback=None):
    actualizados = 0
    try:
        for f in os.listdir(RUTA_DOWNLOADS):
            if session_id not in f:
                continue
            ruta_f = os.path.join(RUTA_DOWNLOADS, f)
            if not os.path.isfile(ruta_f):
                continue
            os.utime(ruta_f, None)
            actualizados += 1

        if actualizados:
            msg = f"🕐 Fechas actualizadas: {actualizados} archivo(s) → timestamp = AHORA"
            _notify(f"  {c(msg, GREEN)}", msg, callback)
    except Exception as e:
        _notify(
            f"  {c(f'⚠️  No se pudo actualizar fechas ({e})', YELLOW)}",
            f"⚠️ No se pudo actualizar fechas: {e}",
            callback
        )


# ══════════════════════════════════════════════════════════
#   DESCARGA HTTP DIRECTA
# ══════════════════════════════════════════════════════════

def _descargar_http(src_url, filepath, referer=""):
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

        L = instaloader.Instaloader(
            dirname_pattern              = RUTA_DOWNLOADS,
            filename_pattern             = '{profile}_{shortcode}_' + session_id,
            download_videos              = True,
            download_video_thumbnails    = False,
            save_metadata                = False,
            post_metadata_txt_pattern    = "",
            quiet                        = True,
        )

        if cookies_path:
            try:
                import http.cookiejar
                jar = http.cookiejar.MozillaCookieJar()
                jar.load(cookies_path, ignore_discard=True, ignore_expires=True)
                L.context._session.cookies.update(jar)
                print(f"  {c('🍪 Cookies inyectadas en Instaloader.', GREEN)}")
            except Exception as ce:
                print(f"  {c(f'⚠️  No se pudieron cargar cookies: {ce}', YELLOW)}")

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

        L.download_post(post, target=Path(RUTA_DOWNLOADS))
        actualizar_fechas_archivos(session_id, callback)

        archivos_sesion = [f for f in os.listdir(RUTA_DOWNLOADS) if session_id in f]

        if not archivos_sesion:
            _notify(
                f"\n  {c('⚠️  Verificación física: 0 archivos. Activando respaldo yt-dlp...', YELLOW)}",
                "⚠️ 0 archivos encontrados → activando yt-dlp...",
                callback
            )
            motor_general(url, callback=callback)
            return

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

        guardados = [f for f in os.listdir(RUTA_DOWNLOADS) if session_id in f]

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
                            os.utime(fpath, None)
                            print(c("  ✅ OK", GREEN))
                            ok += 1
                        else:
                            print(c("  ❌ Falló", RED))
                            fail += 1

                    else:
                        opts_item = {
                            'format':             'best[ext=mp4]/best',
                            'outtmpl':            OUTTMPL_GOLD,
                            'quiet':              True,
                            'no_warnings':        True,
                            'nocheckcertificate': True,
                            'cookiefile':         cookies,
                            'noplaylist':         True,
                            'updatetime':         False,
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
                'updatetime':         False,
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
                        'updatetime':         False,
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
                'updatetime':         False,
            }
            with yt_dlp.YoutubeDL(opts_video) as ydl:
                ydl.download([url])

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
#   DESCARGA SOLO VIDEO — V13
#
#   Función exclusiva para la PantallaFlotante de main.py.
#   Descarga únicamente el video en MP4 de la URL dada,
#   usando yt-dlp como motor universal.
#
#   Compatible con: Instagram, TikTok, Facebook, YouTube,
#   y cualquier URL que yt-dlp soporte.
#
#   Formato de salida: best[ext=mp4]/best
#     → Prefiere MP4 nativo sin necesidad de FFmpeg.
#     → Si no hay MP4 nativo, usa el mejor formato disponible.
#
#   NOTA IMPORTANTE — Facebook:
#     yt-dlp puede necesitar cookies para videos privados de FB.
#     Videos públicos de Facebook generalmente funcionan sin cookies.
# ══════════════════════════════════════════════════════════

def descargar_solo_video(url, callback=None):
    """
    Descarga exclusivamente el video MP4 de la URL.

    Uso desde main.py (PantallaFlotante):
        from mstl_logic import descargar_solo_video
        descargar_solo_video(url, callback=mi_callback)

    Parámetros:
        url      (str)            : URL del video a descargar
        callback (callable | None): función(str) de progreso
    """
    if not verificar_limite_espacio(callback):
        return

    plataforma = detectar_plataforma(url)
    icono = {'instagram': '📸', 'tiktok': '🎵', 'facebook': '📘', 'general': '🌐'}.get(plataforma, '🌐')

    _notify(
        f"\n  {c(f'{icono} Descargando video MP4 ({plataforma.upper()})...', CYAN)}",
        f"{icono} Descargando video MP4...",
        callback
    )

    cookies = _cookies_ok(callback)

    opts = {
        'format':             'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
        'outtmpl':            OUTTMPL_GOLD,
        'quiet':              False,
        'no_warnings':        True,
        'nocheckcertificate': True,
        'cookiefile':         cookies,
        'noplaylist':         True,
        'updatetime':         False,
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info  = ydl.extract_info(url, download=True)
            titulo = sanitizar_nombre(info.get('title', 'video_sin_titulo'))

        # Actualizar timestamp del archivo descargado al momento presente
        # para que aparezca primero en la galería de Android
        for f in os.listdir(RUTA_DOWNLOADS):
            if titulo[:20] in f or (info.get('id') and info['id'] in f):
                os.utime(os.path.join(RUTA_DOWNLOADS, f), None)

        msg_ok = f"✅ Video MP4 guardado: {titulo[:55]}"
        _notify(
            f"\n  {c(msg_ok, GREEN, BOLD)}\n  {c('📂', GOLD)} {RUTA_DOWNLOADS}",
            msg_ok,
            callback
        )
        guardar_historial(f"[Video] {titulo}", url)

    except Exception as e:
        msg_err = f"❌ Error al descargar video ({type(e).__name__}): {e}"
        _notify(f"\n  {c(msg_err, RED)}", msg_err[:70], callback)


# ══════════════════════════════════════════════════════════
#   DESCARGA SOLO IMÁGENES — V13
#
#   Función exclusiva para la PantallaFlotante de main.py.
#   Solo disponible para Instagram y TikTok (la UI de
#   PantallaFlotante no muestra este botón para Facebook).
#
#   Lógica de enrutamiento:
#     Instagram → motor_instagram() ya maneja carruseles,
#       fotos únicas, reels con imágenes mezcladas.
#     TikTok    → motor_tiktok() ya maneja slideshows y
#       carruseles de fotos con descarga HTTP directa.
#     General   → fallback a descargar_solo_video() porque
#       las plataformas genéricas no tienen carruseles de imgs.
#
#   NOTA: Facebook excluido intencionalmente.
#     La API pública de FB bloquea la descarga de imágenes.
#     Solo se ofrece video MP4 desde la ventana flotante.
# ══════════════════════════════════════════════════════════

def descargar_solo_imagenes(url, callback=None):
    """
    Descarga imágenes o carrusel de la URL.

    Solo para Instagram y TikTok (Facebook excluido en la UI).

    Uso desde main.py (PantallaFlotante):
        from mstl_logic import descargar_solo_imagenes
        descargar_solo_imagenes(url, callback=mi_callback)

    Parámetros:
        url      (str)            : URL del post con imágenes
        callback (callable | None): función(str) de progreso
    """
    if not verificar_limite_espacio(callback):
        return

    plataforma = detectar_plataforma(url)

    _notify(
        f"\n  {c(f'🖼️  Descargando imágenes ({plataforma.upper()})...', CYAN)}",
        f"🖼️ Descargando imágenes de {plataforma.upper()}...",
        callback
    )

    if plataforma == 'instagram':
        # motor_instagram maneja tanto fotos únicas como carruseles
        motor_instagram(url, callback=callback)

    elif plataforma == 'tiktok':
        # motor_tiktok maneja slideshows y carruseles automáticamente
        motor_tiktok(url, callback=callback)

    else:
        # Para plataformas genéricas sin soporte de imágenes,
        # caer de vuelta a descarga de video.
        _notify(
            f"\n  {c('⚠️  Plataforma sin soporte de imágenes → descargando video...', YELLOW)}",
            "⚠️ Sin soporte de imágenes → descargando video...",
            callback
        )
        descargar_solo_video(url, callback=callback)


# ══════════════════════════════════════════════════════════
#   ROUTER PRINCIPAL
#
#   Única función que main.py (modo normal) necesita importar.
#   La PantallaFlotante usa descargar_solo_video() y
#   descargar_solo_imagenes() directamente.
# ══════════════════════════════════════════════════════════

def descargar(url, callback=None):
    """
    Punto de entrada principal del módulo (modo normal).

    Uso desde main.py (CyberLoadUI):
        from mstl_logic import descargar
        descargar(url, callback=mi_funcion_de_estado)
    """
    plataforma = detectar_plataforma(url)
    iconos = {'instagram': '📷', 'tiktok': '🎵', 'facebook': '📘', 'general': '🌐'}

    msg = f"{iconos.get(plataforma, '🔗')} Plataforma detectada: {plataforma.upper()}"
    _notify(f"\n  {c(msg, GOLD, BOLD)}", msg, callback)

    if plataforma == 'instagram':
        motor_instagram(url, callback=callback)
    elif plataforma == 'tiktok':
        motor_tiktok(url, callback=callback)
    else:
        # Facebook y General usan motor_general (yt-dlp)
        motor_general(url, callback=callback)
