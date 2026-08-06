"""
Tests for dashboard_designer.py — the tool for modifying dashboard layouts.

Tests cover:
- find_gauge helper
- swap, theme, add, remove, move, resize, threshold operations
- validation (bounds, data sources, threshold logic)
- error handling for missing dashboards and gauges
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch
import sys

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from dashboard_designer import (
    load_dashboard, save_dashboard, find_gauge,
    cmd_list, cmd_swap, cmd_theme, cmd_add_gauge,
    cmd_remove_gauge, cmd_move, cmd_resize, cmd_set_threshold,
    cmd_set_backlight, cmd_validate,
    DASHBOARDS_DIR,
)


# ─── Fixtures ─────────────────────────────────────────────

@pytest.fixture
def sample_dashboard():
    """A minimal valid dashboard config."""
    return {
        "name": "Test Dashboard",
        "display": {"type": "SSD1351", "width": 480, "height": 320},
        "current_theme": "day",
        "themes": {"day": {"bg": "white"}, "night": {"bg": "black"}},
        "gauges": [
            {
                "id": "rpm",
                "type": "dial",
                "position": {"x": 120, "y": 100},
                "radius": 60,
                "data_source": "engine.rpm",
                "yellow_zone": {"start": 3000, "end": 3300},
                "red_zone": {"start": 3300},
            },
            {
                "id": "oil_pressure",
                "type": "dial",
                "position": {"x": 280, "y": 100},
                "radius": 50,
                "data_source": "engine.oil_pressure",
            },
        ],
        "readouts": [
            {"id": "temp", "position": {"x": 50, "y": 250}},
        ],
    }


@pytest.fixture
def mock_args():
    """Namespace-like object for command args."""
    class Args:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    return Args


# ─── find_gauge Tests ────────────────────────────────────

class TestFindGauge:
    def test_finds_existing_gauge(self, sample_dashboard):
        g = find_gauge(sample_dashboard, "rpm")
        assert g is not None
        assert g["id"] == "rpm"

    def test_returns_none_for_missing(self, sample_dashboard):
        assert find_gauge(sample_dashboard, "nonexistent") is None

    def test_handles_empty_gauges(self):
        data = {"gauges": []}
        assert find_gauge(data, "x") is None

    def test_handles_no_gauges_key(self):
        data = {}
        assert find_gauge(data, "x") is None


# ─── Swap Tests ──────────────────────────────────────────

class TestSwap:
    def test_swap_exchanges_positions(self, sample_dashboard, mock_args):
        original_rpm_pos = dict(sample_dashboard["gauges"][0]["position"])
        original_oil_pos = dict(sample_dashboard["gauges"][1]["position"])

        args = mock_args(dashboard="test", gauge1="rpm", gauge2="oil_pressure")
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with patch("dashboard_designer.save_dashboard"):
                cmd_swap(args)

        assert sample_dashboard["gauges"][0]["position"] == original_oil_pos
        assert sample_dashboard["gauges"][1]["position"] == original_rpm_pos

    def test_swap_missing_gauge_exits(self, sample_dashboard, mock_args):
        args = mock_args(dashboard="test", gauge1="nonexistent", gauge2="rpm")
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with pytest.raises(SystemExit):
                cmd_swap(args)


# ─── Theme Tests ─────────────────────────────────────────

class TestTheme:
    def test_theme_changes_current(self, sample_dashboard, mock_args):
        args = mock_args(dashboard="test", theme="night")
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with patch("dashboard_designer.save_dashboard"):
                cmd_theme(args)
        assert sample_dashboard["current_theme"] == "night"

    def test_invalid_theme_exits(self, sample_dashboard, mock_args):
        args = mock_args(dashboard="test", theme="invisible")
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with pytest.raises(SystemExit):
                cmd_theme(args)


# ─── Add/Remove Gauge Tests ──────────────────────────────

class TestAddRemoveGauge:
    def test_add_gauge_appends(self, sample_dashboard, mock_args):
        gauge_json = '{"id": "boost", "type": "bar", "position": {"x": 200, "y": 200}}'
        args = mock_args(dashboard="test", spec=gauge_json)
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with patch("dashboard_designer.save_dashboard"):
                cmd_add_gauge(args)
        assert len(sample_dashboard["gauges"]) == 3
        assert sample_dashboard["gauges"][-1]["id"] == "boost"

    def test_add_duplicate_gauge_exits(self, sample_dashboard, mock_args):
        gauge_json = '{"id": "rpm", "type": "bar"}'
        args = mock_args(dashboard="test", spec=gauge_json)
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with pytest.raises(SystemExit):
                cmd_add_gauge(args)

    def test_add_invalid_json_exits(self, sample_dashboard, mock_args):
        args = mock_args(dashboard="test", spec="not json{")
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with pytest.raises(SystemExit):
                cmd_add_gauge(args)

    def test_add_generates_id_from_label(self, sample_dashboard, mock_args):
        gauge_json = '{"label": "Fuel Pressure"}'
        args = mock_args(dashboard="test", spec=gauge_json)
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with patch("dashboard_designer.save_dashboard"):
                cmd_add_gauge(args)
        assert sample_dashboard["gauges"][-1]["id"] == "fuel_pressure"

    def test_remove_gauge(self, sample_dashboard, mock_args):
        args = mock_args(dashboard="test", gauge_id="rpm")
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with patch("dashboard_designer.save_dashboard"):
                cmd_remove_gauge(args)
        assert len(sample_dashboard["gauges"]) == 1
        assert all(g["id"] != "rpm" for g in sample_dashboard["gauges"])

    def test_remove_nonexistent_warns(self, sample_dashboard, mock_args):
        args = mock_args(dashboard="test", gauge_id="ghost")
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            cmd_remove_gauge(args)  # Should warn, not exit
        assert len(sample_dashboard["gauges"]) == 2  # unchanged


# ─── Move & Resize Tests ─────────────────────────────────

class TestMoveResize:
    def test_move_updates_coordinates(self, sample_dashboard, mock_args):
        args = mock_args(dashboard="test", gauge_id="rpm", x=200, y=150)
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with patch("dashboard_designer.save_dashboard"):
                cmd_move(args)
        assert sample_dashboard["gauges"][0]["position"]["x"] == 200
        assert sample_dashboard["gauges"][0]["position"]["y"] == 150

    def test_move_partial_update(self, sample_dashboard, mock_args):
        """Move should only update provided coordinates."""
        original_y = sample_dashboard["gauges"][0]["position"]["y"]
        args = mock_args(dashboard="test", gauge_id="rpm", x=200, y=None)
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with patch("dashboard_designer.save_dashboard"):
                cmd_move(args)
        assert sample_dashboard["gauges"][0]["position"]["x"] == 200
        assert sample_dashboard["gauges"][0]["position"]["y"] == original_y

    def test_move_missing_gauge_exits(self, sample_dashboard, mock_args):
        args = mock_args(dashboard="test", gauge_id="ghost", x=0, y=0)
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with pytest.raises(SystemExit):
                cmd_move(args)

    def test_resize_with_radius(self, sample_dashboard, mock_args):
        args = mock_args(dashboard="test", gauge_id="rpm", width=100, height=None)
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with patch("dashboard_designer.save_dashboard"):
                cmd_resize(args)
        assert sample_dashboard["gauges"][0]["radius"] == 50  # 100 // 2

    def test_resize_with_size(self, sample_dashboard, mock_args):
        """Gauges with 'size' key use width/height directly."""
        sample_dashboard["gauges"][0]["size"] = {"width": 80, "height": 60}
        sample_dashboard["gauges"][0].pop("radius", None)
        args = mock_args(dashboard="test", gauge_id="rpm", width=120, height=90)
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with patch("dashboard_designer.save_dashboard"):
                cmd_resize(args)
        assert sample_dashboard["gauges"][0]["size"]["width"] == 120
        assert sample_dashboard["gauges"][0]["size"]["height"] == 90


# ─── Threshold Tests ─────────────────────────────────────

class TestThreshold:
    def test_set_yellow_threshold(self, sample_dashboard, mock_args):
        args = mock_args(dashboard="test", gauge_id="rpm", yellow=2800, red=None)
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with patch("dashboard_designer.save_dashboard"):
                cmd_set_threshold(args)
        assert sample_dashboard["gauges"][0]["yellow_zone"]["start"] == 2800

    def test_set_both_thresholds(self, sample_dashboard, mock_args):
        args = mock_args(dashboard="test", gauge_id="rpm", yellow=2800, red=3200)
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with patch("dashboard_designer.save_dashboard"):
                cmd_set_threshold(args)
        yz = sample_dashboard["gauges"][0]["yellow_zone"]
        rz = sample_dashboard["gauges"][0]["red_zone"]
        assert yz["start"] == 2800
        assert yz["end"] == 3200
        assert rz["start"] == 3200


# ─── Backlight Tests ─────────────────────────────────────

class TestBacklight:
    def test_set_backlight_values(self, sample_dashboard, mock_args):
        args = mock_args(
            dashboard="test", backlight=True,
            day=255, night=80, dim=10,
        )
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with patch("dashboard_designer.save_dashboard"):
                cmd_set_backlight(args)
        bl = sample_dashboard["backlight"]
        assert bl["day_brightness"] == 255
        assert bl["night_brightness"] == 80
        assert bl["dim_brightness"] == 10


# ─── Validation Tests ────────────────────────────────────

class TestValidation:
    def test_valid_dashboard_passes(self, sample_dashboard, mock_args):
        args = mock_args(dashboard="test", validate=True)
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            cmd_validate(args)  # Should not raise

    def test_overflow_detected(self, sample_dashboard, mock_args):
        """Gauge extending beyond display width should warn."""
        sample_dashboard["gauges"][0]["position"]["x"] = 500
        sample_dashboard["gauges"][0]["radius"] = 60
        args = mock_args(dashboard="test", validate=True)
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with pytest.raises(SystemExit):
                cmd_validate(args)

    def test_missing_data_source_flagged(self, sample_dashboard, mock_args):
        del sample_dashboard["gauges"][0]["data_source"]
        args = mock_args(dashboard="test", validate=True)
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with pytest.raises(SystemExit):
                cmd_validate(args)

    def test_yellow_red_threshold_logic(self, sample_dashboard, mock_args):
        """Yellow start >= red start should warn."""
        sample_dashboard["gauges"][0]["yellow_zone"]["start"] = 3500
        sample_dashboard["gauges"][0]["red_zone"]["start"] = 3300
        args = mock_args(dashboard="test", validate=True)
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with pytest.raises(SystemExit):
                cmd_validate(args)

    def test_readout_off_screen(self, sample_dashboard, mock_args):
        sample_dashboard["readouts"][0]["position"] = {"x": 999, "y": 999}
        args = mock_args(dashboard="test", validate=True)
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with pytest.raises(SystemExit):
                cmd_validate(args)


# ─── List Tests ──────────────────────────────────────────

class TestList:
    def test_list_with_files(self):
        dash_files = list(DASHBOARDS_DIR.glob("*.json"))
        if dash_files:
            cmd_list(None)

    def test_list_empty(self):
        with patch.object(Path, "glob", return_value=[]):
            cmd_list(None)


# ─── Edge Cases ──────────────────────────────────────────

class TestEdgeCases:
    def test_add_gauge_auto_id_no_label(self, sample_dashboard, mock_args):
        """Gauge without id or label gets 'gauge' as id."""
        gauge_json = '{"type": "bar", "position": {"x": 10, "y": 10}}'
        args = mock_args(dashboard="test", spec=gauge_json)
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with patch("dashboard_designer.save_dashboard"):
                cmd_add_gauge(args)
        assert sample_dashboard["gauges"][-1]["id"] == "gauge"

    def test_resize_without_radius_or_size(self, sample_dashboard, mock_args):
        """Gauge with neither radius nor size gets radius from width//2."""
        sample_dashboard["gauges"][0].pop("radius", None)
        sample_dashboard["gauges"][0].pop("size", None)
        args = mock_args(dashboard="test", gauge_id="rpm", width=100, height=50)
        with patch("dashboard_designer.load_dashboard", return_value=sample_dashboard):
            with patch("dashboard_designer.save_dashboard"):
                cmd_resize(args)
        assert sample_dashboard["gauges"][0]["radius"] == 50
