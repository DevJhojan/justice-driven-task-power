"""
Repositorio para gestión de hábitos en la base de datos.
"""
import sqlite3
from datetime import datetime, date
from typing import List, Optional, Set

from app.data.database import Database
from app.data.models import Habit, HabitCompletion


class HabitRepository:
    """Repositorio para operaciones CRUD de hábitos."""
    
    def __init__(self, db: Database):
        """
        Inicializa el repositorio.
        
        Args:
            db: Instancia de Database.
        """
        self.db = db
    
    def create(self, habit: Habit) -> Habit:
        """
        Crea un nuevo hábito.
        
        Args:
            habit: Hábito a crear (id debe ser None).
        
        Returns:
            Hábito creado con el id asignado.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO habits (title, description, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, (
            habit.title,
            habit.description,
            now,
            now
        ))
        
        habit_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        habit.id = habit_id
        habit.created_at = datetime.fromisoformat(now)
        habit.updated_at = datetime.fromisoformat(now)
        return habit
    
    def get_by_id(self, habit_id: int) -> Optional[Habit]:
        """
        Obtiene un hábito por su ID.
        
        Args:
            habit_id: ID del hábito.
        
        Returns:
            Hábito si existe, None en caso contrario.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM habits WHERE id = ?", (habit_id,))
        row = cursor.fetchone()
        conn.close()
        
        return self._row_to_habit(row) if row else None
    
    def get_all(self) -> List[Habit]:
        """
        Obtiene todos los hábitos.
        
        Returns:
            Lista de todos los hábitos.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM habits ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_habit(row) for row in rows]
    
    def update(self, habit: Habit) -> Habit:
        """
        Actualiza un hábito existente.
        
        Args:
            habit: Hábito a actualizar (debe tener id).
        
        Returns:
            Hábito actualizado.
        """
        if habit.id is None:
            raise ValueError("El hábito debe tener un id para ser actualizado")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE habits
            SET title = ?, description = ?, updated_at = ?
            WHERE id = ?
        """, (
            habit.title,
            habit.description,
            now,
            habit.id
        ))
        
        conn.commit()
        conn.close()
        
        habit.updated_at = datetime.fromisoformat(now)
        return habit
    
    def delete(self, habit_id: int) -> bool:
        """
        Elimina un hábito y todas sus completaciones.
        
        Args:
            habit_id: ID del hábito a eliminar.
        
        Returns:
            True si se eliminó, False si no existía.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Las completaciones se eliminan automáticamente por CASCADE
        cursor.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def add_completion(self, habit_id: int, completion_date: date) -> HabitCompletion:
        """
        Registra una completación de hábito para una fecha específica.
        
        Args:
            habit_id: ID del hábito.
            completion_date: Fecha de completación.
        
        Returns:
            HabitCompletion creado.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT OR IGNORE INTO habit_completions (habit_id, completion_date, created_at)
            VALUES (?, ?, ?)
        """, (
            habit_id,
            completion_date.isoformat(),
            now
        ))
        
        # Si ya existe, obtener el registro existente
        cursor.execute("""
            SELECT * FROM habit_completions 
            WHERE habit_id = ? AND completion_date = ?
        """, (habit_id, completion_date.isoformat()))
        row = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        return self._row_to_completion(row)
    
    def remove_completion(self, habit_id: int, completion_date: date) -> bool:
        """
        Elimina una completación de hábito para una fecha específica.
        
        Args:
            habit_id: ID del hábito.
            completion_date: Fecha de completación.
        
        Returns:
            True si se eliminó, False si no existía.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM habit_completions 
            WHERE habit_id = ? AND completion_date = ?
        """, (habit_id, completion_date.isoformat()))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def get_completions(self, habit_id: int) -> Set[date]:
        """
        Obtiene todas las fechas en las que se completó un hábito.
        
        Args:
            habit_id: ID del hábito.
        
        Returns:
            Conjunto de fechas de completación.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT completion_date FROM habit_completions 
            WHERE habit_id = ?
        """, (habit_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return {date.fromisoformat(row['completion_date']) for row in rows}
    
    def get_completion_count(self, habit_id: int) -> int:
        """
        Obtiene el número total de completaciones de un hábito.
        
        Args:
            habit_id: ID del hábito.
        
        Returns:
            Número de completaciones.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM habit_completions 
            WHERE habit_id = ?
        """, (habit_id,))
        row = cursor.fetchone()
        conn.close()
        
        return row['count'] if row else 0
    
    def _row_to_habit(self, row: sqlite3.Row) -> Habit:
        """
        Convierte una fila de la base de datos en un objeto Habit.
        
        Args:
            row: Fila de la base de datos.
        
        Returns:
            Objeto Habit.
        """
        created_at = None
        if row['created_at']:
            created_at = datetime.fromisoformat(row['created_at'])
        
        updated_at = None
        if row['updated_at']:
            updated_at = datetime.fromisoformat(row['updated_at'])
        
        return Habit(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            created_at=created_at,
            updated_at=updated_at
        )
    
    def _row_to_completion(self, row: sqlite3.Row) -> HabitCompletion:
        """
        Convierte una fila de la base de datos en un objeto HabitCompletion.
        
        Args:
            row: Fila de la base de datos.
        
        Returns:
            Objeto HabitCompletion.
        """
        created_at = None
        if row['created_at']:
            created_at = datetime.fromisoformat(row['created_at'])
        
        return HabitCompletion(
            id=row['id'],
            habit_id=row['habit_id'],
            completion_date=date.fromisoformat(row['completion_date']),
            created_at=created_at
        )

