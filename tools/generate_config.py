#!/usr/bin/env python3
"""
generate_config.py — Generate a new ESP32 firmware configuration.

Takes an engine specification (engine type, sensors, display) and generates
a complete firmware config directory with config.h, sensors.h, display.h,
main.c, platformio.ini, and README.md.

Usage:
    python tools/generate_config.py \
        --engine "perkins_6354" \
        --sensors "rpm:inductive,temp:thermistor,oil:analog_0-5v,volt:analog" \
        --display "3.5inch_tft_ili9488" \
        --platform "esp32" \
        --output firmware/perkins_6354/

The Engine Ensign uses this tool to generate configs for new vessels.
Each generated config is a starting point — thresholds need calibration
against the specific engine's behavior.
"""

import argparse
import json
import os
import sys
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Display specifications
# ---------------------------------------------------------------------------
DISPLAYS = {
    "2.4inch_lcd_ili9341": {
        "driver": "ILI9341",
        "width": 320, "height": 240,
        "rotation": 1,
        "lib": "TFT_eSPI",
        "define": "ILI9341_2_DRIVER",
        "spi_mhz": 40,
    },
    "3.5inch_tft_ili9488": {
        "driver": "ILI9488",
        "width": 480, "height": 320,
        "rotation": 1,
        "lib": "TFT_eSPI",
        "define": "ILI9488_DRIVER",
        "spi_mhz": 40,
    },
    "3.5inch_oled_ssd1351": {
        "driver": "SSD1351",
        "width": 128, "height": 96,
        "rotation": 0,
        "lib": "Adafruit_SSD1351",
        "define": None,
        "spi_mhz": 20,
    },
    "5inch_ips_st7789": {
        "driver": "ST7789",
        "width": 480, "height": 320,
        "rotation": 1,
        "lib": "TFT_eSPI",
        "define": "ST7789_DRIVER",
        "spi_mhz": 40,
    },
    "7inch_tft_ili9488": {
        "driver": "ILI9488",
        "width": 480, "height": 320,
        "rotation": 1,
        "lib": "TFT_eSPI",
        "define": "ILI9488_DRIVER",
        "spi_mhz": 40,
    },
}

# ---------------------------------------------------------------------------
# Sensor type specifications
# ---------------------------------------------------------------------------
SENSOR_TYPES = {
    "rpm:inductive": {
        "pin_var": "ANALOG_RPM_SIGNAL",
        "default_pin": 34,
        "includes": ["init_tachometer", "read_rpm"],
    },
    "rpm:nmea2000": {
        "pin_var": "CAN_TX",
        "default_pin": 5,
        "includes": ["init_nmea2000", "poll_nmea2000"],
    },
    "temp:thermistor": {
        "pin_var": "ANALOG_COOLANT_TEMP",
        "default_pin": 36,
        "includes": ["read_coolant_temp"],
    },
    "temp:nmea2000": {
        "pin_var": None,
        "default_pin": None,
        "includes": [],
    },
    "oil:analog_0-5v": {
        "pin_var": "ANALOG_OIL_PRESSURE",
        "default_pin": 35,
        "includes": ["read_oil_pressure"],
    },
    "oil:nmea2000": {
        "pin_var": None,
        "default_pin": None,
        "includes": [],
    },
    "volt:analog": {
        "pin_var": "ANALOG_BATTERY",
        "default_pin": 39,
        "includes": ["read_battery_voltage"],
    },
    "volt:nmea2000": {
        "pin_var": None,
        "default_pin": None,
        "includes": [],
    },
    "fuel:analog_0-190": {
        "pin_var": "ANALOG_FUEL_LEVEL",
        "default_pin": 32,
        "includes": ["read_fuel_level"],
    },
    "boost:nmea2000": {
        "pin_var": None,
        "default_pin": None,
        "includes": [],
    },
    "oil_temp:thermistor": {
        "pin_var": "ANALOG_OIL_TEMP",
        "default_pin": 39,
        "includes": ["read_oil_temp"],
    },
}

