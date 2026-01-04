"""
Vista principal (Home) de la aplicación
Incluye navegación inferior entre diferentes secciones
"""

import flet as ft
from app.utils.bottom_nav import create_bottom_nav_with_views
from app.ui.resume.resume_view import ResumeView
from app.ui.task.task_view import TaskView
from app.ui.settings.settings_view import SettingsView
from app.ui.habits.habits_view import HabitsView
from app.ui.goals.goals_view import GoalsView
from typing import Callable, Dict, List, Optional, Any

class HomeView:
    """Clase que representa la vista principal de la aplicación"""
    
    def __init__(self):
        """Inicializa la vista principal"""
        self.page_ref = None
    
    def build(self, page: ft.Page) -> ft.Container:
        """
        Construye y retorna el widget principal de la vista con BottomNav
        
        Args:
            page: Objeto Page de Flet (requerido)
        
        Returns:
            Container con el contenido de la vista principal y navegación
        """
        # Guardar referencia a la página
        self.page_ref = page
        
        # Crear ResumeView primero para obtener la referencia a RewardsView y UserService
        resume_view = ResumeView()
        user_service = resume_view.get_user_service()  # Obtener el servicio de usuario compartido
        task_view = TaskView(page, rewards_view=resume_view.rewards_view, user_service=user_service)
        
        # Lista de vistas en orden
        views = [
            resume_view,  # Índice 0 - Pantalla principal
            task_view,     # Índice 1
            HabitsView(),   # Índice 2
            GoalsView(),    # Índice 3
            SettingsView(), # Índice 4
        ]
        
        # Definir iconos para cada vista
        icons: dict[int, Any] = {
            0: ft.Icons.DASHBOARD.value,  # Resume
            1: ft.Icons.TASK.value,        # Task
            2: ft.Icons.REPEAT.value,      # Habits
            3: ft.Icons.FLAG.value,        # Goals
            4: ft.Icons.SETTINGS.value,    # Settings
        }
        
        # Definir etiquetas para cada vista
        labels = {
            0: "Resumen",
            1: "Tareas",
            2: "Hábitos",
            3: "Metas",
            4: "Configuración",
        }
        
        # Crear el BottomNav con las vistas, iconos y etiquetas
        bottom_nav = create_bottom_nav_with_views(
            views=views,
            page=page,
            icons=icons,
            labels=labels,
        )
        # Retornar el layout completo con BottomNav
        return bottom_nav.build(page)

