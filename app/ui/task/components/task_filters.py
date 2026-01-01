"""
Componente Task Filters
Proporciona opciones avanzadas de filtrado y búsqueda para tareas.
Funciona de forma independiente con TaskList para filtrar dinámicamente.
"""

import flet as ft
from typing import Optional, Callable, List, Dict, Any, Tuple
from datetime import datetime, timedelta, date
from app.models.task import Task
from app.utils.task_helper import (
    TASK_STATUS_PENDING,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_CANCELLED,
    VALID_TASK_STATUSES,
)
from app.utils.helpers.responsives import (
    get_responsive_padding,
    get_responsive_spacing,
)


def create_task_filters(
    page: Optional[ft.Page] = None,
    on_filter_change: Optional[Callable[[Dict[str, Any]], None]] = None,
    show_search: bool = True,
    show_status: bool = True,
    show_priority: bool = True,
    show_tags: bool = True,
    show_due_date: bool = True,
    compact: bool = False,
) -> Tuple[ft.Container, Dict[str, Any]]:
    """
    Crea un componente de filtrado simplificado con un menú desplegable para elegir qué filtro mostrar.
    """
    filters_state: Dict[str, Any] = {
        "search": "",
        "status": None,
        "urgent_important": None,
        "tags": [],
        "due_date": None,
    }

    selected_filter: Dict[str, Optional[str]] = {"value": None}
    controls_map: Dict[str, Any] = {}

    def notify_filters():
        if on_filter_change:
            on_filter_change(filters_state)

    spacing = get_responsive_spacing(page=page, mobile=8, tablet=10, desktop=12)

    # Referencias para controles específicos
    search_field_ref: Optional[ft.TextField] = None
    status_chips: List[Any] = []
    priority_chips: List[Any] = []
    tag_chips: List[Any] = []
    due_date_picker: Optional[ft.DatePicker] = None

    filter_body = ft.Container()

    status_options = [
        ("pendiente", "Pendiente", ft.Colors.BLUE_500),
        ("en_progreso", "En progreso", ft.Colors.ORANGE_500),
        ("completada", "Completada", ft.Colors.GREEN_500),
        ("cancelada", "Cancelada", ft.Colors.GREY_500),
    ]

    priority_options = [
        ("Urgente e Importante", ft.Colors.RED_500),
        ("Importante", ft.Colors.AMBER_500),
        ("Urgente", ft.Colors.DEEP_ORANGE_500),
        ("Todas", ft.Colors.BLUE_GREY_400),
    ]

    tag_options = [
        "python",
        "frontend",
        "backend",
        "design",
        "testing",
        "qa",
        "docs",
        "api",
    ]

    def set_selected_filter(filter_key: str):
        selected_filter["value"] = filter_key
        render_filter_body()

    def update_status(value: Optional[str]):
        filters_state["status"] = value
        for chip in status_chips:
            chip.selected = chip.data == value
        notify_filters()

    def update_priority(value: Optional[str]):
        filters_state["urgent_important"] = None if value == "Todas" else value
        for chip in priority_chips:
            chip.selected = chip.data == value
        notify_filters()

    def update_tags(tag: str, selected: bool):
        tags = set(filters_state.get("tags") or [])
        if selected:
            tags.add(tag)
        else:
            tags.discard(tag)
        filters_state["tags"] = list(tags)
        notify_filters()

    def update_due_date(selected_date: Optional[date]):
        filters_state["due_date"] = selected_date
        notify_filters()

    def clear_current_filter(_: Optional[Any] = None):
        key = selected_filter["value"]
        if key == "search" and search_field_ref:
            search_field_ref.value = ""
            filters_state["search"] = ""
        elif key == "status":
            update_status(None)
        elif key == "priority":
            update_priority(None)
        elif key == "tags":
            filters_state["tags"] = []
            for chip in tag_chips:
                chip.selected = False
            notify_filters()
        elif key == "due_date":
            if due_date_picker:
                due_date_picker.value = None
            filters_state["due_date"] = None
            notify_filters()
        if page:
            page.update()

    def render_filter_body():
        nonlocal search_field_ref, due_date_picker
        body_controls: List[ft.Control] = []

        if selected_filter["value"] == "search" and show_search:
            nonlocal search_field_ref
            search_field_ref = ft.TextField(
                label="🔍 Buscar tareas",
                prefix_icon=ft.Icons.SEARCH,
                expand=True,
                on_change=lambda e: (
                    filters_state.__setitem__("search", search_field_ref.value or ""),
                    notify_filters(),
                ),
            )
            body_controls.append(search_field_ref)
            controls_map["search_field"] = search_field_ref
        elif selected_filter["value"] == "status" and show_status:
            status_chips.clear()
            for value, label, color in status_options:
                is_selected = filters_state.get("status") == value
                chip = ft.Chip(
                    label=ft.Text(label, size=12, color=ft.Colors.WHITE if is_selected else None),
                    bgcolor=color if is_selected else None,
                    on_click=lambda e, v=value: (update_status(v), render_filter_body()),
                    data=value,
                )
                status_chips.append(chip)
            body_controls.extend([
                ft.Text("Filtrar por estado", size=12, weight=ft.FontWeight.BOLD),
                ft.Row(status_chips, wrap=True, spacing=8),
                ft.TextButton("Limpiar estado", on_click=clear_current_filter),
            ])
            controls_map["status_chips"] = status_chips
        elif selected_filter["value"] == "priority" and show_priority:
            priority_chips.clear()
            for label, color in priority_options:
                is_selected = filters_state.get("urgent_important") == label or (label == "Todas" and filters_state.get("urgent_important") is None)
                chip = ft.Chip(
                    label=ft.Text(label, size=12, color=ft.Colors.WHITE if is_selected else None),
                    bgcolor=color if is_selected else None,
                    on_click=lambda e, v=label: (update_priority(v if v != "Todas" else None), render_filter_body()),
                    data=label,
                )
                priority_chips.append(chip)
            body_controls.extend([
                ft.Text("Filtrar por prioridad", size=12, weight=ft.FontWeight.BOLD),
                ft.Row(priority_chips, wrap=True, spacing=8),
                ft.TextButton("Limpiar prioridad", on_click=clear_current_filter),
            ])
            controls_map["priority_chips"] = priority_chips
        elif selected_filter["value"] == "tags" and show_tags:
            tag_chips.clear()
            current_tags = set(filters_state.get("tags") or [])
            for tag in tag_options:
                is_selected = tag in current_tags
                chip = ft.Chip(
                    label=ft.Text(tag, size=12, color=ft.Colors.WHITE if is_selected else None),
                    bgcolor=ft.Colors.BLUE_GREY_600 if is_selected else None,
                    on_click=lambda e, t=tag: (update_tags(t, t not in current_tags), render_filter_body()),
                    data=tag,
                )
                tag_chips.append(chip)
            body_controls.extend([
                ft.Text("Filtrar por etiquetas", size=12, weight=ft.FontWeight.BOLD),
                ft.Row(tag_chips, wrap=True, spacing=8),
                ft.TextButton("Limpiar etiquetas", on_click=clear_current_filter),
            ])
            controls_map["tag_chips"] = tag_chips
        elif selected_filter["value"] == "due_date" and show_due_date:
            nonlocal due_date_picker
            
            def handle_date_change(e):
                if e.control.value:
                    update_due_date(e.control.value)
                    if page:
                        page.update()
            
            def handle_date_dismissal(e):
                if page:
                    page.update()
            
            due_date_picker = ft.DatePicker(
                first_date=date.today() - timedelta(days=365),
                last_date=date.today() + timedelta(days=365 * 2),
                on_change=handle_date_change,
                on_dismiss=handle_date_dismissal,
            )
            
            if page and due_date_picker not in page.overlay:
                page.overlay.append(due_date_picker)
            
            def open_date_picker(e):
                if due_date_picker and page:
                    due_date_picker.open = True
                    page.update()
            
            selected_date_text = ft.Text(
                f"Fecha seleccionada: {filters_state.get('due_date') or 'Ninguna'}", 
                size=11, 
                color=ft.Colors.GREY_400
            )
            
            open_button = ft.FilledButton(
                "Elegir fecha",
                icon=ft.Icons.DATE_RANGE,
                on_click=open_date_picker,
            )
            clear_button = ft.TextButton("Limpiar fecha", on_click=clear_current_filter)
            body_controls.extend([
                ft.Text("Filtrar por fecha", size=12, weight=ft.FontWeight.BOLD),
                selected_date_text,
                ft.Row([open_button, clear_button], spacing=8),
            ])
            controls_map["due_date_picker"] = due_date_picker
        else:
            body_controls.append(
                ft.Text("Selecciona un tipo de filtro", size=12, color=ft.Colors.GREY_500)
            )

        filter_body.content = ft.Column(body_controls, spacing=8)
        if page:
            page.update()

    available_filters: List[Tuple[str, str]] = []
    if show_search:
        available_filters.append(("search", "Búsqueda"))
    if show_status:
        available_filters.append(("status", "Estado"))
    if show_priority:
        available_filters.append(("priority", "Prioridad"))
    if show_tags:
        available_filters.append(("tags", "Etiquetas"))
    if show_due_date:
        available_filters.append(("due_date", "Fecha"))

    if available_filters:
        selected_filter["value"] = available_filters[0][0]

    menu_items = [
        ft.PopupMenuItem(content=ft.Text(label), on_click=lambda e, key=key: set_selected_filter(key))
        for key, label in available_filters
    ]

    filter_menu = ft.PopupMenuButton(
        icon=ft.Icons.EXPAND_MORE,
        items=menu_items,
    )

    controls_map.update({
        "filter_menu": filter_menu,
        "filter_body": filter_body,
        "filters_state": filters_state,
        "selected_filter": selected_filter,
        "search_field": search_field_ref,
        "status_chips": status_chips,
        "priority_chips": priority_chips,
        "tag_chips": tag_chips,
        "due_date_picker": due_date_picker,
    })

    render_filter_body()

    # Contenedor principal que toma todo el ancho
    filters_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("¿Cómo deseas filtrar?", size=14, weight=ft.FontWeight.BOLD),
                        filter_menu,
                    ],
                    spacing=spacing,
                ),
                filter_body,
            ],
            spacing=12,
        ),
        padding=get_responsive_padding(page=page),
        border=ft.Border(
            left=ft.BorderSide(2, ft.Colors.RED_700),
        ),
        bgcolor=ft.Colors.GREY_900,
        border_radius=8,
        expand=True,
    )

    return filters_container, controls_map


