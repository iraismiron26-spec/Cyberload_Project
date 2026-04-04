"""
╔══════════════════════════════════════════════════════════╗
║         CYBERLOAD — Descargador Cyberpunk  v2.0          ║
║         KivyMD + mstl_logic.py                          ║
║         Instagram · TikTok · YouTube · Facebook          ║
║         Compatible: Pydroid 3 / Android APK              ║
╚══════════════════════════════════════════════════════════╝

Novedades v2.0:
    · Ruta dinámica de cookies via get_app_external_files_dir()
      → Android: /storage/emulated/0/Android/data/org.test.cyberload/files/
      → Desktop/Pydroid: directorio del script
    · Auto-descarga de cookies.txt desde GitHub en on_start()
      → Si la descarga falla, usa cookies locales (sin interrumpir la app)
    · Flujo de on_start():
        1. Solicitar permisos de almacenamiento
        2. En callback: lanzar hilo de descarga de cookies
        3. Mostrar estado en el label de la UI

IMPORTANTE — ANTES DE USAR:
    Reemplaza GITHUB_COOKIES_URL con tu URL RAW de GitHub.
    Ejemplo:
    GITHUB_COOKIES_URL = "https://raw.githubusercontent.com/tuusuario/turepo/main/cookies.txt"
"""

import os
import sys
import threading
import traceback
from datetime import datetime

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar


# ─────────────────────────────────────────────────────────
#  CONFIGURACIÓN — REEMPLAZA ESTA URL CON LA TUYA
#
#  Cómo obtener tu URL RAW de GitHub:
#    1. Sube cookies.txt a tu repositorio en GitHub
#    2. Abre el archivo en GitHub → haz clic en "Raw"
#    3. Copia la URL de la barra de direcciones
#    Formato: https://raw.githubusercontent.com/USUARIO/REPO/RAMA/cookies.txt
# ─────────────────────────────────────────────────────────
GITHUB_COOKIES_URL = "https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/cookies.txt"


# ─────────────────────────────────────────────────────────
#  RUTA DINÁMICA — DIRECTORIO INTERNO DE LA APP
#
#  En Android devuelve:
#    /storage/emulated/0/Android/data/org.test.cyberload/files
#
#  Esta ruta es privada de la app pero accesible por el explorador
#  de archivos de Android. Es donde guardamos cookies.txt.
#
#  En Pydroid 3 / PC devuelve el directorio del script.
# ─────────────────────────────────────────────────────────

def get_app_external_files_dir() -> str:
    """
    Detecta y retorna el directorio de archivos externos de la app.

    Android → usa la API de Java via jnius para obtener la ruta real
              que Android asigna a la app (evita hardcodear el usuario).
    Fallback → /storage/emulated/0/Android/data/org.test.cyberload/files
    Desktop  → directorio del script actual
    """
    # ── Intento 1: API nativa de Android (más confiable) ───────────
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        context = PythonActivity.mActivity
        ext_dir = context.getExternalFilesDir(None)
        if ext_dir is not None:
            ruta = ext_dir.getAbsolutePath()
            os.makedirs(ruta, exist_ok=True)
            return ruta
    except Exception:
        pass

    # ── Intento 2: Ruta hardcoded para Android (fallback seguro) ────
    android_data = '/storage/emulated/0/Android/data/org.test.cyberload/files'
    if os.path.exists('/storage/emulated/0'):
        try:
            os.makedirs(android_data, exist_ok=True)
            return android_data
        except Exception:
            pass

    # ── Intento 3: Desktop / Pydroid 3 ──────────────────────────────
    return os.path.dirname(os.path.abspath(__file__))


def get_cookies_path() -> str:
    """Retorna la ruta completa de cookies.txt en el directorio de la app."""
    return os.path.join(get_app_external_files_dir(), "cookies.txt")


# ─────────────────────────────────────────────────────────
#  DESCARGA AUTOMÁTICA DE COOKIES DESDE GITHUB
#
#  Intenta descargar cookies.txt desde GITHUB_COOKIES_URL.
#  Si la descarga es exitosa → sobrescribe el archivo local.
#  Si falla (sin internet, URL incorrecta) → usa el archivo
#  local existente sin interrumpir la app.
# ─────────────────────────────────────────────────────────

