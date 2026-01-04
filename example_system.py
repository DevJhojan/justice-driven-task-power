"""
Ejemplo de uso del Sistema de Puntos, Niveles y Recompensas
"""

from app.logic.system_points import PointsSystem, Level, LEVEL_POINTS
from app.logic.system_levels import LevelManager, UserLevel
from app.services.user_service import UserService
from app.services.rewards_service import RewardsService


def example_system():
    """Ejemplo completo del sistema"""
    
    # ============================================================================
    # 1. CREAR USUARIOS Y COMENZAR A GANAR PUNTOS
    # ============================================================================
    print("=" * 80)
    print("SISTEMA DE PUNTOS Y NIVELES")
    print("=" * 80)
    
    user_service = UserService()
    
    # Crear usuario
    user = user_service.create_user("jhojan", "jhojan@example.com")
    print(f"\n✅ Usuario creado: {user.username}")
    print(f"   - ID: {user.id}")
    print(f"   - Nivel: {user.level}")
    print(f"   - Puntos: {user.points}")
    
    # ============================================================================
    # 2. GANAR PUNTOS COMPLETANDO ACCIONES
    # ============================================================================
    print("\n" + "=" * 80)
    print("GANANDO PUNTOS")
    print("=" * 80)
    
    actions = [
        ("task_completed", "Tarea completada"),
        ("task_completed", "Tarea completada"),
        ("subtask_completed", "Subtarea completada"),
        ("task_completed", "Tarea completada"),
        ("habit_completed", "Hábito completado"),
        ("task_completed", "Tarea completada"),
    ]
    
    for action, description in actions:
        level_up = user_service.add_points_to_user(user.id, action)
        user = user_service.get_user(user.id)
        
        print(f"\n✓ {description}")
        print(f"  Nivel: {user.level} | Puntos: {user.points}")
        
        if level_up:
            print(f"  🎉 ¡SUBISTE DE NIVEL! Ahora eres: {user.level}")
    
    # ============================================================================
    # 3. VER ESTADÍSTICAS DEL USUARIO
    # ============================================================================
    print("\n" + "=" * 80)
    print("ESTADÍSTICAS DEL USUARIO")
    print("=" * 80)
    
    stats = user_service.get_user_stats(user.id)
    print(f"\nUsuario: {stats['username']}")
    print(f"Nivel: {stats['icon']} {stats['level']}")
    print(f"Puntos: {stats['points']}")
    print(f"Progreso: {stats['progress_percent']:.1f}%")
    print(f"Próximo nivel: {stats['next_level']} ({stats['total_for_next_level']:.0f} puntos faltantes)")
    
    # ============================================================================
    # 4. VER TABLA DE NIVELES Y PUNTOS
    # ============================================================================
    print("\n" + "=" * 80)
    print("TABLA DE NIVELES Y PUNTOS")
    print("=" * 80)
    
    print(f"\n{'Nivel':<20} {'Puntos':<15} {'Icono':<10}")
    print("-" * 45)
    
    from app.logic.system_points import LEVELS_ORDER, LEVEL_ICONS
    
    for level in LEVELS_ORDER:
        icon = LEVEL_ICONS[level]
        points = LEVEL_POINTS[level]
        print(f"{level.value:<20} {int(points):<15} {icon:<10}")
    
    # ============================================================================
    # 5. SISTEMA DE RECOMPENSAS
    # ============================================================================
    print("\n" + "=" * 80)
    print("SISTEMA DE RECOMPENSAS")
    print("=" * 80)
    
    rewards_service = RewardsService()
    
    # Ver recompensas desbloqueadas
    unlocked = rewards_service.get_unlocked_rewards(user.points)
    print(f"\nRecompensas desbloqueadas ({len(unlocked)}):")
    for reward in unlocked:
        print(f"  {reward.icon} {reward.title} - {int(reward.points_required)} pts")
    
    # Ver próximas recompensas
    next_rewards = rewards_service.get_next_rewards(user.points, limit=3)
    print(f"\nPróximas recompensas a desbloquear:")
    for reward in next_rewards:
        missing = reward.points_required - user.points
        print(f"  {reward.icon} {reward.title} - Faltan {int(missing)} puntos")
    
    # ============================================================================
    # 6. CREAR Y EDITAR RECOMPENSAS
    # ============================================================================
    print("\n" + "=" * 80)
    print("CREAR Y GESTIONAR RECOMPENSAS")
    print("=" * 80)
    
    # Crear nueva recompensa
    new_reward = rewards_service.create_reward({
        "title": "Maestro de Tareas",
        "description": "Completa 50 tareas",
        "points_required": 500,
        "icon": "🏆",
        "color": "#FFD700",
        "category": "achievement",
    })
    print(f"\n✅ Nueva recompensa creada: {new_reward.icon} {new_reward.title}")
    
    # Editar recompensa
    rewards_service.update_reward(new_reward.id, {
        "description": "Completa 100 tareas (actualizado)",
        "points_required": 1000,
    })
    print(f"✏️ Recompensa actualizada")
    
    # ============================================================================
    # 7. RANKING DE USUARIOS
    # ============================================================================
    print("\n" + "=" * 80)
    print("RANKING DE USUARIOS")
    print("=" * 80)
    
    # Crear más usuarios para demostrar ranking
    users_data = [
        ("maria", "maria@example.com", 150),
        ("carlos", "carlos@example.com", 250),
        ("ana", "ana@example.com", 400),
    ]
    
    for username, email, points_to_add in users_data:
        new_user = user_service.create_user(username, email)
        for _ in range(int(points_to_add / 10)):  # Aproximadamente
            user_service.add_points_to_user(new_user.id, "task_completed")
    
    # Ver ranking
    ranking = user_service.get_ranking(limit=5)
    print(f"\n{'Posición':<12} {'Usuario':<15} {'Nivel':<20} {'Puntos':<10}")
    print("-" * 57)
    
    for rank_item in ranking:
        print(f"{rank_item['rank']:<12} {rank_item['user_id']:<15} {rank_item['icon']} {rank_item['level']:<17} {int(rank_item['points']):<10}")
    
    print("\n" + "=" * 80)
    print("FIN DEL EJEMPLO")
    print("=" * 80)


if __name__ == "__main__":
    example_system()
