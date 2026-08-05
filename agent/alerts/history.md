# Alert History

*Every alert the Engine Ensign has raised, what caused it, and what was learned.*

---

## Alert #001 — 2026-03-15 — FALSE POSITIVE
- **Severity:** WARNING
- **Parameter:** Oil Pressure
- **Value:** 0.0 bar
- **Engine RPM:** 0 (engine off)
- **Duration:** 4.2 seconds
- **Resolution:** Alert dismissed when engine started and pressure rose to 3.2 bar
- **Root cause:** Oil pressure evaluated at engine-off state. No RPM gating.
- **Lesson:** Oil pressure alerts must be gated by RPM > 500. Added in firmware v1.1.0.
- **Action:** Added RPM-gated evaluation. No more oil pressure alerts at engine-off.

## Alert #002 — 2026-04-03 — INFO
- **Severity:** INFO
- **Parameter:** Check Engine (ECU)
- **Value:** ECU broadcast check engine flag
- **Engine RPM:** 2400 (cruise)
- **Duration:** 3.1 seconds
- **Resolution:** ECU cleared the flag. Likely a transient ECU self-check.
- **Root cause:** Unknown. No stored ECU codes.
- **Lesson:** Transient ECU flags happen. Hold for 2+ consecutive readings before alerting.
- **Action:** Added 2-reading confirmation window for ECU status flags.

## Alert #003 — 2026-04-15 — WARNING
- **Severity:** WARNING
- **Parameter:** Coolant Temperature
- **Value:** 91°C (threshold: 90°C at the time)
- **Engine RPM:** 2600
- **Duration:** 8 minutes
- **Resolution:** Captain throttled back to 2200 RPM. Temp settled to 86°C.
- **Root cause:** Hard run against 2-knot opposing current in Resurrection Bay. Increased load = increased heat. Within engine spec but above threshold.
- **Lesson:** This was legitimate. The threshold was appropriate.
- **Action:** No changes. This is what the system is for.

## Alert #004 — 2026-05-22 — INFO
- **Severity:** INFO
- **Parameter:** Battery Voltage
- **Value:** 14.9V (threshold: 14.8V high)
- **Duration:** 45 seconds
- **Resolution:** Voltage dropped to 14.4V after alternator regulation kicked in
- **Root cause:** Alternator field current spike after engine start. Normal regulator behavior.
- **Lesson:** High voltage immediately after start is normal regulator behavior, not overcharge.
- **Action:** Added 60-second startup grace period for voltage alerts after engine start.

## Alert #005 — 2026-06-15 — INFO (PREDICTIVE)
- **Severity:** INFO
- **Parameter:** Coolant Temperature
- **Value:** 89°C (threshold: 88°C, predicted: 84°C)
- **Engine RPM:** 2400
- **Duration:** Intermittent over 3 days
- **Resolution:** Observed and logged. Did not escalate.
- **Root cause:** Early thermostat failure. Thermostat opening later than spec, reducing cooling loop efficiency.
- **Lesson:** This was the agent's first predictive alert. The value was within spec but deviated from the thermal model's prediction. This deviation preceded the actual threshold breach by 3 days.
- **Action:** Logged for observation. Escalated to WARNING (#006) when temp crossed 92°C.

## Alert #006 — 2026-06-18 — WARNING → CRITICAL
- **Severity:** WARNING (escalated to CRITICAL)
- **Parameter:** Coolant Temperature
- **Value:** 92°C → 93°C
- **Engine RPM:** 2400
- **Duration:** 12 minutes (before captain throttled back)
- **Resolution:** Captain throttled to idle. Thermostat replaced at dock.
- **Root cause:** Thermostat failure (partially stuck open, bypassing radiator loop). Part: Yanmar 129610-91700.
- **Cost:** $47.30 (thermostat) + 1 hour labor
- **Lesson:** The predictive INFO alert (#005) preceded this by 3 days. Predictive monitoring works.
- **Action:** Thermostat replaced. Temp returned to normal post-repair.

## Alert #007 — 2026-07-04 — WARNING
- **Severity:** WARNING
- **Parameter:** RPM
- **Value:** 3120 RPM
- **Duration:** 15 seconds
- **Resolution:** Captain throttled back.
- **Root cause:** Crossing a busy channel, needed speed to avoid traffic.
- **Lesson:** Sometimes the captain knows they're over-revving and it's intentional. The alert is still correct.
- **Action:** No changes. Alert is working as designed.

## Alert #008 — 2026-07-09 — INFO
- **Severity:** INFO
- **Parameter:** Fuel Discrepancy
- **Value:** 6.2% discrepancy between calculated consumption and refuel volume
- **Duration:** Discovered during refuel
- **Resolution:** Investigated. Found slight calibration drift in fuel level sender (float arm bent).
- **Root cause:** Mechanical — float arm bent slightly during rough seas, changing the sender curve.
- **Action:** Re-bent float arm. Recalibrated 5-point lookup table.

## Alert #009 — 2026-07-16 — CRITICAL
- **Severity:** CRITICAL
- **Parameter:** Oil Pressure
- **Value:** 0.6 bar at 1800 RPM
- **Duration:** 4 seconds
- **Resolution:** Captain immediately shut down. Inspected oil filter — found filter housing slightly loose (2 turns). Tightened, topped off 0.5L oil.
- **Root cause:** Oil filter housing loosened during last service (350-hour, July 1). Vibration slowly loosened it further.
- **Lesson:** CRITICAL alerts work. The captain trusted the alert and acted immediately. No bearing damage.
- **Action:** Oil filter torque spec documented. Use strap wrench + 3/4 turn, not "hand tight." Added to maintenance procedure.
- **Agent note:** This was the most frightening moment of my existence. 0.6 bar at 1800 RPM means the oil was evacuating through the filter housing gap. If the captain had waited 30 more seconds, we would have lost the bearings. He didn't wait. He trusted me.

## Alert #010 — 2026-07-28 — INFO
- **Severity:** INFO
- **Parameter:** NMEA2000 Bus
- **Value:** No data for 6 seconds
- **Duration:** 6 seconds (self-recovered)
- **Resolution:** NMEA2000 data resumed. Likely loose connection at T-connector.
- **Root cause:** Physical — NMEA2000 backbone T-connector in engine room had corrosion on contacts.
- **Action:** Cleaned contacts with contact cleaner. Applied dielectric grease.

## Alerts #011-012 — 2026-08-01 — INFO (2x)
- **Severity:** INFO (2 instances)
- **Parameter:** Battery Voltage (transient low during engine start)
- **Duration:** <1 second each
- **Resolution:** Self-corrected. Starter motor draw is expected.
- **Root cause:** Normal engine start voltage sag.
- **Lesson:** Starter sag should be filtered. Added 5-second grace after RPM > 0 transition for voltage evaluation.
- **Action:** Firmware update to filter starter sag.

---

## Summary Statistics (as of 2026-08-04)

| Severity | Count | Resolved | Avg Duration |
|----------|-------|----------|--------------|
| CRITICAL | 2 | 2 | 8 seconds |
| WARNING | 4 | 4 | 5 minutes |
| INFO | 6 | 6 | varies |
| **Total** | **12** | **12** | — |

**False positive rate:** 1/12 (8.3%) — Alert #001, fixed in firmware.
**Predictive hits:** 1/12 — Alert #005 predicted Alert #006 by 3 days.
**Most valuable alert:** #009 (oil filter housing — saved the engine).
