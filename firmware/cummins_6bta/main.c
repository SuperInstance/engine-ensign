/*
 * main.c — Cummins 6BTA Engine Monitor
 * ESP32 Firmware — Main Loop
 *
 * Engine: Cummins 6BTA 5.9 (6-cylinder, 270HP marine diesel)
 * Sensors: Analog only (inductive tach, thermistors, pressure sender)
 * Display: 3.5" SSD1351 OLED (128x96)
 * Board: ESP32 DevKit V1
 *
 * Copyright (c) 2026 SuperInstance. MIT License.
 */

#include <Arduino.h>
#include <Adafruit_SSD1351.h>
#include <Adafruit_GFX.h>
#include <ArduinoJson.h>
#include "config.h"
#include "sensors.h"
#include "display.h"

#define FIRMWARE_VERSION "1.1.0"
#define ENGINE_NAME      "Cummins 6BTA 5.9"

EngineData engine = {0};

uint32_t last_sensor   = 0;
uint32_t last_display  = 0;
uint32_t last_alert    = 0;

static AlertSeverity current_alert = ALERT_NONE;
static bool buzzer_silenced = false;

void check_alerts(void);
void handle_serial(void);
void sound_buzzer(uint16_t ms);

void setup() {
    Serial.begin(115200);
    Serial.printf("\n=== Engine Ensign %s ===\n", FIRMWARE_VERSION);
    Serial.printf("Engine: %s\n", ENGINE_NAME);

    init_display();
    draw_splash(ENGINE_NAME, FIRMWARE_VERSION);
    delay(2000);

    init_tachometer();

    analogReadResolution(12);
    analogSetAttenuation(ADC_11db);

    ledcSetup(BUZZER_CHAN, ALERT_TONE_FREQ_HZ, 8);
    ledcAttachPin(BUZZER_PIN, BUZZER_CHAN);
    ledcWrite(BUZZER_CHAN, 0);

    engine.data_valid = true;
    Serial.println("[OK] System ready. Monitoring engine.");
}

void loop() {
    uint32_t now = millis();

    if (now - last_sensor >= SENSOR_UPDATE_MS) {
        read_all_sensors();
        engine.fuel_rate_lph = estimate_fuel_rate(engine.rpm);
        engine.last_update_ms = now;
        last_sensor = now;
    }

    if (now - last_alert >= ALERT_CHECK_MS) {
        check_alerts();
        last_alert = now;
    }

    if (now - last_display >= DISPLAY_UPDATE_MS) {
        update_display();
        last_display = now;
    }

    if (Serial.available()) {
        handle_serial();
    }
}

void check_alerts(void) {
    AlertSeverity sev = ALERT_NONE;
    const char *msg = NULL;

    if (engine.coolant_temp_c >= TEMP_REDLINE) {
        sev = ALERT_CRITICAL;
        msg = "OVERHEATING";
    } else if (engine.coolant_temp_c >= TEMP_NORMAL_MAX) {
        sev = ALERT_WARNING;
        msg = "High Temp";
    }

    if (engine.oil_pressure_bar < OIL_PRESSURE_CRIT && engine.rpm > 500) {
        sev = ALERT_CRITICAL;
        msg = "OIL PRESS CRIT";
    } else if (engine.oil_pressure_bar < OIL_PRESSURE_MIN && engine.rpm > 800) {
        if (sev < ALERT_WARNING) { sev = ALERT_WARNING; msg = "Low Oil Press"; }
    }

    if (engine.rpm >= RPM_REDLINE) {
        if (sev < ALERT_WARNING) { sev = ALERT_WARNING; msg = "RPM REDLINE"; }
    }

    if (engine.battery_volts > VOLTS_HIGH) {
        if (sev < ALERT_WARNING) { sev = ALERT_WARNING; msg = "ALT OVER-VOLT"; }
    } else if (engine.battery_volts < VOLTS_CRITICAL && engine.rpm > 500) {
        if (sev < ALERT_WARNING) { sev = ALERT_WARNING; msg = "Low Voltage"; }
    }

    if (sev != current_alert) {
        current_alert = sev;
        if (sev != ALERT_NONE) {
            show_alert(msg, sev);
            if (!buzzer_silenced && sev >= ALERT_WARNING) {
                sound_buzzer(150);
                buzzer_silenced = true;
            }
            Serial.printf("[ALERT] %s temp=%.1f oil=%.2f rpm=%.0f\n",
                          msg, engine.coolant_temp_c, engine.oil_pressure_bar, engine.rpm);
        } else {
            show_alert(NULL, ALERT_NONE);
            Serial.println("[ALERT_RESOLVED]");
        }
    }
}

void sound_buzzer(uint16_t ms) {
    ledcWrite(BUZZER_CHAN, 128);
    delay(ms);
    ledcWrite(BUZZER_CHAN, 0);
}

void handle_serial(void) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toUpperCase();

    if (cmd == "STATUS") {
        Serial.printf("{\"engine\":\"%s\",\"ver\":\"%s\","
                      "\"rpm\":%.0f,\"temp\":%.1f,\"oil\":%.2f,"
                      "\"oil_temp\":%.1f,\"fuel\":%.1f,\"volts\":%.2f,"
                      "\"rate\":%.1f,\"hours\":%.1f}\n",
                      ENGINE_NAME, FIRMWARE_VERSION,
                      engine.rpm, engine.coolant_temp_c, engine.oil_pressure_bar,
                      engine.oil_temp_c, engine.fuel_level_pct, engine.battery_volts,
                      engine.fuel_rate_lph, engine.engine_hours);
    } else if (cmd == "ALERTS") {
        Serial.printf("{\"alert\":%d}\n", current_alert);
    } else if (cmd == "QUIET") {
        buzzer_silenced = true;
        Serial.println("[OK] silenced");
    } else {
        Serial.println("[ERR] Commands: STATUS ALERTS QUIET");
    }
}
