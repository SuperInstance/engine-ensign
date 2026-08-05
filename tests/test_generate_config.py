#!/usr/bin/env python3
"""
Tests for engine-ensign config generator.

The config generator creates firmware files for ESP32 engine monitors.
Tests cover the pure functions: name sanitization, engine classification,
threshold lookup, and generated file content.
"""

import sys
import os
from pathlib import Path

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


# ─── sanitize_name ───────────────────────────────────────────────────────────

class TestSanitizeName:
    def test_simple_name(self):
        assert sanitize_name("perkins_6354") == "perkins_6354"

    def test_spaces_to_underscores(self):
        assert sanitize_name("Cummins 6BTA") == "cummins_6bta"

    def test_special_chars_stripped(self):
        assert sanitize_name("Yanmar 4LH-STE!") == "yanmar_4lh-ste"

    def test_uppercase_lowered(self):
        assert sanitize_name("MERCURY 150") == "mercury_150"

    def test_empty_string(self):
        assert sanitize_name("") == ""

    def test_only_special_chars(self):
        assert sanitize_name("@#$%") == ""

    def test_mixed(self):
        assert sanitize_name("Volvo D4-300") == "volvo_d4-300"


# ─── guess_engine_class ──────────────────────────────────────────────────────

class TestGuessEngineClass:
    @pytest.mark.parametrize("name,expected", [
        ("Cummins 6BTA", "diesel_heavy"),
        ("Caterpillar C12", "diesel_heavy"),
        ("Detroit DD15", "diesel_heavy"),
        ("cat 3406", "diesel_heavy"),
        ("Yanmar 4LH-STE", "diesel_inboard"),
        ("Perkins 6354", "diesel_inboard"),
        ("Volvo D4", "diesel_inboard"),
        ("Isuzu 6BD1", "diesel_inboard"),
        ("Beta Marine 50", "diesel_inboard"),
        ("Mercury 150", "outboard"),
        ("Yamaha F200", "outboard"),
        ("Suzuki DF300", "outboard"),
        ("Evinrude E-TEC 200", "outboard"),
        ("Honda BF250", "outboard"),
        ("mercury 200 outboard", "outboard"),
    ])
    def test_known_engines(self, name, expected):
        assert guess_engine_class(name) == expected

    def test_unknown_engine_defaults_generic(self):
        assert guess_engine_class("Random Engine XYZ") == "generic"
        assert guess_engine_class("Acme Motor") == "generic"

    def test_case_insensitive(self):
        assert guess_engine_class("CUMMINS 6BTA") == "diesel_heavy"
        assert guess_engine_class("cummins 6bta") == "diesel_heavy"
        assert guess_engine_class("YANMAR") == "diesel_inboard"


# ─── Thresholds ──────────────────────────────────────────────────────────────

class TestThresholds:
    def test_all_classes_have_required_keys(self):
        required = {"temp_yellow", "temp_red", "oil_yellow", "oil_red",
                    "rpm_yellow", "rpm_red", "volts_low", "volts_crit", "volts_high"}
        for cls, thresholds in DEFAULT_THRESHOLDS.items():
            missing = required - set(thresholds.keys())
            assert not missing, f"{cls} missing thresholds: {missing}"

    def test_yellow_less_than_red_temps(self):
        for cls, t in DEFAULT_THRESHOLDS.items():
            assert t["temp_yellow"] < t["temp_red"], f"{cls}: yellow temp >= red temp"

    def test_yellow_greater_than_red_oil(self):
        for cls, t in DEFAULT_THRESHOLDS.items():
            assert t["oil_yellow"] > t["oil_red"], f"{cls}: yellow oil <= red oil"

    def test_yellow_less_than_red_rpm(self):
        for cls, t in DEFAULT_THRESHOLDS.items():
            assert t["rpm_yellow"] < t["rpm_red"], f"{cls}: yellow rpm >= red rpm"

    def test_volts_low_greater_than_crit(self):
        for cls, t in DEFAULT_THRESHOLDS.items():
            assert t["volts_low"] > t["volts_crit"], f"{cls}: volts_low <= volts_crit"

    def test_outboard_revs_higher(self):
        """Outboards should rev higher than inboards."""
        outboard = DEFAULT_THRESHOLDS["outboard"]
        diesel = DEFAULT_THRESHOLDS["diesel_inboard"]
        assert outboard["rpm_red"] > diesel["rpm_red"]

    def test_diesel_heavy_runs_hotter(self):
        """Heavy diesels typically run hotter coolant."""
        heavy = DEFAULT_THRESHOLDS["diesel_heavy"]
        light = DEFAULT_THRESHOLDS["diesel_inboard"]
        assert heavy["temp_yellow"] >= light["temp_yellow"]