def descargar_cookies_github(callback=None) -> bool:
    """
    Descarga cookies.txt desde GitHub y lo guarda en la carpeta interna.

    Retorna:
        True  → descarga exitosa
        False → falló (usa cookies locales si existen)
    """
    ruta_destino = get_cookies_path()

    # Si la URL no está configurada, salir sin error
    if "TU_USUARIO" in GITHUB_COOKIES_URL or "TU_REPO" in GITHUB_COOKIES_URL:
        _notificar_ui(
            callback,
            "⚠️ GITHUB_COOKIES_URL no configurada.\nUsando cookies locales si existen.",
            color=(1, 0.7, 0, 1),
        )
        return False

    try:
        import urllib.request
        import ssl
        import certifi

        # Contexto SSL con certificados de certifi
        ctx = ssl.create_default_context(cafile=certifi.where())

        _notificar_ui(callback, "🌐 Descargando cookies desde GitHub...", color=(0, 0.9, 1, 1))

        req = urllib.request.Request(
            GITHUB_COOKIES_URL,
            headers={
                "User-Agent": "Mozilla/5.0 (Android) CyberloadMSTL/2.0"
            }
        )

        os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)

        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            contenido = resp.read()

        with open(ruta_destino, "wb") as f:
            f.write(contenido)

        tamaño_kb = len(contenido) / 1024
        _notificar_ui(
            callback,
            f"✅ Cookies actualizadas ({tamaño_kb:.1f} KB)\n📁 {ruta_destino}",
            color=(0, 1, 0.5, 1),
        )
        print(f"[COOKIES] Descargadas y guardadas en: {ruta_destino}")
        return True

    except Exception as e:
        # Fallo silencioso — la app continúa con cookies locales
        cookies_existen = os.path.exists(ruta_destino)
        if cookies_existen:
            _notificar_ui(
                callback,
                f"⚠️ No se pudo actualizar cookies.\nUsando archivo local existente.",
                color=(1, 0.7, 0, 1),
            )
        else:
            _notificar_ui(
                callback,
                f"⚠️ Sin cookies disponibles.\nAlgunas descargas pueden fallar.",
                color=(1, 0.5, 0, 1),
            )
        print(f"[COOKIES] Error al descargar: {e}. Cookies locales: {cookies_existen}")
        return False


def _notificar_ui(callback, texto, color=(0, 0.9, 1, 1)):
    """Envía un mensaje al label de estado de la UI de forma thread-safe."""
    if callback:
        Clock.schedule_once(lambda dt: callback(texto, color), 0)


# ─────────────────────────────────────────────────────────
#  ESCRITURA DE CRASH LOG
# ─────────────────────────────────────────────────────────

def _escribir_crash_log(exc: Exception) -> None:
    contenido = (
        f"=== CYBERLOAD ERROR LOG ===\n"
        f"Fecha : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Error : {type(exc).__name__}: {exc}\n\n"
        f"--- Traceback completo ---\n"
        f"{traceback.format_exc()}"
    )
    rutas_candidatas = [
        "/sdcard/cyberload_error.txt",
        "/storage/emulated/0/cyberload_error.txt",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "cyberload_error.txt"),
    ]
    for ruta in rutas_candidatas:
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido)
            print(f"[ERROR LOG] Guardado en: {ruta}")
            return
        except Exception:
            continue
    print(contenido)


# ─────────────────────────────────────────────────────────
#  Widget Principal
# ─────────────────────────────────────────────────────────

