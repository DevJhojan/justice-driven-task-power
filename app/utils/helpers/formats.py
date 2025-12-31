"""
Funciones de formateo de datos
Formatea fechas, horas, números, porcentajes y otros datos para mostrar en la UI
"""

from datetime import datetime, date, timedelta
from typing import Optional, Union


def format_date(date_value: Union[date, datetime, str], format_string: str = "%d/%m/%Y") -> str:
    """
    Formatea una fecha a formato legible
    
    Args:
        date_value: Fecha a formatear (date, datetime o string)
        format_string: Formato deseado (default: "%d/%m/%Y")
        
    Returns:
        String con la fecha formateada
        
    Ejemplo:
        >>> from datetime import date
        >>> format_date(date(2024, 12, 25))
        '25/12/2024'
        >>> format_date(date(2024, 12, 25), "%Y-%m-%d")
        '2024-12-25'
    """
    if isinstance(date_value, str):
        try:
            date_value = datetime.strptime(date_value, "%Y-%m-%d").date()
        except ValueError:
            return date_value
    
    if isinstance(date_value, datetime):
        date_value = date_value.date()
    
    if isinstance(date_value, date):
        return date_value.strftime(format_string)
    
    return str(date_value)


def format_time(time_value: Union[datetime, timedelta, int, float], format_type: str = "HH:MM:SS") -> str:
    """
    Formatea tiempo a formato legible
    
    Args:
        time_value: Tiempo a formatear (datetime, timedelta, segundos)
        format_type: Tipo de formato ("HH:MM:SS", "HH:MM", "human")
        
    Returns:
        String con el tiempo formateado
        
    Ejemplo:
        >>> format_time(3665)  # 1 hora, 1 minuto, 5 segundos
        '01:01:05'
        >>> format_time(3665, "human")
        '1 hora 1 minuto'
    """
    # Convertir a segundos totales
    if isinstance(time_value, timedelta):
        total_seconds = int(time_value.total_seconds())
    elif isinstance(time_value, (int, float)):
        total_seconds = int(time_value)
    elif isinstance(time_value, datetime):
        # Si es datetime, formatear como hora
        return time_value.strftime("%H:%M:%S")
    else:
        return str(time_value)
    
    if format_type == "human":
        return _format_time_human(total_seconds)
    elif format_type == "HH:MM":
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    else:  # HH:MM:SS
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _format_time_human(seconds: int) -> str:
    """Formatea segundos a formato legible humano"""
    if seconds < 60:
        return f"{seconds} segundo{'s' if seconds != 1 else ''}"
    
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minuto{'s' if minutes != 1 else ''}"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes == 0:
        return f"{hours} hora{'s' if hours != 1 else ''}"
    else:
        return f"{hours} hora{'s' if hours != 1 else ''} {remaining_minutes} minuto{'s' if remaining_minutes != 1 else ''}"


def format_datetime(datetime_value: Union[datetime, str], format_string: str = "%d/%m/%Y %H:%M") -> str:
    """
    Formatea una fecha y hora a formato legible
    
    Args:
        datetime_value: Fecha y hora a formatear
        format_string: Formato deseado (default: "%d/%m/%Y %H:%M")
        
    Returns:
        String con la fecha y hora formateada
        
    Ejemplo:
        >>> from datetime import datetime
        >>> format_datetime(datetime(2024, 12, 25, 14, 30))
        '25/12/2024 14:30'
    """
    if isinstance(datetime_value, str):
        try:
            datetime_value = datetime.fromisoformat(datetime_value)
        except ValueError:
            return datetime_value
    
    if isinstance(datetime_value, datetime):
        return datetime_value.strftime(format_string)
    
    return str(datetime_value)