# ─── Display specs ───────────────────────────────────────────────────────────

class TestDisplays:
    def test_all_displays_have_required_fields(self):
        required = {"driver", "width", "height", "rotation", "lib", "spi_mhz"}
        for name, spec in DISPLAYS.items():
            missing = required - set(spec.keys())
            assert not missing, f"{name} missing: {missing}"

    def test_all_widths_positive(self):
        for name, spec in DISPLAYS.items():
            assert spec["width"] > 0, f"{name}: width <= 0"

    def test_all_heights_positive(self):
        for name, spec in DISPLAYS.items():
            assert spec["height"] > 0, f"{name}: height <= 0"

    def test_spi_mhz_reasonable(self):
        for name, spec in DISPLAYS.items():
            assert 1 <= spec["spi_mhz"] <= 80, f"{name}: spi_mhz {spec['spi_mhz']} out of range"


# ─── Sensor types ────────────────────────────────────────────────────────────

class TestSensorTypes:
    def test_all_sensors_have_includes(self):
        for spec_name, spec in SENSOR_TYPES.items():
            assert "includes" in spec, f"{spec_name} missing 'includes' key"
            assert isinstance(spec["includes"], list)

    def test_rpm_specs_exist(self):
        rpm_specs = [k for k in SENSOR_TYPES if k.startswith("rpm:")]
        assert len(rpm_specs) >= 2  # at least inductive and nmea2000

    def test_temp_specs_exist(self):
        temp_specs = [k for k in SENSOR_TYPES if k.startswith("temp:")]
        assert len(temp_specs) >= 1


# ─── Generated file content ──────────────────────────────────────────────────

class TestGeneratedConfig:
    @pytest.fixture
    def basic_setup(self):
        engine_name = "Test Engine 300"
        sensors = ["rpm:inductive", "temp:thermistor", "oil:analog_0-5v", "volt:analog"]
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        thresholds = DEFAULT_THRESHOLDS["generic"]
        return engine_name, sensors, display, thresholds

    def test_config_h_has_include_guard(self, basic_setup):
        name, sensors, display, thresholds = basic_setup
        content = generate_config_h(name, sensors, display, thresholds, "esp32")
        assert "#ifndef CONFIG_H" in content
        assert "#define CONFIG_H" in content
        assert "#endif" in content

    def test_config_h_has_thresholds(self, basic_setup):
        name, sensors, display, thresholds = basic_setup
        content = generate_config_h(name, sensors, display, thresholds, "esp32")
        assert "TEMP_NORMAL_MAX" in content
        assert "TEMP_REDLINE" in content
        assert "OIL_PRESSURE_MIN" in content
        assert "RPM_REDLINE" in content

    def test_config_h_has_display_config(self, basic_setup):
        name, sensors, display, thresholds = basic_setup
        content = generate_config_h(name, sensors, display, thresholds, "esp32")
        assert "TFT_WIDTH" in content
        assert "TFT_HEIGHT" in content
        assert str(display["width"]) in content
        assert str(display["height"]) in content

    def test_config_h_has_buzzer(self, basic_setup):
        name, sensors, display, thresholds = basic_setup
        content = generate_config_h(name, sensors, display, thresholds, "esp32")
        assert "BUZZER_PIN" in content
        assert "BUZZER_CHAN" in content


class TestGeneratedSensors:
    def test_sensors_h_has_include_guard(self):
        content = generate_sensors_h("Test", ["rpm:inductive", "temp:thermistor"])
        assert "#ifndef SENSORS_H" in content
        assert "#define SENSORS_H" in content

    def test_sensors_h_has_engine_data_struct(self):
        content = generate_sensors_h("Test", ["rpm:inductive"])
        assert "EngineData" in content
        assert "rpm" in content
        assert "coolant_temp_c" in content

    def test_sensors_h_nmea_includes_init(self):
        content = generate_sensors_h("Test", ["rpm:nmea2000"])
        assert "init_nmea2000" in content

    def test_sensors_h_inductive_includes_init(self):
        content = generate_sensors_h("Test", ["rpm:inductive"])
        assert "init_tachometer" in content
        assert "read_rpm" in content


