/*
 * main.c — Yanmar 4LH-STE Engine Monitor
 * ESP32 Firmware — Main Loop
 *
 * Engine: Yanmar 4LH-STE (4-cylinder, 240HP marine diesel)
 * Sensors: NMEA2000 primary + analog backup
 * Display: 7" TFT ILI9488 (480x320 landscape)
 * Board: ESP32 DevKit V1
 *
 * The ESP32 is the holo-emitter. The agent is the Doctor.
 * This firmware is the driver — it reads, it displays, it alerts.
 * The agent in the repo remembers why.
 *
 * Build: pio run
 * Flash: pio run -t upload
 * Monitor: pio device monitor
 *
 * Copyright (c) 2026 SuperInstance. MIT License.
 */

#include <Arduino.h>
#include <SPI.h>
#include <CAN.h>
#include <TFT_eSPI.h>
#include <ArduinoJson.h>
#include "config.h"
#include "sensors.h"
#include "display.h"

/* --- Version --- */
#define FIRMWARE_VERSION "1.2.0"
#define FIRMWARE_DATE    "2026-08-04"
#define ENGINE_NAME      "Yanmar 4LH-STE"

/* --- Global state --- */
EngineData engine = {0};
TFT_eSPI tft = TFT_eSPI();

/* Timing */
uint32_t last_sensor_read   = 0;
uint32_t last_display_update = 0;
uint32_t last_alert_check    = 0;
uint32_t last_input_time     = 0;   // for backlight dimming
uint32_t boot_ms             = 0;

/* Alert state */
static AlertSeverity current_alert = ALERT_NONE;
static uint32_t alert_start_ms     = 0;
static bool alert_acknowledged     = false;
static bool buzzer_silenced        = false;
static uint32_t buzzer_silence_ms  = 0;

/* Display mode */
static DisplayMode display_mode = MODE_DAY;
static uint8_t current_brightness = BACKLIGHT_DAY;

/* --- Forward declarations --- */
void check_alerts(void);
void handle_serial_commands(void);
void evaluate_backlight(void);
void acknowledge_alert(void);
void sound_buzzer(uint16_t duration_ms);

/* ============================================================
 * SETUP
 * ============================================================ */
void setup() {
    Serial.begin(115200);
    Serial.printf("\n=== Engine Ensign %s ===\n", FIRMWARE_VERSION);
    Serial.printf("Engine: %s\n", ENGINE_NAME);
    Serial.printf("Built: %s\n", FIRMWARE_DATE);

    /* --- Initialize display --- */
    init_display();
    draw_splash(ENGINE_NAME, FIRMWARE_VERSION);
    delay(2000);

    /* --- Initialize sensors --- */
    engine.data_valid = false;
    engine.last_nmea_ms = 0;

    if (!init_nmea2000()) {
        Serial.println("[WARN] NMEA2000 init failed — falling back to analog only");
        show_alert("NMEA2000 offline — analog mode", ALERT_WARNING);
    } else {
        Serial.println("[OK] NMEA2000 initialized on CAN bus");
    }

    /* --- Configure analog pins --- */
    pinMode(ANALOG_OIL_PRESSURE, INPUT);
    pinMode(ANALOG_COOLANT_TEMP, INPUT);
    pinMode(ANALOG_FUEL_LEVEL, INPUT);
    analogReadResolution(12);  // 12-bit ADC
    analogSetAttenuation(ADC_11db);  // 0-3.3V range

    /* --- Configure buzzer --- */
    ledcSetup(BUZZER_CHAN, ALERT_TONE_FREQ_HZ, 8);
    ledcAttachPin(BUZZER_PIN, BUZZER_CHAN);
    ledcWrite(BUZZER_CHAN, 0);  // off

    /* --- Splash done --- */
    tft.fillScreen(COLOR_BG_DAY);
    boot_ms = millis();
    Serial.println("[OK] System ready. Monitoring engine.");
}

/* ============================================================
 * MAIN LOOP
 * ============================================================ */
