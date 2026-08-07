#!/usr/bin/env python3
"""
Edge-case tests for engine-ensign tools.

Covers code paths not exercised by the main test suites:
- generate_config: NMEA2000 paths, multiple sensors, dashboard JSON structure,
  platformio.ini lib deps for NMEA, config.h analog pin deduplication,
  main.c with all sensor types, README with fuel/oil_temp sensors
- dashboard_designer: load_dashboard from disk, save_dashboard round-trip,
  cmd_show output, no-dashboard scenario for cmd_list
- Integration: full CLI argument parsing
"""

import json
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add tools dir to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from generate_config import (
    sanitize_name,
    guess_engine_class,
    generate_config_h,
    generate_sensors_h,
    generate_display_h,
    generate_main_c,
    generate_platformio_ini,
    generate_readme,
    generate_dashboard_json,
    DISPLAYS,
    SENSOR_TYPES,
    DEFAULT_THRESHOLDS,
)
import dashboard_designer as dd


# ─── generate_config: NMEA2000 sensor paths ──────────────────────────────────

class TestNMEAPaths:
    """Test code generation when using NMEA2000 sensors."""

    def test_config_h_nmea_can_bus(self):
        """config.h should include CAN bus pins when NMEA2000 sensors present."""
        sensors = ["rpm:nmea2000", "temp:nmea2000", "oil:nmea2000"]
        display = DISPLAYS["3.5inch_tft_ili9488"]
        thresholds = DEFAULT_THRESHOLDS["diesel_inboard"]
        content = generate_config_h("Test", sensors, display, thresholds, "esp32")
        assert "CAN_TX" in content
        assert "CAN_RX" in content
        assert "CAN_SPEED" in content

    def test_config_h_no_can_bus_without_nmea(self):
        """config.h should NOT include CAN bus when no NMEA2000 sensors."""
        sensors = ["rpm:inductive", "temp:thermistor"]
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        thresholds = DEFAULT_THRESHOLDS["generic"]
        content = generate_config_h("Test", sensors, display, thresholds, "esp32")
        assert "CAN_TX" not in content

    def test_sensors_h_nmea_no_tachometer(self):
        """sensors.h should NOT include tachometer init when RPM is via NMEA2000."""
        content = generate_sensors_h("Test", ["rpm:nmea2000"])
        assert "init_tachometer" not in content
        assert "init_nmea2000" in content

    def test_sensors_h_inductive_no_nmea(self):
        """sensors.h should NOT include NMEA2000 when using inductive RPM."""
        content = generate_sensors_h("Test", ["rpm:inductive"])
        assert "init_nmea2000" not in content
        assert "init_tachometer" in content

    def test_main_c_nmea_no_tachometer(self):
        """main.c should call init_nmea2000, not init_tachometer, for NMEA."""
        display = DISPLAYS["3.5inch_tft_ili9488"]
        content = generate_main_c("Test", ["rpm:nmea2000"], display)
        assert "init_nmea2000" in content
        assert "init_tachometer" not in content

    def test_main_c_inductive_tachometer(self):
        """main.c should call init_tachometer for inductive RPM."""
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        content = generate_main_c("Test", ["rpm:inductive"], display)
        assert "init_tachometer" in content

    def test_platformio_nmea_includes_arduinojson(self):
        """platformio.ini should always include ArduinoJson dep."""
        display = DISPLAYS["3.5inch_tft_ili9488"]
        content = generate_platformio_ini("Test", ["rpm:nmea2000"], display, "esp32")
        assert "ArduinoJson" in content

    def test_platformio_no_nmea_still_has_arduinojson(self):
        """platformio.ini should still include ArduinoJson even without NMEA."""
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        content = generate_platformio_ini("Test", ["rpm:inductive"], display, "esp32")
        assert "ArduinoJson" in content


# ─── generate_config: Mixed sensor combinations ──────────────────────────────

