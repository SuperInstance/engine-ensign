# Generic Diesel Engine Monitor

**Engine:** Any diesel with basic analog senders
**Sensors:** RPM (inductive), coolant temp (thermistor), oil pressure (0-5V)
**Display:** 2.4" ILI9341 LCD (320×240, SPI)
**Board:** ESP32 DevKit V1

The simplest configuration. RPM, temperature, oil pressure, and warnings. Works with most marine diesel engines.

## Wiring

| ESP32 Pin | Function |
|-----------|----------|
| GPIO 34 | RPM signal (inductive pickup) |
| GPIO 35 | Oil pressure (0-5V sender) |
| GPIO 36 | Coolant temp (10k NTC) |
| GPIO 39 | Battery voltage (divider) |
| GPIO 15 | TFT CS |
| GPIO 2 | TFT DC |
| GPIO 23 | SPI MOSI |
| GPIO 18 | SPI CLK |
| GPIO 32 | TFT Backlight |
| GPIO 26 | Buzzer |

## Thresholds

Conservative defaults. Adjust for your specific engine.

| Parameter | Yellow | Red |
|-----------|--------|-----|
| Coolant Temp | 90°C | 100°C |
| Oil Pressure | 1.5 bar | 0.7 bar |
| RPM | 2800 | 3000 |
