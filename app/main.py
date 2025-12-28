"""
Punto de entrada principal de la aplicación.
"""
import warnings
# Suprimir advertencias de pkg_resources (deprecation warning de gcloud/pyrebase4)
warnings.filterwarnings('ignore', category=UserWarning, module='pkg_resources')
warnings.filterwarnings('ignore', category=UserWarning, module='gcloud')

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
    )
    
    # Configurar tema oscuro con matices rojos
    page.dark_theme = ft.Theme(
        color_scheme_seed=ft.Colors.RED_900,  # Rojo oscuro principal
    )
    
    # Personalizar colores del tema (solo si color_scheme está disponible)
    # Tema claro
    if page.theme.color_scheme:
        page.theme.color_scheme.primary = ft.Colors.RED_700
        page.theme.color_scheme.secondary = ft.Colors.RED_600
        page.theme.color_scheme.on_primary = ft.Colors.WHITE
        page.theme.color_scheme.on_secondary = ft.Colors.WHITE
    
    # Tema oscuro
    if page.dark_theme.color_scheme:
        page.dark_theme.color_scheme.primary = ft.Colors.RED_600
        page.dark_theme.color_scheme.secondary = ft.Colors.RED_500
        page.dark_theme.color_scheme.on_primary = ft.Colors.WHITE
        page.dark_theme.color_scheme.on_secondary = ft.Colors.WHITE
    
    # Establecer tema inicial desde configuración del usuario ANTES de cualquier otra cosa
    from app.data.database import get_db
    from app.services.user_settings_service import UserSettingsService
    db = get_db()
    user_settings_service = UserSettingsService(db)
    saved_theme = user_settings_service.get_theme()
    # Establecer el tema ANTES de construir cualquier vista
    page.theme_mode = ft.ThemeMode.DARK if saved_theme == "dark" else ft.ThemeMode.LIGHT
    
    # Inicializar home_view después de establecer el tema
    # Esto asegura que todas las vistas se construyan con el tema correcto
    home_view = HomeView(page)
    # Guardar referencia a home_view en la página para que las vistas puedan acceder
    page._home_view_ref = home_view
    
    def _show_error_page(page: ft.Page, error: Exception, context: str = ""):
        """Muestra una página de error."""
        try:
            from app.ui.error_view import ErrorView
            error_view = ErrorView(page, error, context)
            error_view_obj = error_view.build_view()
            
            # Verificar si ya existe una vista de error
            existing_error_view = None
            for view in page.views:
                if view.route == "/error":
                    existing_error_view = view
                    break
            
            if existing_error_view:
                # Reemplazar la vista de error existente
                index = page.views.index(existing_error_view)
                page.views[index] = error_view_obj
            else:
                # Agregar nueva vista de error
                page.views.append(error_view_obj)
            
            page.go("/error")
            page.update()
        except Exception as ex2:
            # Si no se puede mostrar la página de error, imprimir en consola
            print(f"Error crítico al mostrar página de error:")
            print(f"Error original: {error}")
            print(f"Error al mostrar: {ex2}")
            import traceback
            traceback.print_exc()
    
    # Configurar el manejador de rutas para formularios
    def route_change(e):
        """Maneja los cambios de ruta."""
        # Si la ruta es la principal, HomeView ya la maneja
        if page.route == "/" or not page.route or page.route == "":
            # Si no hay vistas o la última vista no es la principal, reconstruir
            if len(page.views) == 0 or (len(page.views) > 0 and page.views[-1].route != "/"):
                home_view._build_ui()
            return
        
        # Si hay parámetros en la ruta, manejar formularios
        if page.route.startswith("/task-form"):
            try:
                # Verificar si ya existe una vista con esta ruta
                existing_view = None
                for view in page.views:
                    if view.route == page.route:
                        existing_view = view
                        break
                
                if existing_view:
                    # Si ya existe, solo actualizar la página
                    page.update()
                    return
                
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
                    # Regresar a la vista principal y recargar
                    page.go("/")
                    # Recargar todas las vistas
                    home_view._build_ui()
                
                form = TaskForm(page, task_service, task, on_save)
                form_view = form.build_view()
                page.views.append(form_view)
                page.update()
            except Exception as ex:
                # Si hay un error, mostrar página de error
                _show_error_page(page, ex, "Error al abrir formulario de tarea")
        
        elif page.route == "/error":
            # La página de error se maneja externamente, solo necesitamos reconocer la ruta
            pass
        
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
            from app.services.points_service import PointsService
            from app.data.habit_repository import HabitRepository
            from app.data.database import get_db
            
            db = get_db()
            habit_service = HabitService(HabitRepository(db))
            points_service = PointsService(db)
            
            metrics_view = HabitsMetricsView(page, habit_service, points_service)
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
        
        elif page.route == "/firebase-sync":
            from app.ui.settings.sync_view import FirebaseSyncView
            from app.services.firebase_sync_service import FirebaseSyncService
            from app.data.database import get_db
            from app.services.task_service import TaskService
            from app.services.habit_service import HabitService
            from app.services.goal_service import GoalService
            from app.services.points_service import PointsService
            from app.services.user_settings_service import UserSettingsService
            from app.data.task_repository import TaskRepository
            from app.data.habit_repository import HabitRepository
            from app.data.goal_repository import GoalRepository
            from app.data.subtask_repository import SubtaskRepository
            
            db = get_db()
            task_service = TaskService(TaskRepository(db), SubtaskRepository(db))
            habit_service = HabitService(HabitRepository(db))
            goal_service = GoalService(GoalRepository(db))
            points_service = PointsService(db)
            user_settings_service = UserSettingsService(db)
            
            firebase_sync_service = None
            try:
                firebase_sync_service = FirebaseSyncService(
                    db, task_service, habit_service, goal_service,
                    points_service, user_settings_service
                )
            except Exception as ex:
                print(f"Error al inicializar Firebase: {ex}")
            
            sync_view = FirebaseSyncView(page, firebase_sync_service)
            sync_view_obj = sync_view.build_view()
            page.views.append(sync_view_obj)
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
    
    # Establecer la ruta inicial si no está establecida
    if not page.route:
        page.route = "/"
    
    # Construir la UI inicial después de que todo esté configurado
    # Esto asegura que el tema se haya aplicado correctamente antes de construir las vistas
    # Llamar directamente a _build_ui para construir la UI inicial
    home_view._build_ui()


if __name__ == "__main__":
    # Ejecutar la aplicación
    # Para desarrollo: ventana nativa Flet
    # Para producción Android: se construye con build_android.sh
    ft.app(
        target=main, 
        view=ft.AppView.FLET_APP, 
        assets_dir="assets"
    )

