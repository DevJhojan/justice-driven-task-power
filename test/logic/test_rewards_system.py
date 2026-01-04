"""
Tests para el Sistema de Puntos, Niveles y Recompensas
"""

import pytest
from app.logic.system_points import (
    Level, PointsSystem, LEVEL_POINTS, LEVELS_ORDER, POINTS_BY_ACTION
)
from app.logic.system_levels import UserLevel, LevelManager
from app.models.reward import Reward
from app.models.user import User
from app.services.user_service import UserService
from app.services.rewards_service import RewardsService


class TestPointsSystem:
    """Tests del sistema de puntos"""
    
    def test_get_level_by_points(self):
        """Verifica que se obtiene el nivel correcto por puntos"""
        assert PointsSystem.get_level_by_points(0) == Level.NADIE
        assert PointsSystem.get_level_by_points(50) == Level.DESCONOCIDO
        assert PointsSystem.get_level_by_points(100) == Level.NOVATO
        assert PointsSystem.get_level_by_points(500) == Level.CONOCIDO
        assert PointsSystem.get_level_by_points(1000) == Level.RESPETADO
    
    def test_get_points_for_level(self):
        """Verifica que se obtienen los puntos correctos por nivel"""
        assert PointsSystem.get_points_for_level(Level.NADIE) == 0.0
        assert PointsSystem.get_points_for_level(Level.DESCONOCIDO) == 50.0
        assert PointsSystem.get_points_for_level(Level.NOVATO) == 100.0
    
    def test_get_next_level(self):
        """Verifica que se obtiene el siguiente nivel"""
        assert PointsSystem.get_next_level(Level.NADIE) == Level.DESCONOCIDO
        assert PointsSystem.get_next_level(Level.NOVATO) == Level.CONOCIDO
        assert PointsSystem.get_next_level(Level.COMO_DIOS) is None
    
    def test_get_points_to_next_level(self):
        """Verifica el cálculo de puntos faltantes"""
        # Con 0 puntos, faltan 50 para Desconocido
        assert PointsSystem.get_points_to_next_level(0) == 50.0
        # Con 50 puntos, faltan 50 para Novato
        assert PointsSystem.get_points_to_next_level(50) == 50.0
        # Al máximo nivel, no faltan puntos
        assert PointsSystem.get_points_to_next_level(500000) == 0.0
    
    def test_get_progress_to_next_level(self):
        """Verifica el progreso hacia el siguiente nivel"""
        points_in_level, total_for_next = PointsSystem.get_progress_to_next_level(25)
        assert points_in_level == 25.0
        assert total_for_next == 50.0
    
    def test_add_points(self):
        """Verifica la suma de puntos por acción"""
        current = PointsSystem.add_points(0, "task_completed")
        assert current == 10.0
        
        current = PointsSystem.add_points(10, "habit_completed")
        assert current == 25.0


class TestUserLevel:
    """Tests del modelo UserLevel"""
    
    def test_create_user_level(self):
        """Verifica la creación de un nivel de usuario"""
        user_level = UserLevel(user_id="user1")
        assert user_level.user_id == "user1"
        assert user_level.current_points == 0.0
        assert user_level.current_level == Level.NADIE
    
    def test_add_points_and_level_up(self):
        """Verifica que se añaden puntos y sube de nivel"""
        user_level = UserLevel(user_id="user1")
        
        # Añadir puntos sin cambio de nivel
        level_up = user_level.add_points("task_completed")
        assert user_level.current_points == 10.0
        assert level_up is False
        assert user_level.current_level == Level.NADIE
        
        # Añadir puntos hasta cambiar de nivel (necesita 50)
        for _ in range(3):  # 10 + 30 = 40 puntos
            user_level.add_points("task_completed")
        
        # En este punto tiene 40 puntos, aún no cambió de nivel
        assert user_level.current_points == 40.0
        assert user_level.current_level == Level.NADIE
        
        # Añadir uno más para que suba de nivel (40 + 10 = 50 >= 50)
        level_up = user_level.add_points("task_completed")
        assert user_level.current_points == 50.0
        assert user_level.current_level == Level.DESCONOCIDO
        assert level_up is True
    
    def test_progress_percent(self):
        """Verifica el cálculo de progreso en porcentaje"""
        user_level = UserLevel(user_id="user1", current_points=25)
        # 25 de 50 = 50%
        assert user_level.get_progress_percent() == 50.0


