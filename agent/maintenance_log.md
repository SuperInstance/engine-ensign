# Maintenance Log — M/V Aurora

*The ship's engine maintenance history, as remembered by the Engine Ensign.*

---

## Engine: Yanmar 4LH-STE, S/N: 4LH-240-6789

### 2026-03-14 — Initial Installation
- **Hours:** 0.0
- **Work:** ESP32 monitor installed, NMEA2000 connected, first calibration
- **Technician:** Casey DiGennaro (owner)
- **Notes:** CAN transceiver initially wired backwards. Fixed. All sensors calibrated against mechanical gauges. Thermistor required beta correction (-7°C offset corrected).
- **Parts:** SN65HVD230 CAN transceiver, 10k NTC thermistor, VDO oil pressure sender (0-5V)

### 2026-03-21 — 50-Hour Service
- **Hours:** 52.3
- **Work:** Oil change, fuel filter replacement, zinc inspection
- **Oil:** Shell Rimula R5 LE 15W-40, 11.5 L (with filter)
- **Filter:** Yanmar 129770-91510 (oil), Yanmar 129150-55810 (fuel primary), Yanmar 129150-55800 (fuel secondary)
- **Zincs:** Heat exchanger zinc at 60%. Replaced preventively.
- **Notes:** Monitor fuel level calibration refined. 5-point lookup table added.

### 2026-04-05 — Coolant Top-Off
- **Hours:** 89.1
- **Work:** Coolant level was 1.2L low. Topped off.
- **Coolant:** Chevron Delo XLC (pink/red, prediluted 50/50)
- **Notes:** Minor coolant loss, likely from the expansion tank vent during thermal cycling. No further loss observed after top-off. Monitor logged stable coolant temp trend.

### 2026-05-12 — Software Update
- **Hours:** 203.7
- **Work:** Firmware updated to v1.2.0. Added RPM-gated oil pressure evaluation, predictive thermal model hooks.
- **Notes:** Lowered yellow temp threshold from 90°C to 88°C based on accumulated thermal data. Average cruise temp: 83°C (±2°C). See `design_decisions.md`.

### 2026-06-15 — INFO Alert: Thermal Anomaly
- **Hours:** 312.4
- **Work:** Diagnostic only. Monitor flagged 89°C at cruise (predicted 84°C). No action taken yet.
- **Notes:** This was the agent's first predictive alert. The deviation was within spec but abnormal for conditions. Logged for observation.

### 2026-06-18 — WARNING: Coolant Temp 92°C
- **Hours:** 318.9
- **Work:** Thermostat diagnosed as failing (partially open). Replaced.
- **Part:** Yanmar 129610-91700 (thermostat assembly, OEM)
- **Cost:** $47.30
- **Notes:** Caught by the monitor's alert system. The temp had been creeping up for 3 days. Post-replacement, cruise temp returned to 83°C. The monitor's prediction model proved its value.
- **Agent note:** This was the event that made me a crew member. The thermostat was failing slowly enough that no threshold was crossed until June 18 — but the deviation from expected values was visible on June 15. Three days of advance warning.

### 2026-07-01 — 350-Hour Service
- **Hours:** 351.2
- **Work:** Oil change, fuel filters, impeller, belt tension, valve adjustment check
- **Oil:** Shell Rimula R5 LE 15W-40, 11.5 L
- **Filters:** Same as 50-hour (oil + primary + secondary fuel)
- **Impeller:** Globe Marine GOF-1270-1 (neoprene). Old impeller slightly worn but all vanes intact.
- **Belt:** Alternator belt tension adjusted to 10mm deflection at 10N.
- **Valves:** All within spec. No adjustment needed.
- **Notes:** Engine in excellent condition. All monitor readings nominal post-service.

### 2026-07-22 — Firmware Configurations Generated
- **Hours:** 489.0
- **Work:** Generated firmware configs for Cummins 6BTA (friend's vessel *Reel Time*), generic diesel template, and dual outboard setup.
- **Notes:** Each required different thresholds, sensor configs, and display strategies. See respective firmware directories.

### 2026-08-02 — Current Status
- **Hours:** 547.8
- **Engine condition:** Excellent
- **Last oil change:** 351.2 hours (196.6 hours ago — next at 700)
- **Known issues:** None active
- **Monitor uptime:** 1,432 hours (since installation)
- **Alerts raised:** 12 total (2 critical, 4 warning, 6 info)
- **Alerts resolved:** 12 (100%)
- **False alerts:** 1 (early oil pressure false alarm before RPM gating was added, March 2026)