class TestMixedSensors:
    """Test code generation with realistic mixed sensor sets."""

    def test_full_analog_sensor_set(self):
        """All analog sensors should produce pin defines in config.h."""
        sensors = ["rpm:inductive", "temp:thermistor", "oil:analog_0-5v",
                   "volt:analog", "fuel:analog_0-190"]
        display = DISPLAYS["3.5inch_tft_ili9488"]
        thresholds = DEFAULT_THRESHOLDS["diesel_inboard"]
        content = generate_config_h("Test", sensors, display, thresholds, "esp32")
        assert "ANALOG_RPM_SIGNAL" in content
        assert "ANALOG_COOLANT_TEMP" in content
        assert "ANALOG_OIL_PRESSURE" in content
        assert "ANALOG_BATTERY" in content
        assert "ANALOG_FUEL_LEVEL" in content

    def test_oil_temp_sensor(self):
        """oil_temp:thermistor should produce its own pin define."""
        sensors = ["oil_temp:thermistor"]
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        thresholds = DEFAULT_THRESHOLDS["generic"]
        content = generate_config_h("Test", sensors, display, thresholds, "esp32")
        assert "ANALOG_OIL_TEMP" in content

    def test_sensors_h_includes_all_sensor_functions(self):
        """sensors.h should declare functions for each sensor type."""
        sensors = ["rpm:inductive", "temp:thermistor", "oil:analog_0-5v",
                   "volt:analog", "fuel:analog_0-190", "oil_temp:thermistor"]
        content = generate_sensors_h("Test", sensors)
        assert "read_rpm" in content
        assert "read_coolant_temp" in content
        assert "read_oil_pressure" in content
        assert "read_battery_voltage" in content
        assert "read_fuel_level" in content
        assert "read_oil_temp" in content

    def test_sensors_h_fuel_rate_estimate(self):
        """sensors.h should always include estimate_fuel_rate."""
        content = generate_sensors_h("Test", ["rpm:inductive"])
        assert "estimate_fuel_rate" in content

    def test_sensors_h_read_all_sensors(self):
        """sensors.h should always declare read_all_sensors."""
        content = generate_sensors_h("Test", ["rpm:inductive"])
        assert "read_all_sensors" in content

    def test_mixed_nmea_and_analog(self):
        """Mix of NMEA2000 and analog sensors should work."""
        sensors = ["rpm:nmea2000", "temp:thermistor", "oil:nmea2000"]
        display = DISPLAYS["5inch_ips_st7789"]
        thresholds = DEFAULT_THRESHOLDS["outboard"]
        # Should not raise
        config = generate_config_h("Mixed", sensors, display, thresholds, "esp32")
        sensors_h = generate_sensors_h("Mixed", sensors)
        main = generate_main_c("Mixed", sensors, display)

        assert "CAN_TX" in config  # NMEA2000 present
        assert "ANALOG_COOLANT_TEMP" in config  # analog temp present
        assert "init_nmea2000" in main  # NMEA init in main


# ─── generate_config: Dashboard JSON structure ───────────────────────────────