class TaskFilters:
    """
    Clase para gestionar filtros de tareas con caching y aplicación dinámica.
    Proporciona métodos para filtrar tareas según criterios múltiples.
    """
    
    def __init__(
        self,
        page: Optional[ft.Page] = None,
        on_filter_change: Optional[Callable[[Dict[str, Any]], None]] = None,
        show_search: bool = True,
        show_status: bool = True,
        show_priority: bool = True,
        show_tags: bool = True,
        show_due_date: bool = True,
        compact: bool = False,
    ):
        """
        Inicializa el gestor de filtros.
        
        Args:
            page: Objeto Page de Flet
            on_filter_change: Callback cuando cambian los filtros
            show_search: Mostrar búsqueda
            show_status: Mostrar filtro por estado
            show_priority: Mostrar filtro por urgencia/importancia
            show_tags: Mostrar filtro por etiquetas
            show_due_date: Mostrar filtro por fecha
            compact: Diseño compacto
        """
        self.page = page
        self.on_filter_change = on_filter_change
        self.show_search = show_search
        self.show_status = show_status
        self.show_priority = show_priority
        self.show_tags = show_tags
        self.show_due_date = show_due_date
        self.compact = compact
        
        self.current_filters: Dict[str, Any] = {
            "search": "",
            "status": None,
            "urgent_important": None,
            "tags": [],
            "due_date": None,
        }
        
        self._filters_component: Optional[ft.Container] = None
        self._controls_map: Dict[str, Any] = {}
    
    def build(self) -> ft.Container:
        """
        Construye y retorna el componente de filtros.
        
        Returns:
            Container con los controles de filtrado que toma todo el ancho
        """
        if self._filters_component is None:
            self._filters_component, self._controls_map = create_task_filters(
                page=self.page,
                on_filter_change=self._handle_filter_change,
                show_search=self.show_search,
                show_status=self.show_status,
                show_priority=self.show_priority,
                show_tags=self.show_tags,
                show_due_date=self.show_due_date,
                compact=self.compact,
            )
        return self._filters_component
    
    def _handle_filter_change(self, filters: Dict[str, Any]):
        """
        Maneja cambios en los filtros.
        
        Args:
            filters: Dict con filtros actuales
        """
        self.current_filters = filters
        if self.on_filter_change:
            self.on_filter_change(filters)
    
    def apply_filters(self, tasks: List[Task]) -> List[Task]:
        """
        Aplica todos los filtros a una lista de tareas.
        
        Args:
            tasks: Lista de tareas a filtrar
            
        Returns:
            Lista de tareas filtradas
        """
        filtered = tasks
        
        search_text = (self.current_filters.get("search") or "").lower()
        status_value = self.current_filters.get("status")
        priority_value = self.current_filters.get("urgent_important") or self.current_filters.get("priority")
        tags_value = self.current_filters.get("tags") or []
        due_date_value = self.current_filters.get("due_date")
        
        # Aplicar filtros
        if search_text:
            filtered = [
                t for t in filtered
                if search_text in (t.title.lower() if t.title else "") or
                   search_text in (t.description.lower() if t.description else "")
            ]
        
        if status_value:
            filtered = [
                t for t in filtered
                if t.status == status_value
            ]
        
        if priority_value:
            if priority_value == "Urgente e Importante":
                filtered = [t for t in filtered if t.urgent and t.important]
            elif priority_value == "Importante":
                filtered = [t for t in filtered if t.important and not t.urgent]
            elif priority_value == "Urgente":
                filtered = [t for t in filtered if t.urgent and not t.important]
        
        if tags_value:
            filtered = [
                t for t in filtered
                if any(tag in (t.tags or []) for tag in tags_value)
            ]
        
        if due_date_value:
            filtered = [
                t for t in filtered
                if t.due_date and t.due_date == due_date_value
            ]
        
        return filtered
    
    def set_filter(self, filter_name: str, value: Any) -> None:
        """
        Establece un filtro específico.
        
        Args:
            filter_name: Nombre del filtro (search, status, priority, tags, due_date)
            value: Valor del filtro
        """
        filters_state = self._controls_map.get("filters_state") or {}
        if filter_name == "search":
            self.current_filters["search"] = str(value) if value else ""
            filters_state["search"] = self.current_filters["search"]
            search_field = self._controls_map.get("search_field")
            if search_field and isinstance(search_field, ft.TextField):
                search_field.value = self.current_filters["search"]
        elif filter_name == "status":
            self.current_filters["status"] = value
            filters_state["status"] = value
            for chip in self._controls_map.get("status_chips", []) or []:
                chip.selected = chip.data == value
        elif filter_name in ("priority", "urgent_important"):
            self.current_filters["urgent_important"] = value
            filters_state["urgent_important"] = value
            for chip in self._controls_map.get("priority_chips", []) or []:
                chip.selected = chip.data == value or (chip.data == "Todas" and value is None)
        elif filter_name == "tags":
            values = value or []
            self.current_filters["tags"] = list(values) if isinstance(values, (list, tuple, set)) else [value]
            filters_state["tags"] = self.current_filters["tags"]
            for chip in self._controls_map.get("tag_chips", []) or []:
                chip.selected = chip.data in self.current_filters["tags"]
        elif filter_name == "due_date":
            self.current_filters["due_date"] = value
            filters_state["due_date"] = value
            picker = self._controls_map.get("due_date_picker")
            if picker:
                picker.value = value
        if self.on_filter_change:
            self.on_filter_change(self.current_filters)
    
    def get_filters(self) -> Dict[str, Any]:
        """
        Obtiene los filtros actuales desde los controles.
        
        Returns:
            Dict con filtros actuales
        """
        return dict(self.current_filters)
    
    def clear_filters(self) -> None:
        """Limpia todos los filtros y resetea los controles."""
        self.current_filters = {
            "search": "",
            "status": None,
            "urgent_important": None,
            "tags": [],
            "due_date": None,
        }

        filters_state = self._controls_map.get("filters_state")
        if isinstance(filters_state, dict):
            filters_state.update(self.current_filters)

        search_field = self._controls_map.get("search_field")
        if search_field and isinstance(search_field, ft.TextField):
            search_field.value = ""

        for chip in self._controls_map.get("status_chips", []) or []:
            chip.selected = False

        for chip in self._controls_map.get("priority_chips", []) or []:
            chip.selected = False

        for chip in self._controls_map.get("tag_chips", []) or []:
            chip.selected = False

        picker = self._controls_map.get("due_date_picker")
        if picker:
            picker.value = None

        if self.on_filter_change:
            self.on_filter_change(dict(self.current_filters))
    
    def has_active_filters(self) -> bool:
        """
        Verifica si hay filtros activos.
        
        Returns:
            True si hay al menos un filtro activo
        """
        return any([
            self.current_filters.get("search"),
            self.current_filters.get("status"),
            self.current_filters.get("urgent_important"),
            self.current_filters.get("tags"),
            self.current_filters.get("due_date"),
        ])
