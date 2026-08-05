/*
 * config.h — Cummins 6BTA Engine Monitor
 *
 * Engine: Cummins 6BTA 5.9 (6-cylinder, 270HP marine diesel, turbo)
 * Sensors: Analog gauges + temp senders (no NMEA2000)
 * Display: 3.5" OLED (SSD1351, 128x96, SPI)
 * Board: ESP32 DevKit V1
 */

#ifndef CONFIG_H
#define CONFIG_H

/* --- Display (SSD1351 3.5" OLED) --- */
#define OLED_CS     5
#define OLED_DC     2
#define OLED_RST    4
#define OLED_MOSI   23
#define OLED_CLK    18
#define OLED_WIDTH  128
#define OLED_HEIGHT 96

/* --- Analog Inputs --- */
#define ANALOG_RPM_SIGNAL     34  // Inductive pickup / tach signal
#define ANALOG_OIL_PRESSURE   35  // 0-5V sender
#define ANALOG_COOLANT_TEMP   36  // Thermistor
#define ANALOG_OIL_TEMP       39  // Thermistor (oil temp)
#define ANALOG_FUEL_LEVEL     32  // 0-190 ohm sender
#define ANALOG_BATTERY        33  // Voltage divider

/* --- Alert Thresholds (Cummins 6BTA specific) --- */
#define TEMP_NORMAL_MAX      96    // °C — Cummins runs warmer
#define TEMP_REDLINE         104   // °C
#define OIL_PRESSURE_MIN     2.0   // bar — Cummins needs more oil pressure
#define OIL_PRESSURE_CRIT    1.0   // bar
#define RPM_REDLINE          2800  // RPM (Cummins B-series)
#define RPM_YELLOW           2600  // RPM
#define VOLTS_LOW            11.8  // V
#define VOLTS_CRITICAL       10.5  // V
#define VOLTS_HIGH           15.0  // V — 6BTA alternator can spike
#define FUEL_LOW_PERCENT     15
#define FUEL_CRIT_PERCENT    5

/* --- Update Rates --- */
#define SENSOR_UPDATE_MS     500
#define DISPLAY_UPDATE_MS    200  // 5 Hz (OLED is fast)
#define ALERT_CHECK_MS       1000
#define BACKLIGHT_DIM_MS     30000

/* --- Tachometer (inductive pickup) --- */
#define TACH_PULSES_PER_REV  1    // 1 pulse per rev (flywheel ring gear)
#define TACH_DEBOUNCE_US     200  // min 200µs between pulses

/* --- Thermistor calibration --- */
#define THERMISTOR_NOMINAL   10000
#define THERMISTOR_SERIES_R  10000
#define THERMISTOR_BETA      3950
#define ADC_MAX              4095
#define ADC_VREF             3.3

/* --- Fuel consumption estimates (6BTA 5.9) --- */
#define FUEL_RATE_IDLE       2.8   // L/h at 700 RPM
#define FUEL_RATE_CRUISE     18.0  // L/h at 2000 RPM
#define FUEL_RATE_WOT        42.0  // L/h at 2800 RPM

/* --- Buzzer --- */
#define BUZZER_PIN           26
#define BUZZER_CHAN          1
#define ALERT_TONE_FREQ_HZ   2730

#endif // CONFIG_H