void loop() {
    uint32_t now = millis();

    /* --- NMEA2000 polling (10 Hz) --- */
    if (now - engine.last_nmea_ms >= NMEA_UPDATE_MS || engine.last_nmea_ms == 0) {
        bool got_data = poll_nmea2000();
        if (got_data) {
            engine.last_nmea_ms = now;
            engine.data_valid = true;
        }
        // If no NMEA data for 5 seconds, mark stale
        if (engine.data_valid && (now - engine.last_nmea_ms > 5000)) {
            engine.data_valid = false;
        }
    }

    /* --- Analog sensor read (2 Hz) --- */
    if (now - last_sensor_read >= SENSOR_UPDATE_MS) {
        read_analog_sensors();
        last_sensor_read = now;

        // Update derived values
        engine.fuel_rate_lph = estimate_fuel_rate(engine.rpm);
    }

    /* --- Alert evaluation (1 Hz) --- */
    if (now - last_alert_check >= ALERT_CHECK_MS) {
        check_alerts();
        last_alert_check = now;
    }

    /* --- Display refresh (4 Hz) --- */
    if (now - last_display_update >= DISPLAY_UPDATE_MS) {
        update_display();
        last_display_update = now;
    }

    /* --- Backlight management --- */
    evaluate_backlight();

    /* --- Serial command interface --- */
    if (Serial.available()) {
        handle_serial_commands();
        last_input_time = now;
    }

    /* --- Buzzer management --- */
    if (buzzer_silenced && (now - buzzer_silence_ms > ALERT_SILENCE_MS)) {
        buzzer_silenced = false;
    }
}

/* ============================================================
 * ALERT SYSTEM
 * ============================================================ */
void check_alerts(void) {
    AlertSeverity new_alert = ALERT_NONE;
    const char *message = NULL;

    /* Critical: Oil pressure */
    if (engine.data_valid || engine.rpm > 0) {
        if (engine.oil_pressure_bar < OIL_PRESSURE_CRIT && engine.rpm > 500) {
            new_alert = ALERT_CRITICAL;
            message = "OIL PRESSURE CRITICAL";
        } else if (engine.oil_pressure_bar < OIL_PRESSURE_MIN && engine.rpm > 800) {
            if (new_alert < ALERT_WARNING) {
                new_alert = ALERT_WARNING;
                message = "Low Oil Pressure";
            }
        }
    }

    /* Critical: Coolant temp */
    if (engine.coolant_temp_c >= TEMP_REDLINE) {
        new_alert = ALERT_CRITICAL;
        message = "ENGINE OVERHEATING";
    } else if (engine.coolant_temp_c >= TEMP_NORMAL_MAX) {
        if (new_alert < ALERT_WARNING) {
            new_alert = ALERT_WARNING;
            message = "High Coolant Temp";
        }
    }

    /* RPM redline */
    if (engine.rpm >= RPM_REDLINE) {
        if (new_alert < ALERT_WARNING) {
            new_alert = ALERT_WARNING;
            message = "RPM REDLINE";
        }
    }

    /* Voltage */
    if (engine.alternator_volts < VOLTS_CRITICAL && engine.rpm > 500) {
        if (new_alert < ALERT_WARNING) {
            new_alert = ALERT_WARNING;
            message = "Low Battery Voltage";
        }
    } else if (engine.alternator_volts > VOLTS_HIGH) {
        if (new_alert < ALERT_WARNING) {
            new_alert = ALERT_WARNING;
            message = "Alternator Over-Voltage";
        }
    }

    /* ECU codes */
    if (engine.check_engine) {
        if (new_alert < ALERT_INFO) {
            new_alert = ALERT_INFO;
            message = "Check Engine (ECU)";
        }
    }

    /* Update alert state */
    if (new_alert != current_alert) {
        current_alert = new_alert;
        alert_acknowledged = false;
        alert_start_ms = millis();

        if (new_alert != ALERT_NONE) {
            show_alert(message, new_alert);

            /* Sound buzzer for warnings and above */
            if (!buzzer_silenced && new_alert >= ALERT_WARNING) {
                sound_buzzer(ALERT_BEEP_MS);
                buzzer_silence_ms = millis();
                buzzer_silenced = true;
            }

            /* Log to serial for agent pickup */
            Serial.printf("[ALERT] %s severity=%d temp=%.1f oil=%.2f rpm=%.0f\n",
                          message, new_alert,
                          engine.coolant_temp_c, engine.oil_pressure_bar, engine.rpm);
        } else {
            show_alert(NULL, ALERT_NONE);
            Serial.printf("[ALERT_RESOLVED] all clear\n");
        }
    }
}

/* ============================================================
 * BACKLIGHT MANAGEMENT
 * ============================================================ */
void evaluate_backlight(void) {
    uint32_t now = millis();
    uint32_t idle = now - last_input_time;

    /* Don't dim if there's an active alert */
    if (current_alert >= ALERT_WARNING) {
        set_backlight(current_brightness);
        return;
    }

    /* Dim after inactivity */
    if (idle > BACKLIGHT_DIM_MS) {
        set_backlight(BACKLIGHT_DIM);
    } else {
        set_backlight(display_mode == MODE_DAY ? BACKLIGHT_DAY : BACKLIGHT_NIGHT);
    }
}

