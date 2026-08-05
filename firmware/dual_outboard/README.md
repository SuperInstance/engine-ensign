# Dual Outboard Engine Monitor

**Engines:** Twin outboard (port + starboard) on NMEA2000
**Sensors:** NMEA2000 network (RPM, temp, oil, trim, volts per engine)
**Display:** 5" ST7789 IPS (480×320, split-screen)
**Board:** ESP32 DevKit V1

## Wiring

| ESP32 Pin | Function |
|-----------|----------|
| GPIO 5 | CAN TX (NMEA2000) |
| GPIO 35 | CAN RX (NMEA2000) |
| GPIO 15 | TFT CS |
| GPIO 2 | TFT DC |
| GPIO 23 | SPI MOSI |
| GPIO 18 | SPI CLK |
| GPIO 32 | Backlight PWM |
| GPIO 26 | Buzzer |

## NMEA2000 Setup

Both outboards must be on the same NMEA2000 backbone. The ESP32 reads engine data by source address — port engine at address 0, starboard at address 1. Adjust `ENGINE_PORT_SOURCE` and `ENGINE_STARBOARD_SOURCE` in `config.h` if your network assigns different addresses.

## Thresholds

Outboards run cooler (raw water cooled) and rev higher than inboards.

| Parameter | Yellow | Red |
|-----------|--------|-----|
| Coolant Temp | 80°C | 90°C |
| Oil Pressure | 1.0 bar | 0.3 bar |
| RPM | 5800 | 6000 |
| Trim | 20° | 25° |

## Split Screen

The display splits vertically: port engine on the left half, starboard on the right. Shared data (fuel level, total consumption) appears in the bottom bar.
