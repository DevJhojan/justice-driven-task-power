"""
Servicio de lógica de negocio para hábitos.
"""
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from app.data.database import Database
from app.data.habit_repository import HabitRepository
from app.data.models import Habit, HabitCompletion


class HabitService:
    """Servicio para gestionar la lógica de negocio de hábitos."""
    
    def __init__(self):
        """Inicializa el servicio con la base de datos y repositorio."""
        self.db = Database()
        self.repository = HabitRepository(self.db)
    
    def create_habit(self, title: str, description: str = "", frequency: str = "daily", target_days: int = 1) -> Habit:
        """
        Crea un nuevo hábito.
        
        Args:
            title: Título del hábito.
            description: Descripción del hábito.
            frequency: Frecuencia ('daily', 'weekly', 'custom').
            target_days: Número de días objetivo (1-7).
            
        Returns:
            Hábito creado.
        """
        if not title or not title.strip():
            raise ValueError("El título del hábito no puede estar vacío")
        
        if frequency not in ['daily', 'weekly', 'custom']:
            frequency = 'daily'
        
        if target_days < 1 or target_days > 7:
            target_days = 7 if frequency == 'weekly' else 1
        
        habit = Habit(
            id=None,
            title=title.strip(),
            description=description.strip(),
            frequency=frequency,
            target_days=target_days,
            active=True,
            created_at=None,
            updated_at=None
        )
        
        return self.repository.create(habit)
    
    def get_all_habits(self, filter_active: Optional[bool] = None) -> List[Habit]:
        """
        Obtiene todos los hábitos, opcionalmente filtrados por estado.
        
        Args:
            filter_active: Si se proporciona, filtra por estado activo/inactivo.
            
        Returns:
            Lista de hábitos.
        """
        return self.repository.get_all(filter_active)
    
    def get_habit(self, habit_id: int) -> Optional[Habit]:
        """
        Obtiene un hábito por su ID.
        
        Args:
            habit_id: ID del hábito.
            
        Returns:
            Hábito encontrado o None.
        """
        return self.repository.get_by_id(habit_id)
    
    def update_habit(self, habit: Habit) -> Habit:
        """
        Actualiza un hábito existente.
        
        Args:
            habit: Hábito con los datos actualizados.
            
        Returns:
            Hábito actualizado.
        """
        if not habit.title or not habit.title.strip():
            raise ValueError("El título del hábito no puede estar vacío")
        
        habit.title = habit.title.strip()
        habit.description = habit.description.strip()
        
        if habit.frequency not in ['daily', 'weekly', 'custom']:
            habit.frequency = 'daily'
        
        if habit.target_days < 1 or habit.target_days > 7:
            habit.target_days = 7 if habit.frequency == 'weekly' else 1
        
        return self.repository.update(habit)
    
    def delete_habit(self, habit_id: int) -> bool:
        """
        Elimina un hábito.
        
        Args:
            habit_id: ID del hábito a eliminar.
            
        Returns:
            True si se eliminó, False si no existía.
        """
        return self.repository.delete(habit_id)
    
    def toggle_habit_active(self, habit_id: int) -> Optional[Habit]:
        """
        Cambia el estado activo/inactivo de un hábito.
        
        Args:
            habit_id: ID del hábito.
            
        Returns:
            Hábito actualizado o None si no existe.
        """
        return self.repository.toggle_active(habit_id)
    
    def register_completion(self, habit_id: int, completion_date: Optional[date] = None) -> Optional[HabitCompletion]:
        """
        Registra el cumplimiento de un hábito para una fecha específica.
        Solo permite un registro por hábito por día.
        
        Args:
            habit_id: ID del hábito.
            completion_date: Fecha del cumplimiento. Si es None, usa la fecha actual.
            
        Returns:
            Cumplimiento creado o None si ya existía o el hábito no existe.
        """
        habit = self.repository.get_by_id(habit_id)
        if not habit:
            return None
        
        if not habit.active:
            return None
        
        if completion_date is None:
            completion_date = date.today()
        
        # Verificar si ya existe un cumplimiento para esta fecha
        if self.repository.has_completion_for_date(habit_id, completion_date):
            return None  # Ya existe, no se puede duplicar
        
        completion = HabitCompletion(
            id=None,
            habit_id=habit_id,
            completion_date=datetime.combine(completion_date, datetime.min.time()),
            created_at=None
        )
        
        return self.repository.create_completion(completion)
    
    def remove_completion(self, habit_id: int, completion_date: date) -> bool:
        """
        Elimina un registro de cumplimiento.
        
        Args:
            habit_id: ID del hábito.
            completion_date: Fecha del cumplimiento a eliminar.
            
        Returns:
            True si se eliminó, False si no existía.
        """
        return self.repository.delete_completion_by_date(habit_id, completion_date)
    
    def toggle_completion(self, habit_id: int, completion_date: Optional[date] = None) -> Optional[HabitCompletion]:
        """
        Alterna el estado de cumplimiento de un hábito para una fecha.
        Si existe, lo elimina. Si no existe, lo crea.
        
        Args:
            habit_id: ID del hábito.
            completion_date: Fecha del cumplimiento. Si es None, usa la fecha actual.
            
        Returns:
            Cumplimiento creado o None si se eliminó.
        """
        if completion_date is None:
            completion_date = date.today()
        
        # Normalizar fecha (asegurar que es un objeto date, no datetime)
        if isinstance(completion_date, datetime):
            completion_date = completion_date.date()
        
        # Debug: verificar estado antes del toggle
        has_completion = self.repository.has_completion_for_date(habit_id, completion_date)
        print(f"DEBUG toggle_completion: habit_id={habit_id}, date={completion_date}, has_completion={has_completion}")
        
        if has_completion:
            # Existe, eliminarlo
            deleted = self.repository.delete_completion_by_date(habit_id, completion_date)
            print(f"DEBUG toggle_completion: deleted={deleted}")
            # Verificar que se eliminó
            has_after = self.repository.has_completion_for_date(habit_id, completion_date)
            print(f"DEBUG toggle_completion: has_completion after delete={has_after}")
            return None
        else:
            # No existe, crearlo
            result = self.register_completion(habit_id, completion_date)
            print(f"DEBUG toggle_completion: created completion id={result.id if result else None}")
            # Verificar que se creó
            has_after = self.repository.has_completion_for_date(habit_id, completion_date)
            print(f"DEBUG toggle_completion: has_completion after create={has_after}")
            return result
    
    def get_habit_metrics(self, habit_id: int) -> Dict:
        """
        Calcula las métricas de un hábito.
        
        Métricas calculadas:
        - streak: Días consecutivos actuales
        - total_completions: Total de veces completado
        - completion_percentage: Porcentaje de cumplimiento
        - last_completion_date: Última fecha de cumplimiento
        - current_streak_start: Fecha de inicio del streak actual
        
        Args:
            habit_id: ID del hábito.
            
        Returns:
            Diccionario con las métricas.
        """
        habit = self.repository.get_by_id(habit_id)
        if not habit:
            return {
                'streak': 0,
                'total_completions': 0,
                'completion_percentage': 0.0,
                'last_completion_date': None,
                'current_streak_start': None
            }
        
        completions = habit.completions
        if not completions:
            return {
                'streak': 0,
                'total_completions': 0,
                'completion_percentage': 0.0,
                'last_completion_date': None,
                'current_streak_start': None
            }
        
        # Ordenar cumplimientos por fecha (más reciente primero)
        sorted_completions = sorted(completions, key=lambda x: x.completion_date, reverse=True)
        
        total_completions = len(completions)
        last_completion_date = sorted_completions[0].completion_date.date() if sorted_completions else None
        
        # Calcular streak (días consecutivos desde la última fecha)
        streak = 0
        current_streak_start = None
        today = date.today()
        
        if last_completion_date:
            # Verificar si el último cumplimiento es hoy o ayer (permitir 1 día de margen)
            if last_completion_date >= today - timedelta(days=1):
                # Calcular streak hacia atrás desde la última fecha
                expected_date = last_completion_date
                for completion in sorted_completions:
                    comp_date = completion.completion_date.date()
                    if comp_date == expected_date:
                        streak += 1
                        current_streak_start = comp_date
                        expected_date = comp_date - timedelta(days=1)
                    elif comp_date < expected_date:
                        # Hay un gap, terminar el streak
                        break
            else:
                # El último cumplimiento es muy antiguo, streak = 0
                streak = 0
        
        # Calcular porcentaje de cumplimiento
        # Para hábitos diarios: porcentaje basado en los últimos 30 días
        # Para hábitos semanales: porcentaje basado en las últimas 4 semanas
        completion_percentage = 0.0
        
        if habit.frequency == 'daily':
            # Últimos 30 días
            start_date = today - timedelta(days=30)
            recent_completions = [
                c for c in completions 
                if c.completion_date.date() >= start_date
            ]
            completion_percentage = (len(recent_completions) / 30.0) * 100.0
        elif habit.frequency == 'weekly':
            # Últimas 4 semanas
            start_date = today - timedelta(weeks=4)
            recent_completions = [
                c for c in completions 
                if c.completion_date.date() >= start_date
            ]
            # Calcular semanas con al menos target_days cumplimientos
            weeks_data = {}
            for comp in recent_completions:
                comp_date = comp.completion_date.date()
                week_start = comp_date - timedelta(days=comp_date.weekday())
                if week_start not in weeks_data:
                    weeks_data[week_start] = 0
                weeks_data[week_start] += 1
            
            weeks_with_target = sum(1 for count in weeks_data.values() if count >= habit.target_days)
            completion_percentage = (weeks_with_target / 4.0) * 100.0 if weeks_data else 0.0
        
        return {
            'streak': streak,
            'total_completions': total_completions,
            'completion_percentage': round(completion_percentage, 1),
            'last_completion_date': last_completion_date,
            'current_streak_start': current_streak_start
        }
    
    def get_weekly_progress(self, habit_id: int, week_start: Optional[date] = None) -> Dict:
        """
        Obtiene el progreso semanal de un hábito.
        
        Args:
            habit_id: ID del hábito.
            week_start: Fecha de inicio de la semana (lunes). Si es None, usa la semana actual.
            
        Returns:
            Diccionario con el progreso de la semana.
        """
        if week_start is None:
            today = date.today()
            # Calcular el lunes de la semana actual
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)
        
        week_end = week_start + timedelta(days=6)
        
        completions = self.repository.get_completions(habit_id, week_start, week_end)
        completion_dates = {c.completion_date.date() for c in completions}
        
        # Crear un diccionario con el estado de cada día de la semana
        week_progress = {}
        for i in range(7):
            day_date = week_start + timedelta(days=i)
            week_progress[day_date] = day_date in completion_dates
        
        return {
            'week_start': week_start,
            'week_end': week_end,
            'progress': week_progress,
            'completions_count': len(completions),
            'target_days': self.repository.get_by_id(habit_id).target_days if self.repository.get_by_id(habit_id) else 1
        }
    
    def get_monthly_progress(self, habit_id: int, month: Optional[int] = None, year: Optional[int] = None) -> Dict:
        """
        Obtiene el progreso mensual de un hábito.
        
        Args:
            habit_id: ID del hábito.
            month: Mes (1-12). Si es None, usa el mes actual.
            year: Año. Si es None, usa el año actual.
            
        Returns:
            Diccionario con el progreso del mes.
        """
        today = date.today()
        if month is None:
            month = today.month
        if year is None:
            year = today.year
        
        # Primer y último día del mes
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)
        
        completions = self.repository.get_completions(habit_id, month_start, month_end)
        completion_dates = {c.completion_date.date() for c in completions}
        
        return {
            'month': month,
            'year': year,
            'month_start': month_start,
            'month_end': month_end,
            'completions': completion_dates,
            'completions_count': len(completions),
            'total_days': (month_end - month_start).days + 1
        }
    
    def get_statistics(self) -> Dict:
        """
        Obtiene estadísticas generales de todos los hábitos.
        
        Returns:
            Diccionario con estadísticas.
        """
        all_habits = self.repository.get_all()
        active_habits = [h for h in all_habits if h.active]
        
        total_habits = len(all_habits)
        active_count = len(active_habits)
        inactive_count = total_habits - active_count
        
        # Calcular total de cumplimientos
        total_completions = sum(len(h.completions) for h in all_habits)
        
        # Calcular hábitos con streak activo
        habits_with_streak = 0
        for habit in active_habits:
            metrics = self.get_habit_metrics(habit.id)
            if metrics['streak'] > 0:
                habits_with_streak += 1
        
        return {
            'total': total_habits,
            'active': active_count,
            'inactive': inactive_count,
            'total_completions': total_completions,
            'habits_with_streak': habits_with_streak
        }