class CyberLoadUI(BoxLayout):

    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app_ref
        self.orientation = "vertical"
        self.spacing = dp(0)

        self.toolbar = MDTopAppBar(
            title="⚡  C Y B E R L O A D",
            elevation=4,
            md_bg_color=self.app_ref.theme_cls.primary_color,
        )
        self.add_widget(self.toolbar)

        inner = BoxLayout(
            orientation="vertical",
            spacing=dp(20),
            padding=[dp(20), dp(32), dp(20), dp(32)],
        )

        inner.add_widget(MDLabel(
            text="[b]// INGRESA TU ENLACE[/b]",
            markup=True,
            halign="left",
            theme_text_color="Custom",
            text_color=(0, 0.9, 1, 0.7),
            font_style="Overline",
            size_hint_y=None,
            height=dp(20),
        ))

        self.url_field = MDTextField(
            hint_text="https://instagram.com/p/... · tiktok · youtube",
            icon_right="link-variant",
            mode="rectangle",
            line_color_focus=(0, 0.9, 1, 1),
            line_color_normal=(0, 0.9, 1, 0.35),
            hint_text_color_normal=(0, 0.9, 1, 0.4),
            hint_text_color_focus=(0, 0.9, 1, 0.8),
            text_color_normal=(1, 1, 1, 1),
            text_color_focus=(0, 0.9, 1, 1),
            font_size=dp(14),
        )
        inner.add_widget(self.url_field)

        self.btn_descargar = MDRaisedButton(
            text="▶  INICIAR DESCARGA",
            font_style="Button",
            size_hint=(1, None),
            height=dp(54),
            md_bg_color=(1, 0.76, 0, 1),
            text_color=(0.05, 0.05, 0.05, 1),
            elevation=6,
            on_release=self.ejecutar_descarga,
        )
        inner.add_widget(self.btn_descargar)

        scroll = ScrollView(size_hint=(1, None), height=dp(100),
                            do_scroll_x=False, do_scroll_y=True)
        self.lbl_estado = MDLabel(
            text="[ Iniciando... ]",
            halign="center",
            theme_text_color="Custom",
            text_color=(0, 0.9, 1, 0.85),
            font_style="Caption",
            size_hint_y=None,
        )
        self.lbl_estado.bind(
            texture_size=lambda inst, val: setattr(
                inst, "height", max(dp(100), val[1] + dp(12))
            )
        )
        scroll.add_widget(self.lbl_estado)
        inner.add_widget(scroll)

        inner.add_widget(MDLabel(
            text="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            halign="center",
            theme_text_color="Custom",
            text_color=(0, 0.9, 1, 0.2),
            font_style="Caption",
            size_hint_y=None,
            height=dp(20),
        ))

        inner.add_widget(MDLabel(
            text=(
                "📂  Archivos en:\n"
                "/storage/emulated/0/Download/\n\n"
                "🍪  Cookies en:\n"
                "Android/data/org.test.cyberload/files/\n\n"
                "⚙️  Motores: Instaloader · yt-dlp\n"
                "🔌  Requiere conexión activa"
            ),
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 0.28),
            font_style="Caption",
        ))

        self.add_widget(inner)

    def set_estado(self, texto, color=(0, 0.9, 1, 0.85)):
        self.lbl_estado.text = texto
        self.lbl_estado.text_color = color

    # ─────────────────────────────────────────────────────
    #  Funciones de descarga
    # ─────────────────────────────────────────────────────

    def ejecutar_descarga(self, *args):
        url = self.url_field.text.strip()
        if not url:
            self.set_estado("⚠  Ingresa una URL válida", color=(1, 0.5, 0, 1))
            return
        self.btn_descargar.disabled = True
        self.set_estado("🔄  Iniciando descarga...", color=(0, 0.9, 1, 1))
        threading.Thread(target=self._proceso_descarga, args=(url,), daemon=True).start()

    def _proceso_descarga(self, url):
        try:
            from mstl_logic import descargar
            descargar(url, callback=self._ui_callback)
            Clock.schedule_once(lambda dt: self._finalizar(exito=True), 0)
        except ImportError:
            Clock.schedule_once(lambda dt: self._finalizar(
                exito=False,
                detalle="❌ mstl_logic.py no encontrado.\nColócalo junto a main.py"
            ), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self._finalizar(exito=False, detalle=str(e)[:80]), 0)

    def _ui_callback(self, mensaje):
        Clock.schedule_once(
            lambda dt: self.set_estado(f"⚙️  {mensaje[:60]}", color=(0, 0.9, 1, 1)), 0)

    def _finalizar(self, exito=True, detalle=""):
        self.btn_descargar.disabled = False
        if exito:
            self.url_field.text = ""
            self.set_estado(
                "✅  ¡Descarga completa!\n📂 /storage/emulated/0/Download/",
                color=(0, 1, 0.5, 1))
        else:
            self.set_estado(f"❌  Error:\n{detalle}", color=(1, 0.25, 0.25, 1))


