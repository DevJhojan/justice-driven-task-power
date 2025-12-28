"""
Vista para mostrar errores de la aplicación.
"""
import flet as ft
import traceback

# Intentar importar pyperclip, si no está disponible usar método alternativo
try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False


class ErrorView:
    """Vista para mostrar errores con opción de copiar."""
    
    def __init__(self, page: ft.Page, error: Exception, context: str = ""):
        """
        Inicializa la vista de error.
        
        Args:
            page: Página de Flet.
            error: Excepción que ocurrió.
            context: Contexto adicional sobre dónde ocurrió el error.
        """
        self.page = page
        self.error = error
        self.context = context
        
        # Obtener el traceback completo
        self.error_message = str(error)
        self.error_traceback = "".join(traceback.format_exception(
            type(error), error, error.__traceback__
        ))
        self.full_error = f"{self.context}\n\n{self.error_message}\n\n{self.error_traceback}" if self.context else f"{self.error_message}\n\n{self.error_traceback}"
    
    def build_view(self) -> ft.View:
        """Construye la vista de error."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.BLACK if is_dark else ft.Colors.WHITE
        text_color = ft.Colors.WHITE if is_dark else ft.Colors.BLACK
        error_color = ft.Colors.RED_400 if is_dark else ft.Colors.RED_700
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_600
        
        def copy_error(e):
            """Copia el error al portapapeles."""
            try:
                # Intentar usar pyperclip si está disponible
                if HAS_PYPERCLIP:
                    pyperclip.copy(self.full_error)
                else:
                    # Usar métodos del sistema operativo
                    import subprocess
                    import sys
                    if sys.platform == "linux":
                        # Linux: usar xclip o xsel
                        try:
                            subprocess.run(["xclip", "-selection", "clipboard"], input=self.full_error.encode(), check=True)
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            try:
                                subprocess.run(["xsel", "--clipboard", "--input"], input=self.full_error.encode(), check=True)
                            except (subprocess.CalledProcessError, FileNotFoundError):
                                raise Exception("No se encontró xclip ni xsel. Instala uno de ellos: sudo apt-get install xclip")
                    elif sys.platform == "darwin":
                        # macOS: usar pbcopy
                        subprocess.run(["pbcopy"], input=self.full_error.encode(), check=True)
                    elif sys.platform == "win32":
                        # Windows: usar clip
                        subprocess.run(["clip"], input=self.full_error.encode(), check=True, shell=True)
                    else:
                        raise Exception(f"Plataforma no soportada: {sys.platform}")
                
                copy_button.text = "¡Copiado!"
                copy_button.bgcolor = ft.Colors.GREEN
                self.page.update()
                
                # Volver al texto original después de 2 segundos
                def reset_button():
                    copy_button.text = "Copiar Error"
                    copy_button.bgcolor = btn_color
                    self.page.update()
                
                import threading
                timer = threading.Timer(2.0, reset_button)
                timer.start()
            except Exception as ex:
                # Si falla, mostrar el error en el texto
                error_text.value = f"Error al copiar: {ex}\n\n{self.full_error}"
                self.page.update()
        
        def go_back(e):
            """Vuelve a la página principal."""
            self.page.go("/")
            self.page.update()
        
        # Botón de copiar
        copy_button = ft.ElevatedButton(
            "Copiar Error",
            icon=ft.Icons.COPY,
            on_click=copy_error,
            bgcolor=btn_color,
            color=ft.Colors.WHITE
        )
        
        # Texto del error (scrollable)
        error_text = ft.Text(
            self.full_error,
            size=12,
            color=error_color,
            selectable=True,
            font_family="monospace"
        )
        
        # Contenedor del error con scroll
        error_container = ft.Container(
            content=ft.Column(
                [error_text],
                scroll=ft.ScrollMode.AUTO,
                expand=True
            ),
            padding=16,
            border=ft.border.all(2, error_color),
            border_radius=8,
            bgcolor=ft.Colors.GREY_900 if is_dark else ft.Colors.GREY_100,
            expand=True
        )
        
        # Header
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ERROR, color=error_color, size=32),
                    ft.Text(
                        "Error en la Aplicación",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=error_color
                    )
                ],
                spacing=12
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            bgcolor=ft.Colors.RED_900 if is_dark else ft.Colors.RED_50
        )
        
        # Contenido principal
        content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Se ha producido un error. Por favor, copia el mensaje completo para reportarlo.",
                        size=16,
                        color=text_color,
                        weight=ft.FontWeight.BOLD
                    ),
                    error_container,
                    ft.Row(
                        [
                            copy_button,
                            ft.ElevatedButton(
                                "Volver al Inicio",
                                icon=ft.Icons.HOME,
                                on_click=go_back,
                                bgcolor=btn_color,
                                color=ft.Colors.WHITE
                            )
                        ],
                        spacing=12
                    )
                ],
                spacing=16,
                expand=True
            ),
            padding=20,
            expand=True
        )
        
        return ft.View(
            route="/error",
            controls=[
                ft.Column(
                    [header, content],
                    spacing=0,
                    expand=True
                )
            ],
            bgcolor=bg_color
        )

