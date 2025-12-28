"""
Punto de entrada principal de la aplicación.
"""
import flet as ft
from pathlib import Path
from app.ui.home_view import HomeView


def main(page: ft.Page):
    """
    Función principal de la aplicación.
    
    Args:
        page: Página de Flet.
    """
    # Configuración de la página
    page.title = "Productividad Personal"
    page.padding = 0
    page.spacing = 0
    
    # Configurar icono de la ventana para escritorio
    try:
        icon_path = Path("assets/app_icon.png")
        if icon_path.exists():
            page.window.icon = str(icon_path)
    except Exception as e:
        print(f"No se pudo cargar el icono: {e}")
    
    # Configuración para móvil y escritorio
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.vertical_alignment = ft.MainAxisAlignment.START
    
    # Configurar tema con matices rojos - Tema claro
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.RED_700,  # Rojo principal
        primary_swatch=ft.Colors.RED,
    )
    
    # Configurar tema oscuro con matices rojos
    page.dark_theme = ft.Theme(
        color_scheme_seed=ft.Colors.RED_900,  # Rojo oscuro principal
        primary_swatch=ft.Colors.RED,
    )
    
    # Personalizar colores del tema
    # Tema claro
    page.theme.color_scheme.primary = ft.Colors.RED_700
    page.theme.color_scheme.secondary = ft.Colors.RED_600
    page.theme.color_scheme.on_primary = ft.Colors.WHITE
    page.theme.color_scheme.on_secondary = ft.Colors.WHITE
    
    # Tema oscuro
    page.dark_theme.color_scheme.primary = ft.Colors.RED_600
    page.dark_theme.color_scheme.secondary = ft.Colors.RED_500
    page.dark_theme.color_scheme.on_primary = ft.Colors.WHITE
    page.dark_theme.color_scheme.on_secondary = ft.Colors.WHITE
    
    # Inicializar home_view
    home_view = HomeView(page)
    
    # Configurar el manejador de rutas para formularios
    def route_change(e):
        """Maneja los cambios de ruta."""
        # Si la ruta es la principal, HomeView ya la maneja
        if page.route == "/" or not page.route or page.route == "":
            # Asegurar que HomeView esté visible
            if len(page.views) == 0:
                home_view._build_ui()
            return
        
        # Si hay parámetros en la ruta, manejar formularios
        if page.route.startswith("/task-form"):
            from app.ui.tasks.form import TaskForm
            from app.services.task_service import TaskService
            from app.data.task_repository import TaskRepository
            from app.data.subtask_repository import SubtaskRepository
            from app.data.database import get_db
            
            # Obtener ID de la ruta si existe
            task_id = None
            if "?id=" in page.route:
                try:
                    task_id = int(page.route.split("?id=")[1])
                except:
                    pass
            
            db = get_db()
            task_service = TaskService(TaskRepository(db), SubtaskRepository(db))
            task = task_service.get_task(task_id) if task_id else None
            
            def on_save():
                # El callback se ejecutará antes de navegar
                pass
            
            form = TaskForm(page, task_service, task, on_save)
            form_view = form.build_view()
            page.views.append(form_view)
            page.update()
        
        elif page.route.startswith("/habit-form"):
            from app.ui.habits.form import HabitForm
            from app.services.habit_service import HabitService
            from app.data.habit_repository import HabitRepository
            from app.data.database import get_db
            
            # Obtener ID de la ruta si existe
            habit_id = None
            if "?id=" in page.route:
                try:
                    habit_id = int(page.route.split("?id=")[1])
                except:
                    pass
            
            db = get_db()
            habit_service = HabitService(HabitRepository(db))
            habit = habit_service.get_habit(habit_id) if habit_id else None
            
            def on_save():
                # Regresar a la vista principal y recargar
                page.go("/")
                # Recargar todas las vistas
                home_view._build_ui()
            
            form = HabitForm(page, habit_service, habit, on_save)
            form_view = form.build_view()
            page.views.append(form_view)
            page.update()
        
        elif page.route.startswith("/habits-metrics"):
            from app.ui.habits.metrics_view import HabitsMetricsView
            from app.services.habit_service import HabitService
            from app.data.habit_repository import HabitRepository
            from app.data.database import get_db
            
            db = get_db()
            habit_service = HabitService(HabitRepository(db))
            
            metrics_view = HabitsMetricsView(page, habit_service)
            metrics_view_obj = metrics_view.build_view()
            page.views.append(metrics_view_obj)
            page.update()
        
        elif page.route.startswith("/goal-form"):
            from app.ui.goals.form import GoalForm
            from app.services.goal_service import GoalService
            from app.services.points_service import PointsService
            from app.data.goal_repository import GoalRepository
            from app.data.database import get_db
            
            # Obtener ID de la ruta si existe
            goal_id = None
            if "?id=" in page.route:
                try:
                    goal_id = int(page.route.split("?id=")[1])
                except:
                    pass
            
            db = get_db()
            goal_service = GoalService(GoalRepository(db))
            points_service = PointsService(db)
            goal = goal_service.get_goal(goal_id) if goal_id else None
            
            def on_save():
                # Regresar a la vista principal y recargar
                page.go("/")
                # Recargar todas las vistas
                home_view._build_ui()
            
            form = GoalForm(page, goal_service, goal, on_save, points_service)
            form_view = form.build_view()
            page.views.append(form_view)
            page.update()
    
    def view_pop(e):
        """Maneja cuando se hace pop de una vista."""
        page.views.pop()
        if len(page.views) > 0:
            top_view = page.views[-1]
            page.go(top_view.route)
        else:
            page.go("/")
    
    page.on_route_change = route_change
    page.on_view_pop = view_pop


if __name__ == "__main__":
    # Ejecutar la aplicación
    # Para desarrollo: ventana nativa Flet
    # Para producción Android: se construye con build_android.sh
    ft.app(target=main, view=ft.AppView.FLET_APP, assets_dir="assets")