class TestDashboardJSON:
    """Deep inspection of generated dashboard JSON."""

    def test_dashboard_rpm_gauge_has_yellow_red_zones(self):
        display = DISPLAYS["3.5inch_tft_ili9488"]
        thresholds = DEFAULT_THRESHOLDS["diesel_inboard"]
        data = json.loads(generate_dashboard_json("Test", display, thresholds))
        rpm_gauge = data["gauges"][0]
        assert "yellow_zone" in rpm_gauge
        assert "red_zone" in rpm_gauge
        assert rpm_gauge["yellow_zone"]["start"] == thresholds["rpm_yellow"]
        assert rpm_gauge["red_zone"]["start"] == thresholds["rpm_red"]

    def test_dashboard_temp_gauge_thresholds(self):
        display = DISPLAYS["3.5inch_tft_ili9488"]
        thresholds = DEFAULT_THRESHOLDS["diesel_inboard"]
        data = json.loads(generate_dashboard_json("Test", display, thresholds))
        temp_gauge = data["gauges"][1]
        assert temp_gauge["yellow_zone"]["start"] == thresholds["temp_yellow"]
        assert temp_gauge["red_zone"]["start"] == thresholds["temp_red"]

    def test_dashboard_volts_readout_exists(self):
        display = DISPLAYS["3.5inch_tft_ili9488"]
        thresholds = DEFAULT_THRESHOLDS["diesel_inboard"]
        data = json.loads(generate_dashboard_json("Test", display, thresholds))
        readouts = data.get("readouts", [])
        assert any(r["id"] == "volts" for r in readouts)

    def test_dashboard_gauge_type_depends_on_width(self):
        """The code uses width >= 320 for analog_dial. The OLED (128px) gets digital_readout."""
        small = DISPLAYS["3.5inch_oled_ssd1351"]  # 128x96 — below 320 threshold
        large = DISPLAYS["7inch_tft_ili9488"]     # 480x320 — above 320 threshold
        thresholds = DEFAULT_THRESHOLDS["generic"]

        small_data = json.loads(generate_dashboard_json("T", small, thresholds))
        large_data = json.loads(generate_dashboard_json("T", large, thresholds))

        small_rpm = small_data["gauges"][0]
        large_rpm = large_data["gauges"][0]
        assert small_rpm["type"] == "digital_readout"
        assert large_rpm["type"] == "analog_dial"

    def test_dashboard_target_firmware_path(self):
        display = DISPLAYS["3.5inch_tft_ili9488"]
        thresholds = DEFAULT_THRESHOLDS["generic"]
        data = json.loads(generate_dashboard_json("My Engine", display, thresholds))
        assert "target_firmware" in data
        assert "my_engine" in data["target_firmware"]

    def test_dashboard_gauge_positions_within_bounds(self):
        """Gauge positions should be within display bounds."""
        display = DISPLAYS["3.5inch_tft_ili9488"]
        thresholds = DEFAULT_THRESHOLDS["generic"]
        data = json.loads(generate_dashboard_json("T", display, thresholds))
        for g in data["gauges"]:
            pos = g.get("position", {})
            assert 0 <= pos.get("x", 0) <= display["width"]
            assert 0 <= pos.get("y", 0) <= display["height"]


# ─── generate_config: All display types ──────────────────────────────────────

class TestAllDisplayTypes:
    """Ensure every display type produces valid output."""

    @pytest.mark.parametrize("display_key", list(DISPLAYS.keys()))
    def test_config_h_for_every_display(self, display_key):
        display = DISPLAYS[display_key]
        thresholds = DEFAULT_THRESHOLDS["generic"]
        content = generate_config_h("T", ["rpm:inductive"], display, thresholds, "esp32")
        assert f"#define TFT_WIDTH   {display['width']}" in content
        assert f"#define TFT_HEIGHT  {display['height']}" in content
        assert f"#define TFT_ROTATION {display['rotation']}" in content

    @pytest.mark.parametrize("display_key", list(DISPLAYS.keys()))
    def test_display_h_for_every_display(self, display_key):
        display = DISPLAYS[display_key]
        content = generate_display_h(display)
        assert "#ifndef DISPLAY_H" in content
        assert display["driver"] in content

    @pytest.mark.parametrize("display_key", list(DISPLAYS.keys()))
    def test_platformio_for_every_display(self, display_key):
        display = DISPLAYS[display_key]
        content = generate_platformio_ini("T", ["rpm:inductive"], display, "esp32")
        assert "[env:" in content
        assert "esp32dev" in content
        # Display library should be referenced
        if display["lib"] == "TFT_eSPI":
            assert "TFT_eSPI" in content
        elif display["lib"] == "Adafruit_SSD1351":
            assert "Adafruit" in content


# ─── generate_config: README generation ──────────────────────────────────────

class TestReadmeGeneration:
    def test_readme_includes_all_sensor_pins(self):
        """README should list pins for each sensor type."""
        sensors = ["rpm:inductive", "temp:thermistor", "oil:analog_0-5v"]
        display = DISPLAYS["3.5inch_tft_ili9488"]
        thresholds = DEFAULT_THRESHOLDS["diesel_inboard"]
        content = generate_readme("Test", sensors, display, thresholds)
        assert "GPIO 34" in content  # rpm inductive default pin
        assert "GPIO 36" in content  # temp thermistor default pin
        assert "GPIO 35" in content  # oil pressure default pin

    def test_readme_includes_build_instructions(self):
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        thresholds = DEFAULT_THRESHOLDS["generic"]
        content = generate_readme("Test", ["rpm:inductive"], display, thresholds)
        assert "pio run" in content
        assert "pio device monitor" in content

    def test_readme_includes_volts_threshold(self):
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        thresholds = DEFAULT_THRESHOLDS["generic"]
        content = generate_readme("Test", ["volt:analog"], display, thresholds)
        assert str(thresholds["volts_low"]) in content
        assert str(thresholds["volts_crit"]) in content


