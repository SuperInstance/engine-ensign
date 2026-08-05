/*
 * display.h — Generic Diesel Display Driver
 * 2.4" ILI9341 LCD, minimal layout: RPM + Temp + Oil + warnings
 */

#ifndef DISPLAY_H
#define DISPLAY_H

#include <Arduino.h>
#include <TFT_eSPI.h>
#include "config.h"

typedef enum {
    ALERT_NONE = 0, ALERT_INFO, ALERT_WARNING, ALERT_CRITICAL
} AlertSeverity;

void init_display(void);
void update_display(void);
void show_alert(const char *msg, AlertSeverity sev);
void draw_splash(const char *name, const char *ver);

#endif // DISPLAY_H
