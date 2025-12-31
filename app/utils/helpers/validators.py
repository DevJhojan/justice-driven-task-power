"""
Funciones de validación para la aplicación
Valida diferentes tipos de datos y entradas del usuario
"""

import re
from datetime import datetime, date
from typing import Any, Optional


def is_valid_email(email: str) -> bool:
    """
    Valida si un email tiene un formato válido
    
    Args:
        email: String con el email a validar
        
    Returns:
        True si el email es válido, False en caso contrario
        
    Ejemplo:
        >>> is_valid_email("usuario@ejemplo.com")
        True
        >>> is_valid_email("email_invalido")
        False
    """
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_username(username: str, min_length: int = 3, max_length: int = 20) -> bool:
    """
    Valida si un nombre de usuario es válido
    
    Args:
        username: String con el nombre de usuario
        min_length: Longitud mínima (default: 3)
        max_length: Longitud máxima (default: 20)
        
    Returns:
        True si el username es válido, False en caso contrario
        
    Ejemplo:
        >>> is_valid_username("usuario123")
        True
        >>> is_valid_username("ab")  # Muy corto
        False
    """
    if not username or not isinstance(username, str):
        return False
    
    # Solo letras, números y guiones bajos
    pattern = r'^[a-zA-Z0-9_]+$'
    return (
        min_length <= len(username) <= max_length and
        re.match(pattern, username) is not None
    )


def is_valid_password(password: str, min_length: int = 8) -> bool:
    """
    Valida si una contraseña cumple con los requisitos mínimos
    
    Args:
        password: String con la contraseña
        min_length: Longitud mínima requerida (default: 8)
        
    Returns:
        True si la contraseña es válida, False en caso contrario
        
    Ejemplo:
        >>> is_valid_password("MiPassword123")
        True
        >>> is_valid_password("123")  # Muy corta
        False
    """
    if not password or not isinstance(password, str):
        return False
    
    return len(password) >= min_length


def is_valid_date(date_string: str, date_format: str = "%Y-%m-%d") -> bool:
    """
    Valida si una cadena representa una fecha válida
    
    Args:
        date_string: String con la fecha a validar
        date_format: Formato esperado de la fecha (default: "%Y-%m-%d")
        
    Returns:
        True si la fecha es válida, False en caso contrario
        
    Ejemplo:
        >>> is_valid_date("2024-12-25")
        True
        >>> is_valid_date("2024-13-45")  # Fecha inválida
        False
    """
    if not date_string or not isinstance(date_string, str):
        return False
    
    try:
        datetime.strptime(date_string, date_format)
        return True
    except (ValueError, TypeError):
        return False


def is_valid_time(time_string: str, time_format: str = "%H:%M") -> bool:
    """
    Valida si una cadena representa una hora válida
    
    Args:
        time_string: String con la hora a validar
        time_format: Formato esperado de la hora (default: "%H:%M")
        
    Returns:
        True si la hora es válida, False en caso contrario
        
    Ejemplo:
        >>> is_valid_time("14:30")
        True
        >>> is_valid_time("25:00")  # Hora inválida
        False
    """
    if not time_string or not isinstance(time_string, str):
        return False
    
    try:
        datetime.strptime(time_string, time_format)
        return True
    except (ValueError, TypeError):
        return False


def is_valid_number(value: Any, min_value: Optional[float] = None, max_value: Optional[float] = None) -> bool:
    """
    Valida si un valor es un número y opcionalmente está en un rango
    
    Args:
        value: Valor a validar
        min_value: Valor mínimo permitido (opcional)
        max_value: Valor máximo permitido (opcional)
        
    Returns:
        True si el valor es un número válido, False en caso contrario
        
    Ejemplo:
        >>> is_valid_number(42, min_value=0, max_value=100)
        True
        >>> is_valid_number("abc")
        False
    """
    try:
        num = float(value)
        if min_value is not None and num < min_value:
            return False
        if max_value is not None and num > max_value:
            return False
        return True
    except (ValueError, TypeError):
        return False


