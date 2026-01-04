import pytest
from unittest.mock import MagicMock

import flet as ft
from app.ui.resume.resume_view import ResumeView
from app.ui.resume.points_and_levels.points_and_levels_view import PointsAndLevelsView


def test_build_creates_points_view_and_progress_service():
    resume = ResumeView()

    result = resume.build()

    assert isinstance(result, PointsAndLevelsView)
    assert resume.rewards_view is result
    # Debe compartir el mismo progress_service
    assert result.progress_service is resume.progress_service


def test_set_verify_integrity_callback_propagates_to_view():
    resume = ResumeView()
    resume.build()
    callback = MagicMock()

    resume.set_verify_integrity_callback(callback)

    assert resume.verify_integrity_callback is callback
    assert resume.rewards_view.on_verify_integrity is callback
