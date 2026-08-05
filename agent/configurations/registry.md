# Generated Configurations

*Memory of every firmware config the Engine Ensign has generated.*

---

## CFG-001: Yanmar 4LH-STE (Primary)
- **Date:** 2026-03-14
- **Path:** `firmware/yanmar_4lh-ste/`
- **Status:** Active (M/V Aurora)
- **Engine:** Yanmar 4LH-STE, 240HP, 4-cylinder marine diesel
- **Sensors:** NMEA2000 (6 PGNs) + 3 analog backup
- **Display:** 7" ILI9488 TFT (480x320)
- **Notes:** The original. Every other config was derived from lessons learned here.

## CFG-002: Cummins 6BTA 5.9
- **Date:** 2026-07-22
- **Path:** `firmware/cummins_6bta/`
- **Status:** Deployed on M/V *Reel Time* (friend's vessel)
- **Engine:** Cummins 6BTA 5.9, 270HP, 6-cylinder marine diesel
- **Sensors:** Analog only (inductive tach, 2× thermistor, oil pressure, fuel level, battery)
- **Display:** 3.5" SSD1351 OLED (128x96)
- **Notes:** Higher temp thresholds (Cummins runs hotter). No NMEA2000 — this engine has no ECU gateway. All analog, all the time.
- **Adaptations:** Outboard thermistor beta was different from Yanmar (3950 vs 3435). Had to adjust calibration constants. Oil pressure sender was mechanical (VDO 80psi) — required voltage divider + rescaling.

## CFG-003: Generic Diesel
- **Date:** 2026-07-22
- **Path:** `firmware/generic_diesel/`
- **Status:** Template (not deployed to a specific vessel)
- **Engine:** Any diesel with RPM + temp + oil pressure analog senders
- **Sensors:** Inductive tach, thermistor, 0-5V oil pressure, battery voltage
- **Display:** 2.4" ILI9341 LCD (320x240)
- **Notes:** Deliberately conservative thresholds. Designed as a starting point — the agent customizes when deployed to a specific engine. Minimum viable monitoring.

## CFG-004: Dual Outboard
- **Date:** 2026-07-22
- **Path:** `firmware/dual_outboard/`
- **Status:** Template (testing on simulated NMEA2000 network)
- **Engine:** Twin outboard (port + starboard), NMEA2000 network
- **Sensors:** NMEA2000 (RPM, temp, oil, trim, volts per engine)
- **Display:** 5" ST7789 IPS (480x320, split-screen)
- **Notes:** Split-screen layout is the defining feature. Independent alert evaluation per engine. Much higher redline RPM (6000 vs 3300). Much lower temp thresholds (raw water cooled).
- **Challenge:** Outboard NMEA2000 source addresses aren't standardized. Port might be address 3, starboard might be 11. Added configuration for source address mapping.

---

## Pending Configurations

None currently requested.

## Configuration Lessons

1. **Thermistor beta coefficients vary wildly between manufacturers.** Always calibrate against a known reference at two temperatures (ice water + boiling water). Never trust the datasheet.

2. **Analog oil pressure senders are not linear.** They claim to be, but they're not. Calibrate at 3+ points (0 bar, mid-range, max).

3. **NMEA2000 source addresses are not deterministic.** They depend on the order devices were powered on the network. The firmware should scan for engine PGNs and learn the source addresses, not assume them.

4. **Display choice matters more than sensor choice.** A well-designed 2.4" LCD is more useful than a poorly-designed 7" TFT. The information density and readability at distance are what count.

5. **Every new engine type requires threshold recalibration.** Factory specs are a starting point, not the final word. The agent's job is to learn what "normal" means for *this specific engine* and adjust accordingly.