def is_valid_integer(value: Any, min_value: Optional[int] = None, max_value: Optional[int] = None) -> bool:
    """
    Valida si un valor es un entero y opcionalmente está en un rango
    
    Args:
        value: Valor a validar
        min_value: Valor mínimo permitido (opcional)
        max_value: Valor máximo permitido (opcional)
        
    Returns:
        True si el valor es un entero válido, False en caso contrario
        
    Ejemplo:
        >>> is_valid_integer(42, min_value=0, max_value=100)
        True
        >>> is_valid_integer(3.14)  # No es entero
        False
    """
    try:
        num = int(value)
        if min_value is not None and num < min_value:
            return False
        if max_value is not None and num > max_value:
            return False
        return True
    except (ValueError, TypeError):
        return False


def is_valid_string(value: Any, min_length: int = 0, max_length: Optional[int] = None, allow_empty: bool = True) -> bool:
    """
    Valida si un valor es una cadena de texto válida
    
    Args:
        value: Valor a validar
        min_length: Longitud mínima requerida (default: 0)
        max_length: Longitud máxima permitida (opcional)
        allow_empty: Si permite cadenas vacías (default: True)
        
    Returns:
        True si el valor es una cadena válida, False en caso contrario
        
    Ejemplo:
        >>> is_valid_string("Hola mundo", min_length=5)
        True
        >>> is_valid_string("", allow_empty=False)
        False
    """
    if not isinstance(value, str):
        return False
    
    if not allow_empty and len(value.strip()) == 0:
        return False
    
    if len(value) < min_length:
        return False
    
    if max_length is not None and len(value) > max_length:
        return False
    
    return True


def is_valid_url(url: str) -> bool:
    """
    Valida si una cadena es una URL válida
    
    Args:
        url: String con la URL a validar
        
    Returns:
        True si la URL es válida, False en caso contrario
        
    Ejemplo:
        >>> is_valid_url("https://www.ejemplo.com")
        True
        >>> is_valid_url("no-es-url")
        False
    """
    if not url or not isinstance(url, str):
        return False
    
    pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*)?(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?$'
    return re.match(pattern, url) is not None


def is_valid_phone(phone: str) -> bool:
    """
    Valida si un número de teléfono tiene un formato válido
    Acepta formatos internacionales y locales
    
    Args:
        phone: String con el número de teléfono
        
    Returns:
        True si el teléfono es válido, False en caso contrario
        
    Ejemplo:
        >>> is_valid_phone("+1234567890")
        True
        >>> is_valid_phone("123-456-7890")
        True
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Eliminar espacios, guiones y paréntesis
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Debe contener solo números y opcionalmente un + al inicio
    pattern = r'^\+?\d{7,15}$'
    return re.match(pattern, cleaned) is not None


def is_valid_priority(priority: str) -> bool:
    """
    Valida si una prioridad es válida para tareas
    
    Args:
        priority: String con la prioridad
        
    Returns:
        True si la prioridad es válida, False en caso contrario
        
    Ejemplo:
        >>> is_valid_priority("alta")
        True
        >>> is_valid_priority("invalida")
        False
    """
    valid_priorities = ["baja", "media", "alta", "urgente"]
    return priority.lower() in valid_priorities if priority else False


def is_valid_status(status: str) -> bool:
    """
    Valida si un estado es válido para tareas
    
    Args:
        status: String con el estado
        
    Returns:
        True si el estado es válido, False en caso contrario
        
    Ejemplo:
        >>> is_valid_status("pendiente")
        True
        >>> is_valid_status("invalido")
        False
    """
    valid_statuses = ["pendiente", "en_progreso", "completada", "cancelada"]
    return status.lower() in valid_statuses if status else False


def is_future_date(date_value: date) -> bool:
    """
    Valida si una fecha es futura (posterior a hoy)
    
    Args:
        date_value: Objeto date a validar
        
    Returns:
        True si la fecha es futura, False en caso contrario
        
    Ejemplo:
        >>> from datetime import date
        >>> is_future_date(date(2025, 12, 25))
        True
    """
    if not isinstance(date_value, date):
        return False
    return date_value > date.today()


def is_past_date(date_value: date) -> bool:
    """
    Valida si una fecha es pasada (anterior a hoy)
    
    Args:
        date_value: Objeto date a validar
        
    Returns:
        True si la fecha es pasada, False en caso contrario
    """
    if not isinstance(date_value, date):
        return False
    return date_value < date.today()

