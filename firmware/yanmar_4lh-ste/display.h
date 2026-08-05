/*
 * display.h — Yanmar 4LH-STE Display Driver
 *
 * 7" TFT (ILI9488) landscape layout.
 * Loads layout from dashboard JSON when possible,
 * falls back to hardcoded defaults.
 */

#ifndef DISPLAY_H
#define DISPLAY_H

#include <Arduino.h>
#include <TFT_eSPI.h>
#include "config.h"

/* --- Layout constants (fallback defaults) --- */
/* These mirror dashboards/yanmar_7inch_tft.json */

/* Primary gauge cluster */
#define GAUGE_RPM_X        120
#define GAUGE_RPM_Y        160
#define GAUGE_RPM_R        90

#define GAUGE_TEMP_X       360
#define GAUGE_TEMP_Y       100
#define GAUGE_TEMP_R       60

#define GAUGE_OIL_X        360
#define GAUGE_OIL_Y        240
#define GAUGE_OIL_R        60

/* Digital readouts (bottom bar) */
#define READOUT_Y          290
#define READOUT_VOLTS_X    20
#define READOUT_FUEL_X     120
#define READOUT_HOURS_X    220
#define READOUT_FUEL_RATE_X 330

/* Alert banner */
#define ALERT_X            0
#define ALERT_Y            0
#define ALERT_W            TFT_WIDTH
#define ALERT_H            30

/* --- Colors (day mode) --- */
#define COLOR_BG_DAY       TFT_BLACK
#define COLOR_TEXT_DAY     TFT_WHITE
#define COLOR_NORMAL_DAY   TFT_GREEN
#define COLOR_YELLOW_DAY   TFT_YELLOW
#define COLOR_RED_DAY      TFT_RED
#define COLOR_ACCENT_DAY   TFT_CYAN
#define COLOR_DIAL_DAY     TFT_DARKGREY

/* --- Colors (night mode — red/black for night vision) --- */
#define COLOR_BG_NIGHT     TFT_BLACK
#define COLOR_TEXT_NIGHT   0xA800 // dim orange
#define COLOR_NORMAL_NIGHT 0x5000 // dark green
#define COLOR_YELLOW_NIGHT 0xAA00 // dark yellow
#define COLOR_RED_NIGHT    0xA000 // dark red
#define COLOR_ACCENT_NIGHT 0x6020 // muted cyan
#define COLOR_DIAL_NIGHT   0x2104 // very dark grey

/* --- Display modes --- */
typedef enum {
    MODE_DAY,
    MODE_NIGHT,
    MODE_DIM
} DisplayMode;

/* --- Alert severity --- */
typedef enum {
    ALERT_NONE = 0,
    ALERT_INFO,
    ALERT_WARNING,
    ALERT_CRITICAL
} AlertSeverity;

/* --- Display functions --- */

/**
 * Initialize the TFT display, configure backlight PWM.
 */
void init_display(void);

/**
 * Main display update — draws all gauges and readouts.
 * Called at DISPLAY_UPDATE_MS interval.
 */
void update_display(void);

/**
 * Draw the RPM analog dial gauge.
 */
void draw_rpm_gauge(float rpm);

/**
 * Draw coolant temperature as a bar gauge.
 */
void draw_temp_gauge(float temp_c);

/**
 * Draw oil pressure as a bar gauge.
 */
void draw_oil_gauge(float pressure_bar);

/**
 * Draw digital readouts (volts, fuel, hours, rate).
 */
void draw_readouts(const EngineData *data);

/**
 * Show or clear an alert banner.
 * message: text to display (NULL to clear)
 * severity: controls color and buzzer
 */
void show_alert(const char *message, AlertSeverity severity);

/**
 * Set display mode (day/night/dim).
 */
void set_display_mode(DisplayMode mode);

/**
 * Set backlight brightness (0-255).
 */
void set_backlight(uint8_t brightness);

/**
 * Draw a boot splash screen with engine name and version.
 */
void draw_splash(const char *engine_name, const char *version);

#endif // DISPLAY_H
