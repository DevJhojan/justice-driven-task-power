"""
Componente de navegación inferior (Bottom Navigation)
Permite navegar entre diferentes pantallas usando una barra inferior

Uso desde home_view.py o cualquier vista:

    Opción 1 - Usando create_bottom_nav_with_views:
        from app.utils.bottom_nav import create_bottom_nav_with_views
        from app.ui.home_view import HomeView
        from app.ui.task.task_view import TaskView
        from app.ui.settings.settings_view import SettingsView
        
        views = [HomeView(), TaskView(), SettingsView()]
        bottom_nav = create_bottom_nav_with_views(views, page)
        page.add(bottom_nav.build(page))
        page.update()

    Opción 2 - Usando BottomNav directamente con iconos personalizados:
        from app.utils.bottom_nav import BottomNav
        from app.ui.home_view import HomeView
        from app.ui.task.task_view import TaskView
        from app.ui.settings.settings_view import SettingsView
        
        home_view = HomeView()
        task_view = TaskView()
        settings_view = SettingsView()
        
        # Definir iconos y etiquetas personalizados
        icons = {
            0: ft.Icons.HOME,
            1: ft.Icons.TASK,
            2: ft.Icons.SETTINGS,
        }
        labels = {
            0: "Inicio",
            1: "Tareas",
            2: "Configuración",
        }
        
        bottom_nav = BottomNav(
            screens={
                0: home_view.build(),
                1: task_view.build(),
                2: settings_view.build(),
            },
            icons=icons,
            labels=labels
        )
        page.add(bottom_nav.build(page))
        page.update()
"""

import flet as ft
from typing import Callable, Dict, List, Optional


class BottomNav:
    """Clase que maneja la navegación inferior entre pantallas"""
    
    def __init__(
        self, 
        screens: Dict[int, ft.Control], 
        on_navigate: Optional[Callable] = None,
        icons: Optional[Dict[int, str]] = None,
        labels: Optional[Dict[int, str]] = None
    ):
        """
        Inicializa el componente de navegación inferior
        
        Args:
            screens: Diccionario con las pantallas {índice: control}
            on_navigate: Callback opcional que se ejecuta al cambiar de pantalla
            icons: Diccionario con los iconos {índice: icono} (ej: {0: ft.Icons.HOME})
            labels: Diccionario con las etiquetas {índice: etiqueta} (ej: {0: "Inicio"})
        """
        self.screens = screens
        self.on_navigate = on_navigate
        self.current_index = 0
        self.icons = icons or {}
        self.labels = labels or {}
        
        # Crear los destinos de navegación con iconos y etiquetas personalizados
        destinations = []
        num_screens = len(screens)
        
        # Iconos por defecto si no se proporcionan
        default_icons = [
            ft.Icons.HOME.value,
            ft.Icons.TASK.value,
            ft.Icons.SETTINGS.value,
            ft.Icons.DASHBOARD.value,
            ft.Icons.PERSON.value,
        ]
        
        # Etiquetas por defecto si no se proporcionan
        default_labels = [
            "Inicio",
            "Tareas",
            "Configuración",
            "Panel",
            "Perfil",
        ]
        
        for i in range(num_screens):
            # Usar icono personalizado o por defecto
            icon = self.icons.get(i, default_icons[i] if i < len(default_icons) else ft.Icons.CIRCLE.value)
            # Usar etiqueta personalizada o por defecto
            label = self.labels.get(i, default_labels[i] if i < len(default_labels) else f"Pantalla {i+1}")
            
            destinations.append(
                ft.NavigationBarDestination(
                    icon=icon,
                    label=label,
                )
            )
        
        # Crear la barra de navegación
        self.nav_bar = ft.NavigationBar(
            selected_index=0,
            on_change=self._handle_navigation,
            destinations=destinations,
        )
    
    def _handle_navigation(self, e):
        """
        Maneja el evento de cambio de navegación
        
        Args:
            e: Evento de cambio de navegación
        """
        self.current_index = e.control.selected_index
        
        # Actualizar la pantalla mostrada
        if hasattr(self, 'screen_container'):
            current_screen = self.screens.get(self.current_index, self.screens[0])
            self.screen_container.content = current_screen
            e.page.update()
        
        # Ejecutar callback si existe
        if self.on_navigate:
            self.on_navigate(self.current_index)
    
    def build(self, page: ft.Page) -> ft.Container:
        """
        Construye el layout completo con la pantalla actual y la barra de navegación
        
        Args:
            page: Objeto Page de Flet
            
        Returns:
            Container con el layout completo
        """
        # Obtener la pantalla actual
        current_screen = self.screens.get(self.current_index, self.screens[0])
        
        # Contenedor para la pantalla actual (se puede actualizar dinámicamente)
        self.screen_container = ft.Container(
            content=current_screen,
            expand=True,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Contenedor para la pantalla actual - ocupa todo el espacio disponible
                    self.screen_container,
                    # Barra de navegación inferior - solo ocupa su espacio natural
                    self.nav_bar,
                ],
                spacing=0,
                expand=True,
            ),
            expand=True,
        )
    
    def refresh_screen(self, page: ft.Page):
        """
        Actualiza la pantalla actual mostrada
        
        Args:
            page: Objeto Page de Flet
        """
        current_screen = self.screens.get(self.current_index, self.screens[0])
        if hasattr(self, 'screen_container'):
            self.screen_container.content = current_screen
            page.update()
    
    def navigate_to(self, index: int, page: ft.Page):
        """
        Navega a una pantalla específica
        
        Args:
            index: Índice de la pantalla a la que navegar
            page: Objeto Page de Flet
        """
        if index in self.screens:
            self.current_index = index
            self.nav_bar.selected_index = index
            page.update()
    
    def update_screen(self, index: int, screen_content: ft.Control, page: ft.Page):
        """
        Actualiza una pantalla específica con nuevo contenido
        
        Args:
            index: Índice de la pantalla a actualizar
            screen_content: Nuevo contenido de la pantalla
            page: Objeto Page de Flet
        """
        if index in self.screens:
            self.screens[index] = screen_content
            if self.current_index == index:
                # Si es la pantalla actual, actualizar inmediatamente
                page.update()
    
    def get_current_screen(self) -> ft.Control:
        """
        Obtiene la pantalla actual
        
        Returns:
            Control de la pantalla actual
        """
        return self.screens.get(self.current_index, self.screens[0])


