/*
 * main.c — Dual Outboard Engine Monitor
 *
 * Twin outboard on NMEA2000, 5" IPS split-screen display.
 * Monitors port and starboard engines independently.
 *
 * Copyright (c) 2026 SuperInstance. MIT License.
 */

#include <Arduino.h>
#include <CAN.h>
#include <TFT_eSPI.h>
#include <ArduinoJson.h>
#include "config.h"
#include "sensors.h"
#include "display.h"

#define FIRMWARE_VERSION "1.1.0"
#define ENGINE_NAME      "Dual Outboard"

DualEngineData engines = {0};
TFT_eSPI tft = TFT_eSPI();

uint32_t last_sensor = 0, last_display = 0, last_alert = 0, last_nmea = 0;
static AlertSeverity current_alert = ALERT_NONE;
static bool buzzer_silenced = false;
static DisplayMode display_mode = MODE_DAY;

void check_alerts(void);
void handle_serial(void);
void sound_buzzer(uint16_t ms);

void setup() {
    Serial.begin(115200);
    Serial.printf("\n=== Engine Ensign %s ===\n", FIRMWARE_VERSION);
    Serial.printf("Config: %s\n", ENGINE_NAME);

    init_display();
    draw_splash(ENGINE_NAME, FIRMWARE_VERSION);
    delay(2000);

    if (!init_nmea2000()) {
        Serial.println("[WARN] NMEA2000 init failed!");
    } else {
        Serial.println("[OK] NMEA2000 initialized");
    }

    analogReadResolution(12);
    analogSetAttenuation(ADC_11db);

    ledcSetup(BUZZER_CHAN, ALERT_TONE_FREQ_HZ, 8);
    ledcAttachPin(BUZZER_PIN, BUZZER_CHAN);
    ledcWrite(BUZZER_CHAN, 0);

    Serial.println("[OK] Ready. Twin engine monitoring active.");
}

void loop() {
    uint32_t now = millis();

    /* NMEA2000 polling */
    if (now - last_nmea >= NMEA_UPDATE_MS) {
        poll_nmea2000();
        last_nmea = now;
    }

    if (now - last_sensor >= SENSOR_UPDATE_MS) {
        engines.fuel_level_pct = read_fuel_level();
        engines.total_fuel_rate = engines.port.fuel_rate_lph + engines.starboard.fuel_rate_lph;
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

    if (Serial.available()) handle_serial();
}

void check_alerts(void) {
    AlertSeverity sev = ALERT_NONE;
    const char *msg = NULL;
    char buf[64];

    /* Check both engines */
    SingleEngine *e[2] = {&engines.port, &engines.starboard};
    const char *names[2] = {"PORT", "STBD"};

    for (int i = 0; i < 2; i++) {
        if (!e[i]->data_valid) continue;

        if (e[i]->coolant_temp_c >= TEMP_REDLINE) {
            sev = ALERT_CRITICAL;
            snprintf(buf, sizeof(buf), "%s OVERHEATING", names[i]);
            msg = buf;
        } else if (e[i]->coolant_temp_c >= TEMP_NORMAL_MAX) {
            if (sev < ALERT_WARNING) {
                sev = ALERT_WARNING;
                snprintf(buf, sizeof(buf), "%s High Temp", names[i]);
                msg = buf;
            }
        }

        if (e[i]->oil_pressure_bar < OIL_PRESSURE_CRIT && e[i]->rpm > 500) {
            sev = ALERT_CRITICAL;
            snprintf(buf, sizeof(buf), "%s OIL PRESS", names[i]);
            msg = buf;
        }

        if (e[i]->rpm >= RPM_REDLINE) {
            if (sev < ALERT_WARNING) {
                sev = ALERT_WARNING;
                snprintf(buf, sizeof(buf), "%s RPM REDLINE", names[i]);
                msg = buf;
            }
        }

        if (e[i]->check_engine) {
            if (sev < ALERT_INFO) {
                sev = ALERT_INFO;
                snprintf(buf, sizeof(buf), "%s Check Engine", names[i]);
                msg = buf;
            }
        }
    }

    if (sev != current_alert) {
        current_alert = sev;
        if (sev != ALERT_NONE) {
            show_alert(msg, sev);
            if (!buzzer_silenced && sev >= ALERT_WARNING) {
                sound_buzzer(150);
                buzzer_silenced = true;
            }
            Serial.printf("[ALERT] %s\n", msg);
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
    cmd.trim(); cmd.toUpperCase();

    if (cmd == "STATUS") {
        Serial.printf("{\"engine\":\"%s\",\"ver\":\"%s\","
                      "\"port\":{\"rpm\":%.0f,\"temp\":%.1f,\"oil\":%.2f,\"volts\":%.2f,\"trim\":%.1f,\"valid\":%s},"
                      "\"stbd\":{\"rpm\":%.0f,\"temp\":%.1f,\"oil\":%.2f,\"volts\":%.2f,\"trim\":%.1f,\"valid\":%s},"
                      "\"fuel_pct\":%.1f,\"total_rate\":%.1f}\n",
                      ENGINE_NAME, FIRMWARE_VERSION,
                      engines.port.rpm, engines.port.coolant_temp_c,
                      engines.port.oil_pressure_bar, engines.port.alternator_volts,
                      engines.port.trim_degrees, engines.port.data_valid ? "true" : "false",
                      engines.starboard.rpm, engines.starboard.coolant_temp_c,
                      engines.starboard.oil_pressure_bar, engines.starboard.alternator_volts,
                      engines.starboard.trim_degrees, engines.starboard.data_valid ? "true" : "false",
                      engines.fuel_level_pct, engines.total_fuel_rate);
    } else if (cmd == "ALERTS") {
        Serial.printf("{\"alert\":%d}\n", current_alert);
    } else if (cmd == "QUIET") {
        buzzer_silenced = true; Serial.println("[OK] silenced");
    } else {
        Serial.println("[ERR] Commands: STATUS ALERTS QUIET");
    }
}
