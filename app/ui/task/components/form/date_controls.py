"""Controles de fecha (DatePicker) para el formulario de tareas.

Encapsula la creación del DatePicker, el texto visible de la fecha y los
handlers para abrir/limpiar/actualizar la fecha seleccionada.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Callable, Optional, Tuple

import flet as ft

from app.utils.helpers.formats import format_date


def build_due_date_controls(
	page: ft.Page,
	selected_date: Optional[date],
	on_selected_date_change: Callable[[Optional[date]], None],
) -> Tuple[ft.DatePicker, ft.Text, Callable, Callable]:
	"""Construye los controles de fecha de vencimiento.

	Args:
		page: Página de Flet (usada para overlay y update)
		selected_date: Fecha inicial seleccionada
		on_selected_date_change: Callback cuando cambia la fecha (date o None)

	Returns:
		(date_picker, date_text, open_date_picker, clear_date)
	"""

	def _to_date(value) -> Optional[date]:
		if value is None:
			return None
		if isinstance(value, datetime):
			return value.date()
		if isinstance(value, date):
			return value
		return None

	def _set_text(value: Optional[date]) -> None:
		if value:
			date_text.value = f"📅 {format_date(value)}"
		else:
			date_text.value = "📅 Sin fecha"

	date_text = ft.Text(
		"📅 Sin fecha",
		size=14,
		color=ft.Colors.GREY_400,
	)
	_set_text(selected_date)

	def handle_date_change(e):
		new_date = _to_date(getattr(e.control, "value", None))
		on_selected_date_change(new_date)
		_set_text(new_date)
		page.update()

	def handle_date_dismissal(e):
		page.update()

	date_picker = ft.DatePicker(
		first_date=date.today(),
		last_date=date.today() + timedelta(days=365 * 2),
		on_change=handle_date_change,
		on_dismiss=handle_date_dismissal,
	)

	if getattr(page, "overlay", None) is not None and date_picker not in page.overlay:
		page.overlay.append(date_picker)

	def open_date_picker(e):
		date_picker.open = True
		page.update()

	def clear_date(e):
		on_selected_date_change(None)
		_set_text(None)
		page.update()

	return date_picker, date_text, open_date_picker, clear_date
