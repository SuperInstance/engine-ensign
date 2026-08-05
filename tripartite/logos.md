# Logos — The Facilities Manager

## How the firmware WORKS

Logos is the faculty that generates working code from hardware constraints. It doesn't care what the dashboard looks like — it cares that the sensor is read correctly, the ADC is calibrated, the display refreshes without tearing, and the watchdog timer fires if the main loop hangs.

### Hardware Targets

| Platform | Language | Best For | Limitations |
|----------|----------|----------|-------------|
| ESP32 | C (Arduino/PlatformIO) | Sensor reading, simple display, low power | 240MHz dual-core, 520KB SRAM, no OS |
| ESP32-S3 | C (Arduino/PlatformIO) | Faster display, WiFi/BLE, camera input | 512KB SRAM, better I/O |
| Raspberry Pi Zero | Python/C | Web UI, more sensors, logging | 1GHz single-core, needs SD card |
| Raspberry Pi 4 | Python/C | Vision, prediction, multi-display | 1.5GHz quad-core, 4GB RAM |
| Jetson Nano | Python/CUDA | AI inference, camera-based monitoring | GPU compute, 4GB RAM, higher power |

### The Sensor Layer

Logos handles each sensor type differently:

**Analog senders (resistive):** Oil pressure, coolant temp, fuel level. These are variable resistors on a voltage divider. Logos generates the ADC read code, the voltage-to-value conversion table, and the smoothing filter (exponential moving average, α=0.1 for stable readings).

**NMEA2000 (CAN bus):** Modern engines broadcast data on CAN. Logos generates the CAN frame parser, the PGN decoder, and the rate-limited display updater (NMEA2000 floods at 50+ Hz; the screen only needs 5 Hz).

**I2C/SPI digital sensors:** TMP117, BME280, INA219. Logos generates the bus init, the register read, and the CRC check.

**Pulse/frequency:** Tachometer, flow meter. Logos generates the interrupt-based pulse counter with debounce.

### The Display Layer

Each display type gets its own driver:

**TFT (ILI9488, ST7789):** Full color, fast refresh. Logos generates the SPI init, the framebuffer, and the double-buffer swap to prevent tearing.

**OLED (SSD1306, SH1106):** Monochrome, low power. Logos generates the I2C init and the pixel-by-pixel layout.

**LED matrix (MAX7219, HT1632):** Bright, sunlight-readable. Logos generates the multiplexing driver and the brightness control.

**E-ink:** Zero power in steady state. Logos generates the partial-refresh driver for updates without full screen flash.

### Error Handling

Logos is paranoid. Every sensor read is wrapped in error handling:
- Timeout if no response in 2x the expected interval
- Range check: if coolant temp reads -40°C or +150°C, the sensor is faulted
- Stuck value detection: if the same reading persists for 60s with zero variation, flag as suspect
- Watchdog timer: if the main loop hangs for >500ms, reboot the ESP32

### The Principle

The firmware is a driver. It converts physical reality (voltage, frequency, CAN frames) into numbers the agent can reason about. The driver must be correct, fast, and honest. If the sensor says 95°C, the driver reports 95°C — not what it thinks the captain wants to hear. Truth is a precondition for everything above.
