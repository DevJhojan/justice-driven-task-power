"""
Módulo principal de la aplicación Flet.
Contiene la función main() que configura e inicializa la aplicación.
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
    try:
        # Configuración de la página
        page.title = "Productividad Personal"
        page.padding = 0
        page.spacing = 0
        
        # Mostrar indicador de carga inmediatamente para evitar pantalla negra
        page.clean()
        loading_indicator = ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(width=50, height=50, color=ft.Colors.RED_700),
                    ft.Text("Cargando...", size=16, color=ft.Colors.WHITE70),
                ],
                spacing=20,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.BLACK87,
            expand=True,
        )
        page.add(loading_indicator)
        page.update()
        print("Indicador de carga mostrado")

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
        try:
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
        except Exception as e:
            print(f"Error al configurar tema: {e}")
            # Usar tema por defecto si falla
            page.theme_mode = ft.ThemeMode.SYSTEM
        
        # Establecer tema inicial desde configuración del usuario ANTES de cualquier otra cosa
        # Usar tema por defecto primero para evitar pantalla negra
        page.theme_mode = ft.ThemeMode.DARK  # Tema oscuro por defecto
        page.update()  # Actualizar inmediatamente para mostrar algo
        
        try:
            from app.data.database import get_db
            from app.services.user_settings_service import UserSettingsService
            print("Inicializando base de datos...")
            db = get_db()
            print("Base de datos inicializada")
            user_settings_service = UserSettingsService(db)
            saved_theme = user_settings_service.get_theme()
            # Establecer el tema ANTES de construir cualquier vista
            page.theme_mode = ft.ThemeMode.DARK if saved_theme == "dark" else ft.ThemeMode.LIGHT
            page.update()
        except Exception as e:
            print(f"Error al cargar configuración de tema: {e}")
            import traceback
            traceback.print_exc()
            # Usar tema por defecto si falla
            page.theme_mode = ft.ThemeMode.DARK
            page.update()
        
        # Inicializar home_view después de establecer el tema
        # Esto asegura que todas las vistas se construyan con el tema correcto
        print("Inicializando HomeView...")
        try:
            home_view = HomeView(page)
            print("HomeView inicializado correctamente")
            # Guardar referencia a home_view en la página para que las vistas puedan acceder
            page._home_view_ref = home_view
        except Exception as e:
            print(f"Error crítico al inicializar HomeView: {e}")
            import traceback
            traceback.print_exc()
            # Mostrar error en la UI
            try:
                page.clean()
                page.add(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Error al iniciar la aplicación", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                ft.Text(f"Error: {str(e)}", size=14, color=ft.Colors.WHITE70),
                                ft.Text("Por favor, reinicia la aplicación.", size=12, color=ft.Colors.WHITE54),
                            ],
                            spacing=10,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=20,
                        alignment=ft.alignment.center,
                        bgcolor=ft.Colors.BLACK87,
                        expand=True,
                    )
                )
                page.update()
            except Exception as e2:
                print(f"Error al mostrar mensaje de error: {e2}")
            return
        
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
                    
                    from app.ui.tasks.form_tasks import TaskForm
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
                from app.ui.habits.form_habits import HabitForm
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
                from app.ui.goals.form_goals import GoalForm
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
        print("Construyendo UI inicial...")
        try:
            # Limpiar el indicador de carga antes de construir la UI
            page.clean()
            home_view._build_ui()
            print("UI construida correctamente")
            page.update()
        except Exception as e:
            print(f"Error crítico al construir UI: {e}")
            import traceback
            traceback.print_exc()
            # Mostrar error en la UI
            try:
                page.clean()
                page.add(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Error al construir la interfaz", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                ft.Text(f"Error: {str(e)}", size=14, color=ft.Colors.WHITE70),
                                ft.Text("Por favor, reinicia la aplicación.", size=12, color=ft.Colors.WHITE54),
                            ],
                            spacing=10,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=20,
                        alignment=ft.alignment.center,
                        bgcolor=ft.Colors.BLACK87,
                        expand=True,
                    )
                )
                page.update()
            except Exception as e2:
                print(f"Error al mostrar mensaje de error: {e2}")
            return
    except Exception as e:
        # Error crítico en la inicialización
        print(f"Error crítico en main(): {e}")
        import traceback
        traceback.print_exc()
        # Intentar mostrar un mensaje de error básico
        try:
            page.clean()
            page.add(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Error crítico al iniciar", size=20, weight=ft.FontWeight.BOLD),
                            ft.Text(f"Error: {str(e)}", size=14),
                            ft.Text("Por favor, reinicia la aplicación.", size=12),
                        ],
                        spacing=10,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=20,
                    alignment=ft.alignment.center,
                )
            )
            page.update()
        except:
            # Si ni siquiera podemos mostrar el error, solo imprimir
            pass

