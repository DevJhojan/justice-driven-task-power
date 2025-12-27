"""
Repositorio para operaciones CRUD de objetivos en la base de datos.
"""
from datetime import datetime
from typing import List, Optional
from app.data.database import Database
from app.data.models import Goal


class GoalRepository:
    """Repositorio para gestionar objetivos en la base de datos."""
    
    def __init__(self, database: Database):
        """
        Inicializa el repositorio.
        
        Args:
            database: Instancia de Database.
        """
        self.db = database
    
    def create(self, goal: Goal) -> Goal:
        """
        Crea un nuevo objetivo en la base de datos.
        
        Args:
            goal: Objetivo a crear.
            
        Returns:
            Objetivo creado con ID asignado.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        # Si el objetivo tiene un ID, intentar insertarlo (útil para sincronización)
        if goal.id is not None:
            # Verificar si ya existe un objetivo con ese ID
            cursor.execute('SELECT id FROM goals WHERE id = ?', (goal.id,))
            if cursor.fetchone():
                # Ya existe, actualizar en lugar de crear
                conn.close()
                return self.update(goal)
            
            # Insertar con ID específico
            cursor.execute('''
                INSERT INTO goals (id, title, description, frequency, target_date, completed, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                goal.id,
                goal.title,
                goal.description,
                goal.frequency,
                goal.target_date.isoformat() if goal.target_date else None,
                1 if goal.completed else 0,
                goal.created_at.isoformat() if goal.created_at else now,
                goal.updated_at.isoformat() if goal.updated_at else now
            ))
        else:
            # Insertar sin ID (auto-increment)
            cursor.execute('''
                INSERT INTO goals (title, description, frequency, target_date, completed, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                goal.title,
                goal.description,
                goal.frequency,
                goal.target_date.isoformat() if goal.target_date else None,
                1 if goal.completed else 0,
                now,
                now
            ))
            goal.id = cursor.lastrowid
        
        if not goal.created_at:
            goal.created_at = datetime.now()
        if not goal.updated_at:
            goal.updated_at = datetime.now()
        
        conn.commit()
        conn.close()
        
        return goal
    
    def get_by_id(self, goal_id: int) -> Optional[Goal]:
        """
        Obtiene un objetivo por su ID.
        
        Args:
            goal_id: ID del objetivo.
            
        Returns:
            Objetivo encontrado o None.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM goals WHERE id = ?', (goal_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_goal(row)
        return None
    
    def get_all(self, filter_completed: Optional[bool] = None, filter_frequency: Optional[str] = None) -> List[Goal]:
        """
        Obtiene todos los objetivos.
        
        Args:
            filter_completed: Si se proporciona, filtra por estado de completado.
            filter_frequency: Si se proporciona, filtra por frecuencia.
            
        Returns:
            Lista de objetivos.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM goals WHERE 1=1'
        params = []
        
        if filter_completed is not None:
            query += ' AND completed = ?'
            params.append(1 if filter_completed else 0)
        
        if filter_frequency:
            query += ' AND frequency = ?'
            params.append(filter_frequency)
        
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_goal(row) for row in rows]
    
    def update(self, goal: Goal) -> Goal:
        """
        Actualiza un objetivo existente.
        
        Args:
            goal: Objetivo con los datos actualizados.
            
        Returns:
            Objetivo actualizado.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE goals 
            SET title = ?, description = ?, frequency = ?, target_date = ?, completed = ?, updated_at = ?
            WHERE id = ?
        ''', (
            goal.title,
            goal.description,
            goal.frequency,
            goal.target_date.isoformat() if goal.target_date else None,
            1 if goal.completed else 0,
            now,
            goal.id
        ))
        
        goal.updated_at = datetime.now()
        
        conn.commit()
        conn.close()
        
        return goal
    
    def delete(self, goal_id: int) -> bool:
        """
        Elimina un objetivo por su ID y registra la eliminación para sincronización.
        
        Args:
            goal_id: ID del objetivo a eliminar.
            
        Returns:
            True si se eliminó, False si no existía.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Verificar que el objetivo existe antes de eliminarlo
        cursor.execute('SELECT id FROM goals WHERE id = ?', (goal_id,))
        exists = cursor.fetchone() is not None
        
        if not exists:
            conn.close()
            return False
        
        # Eliminar el objetivo
        cursor.execute('DELETE FROM goals WHERE id = ?', (goal_id,))
        deleted = cursor.rowcount > 0
        
        if deleted:
            # Registrar la eliminación para sincronización
            deleted_at = datetime.now().isoformat()
            cursor.execute('''
                INSERT OR REPLACE INTO deleted_items (item_type, item_id, deleted_at, synced_at)
                VALUES (?, ?, ?, NULL)
            ''', ('goal', goal_id, deleted_at))
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def toggle_complete(self, goal_id: int) -> Optional[Goal]:
        """
        Cambia el estado de completado de un objetivo.
        
        Args:
            goal_id: ID del objetivo.
            
        Returns:
            Objetivo actualizado o None si no existe.
        """
        goal = self.get_by_id(goal_id)
        if goal:
            goal.completed = not goal.completed
            return self.update(goal)
        return None
    
    def _row_to_goal(self, row) -> Goal:
        """
        Convierte una fila de la base de datos a un objeto Goal.
        
        Args:
            row: Fila de SQLite.
            
        Returns:
            Objeto Goal.
        """
        created_at = None
        updated_at = None
        target_date = None
        
        if row['created_at']:
            created_at = datetime.fromisoformat(row['created_at'])
        if row['updated_at']:
            updated_at = datetime.fromisoformat(row['updated_at'])
        if row['target_date']:
            target_date = datetime.fromisoformat(row['target_date'])
        
        return Goal(
            id=row['id'],
            title=row['title'],
            description=row['description'] or '',
            frequency=row['frequency'],
            target_date=target_date,
            completed=bool(row['completed']),
            created_at=created_at,
            updated_at=updated_at
        )