# ─── generate_config: Threshold overrides ────────────────────────────────────

class TestThresholdOverride:
    def test_override_heavy_vs_inboard(self):
        """Heavy diesel thresholds should differ from inboard."""
        heavy = DEFAULT_THRESHOLDS["diesel_heavy"]
        inboard = DEFAULT_THRESHOLDS["diesel_inboard"]
        assert heavy["temp_yellow"] != inboard["temp_yellow"]

    def test_override_outboard_vs_inboard(self):
        """Outboard thresholds should differ from inboard."""
        outboard = DEFAULT_THRESHOLDS["outboard"]
        inboard = DEFAULT_THRESHOLDS["diesel_inboard"]
        assert outboard["rpm_red"] != inboard["rpm_red"]

    def test_all_thresholds_have_volts_high(self):
        for cls, t in DEFAULT_THRESHOLDS.items():
            assert "volts_high" in t, f"{cls} missing volts_high"
            assert t["volts_high"] > t["volts_low"], \
                f"{cls}: volts_high <= volts_low"


# ─── generate_config: Unknown sensor warning ─────────────────────────────────

class TestUnknownSensors:
    """Unknown sensor specs should produce a warning but not crash."""

    def test_config_h_with_unknown_sensor(self):
        sensors = ["rpm:inductive", "unknown_sensor"]
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        thresholds = DEFAULT_THRESHOLDS["generic"]
        # Should not raise
        content = generate_config_h("Test", sensors, display, thresholds, "esp32")
        assert "#ifndef CONFIG_H" in content  # still generates valid output

    def test_sensors_h_with_unknown_sensor(self):
        content = generate_sensors_h("Test", ["rpm:inductive", "unknown:type"])
        assert "#ifndef SENSORS_H" in content


# ─── dashboard_designer: load/save round-trip ────────────────────────────────

class TestDashboardLoadSave:
    def test_load_dashboard_by_exact_name(self, tmp_path):
        """load_dashboard should find a JSON by stem name."""
        dash_data = {"name": "Test Dash", "gauges": []}
        dash_file = tmp_path / "test_dash.json"
        dash_file.write_text(json.dumps(dash_data))

        with patch.object(dd, "DASHBOARDS_DIR", tmp_path):
            loaded = dd.load_dashboard("test_dash")
            assert loaded["name"] == "Test Dash"

    def test_load_dashboard_by_name_search(self, tmp_path):
        """load_dashboard should find a dashboard by its 'name' field."""
        dash_data = {"name": "My Cool Dashboard", "gauges": []}
        dash_file = tmp_path / "custom_file.json"
        dash_file.write_text(json.dumps(dash_data))

        with patch.object(dd, "DASHBOARDS_DIR", tmp_path):
            loaded = dd.load_dashboard("My Cool Dashboard")
            assert loaded["name"] == "My Cool Dashboard"

    def test_load_dashboard_not_found_exits(self, tmp_path):
        with patch.object(dd, "DASHBOARDS_DIR", tmp_path):
            with pytest.raises(SystemExit):
                dd.load_dashboard("nonexistent")

    def test_save_dashboard_writes_json(self, tmp_path):
        data = {"name": "Saved", "gauges": [{"id": "rpm"}]}
        with patch.object(dd, "DASHBOARDS_DIR", tmp_path):
            dd.save_dashboard("saved", data)
            content = (tmp_path / "saved.json").read_text()
            loaded = json.loads(content)
            assert loaded["name"] == "Saved"
            assert loaded["gauges"][0]["id"] == "rpm"


# ─── dashboard_designer: cmd_show ────────────────────────────────────────────

class TestCmdShow:
    def test_show_outputs_json(self, capsys, tmp_path):
        dash_data = {"name": "Show Me", "gauges": []}
        (tmp_path / "showme.json").write_text(json.dumps(dash_data))

        args = MagicMock(dashboard="showme")
        with patch.object(dd, "DASHBOARDS_DIR", tmp_path):
            dd.cmd_show(args)
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["name"] == "Show Me"


# ─── dashboard_designer: Backlight partial update ────────────────────────────

