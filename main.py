"""
╔══════════════════════════════════════════════════════════╗
║         CYBERLOAD — Descargador Cyberpunk  v1.6          ║
║         KivyMD + mstl_logic.py                          ║
║         Instagram · TikTok · YouTube · Facebook          ║
║         Compatible: Pydroid 3 / Android APK              ║
╚══════════════════════════════════════════════════════════╝

Cambios v1.6:
    · request_permissions verificado en on_start() — es el único
      lugar correcto en Android. Si estuviera en build() la app
      crashearía porque la actividad aún no está lista para
      mostrar diálogos de sistema.
    · MANAGE_EXTERNAL_STORAGE se añade condicionalmente con
      try/except AttributeError para compatibilidad Android 8/9.
    · Crash log guardado en /sdcard/cyberload_error.txt
    · try-except global en __main__ captura cualquier excepción
      de arranque y la escribe en el log antes de cerrar.

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
#  Se llama desde el bloque try-except de __main__ si la
#  app lanza una excepción no capturada durante el arranque.
#
#  Nombre del archivo: cyberload_error.txt
#  Rutas candidatas (en orden de preferencia):
#    1. /sdcard/cyberload_error.txt
#    2. /storage/emulated/0/cyberload_error.txt
#    3. <carpeta del script>/cyberload_error.txt
# ─────────────────────────────────────────────────────────

def _escribir_crash_log(exc: Exception) -> None:
    """
    Guarda el traceback completo en cyberload_error.txt.
    Prueba /sdcard/, /storage/emulated/0/ y el CWD.
    """
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

    # Último recurso: imprimir en logcat (visible con adb logcat)
    print(contenido)


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
            md_bg_color=(1, 0.76, 0, 1),
            text_color=(0.05, 0.05, 0.05, 1),
            elevation=6,
            on_release=self.ejecutar_descarga,
        )
        inner.add_widget(self.btn_descargar)

        # ── 6. LABEL DE ESTADO (con ScrollView) ─────────
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
        Valida la URL y lanza la descarga en un hilo secundario.
        """
        url = self.url_field.text.strip()

        if not url:
            self._set_estado(
                "⚠  Ingresa una URL válida",
                color=(1, 0.5, 0, 1),
            )
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
        """
        Proceso de descarga en hilo secundario.
        Nunca toca widgets directamente — usa Clock.schedule_once.
        """
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
        """Recibe mensajes de progreso desde el hilo de descarga."""
        Clock.schedule_once(
            lambda dt: self._set_estado(
                f"⚙️  {mensaje[:60]}",
                color=(0, 0.9, 1, 1),
            ), 0,
        )

    def _finalizar(self, exito=True, detalle=""):
        """Actualiza la UI al terminar la descarga."""
        self.btn_descargar.disabled = False

        if exito:
            self.url_field.text = ""
            self._set_estado(
                "✅  ¡Descarga completa!\n📂 /storage/emulated/0/Download/",
                color=(0, 1, 0.5, 1),
            )
        else:
            self._set_estado(
                f"❌  Error:\n{detalle}",
                color=(1, 0.25, 0.25, 1),
            )

    def _set_estado(self, texto, color=(0, 0.9, 1, 0.85)):
        """Helper para actualizar el label de estado."""
        self.lbl_estado.text = texto
        self.lbl_estado.text_color = color


# ─────────────────────────────────────────────────────────
#  Clase Principal MDApp
# ─────────────────────────────────────────────────────────