# ---------------------------------------------------------------------------
# Default thresholds by engine type heuristic
# ---------------------------------------------------------------------------
DEFAULT_THRESHOLDS = {
    "diesel_inboard": {
        "temp_yellow": 88, "temp_red": 95,
        "oil_yellow": 1.5, "oil_red": 0.8,
        "rpm_yellow": 2800, "rpm_red": 3300,
        "volts_low": 11.8, "volts_crit": 10.5, "volts_high": 14.8,
    },
    "diesel_heavy": {
        "temp_yellow": 96, "temp_red": 104,
        "oil_yellow": 2.0, "oil_red": 1.0,
        "rpm_yellow": 2600, "rpm_red": 2800,
        "volts_low": 11.8, "volts_crit": 10.5, "volts_high": 15.0,
    },
    "outboard": {
        "temp_yellow": 80, "temp_red": 90,
        "oil_yellow": 1.0, "oil_red": 0.3,
        "rpm_yellow": 5800, "rpm_red": 6000,
        "volts_low": 11.8, "volts_crit": 10.5, "volts_high": 15.5,
    },
    "generic": {
        "temp_yellow": 90, "temp_red": 100,
        "oil_yellow": 1.5, "oil_red": 0.7,
        "rpm_yellow": 2800, "rpm_red": 3000,
        "volts_low": 11.8, "volts_crit": 10.5, "volts_high": 15.0,
    },
}


def guess_engine_class(engine_name: str) -> str:
    """Guess engine class from engine name."""
    name = engine_name.lower()
    if any(k in name for k in ["cummins", "cat", "caterpillar", "detroit", "6bta", "c12", "c18"]):
        return "diesel_heavy"
    if any(k in name for k in ["outboard", "mercury", "yamaha", "suzuki", "evinrude", "honda"]):
        return "outboard"
    if any(k in name for k in ["yanmar", "perkins", "volvo", "isuzu", "beta"]):
        return "diesel_inboard"
    return "generic"


def sanitize_name(name: str) -> str:
    """Convert engine name to directory-safe name."""
    return re.sub(r'[^a-z0-9_-]', '', name.lower().replace(' ', '_'))


def generate_config_h(engine_name: str, sensors: list, display: dict,
                      thresholds: dict, platform: str) -> str:
    """Generate config.h content."""
    lines = [
        f"/*",
        f" * config.h — {engine_name} Engine Monitor",
        f" * Generated by tools/generate_config.py",
        f" *",
        f' * Engine: {engine_name}',
        f" * Display: {display['driver']} ({display['width']}x{display['height']})",
        f" * Platform: {platform}",
        f" */",
        f"",
        f"#ifndef CONFIG_H",
        f"#define CONFIG_H",
        f"",
        f"/* --- Display ({display['driver']}) --- */",
        f"#define TFT_CS      15",
        f"#define TFT_DC      2",
        f"#define TFT_RST     4",
        f"#define TFT_MOSI    23",
        f"#define TFT_CLK     18",
        f"#define TFT_BL      32",
        f"#define TFT_WIDTH   {display['width']}",
        f"#define TFT_HEIGHT  {display['height']}",
        f"#define TFT_ROTATION {display['rotation']}",
        f"",
    ]

    # Analog pin assignments
    analog_pins = []
    next_adc_pin = 34
    for spec in sensors:
        if spec in SENSOR_TYPES and SENSOR_TYPES[spec].get("default_pin"):
            s = SENSOR_TYPES[spec]
            analog_pins.append(f"#define {s['pin_var']}  {s['default_pin']}")

    if analog_pins:
        lines.append("/* --- Analog Inputs --- */")
        lines.extend(analog_pins)
        lines.append("")

    # NMEA2000 if needed
    if any(s.endswith("nmea2000") for s in sensors):
        lines.extend([
            "/* --- NMEA2000 CAN Bus --- */",
            "#define CAN_TX      5",
            "#define CAN_RX      35",
            "#define CAN_SPEED   250",
            "",
        ])

    # Thresholds
    lines.extend([
        "/* --- Alert Thresholds --- */",
        f"#define TEMP_NORMAL_MAX      {thresholds['temp_yellow']}",
        f"#define TEMP_REDLINE         {thresholds['temp_red']}",
        f"#define OIL_PRESSURE_MIN     {thresholds['oil_yellow']}",
        f"#define OIL_PRESSURE_CRIT    {thresholds['oil_red']}",
        f"#define RPM_REDLINE          {thresholds['rpm_red']}",
        f"#define RPM_YELLOW           {thresholds['rpm_yellow']}",
        f"#define VOLTS_LOW            {thresholds['volts_low']}",
        f"#define VOLTS_CRITICAL       {thresholds['volts_crit']}",
        f"#define VOLTS_HIGH           {thresholds['volts_high']}",
        "",
        "/* --- Update Rates --- */",
        "#define SENSOR_UPDATE_MS     500",
        "#define DISPLAY_UPDATE_MS    250",
        "#define ALERT_CHECK_MS       1000",
        "#define BACKLIGHT_DIM_MS     30000",
        "",
        "/* --- Thermistor --- */",
        "#define THERMISTOR_NOMINAL   10000",
        "#define THERMISTOR_SERIES_R  10000",
        "#define THERMISTOR_BETA      3950",
        "#define ADC_MAX              4095",
        "#define ADC_VREF             3.3",
        "",
        "/* --- Buzzer --- */",
        "#define BUZZER_PIN           26",
        "#define BUZZER_CHAN          1",
        "#define ALERT_TONE_FREQ_HZ   2730",
        "",
        "#endif // CONFIG_H",
    ])
    return '\n'.join(lines) + '\n'


