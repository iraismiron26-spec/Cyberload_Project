"""
╔══════════════════════════════════════════════════════════╗
║         CYBERLOAD — Descargador Cyberpunk                ║
║         KivyMD + mstl_logic.py                          ║
║         Instagram · TikTok · YouTube · Facebook          ║
║         Compatible: Pydroid 3 / Android                  ║
╚══════════════════════════════════════════════════════════╝

Dependencias (instalar en terminal de Pydroid 3):
    pip install kivymd
    pip install yt-dlp
    pip install instaloader       ← para Instagram

Estructura requerida (misma carpeta):
    main.py        ← este archivo
    mstl_logic.py  ← módulo de descarga
"""

import threading

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
#  Widget Principal — Contenedor de la Interfaz
# ─────────────────────────────────────────────────────────

class CyberLoadUI(BoxLayout):
    """
    Layout vertical que contiene todos los widgets
    de la interfaz de descarga.
    Conectado a mstl_logic.descargar() via threading.
    """

    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)

        self.app_ref = app_ref
        self.orientation = "vertical"
        self.spacing = dp(0)

        # ── 1. BARRA SUPERIOR ───────────────────────────
        self.toolbar = MDTopAppBar(
            title="⚡  C Y B E R L O A D",
            elevation=4,
            md_bg_color=self.app_ref.theme_cls.primary_color,
        )
        self.add_widget(self.toolbar)

        # ── 2. CONTENEDOR INTERIOR (con padding) ────────
        inner = BoxLayout(
            orientation="vertical",
            spacing=dp(20),
            padding=[dp(20), dp(32), dp(20), dp(32)],
        )

        # ── 3. LABEL DECORATIVO ─────────────────────────
        inner.add_widget(
            MDLabel(
                text="[b]// INGRESA TU ENLACE[/b]",
                markup=True,
                halign="left",
                theme_text_color="Custom",
                text_color=(0, 0.9, 1, 0.7),
                font_style="Overline",
                size_hint_y=None,
                height=dp(20),
            )
        )

        # ── 4. CAMPO DE TEXTO (URL) ──────────────────────
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

        # ── 5. BOTÓN PRINCIPAL (AMBER / ORO) ────────────
        self.btn_descargar = MDRaisedButton(
            text="▶  INICIAR DESCARGA",
            font_style="Button",
            size_hint=(1, None),
            height=dp(54),
            md_bg_color=(1, 0.76, 0, 1),       # Amber/Dorado
            text_color=(0.05, 0.05, 0.05, 1),   # Texto oscuro para contraste
            elevation=6,
            on_release=self.ejecutar_descarga,
        )
        inner.add_widget(self.btn_descargar)

        # ── 6. LABEL DE ESTADO (con ScrollView) ─────────
        # El ScrollView permite ver mensajes largos de progreso
        # sin que el layout se rompa en pantallas pequeñas.
        scroll = ScrollView(
            size_hint=(1, None),
            height=dp(90),
            do_scroll_x=False,
            do_scroll_y=True,
        )
        self.lbl_estado = MDLabel(
            text="[ Esperando link... ]",
            halign="center",
            theme_text_color="Custom",
            text_color=(0, 0.9, 1, 0.85),
            font_style="Caption",
            size_hint_y=None,
        )
        # Ajuste dinámico de altura: el label crece con el texto
        self.lbl_estado.bind(
            texture_size=lambda inst, val: setattr(inst, 'height', max(dp(90), val[1] + dp(12)))
        )
        scroll.add_widget(self.lbl_estado)
        inner.add_widget(scroll)

        # ── 7. SEPARADOR DECORATIVO ──────────────────────
        inner.add_widget(
            MDLabel(
                text="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                halign="center",
                theme_text_color="Custom",
                text_color=(0, 0.9, 1, 0.2),
                font_style="Caption",
                size_hint_y=None,
                height=dp(20),
            )
        )

        # ── 8. NOTA INFORMATIVA ──────────────────────────
        inner.add_widget(
            MDLabel(
                text=(
                    "📂  Archivos guardados en:\n"
                    "/storage/emulated/0/Download/\n\n"
                    "⚙️  Motores: Instaloader · yt-dlp\n"
                    "🔌  Requiere conexión activa"
                ),
                halign="center",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 0.30),
                font_style="Caption",
            )
        )

        self.add_widget(inner)

    # ─────────────────────────────────────────────────────
    #  Función Principal de Descarga
    # ─────────────────────────────────────────────────────

    def ejecutar_descarga(self, *args):
        """
        Valida la URL y lanza la descarga en un hilo
        secundario para no bloquear la interfaz de Kivy.
        """
        url = self.url_field.text.strip()

        # Validación de campo vacío
        if not url:
            self._set_estado(
                "⚠  Ingresa una URL válida",
                color=(1, 0.5, 0, 1)   # Naranja advertencia
            )
            return

        # Desactivar botón mientras descarga
        self.btn_descargar.disabled = True
        self._set_estado("🔄  Iniciando descarga...", color=(0, 0.9, 1, 1))

        # Lanzar hilo secundario con daemon=True para que
        # no bloquee el cierre de la app si el usuario sale.
        hilo = threading.Thread(
            target=self._proceso_descarga,
            args=(url,),
            daemon=True,
        )
        hilo.start()

    def _proceso_descarga(self, url):
        """
        Proceso de descarga usando mstl_logic.descargar().
        Corre en hilo secundario — NUNCA tocar widgets de Kivy
        directamente aquí. Usar Clock.schedule_once.

        El parámetro callback=self._ui_callback permite que
        los motores notifiquen el progreso en tiempo real.
        """
        try:
            # Importación diferida: evita crash si mstl_logic.py
            # no está en la misma carpeta.
            from mstl_logic import descargar

            # Llamada principal con callback de progreso.
            descargar(url, callback=self._ui_callback)

            # Llegó aquí sin excepción → descarga exitosa.
            Clock.schedule_once(
                lambda dt: self._finalizar(exito=True), 0
            )

        except ImportError:
            Clock.schedule_once(
                lambda dt: self._finalizar(
                    exito=False,
                    detalle=(
                        "❌ mstl_logic.py no encontrado.\n"
                        "Colócalo en la misma carpeta que main.py"
                    )
                ), 0
            )

        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._finalizar(
                    exito=False,
                    detalle=str(e)[:80]
                ), 0
            )

    def _ui_callback(self, mensaje):
        """
        Recibe mensajes de progreso desde el hilo de descarga.
        Usa Clock.schedule_once para llevarlos al hilo principal
        de Kivy de forma segura (requisito de la arquitectura Kivy).

        Parámetro:
            mensaje (str): texto limpio (sin ANSI) enviado por mstl_logic
        """
        Clock.schedule_once(
            lambda dt: self._set_estado(
                f"⚙️  {mensaje[:60]}",
                color=(0, 0.9, 1, 1)   # Cian activo durante descarga
            ), 0
        )

    def _finalizar(self, exito=True, detalle=""):
        """
        Actualiza la UI al terminar la descarga.
        Siempre se llama desde el hilo principal (via Clock).
        Reactiva el botón, muestra el resultado y limpia la URL.
        """
        self.btn_descargar.disabled = False

        if exito:
            # ── Limpiar el campo de URL automáticamente ──
            self.url_field.text = ""
            self._set_estado(
                "✅  ¡Descarga completa!\n📂 /storage/emulated/0/Download/",
                color=(0, 1, 0.5, 1)    # Verde éxito
            )
        else:
            self._set_estado(
                f"❌  Error:\n{detalle}",
                color=(1, 0.25, 0.25, 1)  # Rojo error
            )

    def _set_estado(self, texto, color=(0, 0.9, 1, 0.85)):
        """Helper para actualizar el label de estado."""
        self.lbl_estado.text       = texto
        self.lbl_estado.text_color = color


# ─────────────────────────────────────────────────────────
#  Clase Principal MDApp
# ─────────────────────────────────────────────────────────

class CyberLoadApp(MDApp):
    """
    Aplicación principal KivyMD.
    Tema Cyberpunk: Cian (primary) + Ámbar (accent).
    """

    def build(self):
        # ── Configuración del Tema ───────────────────────
        self.theme_cls.theme_style     = "Dark"
        self.theme_cls.primary_palette = "Cyan"
        self.theme_cls.accent_palette  = "Amber"
        self.title = "CyberLoad"

        # ── Pantalla Raíz ────────────────────────────────
        pantalla = MDScreen(
            md_bg_color=(0.04, 0.04, 0.06, 1),  # Fondo casi negro
        )

        # ── Layout de Interfaz ───────────────────────────
        ui = CyberLoadUI(app_ref=self)
        pantalla.add_widget(ui)

        return pantalla


# ─────────────────────────────────────────────────────────
#  Punto de Entrada
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    CyberLoadApp().run()