class CyberLoadApp(MDApp):
    """
    Aplicación principal KivyMD.
    Tema Cyberpunk: Cian (primary) + Ámbar (accent).

    Ciclo de vida Android:
        build()    → construye la UI. NO pedir permisos aquí.
        on_start() → la actividad ya está visible. Pedir permisos AQUÍ.

    Por qué on_start() y NO build():
        En build() la ventana de Android aún no está inicializada.
        Si se llama a request_permissions() en build(), Android no
        puede mostrar el diálogo del sistema → crash inmediato.
        on_start() garantiza que la actividad está completamente
        lista antes de mostrar cualquier diálogo de permisos.
    """

    def build(self):
        # ── Configuración del Tema ───────────────────────
        self.theme_cls.theme_style     = "Dark"
        self.theme_cls.primary_palette = "Cyan"
        self.theme_cls.accent_palette  = "Amber"
        self.title = "CyberLoad"

        # ── Pantalla Raíz ────────────────────────────────
        pantalla = MDScreen(
            md_bg_color=(0.04, 0.04, 0.06, 1),
        )

        # ── Layout de Interfaz ───────────────────────────
        self.ui = CyberLoadUI(app_ref=self)
        pantalla.add_widget(self.ui)

        return pantalla

    # ─────────────────────────────────────────────────────
    #  on_start — Solicitud de Permisos Android
    #
    #  VERIFICADO v1.6:
    #  Los permisos se solicitan aquí, en on_start(), que es
    #  el único lugar correcto del ciclo de vida de KivyMD.
    #
    #  Flujo:
    #    1. on_start() se ejecuta → la ventana ya es visible
    #    2. request_permissions() muestra el diálogo de sistema
    #    3. El usuario responde → Android llama _callback_permisos
    #    4. _callback_permisos actualiza el label de estado en la UI
    #
    #  El try/except ImportError permite que el archivo funcione
    #  en Pydroid 3 y PC donde el módulo 'android' no existe.
    # ─────────────────────────────────────────────────────

    def on_start(self):
        """Se ejecuta una vez que la ventana principal ya está visible."""
        try:
            from android.permissions import (
                Permission,
                request_permissions,
            )

            # Permisos base — requeridos en todos los Android
            permisos_requeridos = [
                Permission.INTERNET,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ]

            # MANAGE_EXTERNAL_STORAGE existe solo en Android 11+ (API 30+).
            # Se añade condicionalmente para no crashear en Android 8/9
            # donde este Permission no está definido en python-for-android.
            try:
                permisos_requeridos.append(Permission.MANAGE_EXTERNAL_STORAGE)
            except AttributeError:
                # Android 8 o 9: MANAGE_EXTERNAL_STORAGE no disponible.
                # READ/WRITE_EXTERNAL_STORAGE son suficientes en esas versiones.
                pass

            request_permissions(
                permisos_requeridos,
                self._callback_permisos,
            )

        except ImportError:
            # Entorno de escritorio (Pydroid 3, PC) — sin módulo 'android'
            self.ui._set_estado(
                "[ Esperando link... ]",
                color=(0, 0.9, 1, 0.85),
            )

    def _callback_permisos(self, permisos, resultados):
        """
        Llamado por Android cuando el usuario responde al diálogo.

        Parámetros:
            permisos   (list[str]) : nombres de los permisos solicitados
            resultados (list[bool]): True si fue concedido, False si denegado
        """
        denegados = [
            p for p, r in zip(permisos, resultados) if not r
        ]

        if not denegados:
            # Todos los permisos concedidos → listo para descargar
            self.ui._set_estado(
                "✅ Permisos OK\n[ Ingresa un enlace para descargar ]",
                color=(0, 1, 0.5, 1),
            )
        else:
            # Algunos permisos denegados → advertir al usuario
            nombres_cortos = [p.split(".")[-1] for p in denegados]
            self.ui._set_estado(
                f"⚠️ Permisos denegados:\n{', '.join(nombres_cortos)}\n"
                "Las descargas pueden fallar.",
                color=(1, 0.6, 0, 1),
            )


# ─────────────────────────────────────────────────────────
#  Punto de Entrada con Protección de Crash
#
#  VERIFICADO v1.6:
#  Cualquier excepción no capturada durante CyberLoadApp().run()
#  queda registrada en /sdcard/cyberload_error.txt antes de que
#  la app se cierre. Facilita el diagnóstico sin necesidad de
#  conectar el dispositivo por USB ni usar adb logcat.
#
#  Para leer el error después de un crash:
#    Abre el explorador de archivos → /sdcard/ → cyberload_error.txt
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        CyberLoadApp().run()

    except Exception as exc:
        _escribir_crash_log(exc)
        sys.exit(1)
