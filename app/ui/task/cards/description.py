"""
Descripción para Task Card
Proporciona la creación del control de descripción y una clase envoltorio `Description`
que permite construir, cachear y refrescar el control de descripción.
"""

import flet as ft
from typing import Optional
from app.models.task import Task
from app.utils.helpers.responsives import get_responsive_size


def create_description(task: Task, page: Optional[ft.Page] = None, compact: bool = False) -> ft.Text:
    """
    Crea y retorna un control `ft.Text` con la descripción de la tarea.

    Args:
        task: Instancia de `Task` que contiene `description`.
        page: Objeto `ft.Page` para cálculos responsive (opcional).
        compact: Si se renderiza en modo compacto (reduce líneas y tamaños).

    Returns:
        ft.Text con la descripción formateada y recortada si es necesario.
    """
    if compact:
        description_size = get_responsive_size(page=page, mobile=12, tablet=13, desktop=14)
        max_lines = 3
    else:
        description_size = get_responsive_size(page=page, mobile=13, tablet=14, desktop=15)
        max_lines = 5

    return ft.Text(
        task.description,
        size=description_size,
        color=ft.Colors.WHITE_70,
        max_lines=max_lines,
        overflow=ft.TextOverflow.ELLIPSIS,
    )


class Description:
    """Clase envoltorio para el control de descripción de la tarjeta.

    Uso:
        d = Description(task, page=page)
        text_control = d.build()
        d.refresh()  # forzar reconstrucción
    """

    def __init__(self, task: Task, page: Optional[ft.Page] = None, compact: bool = False):
        self.task = task
        self.page = page
        self.compact = compact
        self._text: Optional[ft.Text] = None

    def build(self) -> Optional[ft.Text]:
        """Construye (o retorna cacheado) el control de descripción.

        Retorna `None` si no hay descripción en la tarea.
        """
        if not self.task.description or not self.task.description.strip():
            return None

        if self._text is None:
            self._text = create_description(self.task, page=self.page, compact=self.compact)
        return self._text

    def refresh(self):
        """Forzar reconstrucción en la próxima llamada a `build()`"""
        self._text = None

    def update_description(self, new_description: str):
        """Actualiza la descripción de la tarea y fuerza la reconstrucción."""
        self.task.description = new_description
        self._text = None