def generate_sensors_h(engine_name: str, sensors: list) -> str:
    """Generate sensors.h content."""
    has_nmea = any(s.endswith("nmea2000") for s in sensors)
    has_rpm = any(s.startswith("rpm:") for s in sensors)

    lines = [
        f"/*",
        f" * sensors.h — {engine_name} Sensor Definitions",
        f" * Generated by tools/generate_config.py",
        f" */",
        f"",
        f"#ifndef SENSORS_H",
        f"#define SENSORS_H",
        f"",
        f"#include <Arduino.h>",
        f'#include "config.h"',
        f"",
        f"typedef struct {{",
        f"    float rpm;",
        f"    float coolant_temp_c;",
        f"    float oil_pressure_bar;",
        f"    float battery_volts;",
        f"    float fuel_level_pct;",
        f"    float fuel_rate_lph;",
        f"    float engine_hours;",
        f"    bool  data_valid;",
        f"    uint32_t last_update_ms;",
        f"}} EngineData;",
        f"",
        f"extern EngineData engine;",
        f"",
    ]

    if has_nmea:
        lines.extend([
            "/* --- NMEA2000 --- */",
            "bool init_nmea2000(void);",
            "bool poll_nmea2000(void);",
            "",
        ])

    if has_rpm and not has_nmea:
        lines.extend([
            "/* --- Tachometer --- */",
            "void init_tachometer(void);",
            "float read_rpm(void);",
            "",
        ])

    # Individual sensor functions
    for spec in sensors:
        if spec in SENSOR_TYPES:
            for func in SENSOR_TYPES[spec]["includes"]:
                lines.append(f"float {func}(void);")

    lines.extend([
        "",
        "float estimate_fuel_rate(float rpm);",
        "void read_all_sensors(void);",
        "",
        "#endif // SENSORS_H",
    ])
    return '\n'.join(lines) + '\n'


def generate_display_h(display: dict) -> str:
    """Generate display.h content."""
    lines = [
        "/*",
        f" * display.h — {display['driver']} Display Driver",
        " * Generated by tools/generate_config.py",
        " */",
        "",
        "#ifndef DISPLAY_H",
        "#define DISPLAY_H",
        "",
        "#include <Arduino.h>",
    ]

    if display['lib'] == 'TFT_eSPI':
        lines.append('#include <TFT_eSPI.h>')
    elif display['lib'] == 'Adafruit_SSD1351':
        lines.append('#include <Adafruit_SSD1351.h>')
        lines.append('#include <Adafruit_GFX.h>')

    lines.extend([
        f'#include "config.h"',
        "",
        "typedef enum {",
        "    ALERT_NONE = 0, ALERT_INFO, ALERT_WARNING, ALERT_CRITICAL",
        "} AlertSeverity;",
        "",
        "void init_display(void);",
        "void update_display(void);",
        "void show_alert(const char *msg, AlertSeverity sev);",
        "void draw_splash(const char *name, const char *ver);",
        "",
        "#endif // DISPLAY_H",
    ])
    return '\n'.join(lines) + '\n'