class TestLevelManager:
    """Tests del gestor de niveles"""
    
    def test_get_or_create_user_level(self):
        """Verifica la creación o recuperación de nivel de usuario"""
        manager = LevelManager()
        
        level1 = manager.get_or_create_user_level("user1")
        assert level1.user_id == "user1"
        
        level1_again = manager.get_or_create_user_level("user1")
        assert level1 is level1_again
    
    def test_get_user_level_info(self):
        """Verifica la obtención de información de nivel"""
        manager = LevelManager()
        manager.add_points("user1", "task_completed")
        
        info = manager.get_user_level_info("user1")
        assert info["user_id"] == "user1"
        assert info["current_points"] == 10.0
        assert "progress_percent" in info


class TestReward:
    """Tests del modelo Reward"""
    
    def test_create_reward(self):
        """Verifica la creación de una recompensa"""
        reward = Reward(
            title="Test Reward",
            points_required=100,
            icon="🎁",
        )
        assert reward.title == "Test Reward"
        assert reward.points_required == 100.0
    
    def test_reward_validation(self):
        """Verifica la validación de recompensas"""
        with pytest.raises(ValueError):
            Reward(title="", points_required=100)
        
        with pytest.raises(ValueError):
            Reward(title="Test", points_required=-10)
    
    def test_reward_to_dict(self):
        """Verifica la conversión a diccionario"""
        reward = Reward(title="Test", points_required=100, icon="⭐")
        reward_dict = reward.to_dict()
        
        assert reward_dict["title"] == "Test"
        assert reward_dict["points_required"] == 100.0
        assert "created_at" in reward_dict


class TestUser:
    """Tests del modelo User"""
    
    def test_create_user(self):
        """Verifica la creación de usuario"""
        user = User(username="jhojan", email="jhojan@example.com")
        assert user.username == "jhojan"
        assert user.points == 0.0
        assert user.level == "Nadie"
    
    def test_add_points(self):
        """Verifica la suma de puntos"""
        user = User(username="jhojan")
        user.add_points(50)
        
        assert user.points == 50.0
    
    def test_set_level(self):
        """Verifica el establecimiento de nivel"""
        user = User(username="jhojan")
        user.set_level("Novato")
        
        assert user.level == "Novato"


class TestRewardsService:
    """Tests del servicio de recompensas"""
    
    def test_create_reward(self):
        """Verifica la creación de recompensa"""
        service = RewardsService()
        reward = service.create_reward({
            "title": "Test Reward",
            "points_required": 100,
        })
        
        assert reward.title == "Test Reward"
        assert service.get_reward(reward.id) == reward
    
    def test_get_all_rewards(self):
        """Verifica obtener todas las recompensas"""
        service = RewardsService()
        service.create_reward({"title": "Reward 1", "points_required": 100})
        service.create_reward({"title": "Reward 2", "points_required": 500})
        
        rewards = service.get_all_rewards()
        assert len(rewards) == 2
    
    def test_get_unlocked_rewards(self):
        """Verifica obtener recompensas desbloqueadas"""
        service = RewardsService()
        service.create_reward({
            "title": "Reward 1",
            "points_required": 100,
            "is_active": True,
        })
        service.create_reward({
            "title": "Reward 2",
            "points_required": 500,
            "is_active": True,
        })
        
        unlocked = service.get_unlocked_rewards(250)
        assert len(unlocked) == 1
        assert unlocked[0].title == "Reward 1"
    
    def test_update_reward(self):
        """Verifica la actualización de recompensa"""
        service = RewardsService()
        reward = service.create_reward({
            "title": "Test",
            "points_required": 100,
        })
        
        service.update_reward(reward.id, {
            "title": "Updated Test",
            "points_required": 200,
        })
        
        updated = service.get_reward(reward.id)
        assert updated.title == "Updated Test"
        assert updated.points_required == 200.0


class TestUserService:
    """Tests del servicio de usuario"""
    
    def test_create_user(self):
        """Verifica la creación de usuario"""
        service = UserService()
        user = service.create_user("jhojan", "jhojan@example.com")
        
        assert user.username == "jhojan"
        assert user.email == "jhojan@example.com"
        assert service.get_user(user.id) == user
    
    def test_add_points_to_user(self):
        """Verifica la suma de puntos a usuario"""
        service = UserService()
        user = service.create_user("jhojan")
        
        service.add_points_to_user(user.id, "task_completed")
        
        updated_user = service.get_user(user.id)
        assert updated_user.points == 10.0
    
    def test_level_up(self):
        """Verifica que el usuario sube de nivel"""
        service = UserService()
        user = service.create_user("jhojan")
        
        # Añadir 50 puntos
        for _ in range(5):
            service.add_points_to_user(user.id, "task_completed")
        
        updated_user = service.get_user(user.id)
        assert updated_user.level == "Desconocido"
        assert updated_user.points == 50.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
