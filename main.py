"""
╔══════════════════════════════════════════════════════════╗
║         CYBERLOAD — Descargador Cyberpunk  V13           ║
║         KivyMD + mstl_logic.py                           ║
║         Instagram · TikTok · YouTube · Facebook          ║
║         Compatible: Pydroid 3 / Android APK              ║
╠══════════════════════════════════════════════════════════╣
║  Novedades V13:                                          ║
║  · PantallaFlotante — ventana de descarga rápida estilo  ║
║    Snaptube. Se activa al compartir un enlace a la app.  ║
║  · Detección de Intent SEND via pyjnius                  ║
║  · Filtro de contenido:                                  ║
║    - Facebook → solo botón VIDEO MP4                     ║
║    - Instagram/TikTok → VIDEO + IMÁGENES                 ║
║    - General (YouTube) → solo VIDEO                      ║
║  · Notificación Android al iniciar descarga (plyer)      ║
║  · App va al fondo automáticamente post-descarga         ║
║    (moveTaskToBack) → usuario vuelve a su red social     ║
║  · Modo normal (lanzamiento directo) sin cambios         ║
╚══════════════════════════════════════════════════════════╝
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
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar


# ─────────────────────────────────────────────────────────
#  CONFIGURACIÓN — REEMPLAZA ESTA URL CON LA TUYA
# ─────────────────────────────────────────────────────────
GITHUB_COOKIES_URL = "https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/cookies.txt"


# ─────────────────────────────────────────────────────────
#  RUTA DINÁMICA — DIRECTORIO INTERNO DE LA APP
# ─────────────────────────────────────────────────────────

def get_app_external_files_dir() -> str:
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

    android_data = '/storage/emulated/0/Android/data/org.test.cyberload/files'
    if os.path.exists('/storage/emulated/0'):
        try:
            os.makedirs(android_data, exist_ok=True)
            return android_data
        except Exception:
            pass

    return os.path.dirname(os.path.abspath(__file__))


def get_cookies_path() -> str:
    return os.path.join(get_app_external_files_dir(), "cookies.txt")


# ─────────────────────────────────────────────────────────
#  DESCARGA AUTOMÁTICA DE COOKIES DESDE GITHUB
# ─────────────────────────────────────────────────────────

def descargar_cookies_github(callback=None) -> bool:
    ruta_destino = get_cookies_path()

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

        ctx = ssl.create_default_context(cafile=certifi.where())
        _notificar_ui(callback, "🌐 Descargando cookies desde GitHub...", color=(0, 0.9, 1, 1))

        req = urllib.request.Request(
            GITHUB_COOKIES_URL,
            headers={"User-Agent": "Mozilla/5.0 (Android) CyberloadMSTL/13.0"}
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
        return True

    except Exception as e:
        cookies_existen = os.path.exists(ruta_destino)
        if cookies_existen:
            _notificar_ui(callback, "⚠️ No se pudo actualizar cookies.\nUsando archivo local.", color=(1, 0.7, 0, 1))
        else:
            _notificar_ui(callback, "⚠️ Sin cookies disponibles.\nAlgunas descargas pueden fallar.", color=(1, 0.5, 0, 1))
        return False


def _notificar_ui(callback, texto, color=(0, 0.9, 1, 1)):
    if callback:
        Clock.schedule_once(lambda dt: callback(texto, color), 0)


# ─────────────────────────────────────────────────────────
#  CRASH LOG
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
#  PANTALLA FLOTANTE — V13
#
#  Modo activado cuando el usuario comparte un enlace a la app.
#  Muestra un panel central con:
#    · Icono de la red social detectada
#    · Preview de la URL
#    · Botones de descarga filtrados por plataforma:
#        Facebook          → solo VIDEO MP4
#        Instagram/TikTok  → VIDEO MP4 + IMÁGENES
#        YouTube/General   → solo VIDEO MP4
#    · Botón cancelar
#
#  Flujo de descarga:
#    1. Usuario toca el botón de descarga
#    2. Se lanza hilo de descarga en segundo plano
#    3. Se envía notificación Android "Descargando..."
#    4. La app se envía al fondo (moveTaskToBack)
#       → usuario vuelve automáticamente a su red social
#    5. El hilo de descarga sigue corriendo en background
# ─────────────────────────────────────────────────────────

class PantallaFlotante(MDScreen):
    """Pantalla de descarga rápida para modo Share Intent (V13)."""

    ICONOS = {
        'instagram': '📸  INSTAGRAM',
        'tiktok':    '🎵  TIKTOK',
        'facebook':  '📘  FACEBOOK',
        'youtube':   '▶️  YOUTUBE',
        'general':   '🌐  ENLACE WEB',
    }

    # Plataformas que ofrecen opción de Imágenes
    SOPORTA_IMAGENES = {'instagram', 'tiktok'}

    def __init__(self, url: str, plataforma: str, app_ref, **kwargs):
        super().__init__(md_bg_color=(0.02, 0.02, 0.05, 0.96), **kwargs)
        self.url = url
        self.plataforma = plataforma
        self.app_ref = app_ref
        self._descargando = False
        self._construir_ui()

    def _construir_ui(self):
        """Construye el panel central de descarga."""

        # ── Contenedor raíz (centra el card verticalmente) ────────
        raiz = BoxLayout(
            orientation='vertical',
            padding=[dp(20), dp(60), dp(20), dp(60)],
        )

        # ── Card central ──────────────────────────────────────────
        card = MDCard(
            orientation='vertical',
            padding=[dp(24), dp(20), dp(24), dp(20)],
            spacing=dp(10),
            size_hint=(1, None),
            md_bg_color=(0.07, 0.07, 0.12, 1),
            elevation=14,
            radius=[dp(22), dp(22), dp(22), dp(22)],
        )

        # ── Cabecera: icono + nombre plataforma ───────────────────
        icono_texto = self.ICONOS.get(self.plataforma, '🌐  ENLACE')
        card.add_widget(MDLabel(
            text=icono_texto,
            halign='center',
            theme_text_color='Custom',
            text_color=(0, 0.9, 1, 1),
            font_style='H6',
            size_hint_y=None,
            height=dp(44),
        ))

        # ── Separador ─────────────────────────────────────────────
        card.add_widget(MDLabel(
            text='━━━━━━━━━━━━━━━━━━━━━━━━━━━',
            halign='center',
            theme_text_color='Custom',
            text_color=(0, 0.9, 1, 0.18),
            font_style='Caption',
            size_hint_y=None,
            height=dp(16),
        ))

        # ── Preview de la URL (truncada) ──────────────────────────
        preview = (self.url[:55] + '...') if len(self.url) > 55 else self.url
        card.add_widget(MDLabel(
            text=preview,
            halign='center',
            theme_text_color='Custom',
            text_color=(1, 1, 1, 0.38),
            font_style='Caption',
            size_hint_y=None,
            height=dp(38),
        ))

        # ── Label de estado ───────────────────────────────────────
        self.lbl_estado = MDLabel(
            text='Selecciona una opción ↓',
            halign='center',
            theme_text_color='Custom',
            text_color=(0, 0.9, 1, 0.65),
            font_style='Caption',
            size_hint_y=None,
            height=dp(28),
        )
        card.add_widget(self.lbl_estado)

        # ── Botón: Descargar Video MP4 (siempre visible) ──────────
        self.btn_video = MDRaisedButton(
            text='⬇  DESCARGAR VIDEO MP4',
            size_hint=(1, None),
            height=dp(52),
            md_bg_color=(1, 0.76, 0, 1),
            text_color=(0.04, 0.04, 0.04, 1),
            elevation=5,
            on_release=self._on_descargar_video,
        )
        card.add_widget(self.btn_video)

        # ── Botón: Descargar Imágenes (solo IG y TikTok) ──────────
        # Facebook NO: sus fotos causan errores con la API pública.
        if self.plataforma in self.SOPORTA_IMAGENES:
            self.btn_imgs = MDRaisedButton(
                text='🖼  DESCARGAR IMÁGENES',
                size_hint=(1, None),
                height=dp(52),
                md_bg_color=(0, 0.9, 1, 1),
                text_color=(0.04, 0.04, 0.04, 1),
                elevation=5,
                on_release=self._on_descargar_imagenes,
            )
            card.add_widget(self.btn_imgs)

        # ── Botón: Cancelar ───────────────────────────────────────
        card.add_widget(MDFlatButton(
            text='✕   Cancelar',
            theme_text_color='Custom',
            text_color=(1, 1, 1, 0.32),
            size_hint=(1, None),
            height=dp(40),
            on_release=self._on_cancelar,
        ))

        # ── Altura dinámica del card según botones ────────────────
        tiene_imgs = self.plataforma in self.SOPORTA_IMAGENES
        card.height = dp(340) if tiene_imgs else dp(280)

        raiz.add_widget(card)
        self.add_widget(raiz)

    # ── Handlers de botones ───────────────────────────────────────

    def _on_descargar_video(self, *args):
        if self._descargando:
            return
        self._descargando = True
        self._deshabilitar_botones()
        self._set_estado('🔄 Iniciando descarga de video...', (0, 0.9, 1, 1))
        threading.Thread(
            target=self._hilo_video,
            daemon=True
        ).start()

    def _on_descargar_imagenes(self, *args):
        if self._descargando:
            return
        self._descargando = True
        self._deshabilitar_botones()
        self._set_estado('🔄 Iniciando descarga de imágenes...', (0, 0.9, 1, 1))
        threading.Thread(
            target=self._hilo_imagenes,
            daemon=True
        ).start()

    def _on_cancelar(self, *args):
        self.app_ref.stop()

    # ── Hilos de descarga ─────────────────────────────────────────

    def _hilo_video(self):
        """Hilo: descarga el video y manda la app al fondo."""
        try:
            from mstl_logic import descargar_solo_video
            # Notificar y enviar al fondo ANTES de la descarga larga
            Clock.schedule_once(lambda dt: self._lanzar_y_fondo(
                '📹 Descargando video MP4...',
                '⬇️ Descarga de video iniciada',
            ), 0)
            # La descarga sigue aunque la UI esté al fondo
            descargar_solo_video(self.url)
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._set_estado(f'❌ {str(e)[:55]}', (1, 0.25, 0.25, 1)), 0
            )
            self._descargando = False

    def _hilo_imagenes(self):
        """Hilo: descarga imágenes/carrusel y manda la app al fondo."""
        try:
            from mstl_logic import descargar_solo_imagenes
            Clock.schedule_once(lambda dt: self._lanzar_y_fondo(
                '🖼️ Descargando imágenes...',
                '⬇️ Descarga de imágenes iniciada',
            ), 0)
            descargar_solo_imagenes(self.url)
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._set_estado(f'❌ {str(e)[:55]}', (1, 0.25, 0.25, 1)), 0
            )
            self._descargando = False

    # ── Helpers de UI ─────────────────────────────────────────────

    def _lanzar_y_fondo(self, estado_texto, notif_texto):
        """
        Muestra el estado de descarga, envía la notificación Android
        y manda la app al segundo plano para que el usuario vuelva
        a su red social mientras la descarga corre en el hilo daemon.
        """
        self._set_estado(estado_texto, (0, 1, 0.5, 1))
        self.app_ref.enviar_notificacion('CyberLoad ⬇️', notif_texto)
        # Pequeña pausa para que el usuario vea el estado antes de ir al fondo
        Clock.schedule_once(lambda dt: self.app_ref.ir_a_segundo_plano(), 0.8)

    def _set_estado(self, texto, color=(0, 0.9, 1, 0.65)):
        self.lbl_estado.text = texto
        self.lbl_estado.text_color = color

    def _deshabilitar_botones(self):
        self.btn_video.disabled = True
        if hasattr(self, 'btn_imgs'):
            self.btn_imgs.disabled = True


# ─────────────────────────────────────────────────────────
#  UI NORMAL — Pantalla principal de la app
#  Sin cambios respecto a V12. Solo se usa cuando la app
#  es lanzada directamente (NO via share intent).
# ─────────────────────────────────────────────────────────

class CyberLoadUI(BoxLayout):

    def __init__(self, app_ref, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.app_ref = app_ref
        self._construir()

    def _construir(self):
        self.add_widget(MDTopAppBar(
            title="⚡ CYBERLOAD V13",
            md_bg_color=(0, 0.9, 1, 0.12),
            specific_text_color=(0, 0.9, 1, 1),
            elevation=2,
        ))

        inner = BoxLayout(
            orientation='vertical',
            padding=[dp(20), dp(16), dp(20), dp(16)],
            spacing=dp(14),
        )

        inner.add_widget(MDLabel(
            text="CYBERLOAD",
            halign="center",
            theme_text_color="Custom",
            text_color=(0, 0.9, 1, 1),
            font_style="H4",
            size_hint_y=None,
            height=dp(56),
        ))

        inner.add_widget(MDLabel(
            text="Instagram · TikTok · YouTube · Facebook",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 0.76, 0, 0.8),
            font_style="Caption",
            size_hint_y=None,
            height=dp(22),
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
                "🔌  Requiere conexión activa\n\n"
                "💡  Comparte un enlace a esta app\n"
                "    para descarga rápida ⚡"
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
#  CLASE PRINCIPAL MDApp
# ─────────────────────────────────────────────────────────

class CyberLoadApp(MDApp):

    def build(self):
        self.theme_cls.theme_style     = "Dark"
        self.theme_cls.primary_palette = "Cyan"
        self.theme_cls.accent_palette  = "Amber"
        self.title = "CyberLoad"

        # ── Detectar si la app fue lanzada via Share Intent ───────
        self._url_compartida  = None
        self._plataforma_compartida = 'general'
        self._capturar_intent_share()

        # ── Modo flotante (share intent) ──────────────────────────
        if self._url_compartida:
            return PantallaFlotante(
                url=self._url_compartida,
                plataforma=self._plataforma_compartida,
                app_ref=self,
            )

        # ── Modo normal (lanzamiento directo) ─────────────────────
        pantalla = MDScreen(md_bg_color=(0.04, 0.04, 0.06, 1))
        self.ui  = CyberLoadUI(app_ref=self)
        pantalla.add_widget(self.ui)
        return pantalla

    # ─────────────────────────────────────────────────────
    #  CAPTURA DEL INTENT SHARE (V13)
    #
    #  Detecta si la app fue abierta via "Compartir" desde
    #  otra app (Instagram, Chrome, etc.).
    #
    #  android.intent.action.SEND con mimeType text/plain
    #  → el texto del enlace viene en EXTRA_TEXT.
    #
    #  Si el texto contiene una URL (http/https), la guarda
    #  en self._url_compartida y detecta la plataforma.
    # ─────────────────────────────────────────────────────

    def _capturar_intent_share(self):
        try:
            from jnius import autoclass

            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            intent   = activity.getIntent()
            action   = intent.getAction()

            ACCION_SEND = 'android.intent.action.SEND'
            EXTRA_TEXT  = 'android.intent.extra.TEXT'

            if action == ACCION_SEND:
                texto = intent.getStringExtra(EXTRA_TEXT)
                if texto:
                    # Extraer la URL si viene con texto extra
                    # (ej. "Mira este video https://...")
                    import re
                    match = re.search(r'https?://\S+', texto)
                    url = match.group(0) if match else texto.strip()

                    if url.startswith('http'):
                        self._url_compartida = url
                        # Detectar plataforma
                        from mstl_logic import detectar_plataforma
                        self._plataforma_compartida = detectar_plataforma(url)
                        print(f"[SHARE] URL capturada: {url[:60]}")
                        print(f"[SHARE] Plataforma: {self._plataforma_compartida}")

        except Exception as e:
            # No Android o pyjnius no disponible → modo normal
            print(f"[SHARE] Sin intent compartido ({type(e).__name__})")

    # ─────────────────────────────────────────────────────
    #  NOTIFICACIÓN ANDROID (V13)
    #
    #  Usa plyer como capa principal (más limpio y portable).
    #  Si plyer falla, intenta pyjnius directo como fallback.
    #  En Pydroid 3 / Desktop: solo imprime en consola.
    # ─────────────────────────────────────────────────────

    def enviar_notificacion(self, titulo: str, texto: str):
        # ── Intento 1: plyer (recomendado) ────────────────────────
        try:
            from plyer import notification
            notification.notify(
                title=titulo,
                message=texto,
                app_name='CyberLoad',
            )
            print(f"[NOTIF] ✅ {titulo}: {texto}")
            return
        except Exception as e_plyer:
            print(f"[NOTIF] plyer falló ({e_plyer}), intentando pyjnius...")

        # ── Intento 2: pyjnius directo (fallback Android) ─────────
        try:
            from jnius import autoclass

            PythonActivity  = autoclass('org.kivy.android.PythonActivity')
            context         = PythonActivity.mActivity

            NotificationManager = autoclass('android.app.NotificationManager')
            NotificationChannel = autoclass('android.app.NotificationChannel')
            Builder             = autoclass('android.app.Notification$Builder')
            CharSequence        = autoclass('java.lang.CharSequence')

            canal_id     = "cyberload_v13"
            importancia  = NotificationManager.IMPORTANCE_DEFAULT

            # Crear canal (obligatorio en Android 8+ / API 26+)
            nm = context.getSystemService(context.NOTIFICATION_SERVICE)
            canal = NotificationChannel(canal_id, "CyberLoad Descargas", importancia)
            nm.createNotificationChannel(canal)

            # Construir notificación
            builder = Builder(context, canal_id)
            builder.setContentTitle(titulo)
            builder.setContentText(texto)
            builder.setSmallIcon(context.getApplicationInfo().icon)
            builder.setAutoCancel(True)

            nm.notify(13001, builder.build())
            print(f"[NOTIF] ✅ pyjnius: {titulo}")

        except Exception as e_jnius:
            # Entorno de escritorio / Pydroid — solo log
            print(f"[NOTIF] {titulo}: {texto} (sin notif Android: {e_jnius})")

    # ─────────────────────────────────────────────────────
    #  IR AL SEGUNDO PLANO (V13)
    #
    #  Envía la Activity al fondo sin matar el proceso.
    #  Los hilos daemon de descarga siguen corriendo.
    #  El usuario vuelve automáticamente a la app anterior
    #  (su red social).
    # ─────────────────────────────────────────────────────

    def ir_a_segundo_plano(self):
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            PythonActivity.mActivity.moveTaskToBack(True)
            print("[BG] App enviada al segundo plano ✅")
        except Exception as e:
            print(f"[BG] moveTaskToBack falló ({e}) → cerrando app")
            self.stop()

    # ─────────────────────────────────────────────────────
    #  ON_START — Solicitar permisos (ambos modos)
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

            # Solo descargar cookies en modo normal (no en flotante)
            if self._url_compartida:
                # Modo flotante: solo pedir permisos, sin más
                request_permissions(permisos_requeridos, self._callback_permisos_flotante)
            else:
                # Modo normal: pedir permisos + descargar cookies
                self.ui.set_estado("🔐 Solicitando permisos...", color=(0, 0.9, 1, 0.7))
                request_permissions(permisos_requeridos, self._callback_permisos)

        except ImportError:
            # Desktop / Pydroid 3 — sin permisos Android
            if not self._url_compartida:
                self.ui.set_estado("🌐 Verificando cookies...", color=(0, 0.9, 1, 0.7))
                threading.Thread(target=self._hilo_cookies, daemon=True).start()

    def _callback_permisos_flotante(self, permisos, resultados):
        """Callback de permisos en modo flotante — sin acción extra."""
        denegados = [p for p, r in zip(permisos, resultados) if not r]
        if denegados:
            print(f"[PERMS] Denegados: {[p.split('.')[-1] for p in denegados]}")

    def _callback_permisos(self, permisos, resultados):
        """Callback de permisos en modo normal."""
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
        threading.Thread(target=self._hilo_cookies, daemon=True).start()

    def _hilo_cookies(self):
        def ui_callback(texto, color):
            self.ui.set_estado(texto, color)

        exito = descargar_cookies_github(callback=ui_callback)

        def estado_final(dt):
            cookies_ok = os.path.exists(get_cookies_path())
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
#  PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        CyberLoadApp().run()
    except Exception as exc:
        _escribir_crash_log(exc)
        sys.exit(1)
