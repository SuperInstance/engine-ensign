/*
 * sensors.h — Cummins 6BTA Sensor Definitions
 *
 * Analog-only configuration. No NMEA2000 bus — this engine
 * uses traditional analog senders.
 */

#ifndef SENSORS_H
#define SENSORS_H

#include <Arduino.h>
#include "config.h"

typedef struct {
    float    rpm;
    float    coolant_temp_c;
    float    oil_pressure_bar;
    float    oil_temp_c;
    float    fuel_level_pct;
    float    battery_volts;
    float    fuel_rate_lph;
    float    engine_hours;
    bool     data_valid;
    uint32_t last_update_ms;
} EngineData;

extern EngineData engine;

/* --- Tachometer (pulse counter on GPIO 34) --- */
void init_tachometer(void);
float read_rpm(void);

/* --- Analog sensors --- */
float read_coolant_temp(void);
float read_oil_pressure(void);
float read_oil_temp(void);
float read_fuel_level(void);
float read_battery_voltage(void);
float estimate_fuel_rate(float rpm);

/* --- Combined read --- */
void read_all_sensors(void);

#endif // SENSORS_H