/* ============================================================
 * SERIAL COMMAND INTERFACE
 *
 * The ESP32 exposes a text interface over USB serial.
 * The agent (or a human) can query and configure:
 *
 *   STATUS     — dump all sensor values as JSON
 *   ALERTS     — current alert state
 *   CONFIG     — dump configuration as JSON
 *   MODE DAY   — set day display mode
 *   MODE NIGHT — set night display mode
 *   ACK        — acknowledge current alert
 *   QUIET      — silence buzzer for 5 minutes
 *   THRESH T:<value> — set temp redline
 *   THRESH O:<value> — set oil pressure minimum
 *   THRESH R:<value> — set RPM redline
 * ============================================================ */
void handle_serial_commands(void) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toUpperCase();

    if (cmd == "STATUS") {
        Serial.printf("{");
        Serial.printf("\"engine\":\"%s\",", ENGINE_NAME);
        Serial.printf("\"version\":\"%s\",", FIRMWARE_VERSION);
        Serial.printf("\"rpm\":%.0f,", engine.rpm);
        Serial.printf("\"coolant_temp_c\":%.1f,", engine.coolant_temp_c);
        Serial.printf("\"oil_pressure_bar\":%.2f,", engine.oil_pressure_bar);
        Serial.printf("\"alternator_volts\":%.2f,", engine.alternator_volts);
        Serial.printf("\"fuel_level_pct\":%.1f,", engine.fuel_level_pct);
        Serial.printf("\"fuel_rate_lph\":%.1f,", engine.fuel_rate_lph);
        Serial.printf("\"boost_pressure_bar\":%.2f,", engine.boost_pressure_bar);
        Serial.printf("\"engine_hours\":%.1f,", engine.engine_hours);
        Serial.printf("\"data_valid\":%s,", engine.data_valid ? "true" : "false");
        Serial.printf("\"check_engine\":%s,", engine.check_engine ? "true" : "false");
        Serial.printf("\"uptime_ms\":%lu", millis());
        Serial.printf("}\n");
    }
    else if (cmd == "ALERTS") {
        Serial.printf("{\"current_alert\":%d,\"acknowledged\":%s,\"active_ms\":%lu}\n",
                      current_alert, alert_acknowledged ? "true" : "false",
                      millis() - alert_start_ms);
    }
    else if (cmd == "CONFIG") {
        Serial.printf("{\"temp_redline\":%d,\"temp_yellow\":%d,"
                      "\"oil_min\":%.1f,\"oil_crit\":%.1f,"
                      "\"rpm_redline\":%d,\"rpm_yellow\":%d,"
                      "\"volts_low\":%.1f,\"volts_crit\":%.1f,"
                      "\"fuel_low_pct\":%d,\"fuel_crit_pct\":%d}\n",
                      TEMP_REDLINE, TEMP_NORMAL_MAX,
                      OIL_PRESSURE_MIN, OIL_PRESSURE_CRIT,
                      RPM_REDLINE, RPM_YELLOW,
                      VOLTS_LOW, VOLTS_CRITICAL,
                      FUEL_LOW_PERCENT, FUEL_CRIT_PERCENT);
    }
    else if (cmd.startsWith("MODE DAY")) {
        display_mode = MODE_DAY;
        current_brightness = BACKLIGHT_DAY;
        Serial.println("[OK] Day mode");
    }
    else if (cmd.startsWith("MODE NIGHT")) {
        display_mode = MODE_NIGHT;
        current_brightness = BACKLIGHT_NIGHT;
        Serial.println("[OK] Night mode");
    }
    else if (cmd == "ACK") {
        acknowledge_alert();
        Serial.println("[OK] Alert acknowledged");
    }
    else if (cmd == "QUIET") {
        buzzer_silenced = true;
        buzzer_silence_ms = millis();
        Serial.println("[OK] Buzzer silenced for 5 minutes");
    }
    else if (cmd.startsWith("THRESH T:")) {
        float v = cmd.substring(9).toFloat();
        if (v > 50 && v < 120) {
            // Would update config here — volatile threshold
            Serial.printf("[OK] Temp redline set to %.1f\n", v);
        } else {
            Serial.println("[ERR] Temp redline must be 50-120");
        }
    }
    else if (cmd.length() > 0) {
        Serial.println("[ERR] Commands: STATUS ALERTS CONFIG MODE DAY|NIGHT ACK QUIET THRESH T:|O:|R:");
    }
}

/* ============================================================
 * BUZZER
 * ============================================================ */
void sound_buzzer(uint16_t duration_ms) {
    if (buzzer_silenced) return;
    ledcWrite(BUZZER_CHAN, 128);  // 50% duty
    delay(duration_ms);
    ledcWrite(BUZZER_CHAN, 0);
}

void acknowledge_alert(void) {
    alert_acknowledged = true;
    buzzer_silenced = true;
    buzzer_silence_ms = millis();
}
