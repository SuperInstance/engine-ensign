# Cummins 6BTA Engine Monitor

**Engine:** Cummins 6BTA 5.9 (6-cylinder, 270HP marine diesel, turbo)
**Sensors:** Analog only — inductive tach, thermistors, oil pressure sender
**Display:** 3.5" SSD1351 OLED (128×96, SPI)
**Board:** ESP32 DevKit V1

## Wiring Guide

| ESP32 Pin | Function | Sensor |
|-----------|----------|--------|
| GPIO 34 | Tach signal | Inductive pickup on flywheel |
| GPIO 35 | Oil pressure | VDO 0-5V sender (0.5V=0bar, 4.5V=10bar) |
| GPIO 36 | Coolant temp | 10k NTC thermistor |
| GPIO 39 | Oil temp | 10k NTC thermistor (sump plug) |
| GPIO 32 | Fuel level | 0-190Ω tank sender via divider |
| GPIO 33 | Battery V | 15k/47k voltage divider |
| GPIO 5 | OLED CS | Display |
| GPIO 2 | OLED DC | Display |
| GPIO 4 | OLED RST | Display |
| GPIO 23 | SPI MOSI | Shared |
| GPIO 18 | SPI CLK | Shared |
| GPIO 26 | Buzzer | Piezo |

## Thresholds

| Parameter | Yellow | Red |
|-----------|--------|-----|
| Coolant Temp | 96°C | 104°C |
| Oil Pressure | 2.0 bar | 1.0 bar |
| RPM | 2600 | 2800 |
| Voltage | 11.8V | 10.5V / 15.0V high |

Cummins B-series runs hotter and needs higher oil pressure than the Yanmar. These thresholds reflect the engine's operating characteristics.
