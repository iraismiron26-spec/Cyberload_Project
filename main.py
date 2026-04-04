"""
╔══════════════════════════════════════════════════════════╗
║         CYBERLOAD — Descargador Cyberpunk  v1.9          ║
║         KivyMD + mstl_logic.py                          ║
║         Instagram · TikTok · YouTube · Facebook          ║
║         Compatible: Pydroid 3 / Android APK              ║
╚══════════════════════════════════════════════════════════╝

Sin cambios de lógica en v1.9.
Permisos en on_start() — correcto y verificado.
Crash log en /sdcard/cyberload_error.txt.

Dependencias (instalar en terminal de Pydroid 3):
    pip install kivymd yt-dlp instaloader
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

        scroll = ScrollView(size_hint=(1, None), height=dp(90),
                            do_scroll_x=False, do_scroll_y=True)
        self.lbl_estado = MDLabel(
            text="[ Solicitando permisos... ]",
            halign="center",
            theme_text_color="Custom",
            text_color=(0, 0.9, 1, 0.85),
            font_style="Caption",
            size_hint_y=None,
        )
        self.lbl_estado.bind(
            texture_size=lambda inst, val: setattr(
                inst, "height", max(dp(90), val[1] + dp(12))
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
                "📂  Archivos guardados en:\n"
                "/storage/emulated/0/Download/\n\n"
                "⚙️  Motores: Instaloader · yt-dlp\n"
                "🔌  Requiere conexión activa"
            ),
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 0.30),
            font_style="Caption",
        ))

        self.add_widget(inner)

    def ejecutar_descarga(self, *args):
        url = self.url_field.text.strip()
        if not url:
            self._set_estado("⚠  Ingresa una URL válida", color=(1, 0.5, 0, 1))
            return
        self.btn_descargar.disabled = True
        self._set_estado("🔄  Iniciando descarga...", color=(0, 0.9, 1, 1))
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
            lambda dt: self._set_estado(f"⚙️  {mensaje[:60]}", color=(0, 0.9, 1, 1)), 0)

    def _finalizar(self, exito=True, detalle=""):
        self.btn_descargar.disabled = False
        if exito:
            self.url_field.text = ""
            self._set_estado(
                "✅  ¡Descarga completa!\n📂 /storage/emulated/0/Download/",
                color=(0, 1, 0.5, 1))
        else:
            self._set_estado(f"❌  Error:\n{detalle}", color=(1, 0.25, 0.25, 1))

    def _set_estado(self, texto, color=(0, 0.9, 1, 0.85)):
        self.lbl_estado.text = texto
        self.lbl_estado.text_color = color


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

    def on_start(self):
        """
        PERMISOS EN on_start() — OBLIGATORIO.
        Nunca en build(): la actividad Android no está lista aún.
        """
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
                pass  # Android 8/9: no disponible

            request_permissions(permisos_requeridos, self._callback_permisos)

        except ImportError:
            self.ui._set_estado("[ Esperando link... ]", color=(0, 0.9, 1, 0.85))

    def _callback_permisos(self, permisos, resultados):
        denegados = [p for p, r in zip(permisos, resultados) if not r]
        if not denegados:
            self.ui._set_estado(
                "✅ Permisos OK\n[ Ingresa un enlace para descargar ]",
                color=(0, 1, 0.5, 1))
        else:
            nombres = [p.split(".")[-1] for p in denegados]
            self.ui._set_estado(
                f"⚠️ Permisos denegados:\n{', '.join(nombres)}\nLas descargas pueden fallar.",
                color=(1, 0.6, 0, 1))


# ─────────────────────────────────────────────────────────
#  Punto de Entrada
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        CyberLoadApp().run()
    except Exception as exc:
        _escribir_crash_log(exc)
        sys.exit(1)
