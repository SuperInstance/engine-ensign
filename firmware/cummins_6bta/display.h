/*
 * display.h — Cummins 6BTA OLED Display Driver
 *
 * 3.5" SSD1351 OLED — compact layout.
 * Prioritizes digital readouts over analog dials (screen is small).
 */

#ifndef DISPLAY_H
#define DISPLAY_H

#include <Arduino.h>
#include <Adafruit_SSD1351.h>
#include <Adafruit_GFX.h>
#include "config.h"

/* Colors */
#define COLOR_BG     0x0000  // Black
#define COLOR_TEXT   0xFFFF  // White
#define COLOR_GREEN  0x07E0
#define COLOR_YELLOW 0xFFE0
#define COLOR_RED    0xF800
#define COLOR_CYAN   0x07FF

/* Layout positions */
#define LINE_RPM_Y      8
#define LINE_TEMP_Y     28
#define LINE_OIL_Y      44
#define LINE_OILT_Y     60
#define LINE_FUEL_Y     76
#define LINE_VOLTS_Y    88

typedef enum {
    ALERT_NONE = 0,
    ALERT_INFO,
    ALERT_WARNING,
    ALERT_CRITICAL
} AlertSeverity;

void init_display(void);
void update_display(void);
void show_alert(const char *msg, AlertSeverity sev);
void draw_splash(const char *name, const char *ver);

#endif // DISPLAY_H