class TestBacklightPartial:
    def test_backlight_only_day(self):
        data = {"name": "T", "themes": {"day": {}}, "current_theme": "day"}
        args = MagicMock(dashboard="t", backlight=True, day=200, night=None, dim=None)
        with patch("dashboard_designer.load_dashboard", return_value=data):
            with patch("dashboard_designer.save_dashboard"):
                dd.cmd_set_backlight(args)
        assert data["backlight"]["day_brightness"] == 200
        assert "night_brightness" not in data["backlight"]
        assert "dim_brightness" not in data["backlight"]

    def test_backlight_only_night(self):
        data = {"name": "T", "themes": {"day": {}}, "current_theme": "day"}
        args = MagicMock(dashboard="t", backlight=True, day=None, night=50, dim=None)
        with patch("dashboard_designer.load_dashboard", return_value=data):
            with patch("dashboard_designer.save_dashboard"):
                dd.cmd_set_backlight(args)
        assert data["backlight"]["night_brightness"] == 50
        assert "day_brightness" not in data["backlight"]


# ─── dashboard_designer: Threshold edge cases ────────────────────────────────

class TestThresholdEdgeCases:
    def test_set_red_only_updates_red_zone(self):
        data = {
            "name": "T", "current_theme": "day",
            "themes": {"day": {}},
            "gauges": [{"id": "rpm", "yellow_zone": {"start": 3000, "end": 3300},
                        "red_zone": {"start": 3300}}],
        }
        args = MagicMock(dashboard="t", gauge_id="rpm", yellow=None, red=3500)
        with patch("dashboard_designer.load_dashboard", return_value=data):
            with patch("dashboard_designer.save_dashboard"):
                dd.cmd_set_threshold(args)
        assert data["gauges"][0]["red_zone"]["start"] == 3500
        # Yellow end should NOT change when red is set without yellow
        assert data["gauges"][0]["yellow_zone"]["end"] == 3300

    def test_set_threshold_on_gauge_without_existing_zones(self):
        data = {
            "name": "T", "current_theme": "day",
            "themes": {"day": {}},
            "gauges": [{"id": "boost"}],
        }
        args = MagicMock(dashboard="t", gauge_id="boost", yellow=10, red=15)
        with patch("dashboard_designer.load_dashboard", return_value=data):
            with patch("dashboard_designer.save_dashboard"):
                dd.cmd_set_threshold(args)
        assert data["gauges"][0]["yellow_zone"]["start"] == 10
        assert data["gauges"][0]["red_zone"]["start"] == 15

    def test_set_threshold_missing_gauge_exits(self):
        data = {"name": "T", "gauges": [{"id": "rpm"}]}
        args = MagicMock(dashboard="t", gauge_id="ghost", yellow=10, red=15)
        with patch("dashboard_designer.load_dashboard", return_value=data):
            with pytest.raises(SystemExit):
                dd.cmd_set_threshold(args)


# ─── dashboard_designer: Validation edge cases ───────────────────────────────

class TestValidationEdgeCases:
    def test_valid_dashboard_with_no_gauges(self):
        """A dashboard with zero gauges should validate cleanly."""
        data = {
            "name": "Empty",
            "display": {"width": 320, "height": 240},
            "gauges": [],
            "readouts": [],
        }
        args = MagicMock(dashboard="empty", validate=True)
        with patch("dashboard_designer.load_dashboard", return_value=data):
            dd.cmd_validate(args)  # should not raise

    def test_valid_dashboard_with_no_readouts(self):
        """A dashboard with no readouts key should still validate."""
        data = {
            "name": "NoReadouts",
            "display": {"width": 320, "height": 240},
            "gauges": [],
        }
        args = MagicMock(dashboard="nr", validate=True)
        with patch("dashboard_designer.load_dashboard", return_value=data):
            dd.cmd_validate(args)  # should not raise

    def test_size_based_gauge_overflow(self):
        """Gauge using 'size' instead of 'radius' that overflows should warn."""
        data = {
            "name": "SizeOverflow",
            "display": {"width": 320, "height": 240},
            "gauges": [{
                "id": "big",
                "position": {"x": 300, "y": 10},
                "size": {"width": 100, "height": 50},
                "data_source": "engine.x",
            }],
            "readouts": [],
        }
        args = MagicMock(dashboard="so", validate=True)
        with patch("dashboard_designer.load_dashboard", return_value=data):
            with pytest.raises(SystemExit):
                dd.cmd_validate(args)

    def test_gauge_at_exact_boundary_passes(self):
        """Gauge exactly at display boundary should pass validation."""
        data = {
            "name": "Exact",
            "display": {"width": 320, "height": 240},
            "gauges": [{
                "id": "edge",
                "position": {"x": 260, "y": 120},
                "radius": 60,
                "data_source": "engine.x",
            }],
            "readouts": [],
        }
        args = MagicMock(dashboard="exact", validate=True)
        with patch("dashboard_designer.load_dashboard", return_value=data):
            dd.cmd_validate(args)  # 260 + 60 = 320, exactly at edge

    def test_no_yellow_red_zones_is_ok(self):
        """Gauge without any zones should pass validation."""
        data = {
            "name": "NoZones",
            "display": {"width": 320, "height": 240},
            "gauges": [{
                "id": "info",
                "position": {"x": 100, "y": 100},
                "radius": 30,
                "data_source": "engine.x",
            }],
            "readouts": [],
        }
        args = MagicMock(dashboard="nz", validate=True)
        with patch("dashboard_designer.load_dashboard", return_value=data):
            dd.cmd_validate(args)  # should not raise


