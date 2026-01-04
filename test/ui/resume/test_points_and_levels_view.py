def mock_page():
import pytest

from app.ui.resume.points_and_levels.points_and_levels_view import PointsAndLevelsView


def test_set_user_points_updates_text():
    view = PointsAndLevelsView()
    view.set_user_points(12.345)

    assert view.points_text.value == "12.35"


def test_set_user_level_updates_icon_and_description():
    view = PointsAndLevelsView()
    view.set_user_level("Maestro")

    assert view.level_text.value == "Maestro"
    assert view.level_icon.value == view.level_icons.get("Maestro")
    assert view.level_description.value == view.level_descriptions.get("Maestro")


def test_update_progress_from_stats_updates_progressbar():
    view = PointsAndLevelsView()
    stats = {
        "progress_percent": 50.0,
        "next_level": "Aprendiz",
        "points_in_current_level": 10.0,
        "total_for_next_level": 20.0,
        "level": "Novato",
    }

    view.update_progress_from_stats(stats)

    assert view.progress_bar.value == pytest.approx(0.5)
    assert "50.0%" in view.progress_detail_text.value
    assert view.next_level_text.value.endswith("Aprendiz")


def test_on_verify_integrity_without_callback_shows_warning():
    view = PointsAndLevelsView(on_verify_integrity=None)
    view._on_verify_integrity_click(None)

    assert view.integrity_panel.visible is True
    # Debe mostrar advertencia por falta de callback
    messages = " ".join(getattr(ctrl, "value", "") for ctrl in view.integrity_log_text.controls)
    assert "callback" in messages.lower()


@pytest.mark.asyncio
async def test_run_verification_executes_callback():
    called = {"done": False}

    async def fake_verify():
        called["done"] = True
        return {}

    view = PointsAndLevelsView(on_verify_integrity=fake_verify)
    # Simular que el panel ya está visible
    view.integrity_panel.visible = True

    await view._run_verification_and_update_panel()

    assert called["done"] is True