class TestGeneratedDisplay:
    def test_display_h_has_include_guard(self):
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        content = generate_display_h(display)
        assert "#ifndef DISPLAY_H" in content

    def test_display_h_has_alert_severity(self):
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        content = generate_display_h(display)
        assert "AlertSeverity" in content
        assert "ALERT_NONE" in content
        assert "ALERT_CRITICAL" in content

    def test_display_h_correct_lib(self):
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        content = generate_display_h(display)
        assert "TFT_eSPI" in content  # TFT_eSPI display

    def test_display_h_ssd1351(self):
        display = DISPLAYS["3.5inch_oled_ssd1351"]
        content = generate_display_h(display)
        assert "Adafruit_SSD1351" in content


class TestGeneratedMain:
    def test_main_c_has_setup_and_loop(self):
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        content = generate_main_c("Test", ["rpm:inductive"], display)
        assert "void setup()" in content
        assert "void loop()" in content

    def test_main_c_has_alert_checking(self):
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        content = generate_main_c("Test", ["rpm:inductive", "temp:thermistor"], display)
        assert "check_alerts" in content
        assert "ALERT_CRITICAL" in content or "ALERT_WARNING" in content

    def test_main_c_has_serial_commands(self):
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        content = generate_main_c("Test", ["rpm:inductive"], display)
        assert "STATUS" in content
        assert "ALERTS" in content
        assert "QUIET" in content

    def test_main_c_nmea_init(self):
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        content = generate_main_c("Test", ["rpm:nmea2000"], display)
        assert "init_nmea2000" in content


class TestGeneratedPlatformIO:
    def test_platformio_has_env(self):
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        content = generate_platformio_ini("Test Engine", ["rpm:inductive"], display, "esp32")
        assert "[env:" in content

    def test_platformio_esp32_board(self):
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        content = generate_platformio_ini("Test Engine", ["rpm:inductive"], display, "esp32")
        assert "esp32dev" in content

    def test_platformio_esp32s3_board(self):
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        content = generate_platformio_ini("Test Engine", ["rpm:inductive"], display, "esp32s3")
        assert "esp32-s3-devkitc-1" in content

    def test_platformio_has_lib_deps(self):
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        content = generate_platformio_ini("Test Engine", ["rpm:inductive"], display, "esp32")
        assert "lib_deps" in content


class TestGeneratedReadme:
    def test_readme_has_engine_name(self):
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        thresholds = DEFAULT_THRESHOLDS["generic"]
        content = generate_readme("Test Engine 300", ["rpm:inductive"], display, thresholds)
        assert "Test Engine 300" in content

    def test_readme_has_wiring_table(self):
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        thresholds = DEFAULT_THRESHOLDS["generic"]
        content = generate_readme("Test", ["rpm:inductive"], display, thresholds)
        assert "ESP32 Pin" in content or "GPIO" in content

    def test_readme_has_thresholds(self):
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        thresholds = DEFAULT_THRESHOLDS["generic"]
        content = generate_readme("Test", ["rpm:inductive"], display, thresholds)
        assert "Thresholds" in content
        assert str(thresholds["temp_yellow"]) in content


class TestGeneratedDashboard:
    def test_dashboard_valid_json(self):
        import json
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        thresholds = DEFAULT_THRESHOLDS["generic"]
        content = generate_dashboard_json("Test Engine", display, thresholds)
        data = json.loads(content)
        assert isinstance(data, dict)

    def test_dashboard_has_gauges(self):
        import json
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        thresholds = DEFAULT_THRESHOLDS["generic"]
        data = json.loads(generate_dashboard_json("Test", display, thresholds))
        assert "gauges" in data
        assert len(data["gauges"]) >= 1

    def test_dashboard_has_themes(self):
        import json
        display = DISPLAYS["2.4inch_lcd_ili9341"]
        thresholds = DEFAULT_THRESHOLDS["generic"]
        data = json.loads(generate_dashboard_json("Test", display, thresholds))
        assert "themes" in data
        assert "day" in data["themes"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
