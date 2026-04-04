"""
╔══════════════════════════════════════════════════════════╗
║         CYBERLOAD — Descargador Cyberpunk  v1.7          ║
║         KivyMD + mstl_logic.py                          ║
║         Instagram · TikTok · YouTube · Facebook          ║
║         Compatible: Pydroid 3 / Android APK              ║
╚══════════════════════════════════════════════════════════╝

Permisos Android (verificado v1.7):
    · request_permissions() está en on_start() — CORRECTO.
      Si estuviera en build() la app crashearía porque la
      actividad de Android aún no está lista para diálogos.
    · MANAGE_EXTERNAL_STORAGE se añade con try/except
      AttributeError para compatibilidad con Android 8/9.
    · Crash log en /sdcard/cyberload_error.txt.

Dependencias (instalar en terminal de Pydroid 3):
    pip install kivymd
    pip install yt-dlp
    pip install instaloader
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
#
#  Guarda el traceback en /sdcard/cyberload_error.txt.
#  Prueba 3 rutas en orden y escribe en la primera que funcione.
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
#  Widget Principal — Contenedor de la Interfaz
# ─────────────────────────────────────────────────────────

class CyberLoadUI(BoxLayout):

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

        # ── 2. CONTENEDOR INTERIOR ───────────────────────
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

        # ── 5. BOTÓN PRINCIPAL ───────────────────────────
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

        # ── 6. LABEL DE ESTADO ───────────────────────────
        scroll = ScrollView(
            size_hint=(1, None),
            height=dp(90),
            do_scroll_x=False,
            do_scroll_y=True,
        )
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

        # ── 7. SEPARADOR ─────────────────────────────────
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
    #  Funciones de descarga
    # ─────────────────────────────────────────────────────

    def ejecutar_descarga(self, *args):
        url = self.url_field.text.strip()

        if not url:
            self._set_estado("⚠  Ingresa una URL válida", color=(1, 0.5, 0, 1))
            return

        self.btn_descargar.disabled = True
        self._set_estado("🔄  Iniciando descarga...", color=(0, 0.9, 1, 1))

        hilo = threading.Thread(
            target=self._proceso_descarga,
            args=(url,),
            daemon=True,
        )
        hilo.start()

    def _proceso_descarga(self, url):
        try:
            from mstl_logic import descargar
            descargar(url, callback=self._ui_callback)
            Clock.schedule_once(lambda dt: self._finalizar(exito=True), 0)

        except ImportError:
            Clock.schedule_once(
                lambda dt: self._finalizar(
                    exito=False,
                    detalle=(
                        "❌ mstl_logic.py no encontrado.\n"
                        "Colócalo en la misma carpeta que main.py"
                    ),
                ), 0,
            )

        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._finalizar(exito=False, detalle=str(e)[:80]), 0
            )

    def _ui_callback(self, mensaje):
        Clock.schedule_once(
            lambda dt: self._set_estado(
                f"⚙️  {mensaje[:60]}", color=(0, 0.9, 1, 1),
            ), 0,
        )

    def _finalizar(self, exito=True, detalle=""):
        self.btn_descargar.disabled = False
        if exito:
            self.url_field.text = ""
            self._set_estado(
                "✅  ¡Descarga completa!\n📂 /storage/emulated/0/Download/",
                color=(0, 1, 0.5, 1),
            )
        else:
            self._set_estado(f"❌  Error:\n{detalle}", color=(1, 0.25, 0.25, 1))

    def _set_estado(self, texto, color=(0, 0.9, 1, 0.85)):
        self.lbl_estado.text = texto
        self.lbl_estado.text_color = color


# ─────────────────────────────────────────────────────────
#  Clase Principal MDApp
# ─────────────────────────────────────────────────────────

class CyberLoadApp(MDApp):
    """
    Ciclo de vida:
        build()    → construye la UI. NO pedir permisos aquí.
        on_start() → actividad visible. Pedir permisos AQUÍ.
    """

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
        VERIFICADO v1.7: Permisos solicitados aquí, en on_start().
        Nunca en build() — causaría crash en Android 6+ (API 23+).
        """
        try:
            from android.permissions import Permission, request_permissions

            permisos_requeridos = [
                Permission.INTERNET,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ]

            # MANAGE_EXTERNAL_STORAGE solo existe en Android 11+ (API 30+).
            # try/except evita crash en Android 8 y 9.
            try:
                permisos_requeridos.append(Permission.MANAGE_EXTERNAL_STORAGE)
            except AttributeError:
                pass

            request_permissions(permisos_requeridos, self._callback_permisos)

        except ImportError:
            # Pydroid 3 o PC — sin módulo android
            self.ui._set_estado(
                "[ Esperando link... ]",
                color=(0, 0.9, 1, 0.85),
            )

    def _callback_permisos(self, permisos, resultados):
        denegados = [p for p, r in zip(permisos, resultados) if not r]

        if not denegados:
            self.ui._set_estado(
                "✅ Permisos OK\n[ Ingresa un enlace para descargar ]",
                color=(0, 1, 0.5, 1),
            )
        else:
            nombres_cortos = [p.split(".")[-1] for p in denegados]
            self.ui._set_estado(
                f"⚠️ Permisos denegados:\n{', '.join(nombres_cortos)}\n"
                "Las descargas pueden fallar.",
                color=(1, 0.6, 0, 1),
            )


# ─────────────────────────────────────────────────────────
#  Punto de Entrada — Protección de Crash Global
#
#  Cualquier excepción de arranque se guarda en:
#  /sdcard/cyberload_error.txt
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        CyberLoadApp().run()
    except Exception as exc:
        _escribir_crash_log(exc)
        sys.exit(1)