# ─────────────────────────────────────────────────────────
#  Clase Principal MDApp
# ─────────────────────────────────────────────────────────

class CyberLoadApp(MDApp):

    def build(self):
        self.theme_cls.theme_style     = "Dark"
        self.theme_cls.primary_palette = "Cyan"
        self.theme_cls.accent_palette  = "Amber"
        self.title = "CyberLoad"
        pantalla = MDScreen(md_bg_color=(0.04, 0.04, 0.06, 1))
        self.ui = CyberLoadUI(app_ref=self)
        pantalla.add_widget(self.ui)
        return pantalla

    # ─────────────────────────────────────────────────────
    #  on_start — Flujo completo v2.0:
    #    1. Solicitar permisos de almacenamiento + internet
    #    2. En callback: lanzar hilo de descarga de cookies
    #    3. Hilo de cookies actualiza el label de estado
    # ─────────────────────────────────────────────────────

    def on_start(self):
        try:
            from android.permissions import Permission, request_permissions

            permisos_requeridos = [
                Permission.INTERNET,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ]
            try:
                permisos_requeridos.append(Permission.MANAGE_EXTERNAL_STORAGE)
            except AttributeError:
                pass  # Android 8/9

            self.ui.set_estado("🔐 Solicitando permisos...", color=(0, 0.9, 1, 0.7))
            request_permissions(permisos_requeridos, self._callback_permisos)

        except ImportError:
            # Desktop / Pydroid 3
            self.ui.set_estado("🌐 Verificando cookies...", color=(0, 0.9, 1, 0.7))
            threading.Thread(target=self._hilo_cookies, daemon=True).start()

    def _callback_permisos(self, permisos, resultados):
        """Llamado por Android al responder el diálogo de permisos."""
        denegados = [p for p, r in zip(permisos, resultados) if not r]

        if denegados:
            nombres = [p.split(".")[-1] for p in denegados]
            self.ui.set_estado(
                f"⚠️ Permisos denegados: {', '.join(nombres)}\n"
                "Las descargas pueden fallar.",
                color=(1, 0.6, 0, 1)
            )
        else:
            self.ui.set_estado("✅ Permisos OK\n🌐 Descargando cookies...",
                               color=(0, 0.9, 1, 0.8))

        # Lanzar descarga de cookies independientemente del resultado
        threading.Thread(target=self._hilo_cookies, daemon=True).start()

    def _hilo_cookies(self):
        """Descarga cookies en hilo secundario para no bloquear la UI."""
        def ui_callback(texto, color):
            self.ui.set_estado(texto, color)

        exito = descargar_cookies_github(callback=ui_callback)

        # Mostrar estado final
        def estado_final(dt):
            cookies_path = get_cookies_path()
            cookies_ok = os.path.exists(cookies_path)
            if exito:
                self.ui.set_estado(
                    "✅ Cookies actualizadas\n[ Ingresa un enlace para descargar ]",
                    color=(0, 1, 0.5, 1)
                )
            elif cookies_ok:
                self.ui.set_estado(
                    "🍪 Cookies locales OK\n[ Ingresa un enlace para descargar ]",
                    color=(0, 0.9, 1, 0.85)
                )
            else:
                self.ui.set_estado(
                    "⚠️ Sin cookies — descarga limitada\n[ Ingresa un enlace ]",
                    color=(1, 0.7, 0, 1)
                )

        Clock.schedule_once(estado_final, 0)


# ─────────────────────────────────────────────────────────
#  Punto de Entrada
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        CyberLoadApp().run()
    except Exception as exc:
        _escribir_crash_log(exc)
        sys.exit(1)
