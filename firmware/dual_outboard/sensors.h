/*
 * sensors.h — Dual Outboard Sensor Definitions
 *
 * Two engines on NMEA2000. Source addresses distinguish port/starboard.
 */

#ifndef SENSORS_H
#define SENSORS_H

#include <Arduino.h>
#include "config.h"

typedef struct {
    float    rpm;
    float    coolant_temp_c;
    float    oil_pressure_bar;
    float    alternator_volts;
    float    fuel_rate_lph;
    float    trim_degrees;
    bool     check_engine;
    bool     over_temp;
    bool     low_oil;
    uint32_t last_nmea_ms;
    bool     data_valid;
} SingleEngine;

typedef struct {
    SingleEngine port;
    SingleEngine starboard;
    float fuel_level_pct;   // Combined fuel tank
    float total_fuel_rate;  // Both engines combined
} DualEngineData;

extern DualEngineData engines;

bool init_nmea2000(void);
bool poll_nmea2000(void);
void parse_pgn(uint32_t pgn, uint8_t source, const uint8_t *data, uint8_t len);
float read_fuel_level(void);

#endif // SENSORS_H
