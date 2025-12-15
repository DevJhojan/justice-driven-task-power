"""
Repositorio para operaciones CRUD de hábitos en la base de datos.
"""
from datetime import datetime, date
from typing import List, Optional
from app.data.database import Database
from app.data.models import Habit, HabitCompletion


class HabitRepository:
    """Repositorio para gestionar hábitos en la base de datos."""
    
    def __init__(self, database: Database):
        """
        Inicializa el repositorio.
        
        Args:
            database: Instancia de Database.
        """
        self.db = database
    
    def create(self, habit: Habit) -> Habit:
        """
        Crea un nuevo hábito en la base de datos.
        
        Args:
            habit: Hábito a crear.
            
        Returns:
            Hábito creado con ID asignado.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO habits (title, description, frequency, target_days, active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            habit.title,
            habit.description,
            habit.frequency,
            habit.target_days,
            1 if habit.active else 0,
            now,
            now
        ))
        
        habit.id = cursor.lastrowid
        habit.created_at = datetime.now()
        habit.updated_at = datetime.now()
        
        conn.commit()
        conn.close()
        
        return habit
    
    def get_by_id(self, habit_id: int) -> Optional[Habit]:
        """
        Obtiene un hábito por su ID.
        
        Args:
            habit_id: ID del hábito.
            
        Returns:
            Hábito encontrado o None.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM habits WHERE id = ?', (habit_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            habit = self._row_to_habit(row)
            # Cargar cumplimientos
            habit.completions = self.get_completions(habit_id)
            return habit
        return None
    
    def get_all(self, filter_active: Optional[bool] = None) -> List[Habit]:
        """
        Obtiene todos los hábitos.
        
        Args:
            filter_active: Si se proporciona, filtra por estado activo/inactivo.
            
        Returns:
            Lista de hábitos.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        if filter_active is not None:
            cursor.execute('''
                SELECT * FROM habits 
                WHERE active = ?
                ORDER BY created_at DESC
            ''', (1 if filter_active else 0,))
        else:
            cursor.execute('SELECT * FROM habits ORDER BY created_at DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        habits = [self._row_to_habit(row) for row in rows]
        # Cargar cumplimientos para cada hábito
        for habit in habits:
            habit.completions = self.get_completions(habit.id)
        return habits
    
    def update(self, habit: Habit) -> Habit:
        """
        Actualiza un hábito existente.
        
        Args:
            habit: Hábito con los datos actualizados.
            
        Returns:
            Hábito actualizado.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE habits 
            SET title = ?, description = ?, frequency = ?, target_days = ?, active = ?, updated_at = ?
            WHERE id = ?
        ''', (
            habit.title,
            habit.description,
            habit.frequency,
            habit.target_days,
            1 if habit.active else 0,
            now,
            habit.id
        ))
        
        habit.updated_at = datetime.now()
        
        conn.commit()
        conn.close()
        
        return habit
    
    def delete(self, habit_id: int) -> bool:
        """
        Elimina un hábito por su ID (borrado físico).
        Los cumplimientos se eliminan automáticamente por CASCADE.
        
        Args:
            habit_id: ID del hábito a eliminar.
            
        Returns:
            True si se eliminó, False si no existía.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM habits WHERE id = ?', (habit_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def toggle_active(self, habit_id: int) -> Optional[Habit]:
        """
        Cambia el estado activo/inactivo de un hábito.
        
        Args:
            habit_id: ID del hábito.
            
        Returns:
            Hábito actualizado o None si no existe.
        """
        habit = self.get_by_id(habit_id)
        if habit:
            habit.active = not habit.active
            return self.update(habit)
        return None
    
    def get_completions(self, habit_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[HabitCompletion]:
        """
        Obtiene los cumplimientos de un hábito.
        
        Args:
            habit_id: ID del hábito.
            start_date: Fecha de inicio (opcional).
            end_date: Fecha de fin (opcional).
            
        Returns:
            Lista de cumplimientos.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        if start_date and end_date:
            start_str = start_date.isoformat()
            end_str = end_date.isoformat()
            cursor.execute('''
                SELECT * FROM habit_completions 
                WHERE habit_id = ? AND completion_date >= ? AND completion_date <= ?
                ORDER BY completion_date DESC
            ''', (habit_id, start_str, end_str))
        elif start_date:
            start_str = start_date.isoformat()
            cursor.execute('''
                SELECT * FROM habit_completions 
                WHERE habit_id = ? AND completion_date >= ?
                ORDER BY completion_date DESC
            ''', (habit_id, start_str))
        elif end_date:
            end_str = end_date.isoformat()
            cursor.execute('''
                SELECT * FROM habit_completions 
                WHERE habit_id = ? AND completion_date <= ?
                ORDER BY completion_date DESC
            ''', (habit_id, end_str))
        else:
            cursor.execute('''
                SELECT * FROM habit_completions 
                WHERE habit_id = ? 
                ORDER BY completion_date DESC
            ''', (habit_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_completion(row) for row in rows]
    
    def create_completion(self, completion: HabitCompletion) -> HabitCompletion:
        """
        Crea un nuevo registro de cumplimiento.
        Usa INSERT OR IGNORE para evitar duplicados (restricción UNIQUE).
        
        Args:
            completion: Cumplimiento a crear.
            
        Returns:
            Cumplimiento creado con ID asignado.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        # Normalizar fecha a medianoche (solo fecha)
        completion_date = completion.completion_date.replace(hour=0, minute=0, second=0, microsecond=0)
        completion_date_str = completion_date.isoformat()
        
        # Verificar si ya existe un cumplimiento para este hábito en esta fecha
        cursor.execute('''
            SELECT id FROM habit_completions 
            WHERE habit_id = ? AND completion_date = ?
        ''', (completion.habit_id, completion_date_str))
        
        existing = cursor.fetchone()
        if existing:
            conn.close()
            # Retornar el existente
            completion.id = existing['id']
            return completion
        
        cursor.execute('''
            INSERT INTO habit_completions (habit_id, completion_date, created_at)
            VALUES (?, ?, ?)
        ''', (
            completion.habit_id,
            completion_date_str,
            now
        ))
        
        completion.id = cursor.lastrowid
        completion.created_at = datetime.now()
        
        conn.commit()
        conn.close()
        
        return completion
    
    def delete_completion(self, completion_id: int) -> bool:
        """
        Elimina un registro de cumplimiento por su ID.
        
        Args:
            completion_id: ID del cumplimiento a eliminar.
            
        Returns:
            True si se eliminó, False si no existía.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM habit_completions WHERE id = ?', (completion_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def delete_completion_by_date(self, habit_id: int, completion_date: date) -> bool:
        """
        Elimina un registro de cumplimiento por hábito y fecha.
        
        Args:
            habit_id: ID del hábito.
            completion_date: Fecha del cumplimiento.
            
        Returns:
            True si se eliminó, False si no existía.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Normalizar fecha
        if isinstance(completion_date, datetime):
            completion_date = completion_date.date()
        completion_date_str = completion_date.isoformat()
        
        cursor.execute('''
            DELETE FROM habit_completions 
            WHERE habit_id = ? AND completion_date = ?
        ''', (habit_id, completion_date_str))
        
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def has_completion_for_date(self, habit_id: int, completion_date: date) -> bool:
        """
        Verifica si existe un cumplimiento para un hábito en una fecha específica.
        
        Args:
            habit_id: ID del hábito.
            completion_date: Fecha a verificar.
            
        Returns:
            True si existe, False si no.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Normalizar fecha
        if isinstance(completion_date, datetime):
            completion_date = completion_date.date()
        completion_date_str = completion_date.isoformat()
        
        cursor.execute('''
            SELECT COUNT(*) as count FROM habit_completions 
            WHERE habit_id = ? AND completion_date = ?
        ''', (habit_id, completion_date_str))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['count'] > 0
    
    def _row_to_habit(self, row) -> Habit:
        """
        Convierte una fila de la base de datos a un objeto Habit.
        
        Args:
            row: Fila de SQLite.
            
        Returns:
            Objeto Habit.
        """
        created_at = None
        updated_at = None
        
        if row['created_at']:
            created_at = datetime.fromisoformat(row['created_at'])
        if row['updated_at']:
            updated_at = datetime.fromisoformat(row['updated_at'])
        
        return Habit(
            id=row['id'],
            title=row['title'],
            description=row['description'] or '',
            frequency=row['frequency'],
            target_days=row['target_days'],
            active=bool(row['active']),
            created_at=created_at,
            updated_at=updated_at,
            completions=[]  # Se cargarán después
        )
    
    def _row_to_completion(self, row) -> HabitCompletion:
        """
        Convierte una fila de la base de datos a un objeto HabitCompletion.
        
        Args:
            row: Fila de SQLite.
            
        Returns:
            Objeto HabitCompletion.
        """
        created_at = None
        completion_date = None
        
        if row['created_at']:
            created_at = datetime.fromisoformat(row['created_at'])
        if row['completion_date']:
            completion_date = datetime.fromisoformat(row['completion_date'])
            # Normalizar a medianoche
            completion_date = completion_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return HabitCompletion(
            id=row['id'],
            habit_id=row['habit_id'],
            completion_date=completion_date,
            created_at=created_at
        )
