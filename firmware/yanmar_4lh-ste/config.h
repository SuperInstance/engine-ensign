/*
 * config.h — Yanmar 4LH-STE Engine Monitor
 * PlatformIO configuration constants
 *
 * Engine: Yanmar 4LH-STE (4-cylinder, 240HP marine diesel)
 * Sensors: 6x NMEA2000 + analog backup
 * Display: 7" TFT (ILI9488, 480x320, 4-wire SPI)
 * Board: ESP32 DevKit V1
 */

#ifndef CONFIG_H
#define CONFIG_H

/* --- Platform --- */
#define BOARD_ESP32
#define CPU_FREQ_MHZ 240

/* --- Display (ILI9488 7" TFT) --- */
#define TFT_CS      15
#define TFT_DC      2
#define TFT_RST     4
#define TFT_MOSI    23
#define TFT_CLK     18
#define TFT_BL      32      // Backlight PWM pin
#define TFT_ROTATION 1      // Landscape
#define TFT_WIDTH   480
#define TFT_HEIGHT  320

/* --- SPI Bus --- */
#define SPI_MISO    19
#define SPI_MOSI    23
#define SPI_CLK     18

/* --- NMEA2000 (CAN bus) --- */
#define CAN_TX      5
#define CAN_RX      35
#define CAN_SPEED   250     // 250 kbps (NMEA2000 standard)

/* --- Analog Inputs (backup sensors) --- */
#define ANALOG_OIL_PRESSURE  34   // 0-5V sender
#define ANALOG_COOLANT_TEMP  36   // thermistor
#define ANALOG_FUEL_LEVEL    39   // 0-190 ohm sender via voltage divider

/* --- Alert Thresholds --- */
#define TEMP_NORMAL_MAX      88    // °C — yellow above this
#define TEMP_REDLINE         95    // °C — red above this, SHUTDOWN
#define OIL_PRESSURE_MIN     1.5   // bar — yellow below this at >800 RPM
#define OIL_PRESSURE_CRIT    0.8   // bar — red below this, SHUTDOWN
#define RPM_REDLINE          3300  // RPM
#define RPM_YELLOW           3100  // RPM
#define VOLTS_LOW            11.8  // V — yellow
#define VOLTS_CRITICAL       10.5  // V — red
#define VOLTS_HIGH           14.8  // V — alternator overcharge warning
#define FUEL_LOW_PERCENT     15    // % — yellow
#define FUEL_CRIT_PERCENT    5     // % — red

/* --- Update Rates (ms) --- */
#define SENSOR_UPDATE_MS     500   // 2 Hz sensor reads
#define DISPLAY_UPDATE_MS    250   // 4 Hz display refresh
#define NMEA_UPDATE_MS       100   // 10 Hz NMEA2000 polling
#define ALERT_CHECK_MS       1000  // 1 Hz alert evaluation
#define BACKLIGHT_DIM_MS     30000 // Dim after 30s inactivity

/* --- PWM --- */
#define BACKLIGHT_PWM_CH     0
#define BACKLIGHT_FREQ       5000  // Hz
#define BACKLIGHT_RES        8     // 8-bit resolution (0-255)
#define BACKLIGHT_DAY        220
#define BACKLIGHT_NIGHT      60
#define BACKLIGHT_DIM        15

/* --- Buzzer --- */
#define BUZZER_PIN           26
#define BUZZER_CHAN          1
#define ALERT_TONE_FREQ_HZ   2730  // piercing but not panic-inducing
#define ALERT_BEEP_MS        150
#define ALERT_SILENCE_MS     5000  // silence after acknowledge

/* --- Calibration --- */
#define THERMISTOR_NOMINAL   10000 // ohms at 25°C
#define THERMISTOR_SERIES_R  10000 // pull-up resistor
#define THERMISTOR_BETA      3950  // beta coefficient
#define ADC_MAX              4095  // 12-bit ADC
#define ADC_VREF             3.3   // ESP32 ADC reference

/* --- Fuel Consumption (Yanmar 4LH-STE spec) --- */
#define FUEL_RATE_IDLE       2.1   // L/h at 800 RPM
#define FUEL_RATE_CRUISE     12.5  // L/h at 2400 RPM
#define FUEL_RATE_WOT        28.0  // L/h at 3300 RPM (don't)

#endif // CONFIG_H
