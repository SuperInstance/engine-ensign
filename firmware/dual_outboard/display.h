/*
 * display.h — Dual Outboard Display Driver
 *
 * 5" IPS split-screen layout: port on left, starboard on right.
 */

#ifndef DISPLAY_H
#define DISPLAY_H

#include <Arduino.h>
#include <TFT_eSPI.h>
#include "config.h"

/* Split screen layout */
#define SPLIT_X           240   // Vertical divider
#define HALF_WIDTH        240

/* Port side gauge positions */
#define PORT_RPM_X        120
#define PORT_RPM_Y        120
#define PORT_RPM_R        70

/* Starboard side gauge positions */
#define STBD_RPM_X        360
#define STBD_RPM_Y        120
#define STBD_RPM_R        70

/* Bottom bar (shared) */
#define FUEL_Y            270
#define TRIM_Y            290

/* Alert banner */
#define ALERT_Y           0
#define ALERT_H           28

typedef enum {
    ALERT_NONE = 0, ALERT_INFO, ALERT_WARNING, ALERT_CRITICAL
} AlertSeverity;

typedef enum { MODE_DAY, MODE_NIGHT, MODE_DIM } DisplayMode;

void init_display(void);
void update_display(void);
void show_alert(const char *msg, AlertSeverity sev);
void draw_splash(const char *name, const char *ver);
void set_display_mode(DisplayMode mode);
void set_backlight(uint8_t brightness);

#endif // DISPLAY_H
