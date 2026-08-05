/*
 * sensors.h — Yanmar 4LH-STE Sensor Definitions
 *
 * Defines sensor data structures, pin mappings, NMEA2000 PGN parsers,
 * and analog sensor reading functions.
 */

#ifndef SENSORS_H
#define SENSORS_H

#include <Arduino.h>
#include "config.h"

/* --- NMEA2000 PGNs we care about --- */
#define PGN_RPM              127488L
#define PGN_ENGINE_PARAMS    127489L
#define PGN_ENGINE_BIN_STATUS 127501L
#define PGN_FLUID_LEVEL      127505L
#define PGN_FLUID_PRESSURE   127506L
#define PGN_TEMPERATURE      127507L
#define PGN_ENGINE_RATIO     127493L

/* --- Sensor data structure --- */
typedef struct {
    /* Primary (NMEA2000) */
    float    rpm;              // Engine RPM
    float    coolant_temp_c;  // Coolant temperature °C
    float    oil_pressure_bar;// Oil pressure in bar
    float    boost_pressure_bar; // Turbo boost
    float    alternator_volts; // Alternator voltage
    float    fuel_level_pct;  // Fuel tank level %

    /* Derived */
    float    fuel_rate_lph;   // Liters per hour (computed)
    float    engine_hours;    // Total engine hours
    float    fuel_used_total; // Total fuel used (L)

    /* Status flags */
    bool     check_engine;    // Check engine lamp
    bool     over_temp;       // Overheat warning from ECU
    bool     low_oil_pressure;// Low oil pressure from ECU
    bool     low_fuel;        // Low fuel warning
    bool     data_valid;      // NMEA2000 data is fresh

    /* Timestamps (millis) */
    uint32_t last_nmea_ms;    // Last NMEA2000 message received
    uint32_t last_analog_ms;  // Last analog read
} EngineData;

/* --- Global engine data --- */
extern EngineData engine;

/* --- Sensor functions --- */

/**
 * Initialize NMEA2000 CAN bus interface.
 * Returns true if the CAN controller initialized successfully.
 */
bool init_nmea2000(void);

/**
 * Poll the NMEA2000 bus for new engine data.
 * Call this frequently (10+ Hz). Non-blocking.
 * Returns true if new data was received.
 */
bool poll_nmea2000(void);

/**
 * Read all analog backup sensors and merge into engine data.
 * Called at SENSOR_UPDATE_MS interval.
 */
void read_analog_sensors(void);

/**
 * Parse a single NMEA2000 PGN and update engine data.
 * Called internally by poll_nmea2000().
 */
void parse_pgn(uint32_t pgn, const uint8_t *data, uint8_t len);

/* --- Individual sensor readers --- */

/**
 * Read coolant temperature from thermistor.
 * Uses beta equation with calibration from config.h.
 * Returns temperature in °C.
 */
float read_coolant_temp(void);

/**
 * Read oil pressure from analog sender.
 * 0.5V = 0 bar, 4.5V = 10 bar (linear).
 * Returns pressure in bar.
 */
float read_oil_pressure(void);

/**
 * Read fuel level from tank sender.
 * 0-190 ohm via voltage divider, mapped to 0-100%.
 */
float read_fuel_level(void);

/**
 * Read battery voltage via voltage divider.
 * Divider: 15k/47k → factor 3.13.
 */
float read_battery_voltage(void);

/**
 * Estimate fuel consumption rate based on RPM.
 * Uses linear interpolation between known data points.
 */
float estimate_fuel_rate(float rpm);

#endif // SENSORS_H