def generate_main_c(engine_name: str, sensors: list, display: dict) -> str:
    """Generate main.c content."""
    has_nmea = any(s.endswith("nmea2000") for s in sensors)
    safe_name = sanitize_name(engine_name)

    lines = [
        "/*",
        f" * main.c — {engine_name} Engine Monitor",
        " * ESP32 Firmware — Main Loop",
        " * Generated by tools/generate_config.py",
        " *",
        " * Copyright (c) 2026 SuperInstance. MIT License.",
        " */",
        "",
        "#include <Arduino.h>",
    ]

    if has_nmea:
        lines.append("#include <CAN.h>")
    if display['lib'] == 'TFT_eSPI':
        lines.append("#include <TFT_eSPI.h>")
    elif display['lib'] == 'Adafruit_SSD1351':
        lines.append("#include <Adafruit_SSD1351.h>")
        lines.append("#include <Adafruit_GFX.h>")

    lines.extend([
        "#include <ArduinoJson.h>",
        '#include "config.h"',
        '#include "sensors.h"',
        '#include "display.h"',
        "",
        f'#define FIRMWARE_VERSION "1.0.0"',
        f'#define ENGINE_NAME      "{engine_name}"',
        "",
        "EngineData engine = {0};",
        "",
        "uint32_t last_sensor = 0, last_display = 0, last_alert = 0;",
        "static AlertSeverity current_alert = ALERT_NONE;",
        "static bool buzzer_silenced = false;",
        "",
        "void check_alerts(void);",
        "void handle_serial(void);",
        "void sound_buzzer(uint16_t ms);",
        "",
        "void setup() {",
        "    Serial.begin(115200);",
        '    Serial.printf("\\n=== Engine Ensign %s ===\\n", FIRMWARE_VERSION);',
        '    Serial.printf("Engine: %s\\n", ENGINE_NAME);',
        "",
        "    init_display();",
        "    draw_splash(ENGINE_NAME, FIRMWARE_VERSION);",
        "    delay(2000);",
        "",
    ]

    if has_nmea:
        lines.extend([
            "    if (!init_nmea2000()) {",
            '        Serial.println("[WARN] NMEA2000 init failed!");',
            "    } else {",
            '        Serial.println("[OK] NMEA2000 initialized");',
            "    }",
            "",
        ])
    else:
        lines.extend([
            "    init_tachometer();",
            "",
        ])

    lines.extend([
        "    analogReadResolution(12);",
        "    analogSetAttenuation(ADC_11db);",
        "",
        "    ledcSetup(BUZZER_CHAN, ALERT_TONE_FREQ_HZ, 8);",
        "    ledcAttachPin(BUZZER_PIN, BUZZER_CHAN);",
        "    ledcWrite(BUZZER_CHAN, 0);",
        "    engine.data_valid = true;",
        '    Serial.println("[OK] System ready. Monitoring engine.");',
        "}",
        "",
        "void loop() {",
        "    uint32_t now = millis();",
        "",
        "    if (now - last_sensor >= SENSOR_UPDATE_MS) {",
        "        read_all_sensors();",
        "        engine.fuel_rate_lph = estimate_fuel_rate(engine.rpm);",
        "        engine.last_update_ms = now;",
        "        last_sensor = now;",
        "    }",
        "",
        "    if (now - last_alert >= ALERT_CHECK_MS) {",
        "        check_alerts();",
        "        last_alert = now;",
        "    }",
        "",
        "    if (now - last_display >= DISPLAY_UPDATE_MS) {",
        "        update_display();",
        "        last_display = now;",
        "    }",
        "",
        "    if (Serial.available()) handle_serial();",
        "}",
        "",
        "void check_alerts(void) {",
        "    AlertSeverity sev = ALERT_NONE;",
        "    const char *msg = NULL;",
        "",
        "    if (engine.coolant_temp_c >= TEMP_REDLINE) {",
        '        sev = ALERT_CRITICAL; msg = "OVERHEATING";',
        "    } else if (engine.coolant_temp_c >= TEMP_NORMAL_MAX) {",
        '        sev = ALERT_WARNING; msg = "High Temp";',
        "    }",
        "",
        "    if (engine.oil_pressure_bar < OIL_PRESSURE_CRIT && engine.rpm > 500) {",
        '        sev = ALERT_CRITICAL; msg = "OIL PRESS CRIT";',
        "    } else if (engine.oil_pressure_bar < OIL_PRESSURE_MIN && engine.rpm > 800) {",
        '        if (sev < ALERT_WARNING) { sev = ALERT_WARNING; msg = "Low Oil Press"; }',
        "    }",
        "",
        "    if (engine.rpm >= RPM_REDLINE) {",
        '        if (sev < ALERT_WARNING) { sev = ALERT_WARNING; msg = "RPM REDLINE"; }',
        "    }",
        "",
        "    if (sev != current_alert) {",
        "        current_alert = sev;",
        "        if (sev != ALERT_NONE) {",
        "            show_alert(msg, sev);",
        "            if (!buzzer_silenced && sev >= ALERT_WARNING) {",
        "                sound_buzzer(150);",
        "                buzzer_silenced = true;",
        "            }",
        "            Serial.printf(\"[ALERT] %s temp=%.1f oil=%.2f rpm=%.0f\\n\",",
        "                          msg, engine.coolant_temp_c, engine.oil_pressure_bar, engine.rpm);",
        "        } else {",
        '            show_alert(NULL, ALERT_NONE);',
        '            Serial.println("[ALERT_RESOLVED]");',
        "        }",
        "    }",
        "}",
        "",
        "void sound_buzzer(uint16_t ms) {",
        "    ledcWrite(BUZZER_CHAN, 128);",
        "    delay(ms);",
        "    ledcWrite(BUZZER_CHAN, 0);",
        "}",
        "",
        "void handle_serial(void) {",
        "    String cmd = Serial.readStringUntil('\\n');",
        "    cmd.trim(); cmd.toUpperCase();",
        "    if (cmd == \"STATUS\") {",
        "        Serial.printf(\"{\\\"engine\\\":\\\"%s\\\",\\\"rpm\\\":%.0f,\\\"temp\\\":%.1f,\"",
        "                      \"\\\"oil\\\":%.2f,\\\"volts\\\":%.2f,\\\"rate\\\":%.1f}\\n\",",
        "                      ENGINE_NAME, engine.rpm, engine.coolant_temp_c,",
        "                      engine.oil_pressure_bar, engine.battery_volts, engine.fuel_rate_lph);",
        "    } else if (cmd == \"ALERTS\") {",
        "        Serial.printf(\"{\\\"alert\\\":%d}\\n\", current_alert);",
        "    } else if (cmd == \"QUIET\") {",
        "        buzzer_silenced = true;",
        '        Serial.println("[OK] silenced");',
        "    } else {",
        '        Serial.println("[ERR] Commands: STATUS ALERTS QUIET");',
        "    }",
        "}",
    ])
    return '\n'.join(lines) + '\n'


def generate_platformio_ini(engine_name: str, sensors: list, display: dict,
                            platform: str) -> str:
    """Generate platformio.ini content."""
    safe = sanitize_name(engine_name)

    lines = [
        f"; platformio.ini — {engine_name} Engine Monitor",
        f"; Generated by tools/generate_config.py",
        "",
        f"[env:{safe}]",
    ]

    if platform == "esp32":
        lines.extend([
            "platform          = espressif32",
            "board             = esp32dev",
        ])
    elif platform == "esp32s3":
        lines.extend([
            "platform          = espressif32",
            "board             = esp32-s3-devkitc-1",
        ])
    else:
        lines.extend([
            "platform          = espressif32",
            "board             = esp32dev",
        ])

    lines.extend([
        "framework         = arduino",
        "monitor_speed     = 115200",
        "upload_speed      = 921600",
        "",
        "build_flags =",
        "    -DCORE_DEBUG_LEVEL=0",
    ])

    if display['lib'] == 'TFT_eSPI':
        lines.extend([
            "    -DUSER_SETUP_LOADED=1",
            f"    -D{display['define']}=1" if display.get('define') else "",
            f"    -DTFT_WIDTH={display['width']}",
            f"    -DTFT_HEIGHT={display['height']}",
            "    -DTFT_CS=15",
            "    -DTFT_DC=2",
            "    -DTFT_RST=4",
            "    -DTFT_MOSI=23",
            "    -DTFT_CLK=18",
            "    -DTFT_MISO=19",
            "    -DTFT_BL=32",
            f"    -DTFT_ROTATION={display['rotation']}",
            f"    -DSPI_FREQUENCY={display['spi_mhz'] * 1000000}",
        ])

    lines.append("")
    lines.append("lib_deps =")

    if display['lib'] == 'TFT_eSPI':
        lines.append("    TFT_eSPI")
    elif display['lib'] == 'Adafruit_SSD1351':
        lines.append("    adafruit/Adafruit SSD1351 library")
        lines.append("    adafruit/Adafruit GFX Library")

    if any(s.endswith("nmea2000") for s in sensors):
        lines.append("    arduino-libraries/ArduinoJson@^6.21.0")
    else:
        lines.append("    arduino-libraries/ArduinoJson@^6.21.0")

    # Filter empty strings
    lines = [l for l in lines if l != "" or True]  # keep blanks for readability
    return '\n'.join(lines) + '\n'


def generate_readme(engine_name: str, sensors: list, display: dict,
                    thresholds: dict) -> str:
    """Generate README.md content."""
    safe = sanitize_name(engine_name)

    lines = [
        f"# {engine_name} Engine Monitor",
        "",
        f"**Engine:** {engine_name}",
        f"**Sensors:** {', '.join(sensors)}",
        f"**Display:** {display['driver']} ({display['width']}×{display['height']})",
        f"**Board:** ESP32 DevKit V1",
        "",
        "*Generated by `tools/generate_config.py`. Thresholds are starting estimates — calibrate against the specific engine.*",
        "",
        "## Wiring",
        "",
        "| ESP32 Pin | Function |",
        "|-----------|----------|",
        "| GPIO 15 | TFT CS |",
        "| GPIO 2 | TFT DC |",
        "| GPIO 23 | SPI MOSI |",
        "| GPIO 18 | SPI CLK |",
        "| GPIO 32 | Backlight |",
        "| GPIO 26 | Buzzer |",
    ]

    # Add sensor-specific pins
    for spec in sensors:
        if spec in SENSOR_TYPES and SENSOR_TYPES[spec].get("default_pin"):
            s = SENSOR_TYPES[spec]
            lines.append(f"| GPIO {s['default_pin']} | {spec} |")

    lines.extend([
        "",
        "## Thresholds",
        "",
        "| Parameter | Yellow | Red |",
        "|-----------|--------|-----|",
        f"| Coolant Temp | {thresholds['temp_yellow']}°C | {thresholds['temp_red']}°C |",
        f"| Oil Pressure | {thresholds['oil_yellow']} bar | {thresholds['oil_red']} bar |",
        f"| RPM | {thresholds['rpm_yellow']} | {thresholds['rpm_red']} |",
        f"| Voltage | {thresholds['volts_low']}V | {thresholds['volts_crit']}V |",
        "",
        "## Build",
        "",
        "```bash",
        "pio run",
        "pio run -t upload",
        "pio device monitor",
        "```",
    ])
    return '\n'.join(lines) + '\n'


def generate_dashboard_json(engine_name: str, display: dict,
                            thresholds: dict) -> str:
    """Generate a dashboard JSON config."""
    safe = sanitize_name(engine_name)
    dash = {
        "name": f"{engine_name} {display['width']}x{display['height']}",
        "target_firmware": f"firmware/{safe}",
        "display": {
            "type": display['driver'],
            "width": display['width'],
            "height": display['height'],
        },
        "themes": {
            "day": {
                "background": "#000000",
                "text": "#FFFFFF",
                "normal": "#00FF00",
                "warning": "#FFFF00",
                "critical": "#FF0000",
            }
        },
        "current_theme": "day",
        "gauges": [
            {
                "id": "rpm",
                "type": "analog_dial" if display['width'] >= 320 else "digital_readout",
                "label": "RPM",
                "data_source": "engine.rpm",
                "position": {"x": display['width'] // 4, "y": display['height'] // 2},
                "radius": min(display['width'], display['height']) // 4,
                "min": 0,
                "max": thresholds['rpm_red'] + 500,
                "yellow_zone": {"start": thresholds['rpm_yellow'], "end": thresholds['rpm_red']},
                "red_zone": {"start": thresholds['rpm_red'], "end": thresholds['rpm_red'] + 500},
                "digital_readout": True,
            },
            {
                "id": "coolant_temp",
                "type": "bar_gauge" if display['width'] >= 320 else "digital_readout",
                "label": "TEMP",
                "data_source": "engine.coolant_temp_c",
                "position": {"x": display['width'] - 80, "y": 40},
                "min": 40,
                "max": 120,
                "yellow_zone": {"start": thresholds['temp_yellow'], "end": thresholds['temp_red']},
                "red_zone": {"start": thresholds['temp_red'], "end": 120},
            },
        ],
        "readouts": [
            {
                "id": "volts",
                "label": "BAT",
                "data_source": "engine.battery_volts",
                "format": "%.1fV",
            },
        ],
    }
    return json.dumps(dash, indent=2) + '\n'


def main():
    parser = argparse.ArgumentParser(
        description="Generate ESP32 firmware config for a new engine monitoring setup."
    )
    parser.add_argument("--engine", required=True,
                        help="Engine name (e.g., 'perkins_6354')")
    parser.add_argument("--sensors", required=True,
                        help="Comma-separated sensor specs (e.g., 'rpm:inductive,temp:thermistor,oil:analog_0-5v')")
    parser.add_argument("--display", required=True,
                        choices=list(DISPLAYS.keys()),
                        help="Display type")
    parser.add_argument("--platform", default="esp32",
                        choices=["esp32", "esp32s3"],
                        help="ESP32 platform variant")
    parser.add_argument("--output", required=True,
                        help="Output directory (e.g., firmware/perkins_6354/)")
    parser.add_argument("--engine-class", default=None,
                        choices=list(DEFAULT_THRESHOLDS.keys()),
                        help="Override engine class detection for thresholds")
    parser.add_argument("--dashboards-dir", default="../dashboards",
                        help="Where to write the dashboard JSON (relative to output)")

    args = parser.parse_args()

    # Parse sensors
    sensor_list = [s.strip() for s in args.sensors.split(',')]
    for s in sensor_list:
        if s not in SENSOR_TYPES:
            print(f"Warning: unknown sensor type '{s}'. Known types: {', '.join(SENSOR_TYPES.keys())}", file=sys.stderr)

    # Get display spec
    display = DISPLAYS[args.display]

    # Determine thresholds
    engine_class = args.engine_class or guess_engine_class(args.engine)
    thresholds = DEFAULT_THRESHOLDS[engine_class]

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_name = sanitize_name(args.engine)

    # Generate files
    files = {
        "config.h": generate_config_h(args.engine, sensor_list, display, thresholds, args.platform),
        "sensors.h": generate_sensors_h(args.engine, sensor_list),
        "display.h": generate_display_h(display),
        "main.c": generate_main_c(args.engine, sensor_list, display),
        "platformio.ini": generate_platformio_ini(args.engine, sensor_list, display, args.platform),
        "README.md": generate_readme(args.engine, sensor_list, display, thresholds),
    }

    for filename, content in files.items():
        filepath = output_dir / filename
        filepath.write_text(content)
        print(f"  ✓ {filepath}")

    # Generate dashboard JSON
    dash_dir = Path(args.dashboards_dir) if not os.path.isabs(args.dashboards_dir) else Path(args.dashboards_dir)
    if not dash_dir.is_absolute():
        dash_dir = output_dir.parent.parent / "dashboards"
    dash_dir.mkdir(parents=True, exist_ok=True)
    dash_file = dash_dir / f"{safe_name}.json"
    dash_file.write_text(generate_dashboard_json(args.engine, display, thresholds))
    print(f"  ✓ {dash_file}")

    print(f"\n✓ Generated {len(files) + 1} files for {args.engine}")
    print(f"  Engine class: {engine_class}")
    print(f"  Thresholds: temp {thresholds['temp_yellow']}/{thresholds['temp_red']}°C, "
          f"oil {thresholds['oil_yellow']}/{thresholds['oil_red']} bar, "
          f"rpm {thresholds['rpm_yellow']}/{thresholds['rpm_red']}")
    print(f"\n⚠ Thresholds are starting estimates. Calibrate against the specific engine.")
    print(f"  See agent/design_decisions.md for the calibration methodology.")


if __name__ == "__main__":
    main()