def format_number(number: Union[int, float], decimals: int = 2, thousands_separator: bool = True) -> str:
    """
    Formatea un número con separadores de miles y decimales
    
    Args:
        number: Número a formatear
        decimals: Número de decimales (default: 2)
        thousands_separator: Si usar separador de miles (default: True)
        
    Returns:
        String con el número formateado
        
    Ejemplo:
        >>> format_number(1234567.89)
        '1.234.567,89'
        >>> format_number(1234567.89, decimals=0)
        '1.234.568'
    """
    if not isinstance(number, (int, float)):
        return str(number)
    
    # Formatear con decimales
    formatted = f"{number:,.{decimals}f}"
    
    # Ajustar separadores según configuración regional
    if thousands_separator:
        # Reemplazar coma por punto para miles y punto por coma para decimales
        parts = formatted.split('.')
        if len(parts) == 2:
            thousands = parts[0].replace(',', '.')
            decimals_str = parts[1]
            return f"{thousands},{decimals_str}"
        else:
            return parts[0].replace(',', '.')
    else:
        return formatted.replace(',', '')


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Formatea un valor como porcentaje
    
    Args:
        value: Valor a formatear (0.0 a 1.0 o 0 a 100)
        decimals: Número de decimales (default: 1)
        
    Returns:
        String con el porcentaje formateado
        
    Ejemplo:
        >>> format_percentage(0.856)
        '85.6%'
        >>> format_percentage(85.6)
        '85.6%'
    """
    # Si el valor es mayor a 1, asumir que ya está en porcentaje
    if value > 1:
        percentage = value
    else:
        percentage = value * 100
    
    return f"{percentage:.{decimals}f}%"


def format_currency(amount: Union[int, float], currency_symbol: str = "$", decimals: int = 2) -> str:
    """
    Formatea un monto como moneda
    
    Args:
        amount: Cantidad a formatear
        currency_symbol: Símbolo de moneda (default: "$")
        decimals: Número de decimales (default: 2)
        
    Returns:
        String con el monto formateado
        
    Ejemplo:
        >>> format_currency(1234.56)
        '$1.234,56'
        >>> format_currency(1234.56, "€")
        '€1.234,56'
    """
    formatted_number = format_number(amount, decimals=decimals)
    return f"{currency_symbol}{formatted_number}"


def format_points(points: int) -> str:
    """
    Formatea puntos con separador de miles
    
    Args:
        points: Cantidad de puntos
        
    Returns:
        String con los puntos formateados
        
    Ejemplo:
        >>> format_points(12345)
        '12.345 puntos'
    """
    formatted = format_number(points, decimals=0)
    return f"{formatted} puntos"


def format_duration(start_time: datetime, end_time: datetime) -> str:
    """
    Formatea la duración entre dos fechas/horas
    
    Args:
        start_time: Fecha/hora de inicio
        end_time: Fecha/hora de fin
        
    Returns:
        String con la duración formateada
        
    Ejemplo:
        >>> from datetime import datetime
        >>> start = datetime(2024, 12, 25, 10, 0)
        >>> end = datetime(2024, 12, 25, 14, 30)
        >>> format_duration(start, end)
        '4 horas 30 minutos'
    """
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time)
    if isinstance(end_time, str):
        end_time = datetime.fromisoformat(end_time)
    
    duration = end_time - start_time
    return format_time(duration, format_type="human")


def format_relative_time(datetime_value: datetime) -> str:
    """
    Formatea una fecha/hora como tiempo relativo (ej: "hace 2 horas")
    
    Args:
        datetime_value: Fecha/hora a formatear
        
    Returns:
        String con el tiempo relativo
        
    Ejemplo:
        >>> from datetime import datetime, timedelta
        >>> past = datetime.now() - timedelta(hours=2)
        >>> format_relative_time(past)
        'hace 2 horas'
    """
    if isinstance(datetime_value, str):
        datetime_value = datetime.fromisoformat(datetime_value)
    
    now = datetime.now()
    diff = now - datetime_value
    
    if diff.total_seconds() < 60:
        seconds = int(diff.total_seconds())
        return f"hace {seconds} segundo{'s' if seconds != 1 else ''}"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() // 60)
        return f"hace {minutes} minuto{'s' if minutes != 1 else ''}"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() // 3600)
        return f"hace {hours} hora{'s' if hours != 1 else ''}"
    elif diff.days < 7:
        days = diff.days
        return f"hace {days} día{'s' if days != 1 else ''}"
    elif diff.days < 30:
        weeks = diff.days // 7
        return f"hace {weeks} semana{'s' if weeks != 1 else ''}"
    elif diff.days < 365:
        months = diff.days // 30
        return f"hace {months} mes{'es' if months != 1 else ''}"
    else:
        years = diff.days // 365
        return f"hace {years} año{'s' if years != 1 else ''}"


def format_file_size(size_bytes: int) -> str:
    """
    Formatea el tamaño de un archivo en formato legible
    
    Args:
        size_bytes: Tamaño en bytes
        
    Returns:
        String con el tamaño formateado (KB, MB, GB, etc.)
        
    Ejemplo:
        >>> format_file_size(1024)
        '1.0 KB'
        >>> format_file_size(1048576)
        '1.0 MB'
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.1f} GB"


def format_level(level: int) -> str:
    """
    Formatea un nivel con formato especial
    
    Args:
        level: Número de nivel
        
    Returns:
        String con el nivel formateado
        
    Ejemplo:
        >>> format_level(5)
        'Nivel 5'
    """
    return f"Nivel {level}"


def format_completion_percentage(completed: int, total: int) -> str:
    """
    Formatea el porcentaje de completitud
    
    Args:
        completed: Cantidad completada
        total: Cantidad total
        
    Returns:
        String con el porcentaje de completitud
        
    Ejemplo:
        >>> format_completion_percentage(75, 100)
        '75% (75/100)'
    """
    if total == 0:
        return "0% (0/0)"
    
    percentage = int((completed / total) * 100)
    return f"{percentage}% ({completed}/{total})"


def format_task_count(count: int) -> str:
    """
    Formatea el conteo de tareas
    
    Args:
        count: Cantidad de tareas
        
    Returns:
        String formateado
        
    Ejemplo:
        >>> format_task_count(5)
        '5 tareas'
        >>> format_task_count(1)
        '1 tarea'
    """
    if count == 0:
        return "Sin tareas"
    elif count == 1:
        return "1 tarea"
    else:
        return f"{count} tareas"


def format_habit_streak(days: int) -> str:
    """
    Formatea una racha de días de hábito
    
    Args:
        days: Cantidad de días consecutivos
        
    Returns:
        String con la racha formateada
        
    Ejemplo:
        >>> format_habit_streak(7)
        'Racha de 7 días 🔥'
    """
    if days == 0:
        return "Sin racha"
    elif days < 7:
        return f"Racha de {days} día{'s' if days != 1 else ''}"
    elif days < 30:
        return f"Racha de {days} días 🔥"
    elif days < 100:
        return f"Racha de {days} días 🔥🔥"
    else:
        return f"Racha de {days} días 🔥🔥🔥"

