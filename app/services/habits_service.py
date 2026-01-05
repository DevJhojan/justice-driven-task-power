"""
Servicio de Hábitos (Habits Service)
Gestiona la lógica de negocio y persistencia de hábitos en BD
"""

from typing import Dict, List, Optional
from app.models.habit import Habit
from app.services.database_service import DatabaseService


class HabitsService:
    """Servicio para gestionar hábitos con persistencia en BD"""
    
    def __init__(self, database_service: Optional[DatabaseService] = None):
        """
        Inicializa el servicio de hábitos
        
        Args:
            database_service: Servicio de BD (crea uno nuevo si no se proporciona)
        """
        self.database_service = database_service or DatabaseService()
        self.habits: Dict[str, Habit] = {}
    
    async def initialize(self):
        """Inicializa la tabla de hábitos en la BD"""
        try:
            await self.database_service.execute(
                """
                CREATE TABLE IF NOT EXISTS habits (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    frequency TEXT DEFAULT 'daily',
                    frequency_times INTEGER DEFAULT 1,
                    streak INTEGER DEFAULT 0,
                    last_completed TEXT,
                    created_at TEXT
                )
                """
            )
            # Intentar agregar columna nueva si la tabla ya existía
            try:
                await self.database_service.execute(
                    "ALTER TABLE habits ADD COLUMN frequency_times INTEGER DEFAULT 1"
                )
                await self.database_service.commit()
            except Exception:
                # Si ya existe la columna, ignorar el error
                pass
            await self.database_service.commit()
            print("[HabitsService] Tabla de hábitos creada/verificada")
            
            # Cargar hábitos existentes
            await self.load_from_db()
        except Exception as e:
            print(f"[HabitsService] Error inicializando BD: {e}")
    
    async def load_from_db(self):
        """Carga hábitos desde la BD"""
        try:
            habits_data = await self.database_service.get_all("habits")
            self.habits = {}
            for habit_data in habits_data:
                habit = Habit.from_dict(habit_data)
                self.habits[habit.id] = habit
            print(f"[HabitsService] Cargados {len(self.habits)} hábitos desde BD")
        except Exception as e:
            print(f"[HabitsService] Error cargando hábitos: {e}")
    
    async def create_habit(
        self,
        title: str,
        description: str,
        frequency: str = "daily",
        frequency_times: int = 1,
    ) -> Habit:
        """
        Crea un nuevo hábito
        
        Args:
            title: Título del hábito
            description: Descripción del hábito
            frequency: Frecuencia (daily, weekly, monthly, semiannual, annual)
            frequency_times: Veces por periodo (ej: por semana, por mes)
        
        Returns:
            Hábito creado
        """
        try:
            habit = Habit(
                title=title,
                description=description,
                frequency=frequency,
                frequency_times=frequency_times,
            )
            
            self.habits[habit.id] = habit
            await self._save_to_db(habit)
            print(f"[HabitsService] Hábito creado: {habit.title}")
            return habit
        except Exception as e:
            print(f"[HabitsService] Error creando hábito: {e}")
            raise
    
    async def complete_habit(self, habit_id: str) -> bool:
        """
        Marca/desmarca un hábito como completado hoy
        
        Args:
            habit_id: ID del hábito
        
        Returns:
            True si se completó, False si se desmarcó
        """
        try:
            if habit_id not in self.habits:
                print(f"[HabitsService] Hábito no encontrado: {habit_id}")
                return False
            
            habit = self.habits[habit_id]
            
            # Si ya fue completado hoy, desmarcarlo
            if habit.was_completed_today():
                # Desmarcar: restar 1 a la racha (mínimo 0)
                habit.streak = max(0, habit.streak - 1)
                habit.last_completed = None
                was_completed = False
            else:
                # Marcar como completado
                habit.complete_today()
                was_completed = True
            
            await self._update_in_db(habit)
            return was_completed
        except Exception as e:
            print(f"[HabitsService] Error completando hábito: {e}")
            raise

    async def update_habit(
        self,
        habit_id: str,
        title: str,
        description: str,
        frequency: str = "daily",
        frequency_times: int = 1,
    ) -> Optional[Habit]:
        """Actualiza título, descripción, frecuencia y cantidad de un hábito"""
        try:
            habit = self.habits.get(habit_id)
            if not habit:
                print(f"[HabitsService] Hábito no encontrado: {habit_id}")
                return None
            habit.title = title
            habit.description = description
            habit.frequency = frequency
            habit.frequency_times = frequency_times
            await self._update_in_db(habit)
            return habit
        except Exception as e:
            print(f"[HabitsService] Error actualizando hábito: {e}")
            raise
    
    async def delete_habit(self, habit_id: str) -> bool:
        """
        Elimina un hábito
        
        Args:
            habit_id: ID del hábito
        
        Returns:
            True si se eliminó, False si no existe
        """
        try:
            if habit_id not in self.habits:
                print(f"[HabitsService] Hábito no encontrado: {habit_id}")
                return False
            
            del self.habits[habit_id]
            await self._delete_from_db(habit_id)
            print(f"[HabitsService] Hábito eliminado: {habit_id}")
            return True
        except Exception as e:
            print(f"[HabitsService] Error eliminando hábito: {e}")
            raise
    
    def get_all_habits(self) -> List[Habit]:
        """
        Obtiene todos los hábitos
        
        Returns:
            Lista de hábitos
        """
        return list(self.habits.values())
    
    def get_habit(self, habit_id: str) -> Optional[Habit]:
        """
        Obtiene un hábito por ID
        
        Args:
            habit_id: ID del hábito
        
        Returns:
            Hábito o None si no existe
        """
        return self.habits.get(habit_id)
    
    # Métodos privados de persistencia
    async def _save_to_db(self, habit: Habit):
        """Guarda un hábito en la BD"""
        try:
            await self.database_service.execute(
                """
                INSERT INTO habits (id, title, description, frequency, frequency_times, streak, last_completed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    habit.id,
                    habit.title,
                    habit.description,
                    habit.frequency,
                    habit.frequency_times,
                    habit.streak,
                    habit.last_completed,
                    habit.created_at,
                ),
            )
            await self.database_service.commit()
        except Exception as e:
            print(f"[HabitsService] Error guardando hábito: {e}")
            raise
    
    async def _update_in_db(self, habit: Habit):
        """Actualiza un hábito en la BD"""
        try:
            await self.database_service.execute(
                """
                UPDATE habits
                SET title = ?, description = ?, frequency = ?, frequency_times = ?, streak = ?, last_completed = ?
                WHERE id = ?
                """,
                (
                    habit.title,
                    habit.description,
                    habit.frequency,
                    habit.frequency_times,
                    habit.streak,
                    habit.last_completed,
                    habit.id,
                ),
            )
            await self.database_service.commit()
        except Exception as e:
            print(f"[HabitsService] Error actualizando hábito: {e}")
            raise
    
    async def _delete_from_db(self, habit_id: str):
        """Elimina un hábito de la BD"""
        try:
            await self.database_service.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
            await self.database_service.commit()
        except Exception as e:
            print(f"[HabitsService] Error eliminando hábito: {e}")
            raise