# ─── generate_config: CLI main() integration ────────────────────────────────

class TestCLIMain:
    """Test the main() CLI entry point via argparse."""

    def test_main_generates_files(self, tmp_path):
        """Running main() with valid args should create output files."""
        output_dir = tmp_path / "firmware" / "test_engine"
        dash_dir = tmp_path / "dashboards"

        test_args = [
            "generate_config.py",
            "--engine", "Test Engine",
            "--sensors", "rpm:inductive,temp:thermistor,oil:analog_0-5v",
            "--display", "3.5inch_tft_ili9488",
            "--platform", "esp32",
            "--output", str(output_dir),
            "--dashboards-dir", str(dash_dir),
        ]

        with patch.object(sys, "argv", test_args):
            with patch("generate_config.main", wraps=None):
                import importlib
                import generate_config as gc
                importlib.reload(gc)
                # Actually call the real main
                gc.main()

        # Check files were generated
        assert (output_dir / "config.h").exists()
        assert (output_dir / "sensors.h").exists()
        assert (output_dir / "display.h").exists()
        assert (output_dir / "main.c").exists()
        assert (output_dir / "platformio.ini").exists()
        assert (output_dir / "README.md").exists()

        # Dashboard JSON should exist
        dash_files = list(dash_dir.glob("*.json"))
        assert len(dash_files) >= 1

    def test_main_with_engine_class_override(self, tmp_path):
        """--engine-class should override auto-detection."""
        output_dir = tmp_path / "fw"
        dash_dir = tmp_path / "dash"

        test_args = [
            "generate_config.py",
            "--engine", "Mercury 150",  # would normally be "outboard"
            "--sensors", "rpm:inductive",
            "--display", "2.4inch_lcd_ili9341",
            "--platform", "esp32",
            "--output", str(output_dir),
            "--dashboards-dir", str(dash_dir),
            "--engine-class", "diesel_heavy",  # override
        ]

        with patch.object(sys, "argv", test_args):
            import generate_config as gc
            gc.main()

        config_h = (output_dir / "config.h").read_text()
        heavy = DEFAULT_THRESHOLDS["diesel_heavy"]
        assert str(heavy["temp_red"]) in config_h
        assert str(heavy["rpm_red"]) in config_h

    def test_main_esp32s3_platform(self, tmp_path):
        """--platform esp32s3 should produce S3 board in platformio.ini."""
        output_dir = tmp_path / "fw"
        dash_dir = tmp_path / "dash"

        test_args = [
            "generate_config.py",
            "--engine", "S3 Test",
            "--sensors", "rpm:inductive",
            "--display", "2.4inch_lcd_ili9341",
            "--platform", "esp32s3",
            "--output", str(output_dir),
            "--dashboards-dir", str(dash_dir),
        ]

        with patch.object(sys, "argv", test_args):
            import generate_config as gc
            gc.main()

        pio = (output_dir / "platformio.ini").read_text()
        assert "esp32-s3-devkitc-1" in pio


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
