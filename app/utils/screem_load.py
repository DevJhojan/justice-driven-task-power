"""
Pantalla de carga de la aplicación
Muestra una imagen de fondo y una barra de carga horizontal

Uso básico:
    from app.utils.screem_load import LoadingScreen
    
    # Crear la pantalla de carga
    loading_screen = LoadingScreen()
    
    # Agregar a la página
    page.add(loading_screen.build())
    page.update()
    
    # Iniciar la animación
    loading_screen.start_loading(page, duration=5.0)

Uso con callback:
    def on_loading_complete():
        # Hacer algo cuando termine la carga
        print("Carga completada!")
    
    loading_screen = LoadingScreen(on_complete=on_loading_complete)
    page.add(loading_screen.build())
    loading_screen.start_loading(page, duration=5.0)
"""

import flet as ft
from app.utils.helpers import (
    get_asset_path,
    get_responsive_padding,
    get_responsive_width,
    format_percentage,
)


class LoadingScreen:
    """Clase que representa la pantalla de carga"""
    
    def __init__(self, on_complete=None):
        """
        Inicializa la pantalla de carga
        
        Args:
            on_complete: Callback opcional que se ejecuta cuando la animación termina
        """
        self.bar_height = 20
        self.progress_value = 0.0
        self.animation_running = False
        self.on_complete = on_complete  # Callback cuando termine la animación
        
        # Contenedor del fondo de la barra (oscuro para combinar con la imagen)
        # Usamos un color oscuro que combine con la imagen dorada
        self.bar_background = ft.Container(
            height=self.bar_height,
            bgcolor="#1A1A1A",  # Gris muy oscuro que combina con la imagen
            border_radius=10,
        )
        
        # Contenedor del progreso (dorado/amarillo para combinar con la imagen dorada)
        self.progress_fill = ft.Container(
            width=0,
            height=self.bar_height,
            bgcolor="#FFD700",  # Color dorado (Gold)
            border_radius=10,
        )
        
        # Row para alinear el progreso desde la izquierda
        self.progress_row = ft.Row(
            controls=[self.progress_fill],
            spacing=0,
            alignment=ft.MainAxisAlignment.START,
        )
        
        # Label que muestra el porcentaje (centrado sobre la barra)
        self.percentage_label = ft.Text(
            value="0%",
            size=12,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
            text_align=ft.TextAlign.CENTER,
        )
        
        # Container para centrar el label sobre la barra
        # Usamos un Column centrado para alinear el texto
        self.label_container = ft.Container(
            content=ft.Column(
                controls=[self.percentage_label],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0,
            ),
            width=600,  # Se actualizará dinámicamente
            height=self.bar_height,
        )
        
        # Stack que contiene el fondo, el progreso y el label
        self.progress_bar = ft.Stack(
            controls=[
                self.bar_background,
                self.progress_row,
                self.label_container,  # Label sobre la barra
            ],
            height=self.bar_height,
        )
        
    def build(self, page: ft.Page = None) -> ft.Container:
        """
        Construye y retorna el widget de la pantalla de carga
        
        Args:
            page: Objeto Page de Flet (opcional, para cálculos responsive)
        
        Returns:
            Container con la pantalla de carga completa
        """
        # Obtener la ruta de la imagen usando helper
        image_path = get_asset_path("app_icon.png")
        
        # Calcular padding responsive usando helper
        padding_value = get_responsive_padding(page=page)
        
        # Crear la imagen de fondo que ocupa toda la pantalla de forma responsive
        background_image = ft.Image(
            src=str(image_path),
            expand=True,
            # La imagen se ajustará automáticamente al contenedor
        )
        
        # Contenedor para la imagen que ocupa todo el ancho y alto
        # Usamos posicionamiento absoluto para que ocupe toda la pantalla
        image_container = ft.Container(
            content=background_image,
            left=0,
            right=0,
            top=0,
            bottom=0,
            expand=True,
        )
        
        # Contenedor principal con la imagen de fondo completa y la barra en la parte inferior
        return ft.Container(
            content=ft.Stack(
                controls=[
                    # Imagen de fondo que ocupa toda la pantalla
                    image_container,
                    # Barra de progreso en la parte inferior (bottom bar) - responsive
                    ft.Container(
                        content=self.progress_bar,
                        bottom=0,
                        left=0,
                        right=0,
                        padding=padding_value,  # Padding responsive
                    ),
                ],
            ),
            expand=True,
            bgcolor=ft.Colors.BLACK,  # Fondo negro por si la imagen no carga
        )
    
    def start_loading(self, page: ft.Page, duration: float = 5.0):
        """
        Inicia la animación de carga usando un enfoque asíncrono
        
        Args:
            page: Objeto Page de Flet
            duration: Duración de la animación en segundos (default: 5.0)
        """
        import asyncio
        
        self.animation_running = True
        
        # Calcular el ancho máximo disponible usando helper responsive
        # get_responsive_width ya multiplica el padding por 2 internamente
        def get_max_width():
            # Usar helper para obtener el ancho con padding responsive
            # get_responsive_width ya resta el padding * 2 automáticamente
            return get_responsive_width(page=page)
        
        max_width = get_max_width()
        
        # Actualizar el ancho del fondo de la barra y del label
        self.bar_background.width = max_width
        self.progress_bar.width = max_width
        self.label_container.width = max_width
        
        async def animate():
            """Función asíncrona para animar la barra de progreso"""
            steps = 100
            step_duration = duration / steps
            
            for step in range(steps + 1):
                if not self.animation_running:
                    break
                
                # Recalcular el ancho en cada paso para ser responsive
                current_max_width = get_max_width()
                    
                progress = step / steps
                self.progress_value = progress
                
                # Calcular el ancho del progreso
                progress_width = current_max_width * progress
                
                # Calcular el porcentaje usando helper de formateo
                self.percentage_label.value = format_percentage(progress, decimals=0)
                
                # Actualizar los valores con el ancho actualizado
                self.progress_fill.width = progress_width
                self.bar_background.width = current_max_width
                self.progress_bar.width = current_max_width
                self.label_container.width = current_max_width
                
                # Actualizar la página
                page.update()
                
                # Esperar antes del siguiente paso
                await asyncio.sleep(step_duration)
            
            self.animation_running = False
            
            # Ejecutar callback si existe
            if self.on_complete:
                self.on_complete()
        
        # Ejecutar la animación asíncrona
        page.run_task(animate)
    
    def stop_loading(self):
        """
        Detiene la animación de carga
        """
        self.animation_running = False
    
    def is_complete(self) -> bool:
        """
        Verifica si la animación ha terminado
        
        Returns:
            True si la animación ha terminado, False en caso contrario
        """
        return not self.animation_running and self.progress_value >= 1.0
 