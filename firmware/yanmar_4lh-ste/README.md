# Yanmar 4LH-STE Engine Monitor

**Engine:** Yanmar 4LH-STE (4-cylinder, 240HP marine diesel)
**Sensors:** NMEA2000 (6 PGNs) + analog backup (oil pressure, coolant temp, fuel level)
**Display:** 7" TFT ILI9488 (480×320, landscape, 4-wire SPI)
**Board:** ESP32 DevKit V1

## Wiring Guide

### ESP32 Pin Assignments

| ESP32 Pin | Function | Notes |
|-----------|----------|-------|
| GPIO 5 | CAN TX | NMEA2000 transceiver |
| GPIO 35 | CAN RX | NMEA2000 transceiver (input only) |
| GPIO 15 | TFT CS | Display chip select |
| GPIO 2 | TFT DC | Display data/command |
| GPIO 4 | TFT RST | Display reset |
| GPIO 23 | SPI MOSI | Shared SPI bus |
| GPIO 18 | SPI CLK | Shared SPI bus |
| GPIO 19 | SPI MISO | Shared SPI bus |
| GPIO 32 | TFT Backlight | PWM dimming |
| GPIO 34 | Oil Pressure | Analog 0-5V sender |
| GPIO 36 | Coolant Temp | Thermistor (10k NTC) |
| GPIO 39 | Fuel Level | 0-190Ω sender via divider |
| GPIO 26 | Buzzer | PWM piezo |

### NMEA2000 Connection

The Yanmar 4LH-STE's engine gateway broadcasts on NMEA2000 at 250 kbps. Connect via:

```
ESP32 GPIO 5 (CAN TX) → SN65HVD230 CAN TX
ESP32 GPIO 35 (CAN RX) → SN65HVD230 CAN RX
SN65HVD230 CANH → NMEA2000 backbone CANH (white)
SN65HVD230 CANL → NMEA2000 backbone CANL (blue)
```

Use a **MCP2562** or **SN65HVD230** CAN transceiver between the ESP32 and the NMEA2000 backbone. The ESP32's internal CAN controller handles the protocol.

### Analog Backup Sensors

If NMEA2000 goes offline, these analog sensors provide redundancy:

- **Oil Pressure:** VDO 0-5V sender (0.5V=0 bar, 4.5V=10 bar)
- **Coolant Temp:** 10k NTC thermistor in engine coolant port
- **Fuel Level:** Standard 0-190Ω tank sender (via voltage divider)

### Display

ILI9488 7" TFT, 4-wire SPI mode. Runs at 40MHz SPI clock for smooth animation.

## Default Thresholds

| Parameter | Yellow | Red |
|-----------|--------|-----|
| Coolant Temp | 88°C | 95°C |
| Oil Pressure (cruising) | 1.5 bar | 0.8 bar |
| RPM | 3100 | 3300 |
| Battery Voltage | 11.8V | 10.5V |
| Fuel Level | 15% | 5% |

## Serial Commands

Connect via USB at 115200 baud:

| Command | Action |
|---------|--------|
| `STATUS` | Dump all sensor values as JSON |
| `ALERTS` | Current alert state |
| `CONFIG` | Dump threshold configuration |
| `MODE DAY` | Day display mode (bright) |
| `MODE NIGHT` | Night display mode (dim red) |
| `ACK` | Acknowledge current alert |
| `QUIET` | Silence buzzer for 5 minutes |
| `THRESH T:90` | Set temp redline to 90°C |

## Dashboard

See [`dashboards/yanmar_7inch_tft.json`](../../dashboards/yanmar_7inch_tft.json) for the screen layout config.
