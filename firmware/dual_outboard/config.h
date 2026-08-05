/*
 * config.h — Dual Outboard Engine Monitor
 *
 * Engines: Twin outboard (port + starboard) on NMEA2000
 * Display: 5" IPS (ST7789, 480x320, SPI)
 * Board: ESP32 DevKit V1
 */

#ifndef CONFIG_H
#define CONFIG_H

/* --- Display (ST7789 5" IPS) --- */
#define TFT_CS      15
#define TFT_DC      2
#define TFT_RST     4
#define TFT_MOSI    23
#define TFT_CLK     18
#define TFT_BL      32
#define TFT_WIDTH   480
#define TFT_HEIGHT  320
#define TFT_ROTATION 1

/* --- NMEA2000 CAN Bus --- */
#define CAN_TX      5
#define CAN_RX      35
#define CAN_SPEED   250

/* --- Dual Engine Addresses --- */
#define ENGINE_PORT_SOURCE      0  // NMEA2000 source address for port engine
#define ENGINE_STARBOARD_SOURCE 1  // NMEA2000 source address for starboard engine

/* --- Alert Thresholds (typical outboard) --- */
#define TEMP_NORMAL_MAX      80     // Outboards run cooler (raw water cooled)
#define TEMP_REDLINE         90
#define OIL_PRESSURE_MIN     1.0    // Outboards have lower oil pressure
#define OIL_PRESSURE_CRIT    0.3
#define RPM_REDLINE          6000   // Outboards rev high
#define RPM_YELLOW           5800
#define VOLTS_LOW            11.8
#define VOLTS_CRITICAL       10.5
#define VOLTS_HIGH           15.5
#define FUEL_LOW_PERCENT     15
#define FUEL_CRIT_PERCENT    5

/* --- Trim/Tilt --- */
#define TRIM_MAX_DEGREES     25     // Max useful trim angle
#define TRIM_WARNING_DEGREES 20     // Over-trim warning

/* --- Update Rates --- */
#define SENSOR_UPDATE_MS     250    // 4 Hz (outboards change fast)
#define DISPLAY_UPDATE_MS    200    // 5 Hz
#define NMEA_UPDATE_MS       100
#define ALERT_CHECK_MS       500    // 2 Hz (twin engine = more to check)
#define BACKLIGHT_DIM_MS     30000

/* --- Buzzer --- */
#define BUZZER_PIN           26
#define BUZZER_CHAN          1
#define ALERT_TONE_FREQ_HZ   2730

/* --- PWM Backlight --- */
#define BACKLIGHT_PWM_CH     0
#define BACKLIGHT_FREQ       5000
#define BACKLIGHT_RES        8
#define BACKLIGHT_DAY        220
#define BACKLIGHT_NIGHT      60
#define BACKLIGHT_DIM        15

#endif // CONFIG_H
