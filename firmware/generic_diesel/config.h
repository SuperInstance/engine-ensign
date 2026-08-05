/*
 * config.h — Generic Diesel Engine Monitor
 *
 * Engine: Generic diesel (RPM + coolant temp + oil pressure)
 * Display: 2.4" LCD (ILI9341, 320x240, SPI)
 * Board: ESP32 DevKit V1
 */

#ifndef CONFIG_H
#define CONFIG_H

/* --- Display (ILI9341 2.4" LCD) --- */
#define TFT_CS      15
#define TFT_DC      2
#define TFT_RST     4
#define TFT_MOSI    23
#define TFT_CLK     18
#define TFT_BL      32
#define TFT_WIDTH   320
#define TFT_HEIGHT  240
#define TFT_ROTATION 1

/* --- Analog Inputs --- */
#define ANALOG_RPM_SIGNAL     34
#define ANALOG_COOLANT_TEMP   36
#define ANALOG_OIL_PRESSURE   35
#define ANALOG_BATTERY        39

/* --- Conservative Default Thresholds --- */
#define TEMP_NORMAL_MAX      90
#define TEMP_REDLINE         100
#define OIL_PRESSURE_MIN     1.5
#define OIL_PRESSURE_CRIT    0.7
#define RPM_REDLINE          3000
#define RPM_YELLOW           2800
#define VOLTS_LOW            11.8
#define VOLTS_CRITICAL       10.5
#define VOLTS_HIGH           15.0

/* --- Update Rates --- */
#define SENSOR_UPDATE_MS     500
#define DISPLAY_UPDATE_MS    250
#define ALERT_CHECK_MS       1000
#define BACKLIGHT_DIM_MS     30000

/* --- Thermistor --- */
#define THERMISTOR_NOMINAL   10000
#define THERMISTOR_SERIES_R  10000
#define THERMISTOR_BETA      3950
#define ADC_MAX              4095
#define ADC_VREF             3.3

/* --- Buzzer --- */
#define BUZZER_PIN           26
#define BUZZER_CHAN          1
#define ALERT_TONE_FREQ_HZ   2730

#endif // CONFIG_H