# ============================================================================
# FUNCIONES HELPER PARA INTEGRACIÓN
# ============================================================================

def create_bottom_nav_with_views(
    views: list,
    page: ft.Page,
    on_navigate: Optional[Callable] = None,
    destinations: Optional[list] = None,
    icons: Optional[Dict[int, str]] = None,
    labels: Optional[Dict[int, str]] = None
) -> BottomNav:
    """
    Crea un BottomNav con vistas que tienen método build()
    
    Args:
        views: Lista de objetos vista (deben tener método build())
        page: Objeto Page de Flet
        on_navigate: Callback opcional que se ejecuta al cambiar de pantalla
        destinations: Lista opcional de NavigationBarDestination personalizados
        icons: Diccionario con los iconos {índice: icono} (ej: {0: ft.Icons.HOME})
        labels: Diccionario con las etiquetas {índice: etiqueta} (ej: {0: "Inicio"})
        
    Returns:
        Instancia de BottomNav configurada
        
    Ejemplo:
        from app.ui.home_view import HomeView
        from app.ui.task.task_view import TaskView
        from app.ui.settings.settings_view import SettingsView
        
        views = [HomeView(), TaskView(), SettingsView()]
        icons = {0: ft.Icons.HOME, 1: ft.Icons.TASK, 2: ft.Icons.SETTINGS}
        labels = {0: "Inicio", 1: "Tareas", 2: "Config"}
        bottom_nav = create_bottom_nav_with_views(views, page, icons=icons, labels=labels)
    """
    # Construir las pantallas desde las vistas
    screens = {}
    for i, view in enumerate(views):
        if hasattr(view, 'build'):
            screens[i] = view.build()
            # Si la vista tiene método initialize async, llamarlo después
            if hasattr(view, 'initialize') and callable(getattr(view, 'initialize')):
                # Programar la inicialización async
                async def init_view(v=view):
                    await v.initialize()
                page.run_task(init_view)
        else:
            # Si no tiene método build, usar directamente
            screens[i] = view
    
    # Crear el BottomNav con las pantallas construidas y los iconos/etiquetas
    bottom_nav = BottomNav(screens, on_navigate, icons=icons, labels=labels)
    
    # Actualizar los destinos si se proporcionaron personalizados
    if destinations and len(destinations) == len(views):
        bottom_nav.nav_bar.destinations = destinations
    
    return bottom_nav


def wrap_view_with_bottom_nav(
    view,
    other_views: list,
    page: ft.Page,
    current_index: int = 0,
    on_navigate: Optional[Callable] = None,
    icons: Optional[Dict[int, str]] = None,
    labels: Optional[Dict[int, str]] = None
) -> ft.Container:
    """
    Envuelve una vista con BottomNav, incluyendo otras vistas para navegación
    
    Args:
        view: Vista principal (objeto con método build())
        other_views: Lista de otras vistas para navegación
        page: Objeto Page de Flet
        current_index: Índice de la vista inicial (default: 0)
        on_navigate: Callback opcional que se ejecuta al cambiar de pantalla
        icons: Diccionario con los iconos {índice: icono} (ej: {0: ft.Icons.HOME})
        labels: Diccionario con las etiquetas {índice: etiqueta} (ej: {0: "Inicio"})
        
    Returns:
        Container con la vista envuelta en BottomNav
        
    Ejemplo:
        from app.ui.home_view import HomeView
        from app.ui.task.task_view import TaskView
        from app.ui.settings.settings_view import SettingsView
        
        home_view = HomeView()
        other_views = [TaskView(), SettingsView()]
        icons = {0: ft.Icons.HOME, 1: ft.Icons.TASK, 2: ft.Icons.SETTINGS}
        labels = {0: "Inicio", 1: "Tareas", 2: "Config"}
        wrapped = wrap_view_with_bottom_nav(home_view, other_views, page, icons=icons, labels=labels)
    """
    # Combinar todas las vistas
    all_views = [view] + other_views
    
    # Crear el BottomNav con iconos y etiquetas personalizados
    bottom_nav = create_bottom_nav_with_views(all_views, page, on_navigate, icons=icons, labels=labels)
    bottom_nav.current_index = current_index
    bottom_nav.nav_bar.selected_index = current_index
    
    # Retornar el layout completo
    return bottom_nav.build(page)
