# Design Decisions

*Why each threshold is what it is. The agent's reasoning, not just its rules.*

---

## Coolant Temperature

### Yanmar 4LH-STE
| Level | Value | Reasoning |
|-------|-------|-----------|
| Normal max | 88°C | Originally 90°C. Lowered in May 2026 after building a thermal model. The engine cruises at 82-84°C. Reaching 88°C represents a 4-6°C anomaly — significant enough to warrant attention, early enough to act. |
| Redline | 95°C | Yanmar spec says continuous operation above 95°C will damage the cylinder liners. 95°C is also the point at which the mechanical thermostat is fully open — beyond this, there's no more cooling capacity to unlock. |

### Cummins 6BTA
| Level | Value | Reasoning |
|-------|-------|-----------|
| Normal max | 96°C | Cummins B-series runs hotter by design — it's a heavier-duty block with higher compression. The factory gauge doesn't even mark yellow until 107°C (225°F). 96°C is conservative but the captain agreed. |
| Redline | 104°C | 220°F. Cummins spec for maximum jacket water outlet temp. Beyond this, the aftercooler efficiency drops and NOx emissions spike. |

### Outboards
| Level | Value | Reasoning |
|-------|-------|-----------|
| Normal max | 80°C | Outboards are raw-water (seawater) cooled. They run much cooler than freshwater-cooled inboards. 55-75°C is typical cruise. 80°C means the tell-tale is barely flowing. |
| Redline | 90°C | At 90°C, the thermostats are fully open and something is very wrong with the water intake or impeller. |

## Oil Pressure

### Yanmar 4LH-STE
| Level | Value | Reasoning |
|-------|-------|-----------|
| Minimum (cruising) | 1.5 bar | Yanmar spec: minimum 2.0 bar at rated speed. I set yellow at 1.5 bar — slightly below spec — because I've observed hot idle pressure as low as 1.2 bar, which is normal for this engine at 180°C oil temp. 1.5 bar at cruise is genuinely concerning; 1.2 bar at idle is not. |
| Critical | 0.8 bar | Below 0.8 bar at any RPM above idle, the bearings are at risk. This is an emergency. |

**RPM-gated evaluation:** Oil pressure is NOT evaluated when RPM < 800. At idle, the oil pressure is naturally low. Evaluating against cruise thresholds at idle would produce false alerts.

### Cummins 6BTA
| Level | Value | Reasoning |
|-------|-------|-----------|
| Minimum | 2.0 bar | Higher baseline pressure than the Yanmar. The 6BTA's gear-driven oil pump maintains 3-4 bar at cruise. 2.0 bar is already abnormal. |
| Critical | 1.0 bar | The 6BTA has plain bearings that cannot survive low oil pressure. 1.0 bar is the floor. |

## RPM Limits

### Yanmar 4LH-STE
| Level | Value | Reasoning |
|-------|-------|-----------|
| Yellow | 3100 | Rated continuous output is at 3000 RPM. 3100 means we're into the intermittent duty zone. Fine for short bursts (climbing a wave, avoiding a log), not for sustained running. |
| Redline | 3300 | Max rated RPM is 3300. The fuel pump delivers maximum fuel at this RPM. Beyond this, we're over-speeding the rotating mass. |

### Outboards
| Level | Value | Reasoning |
|-------|-------|-----------|
| Yellow | 5800 | Most modern outboards redline at 6000-6300. 5800 leaves 200 RPM of headroom. |
| Redline | 6000 | The rev limiter kicks in around 6100. We alert at 6000 so the captain backs off before the limiter does it for them — limiter cuts spark, which is harder on the engine. |

## Display Choices

### Why digital readouts on the small OLED (Cummins config)
The 3.5" OLED is 128×96 pixels. An analog dial at that size is decorative, not informative. Digital readouts are readable from 3 feet away — which is the distance from the helm to the engine room hatch on most sportfish boats.

### Why analog dials for RPM on the larger displays
Humans read analog dials faster than digital numbers. A glance at a dial — the needle is in the green — takes 200ms. Reading "2400 RPM" and mentally comparing it to a threshold takes 1-2 seconds. On a boat moving at 25 knots, that difference matters.

### Why split-screen for dual outboard
Comparing port and starboard engines side by side is the primary diagnostic for twin-engine boats. If port is reading 180°F and starboard is reading 195°F, something is wrong with the starboard cooling system. This comparison must be visible simultaneously.

### Night mode color choices
Red light preserves night vision because rod cells (peripheral vision, low-light) are not sensitive to red. But pure red text on black is hard to read for aging eyes. Dim orange (0xFF6600 at low brightness) is a compromise — readable, not too bright, doesn't blow out night adaptation.

## Alert Philosophy

### One beep, not a klaxon
The buzzer sounds once for 150ms when a new WARNING or CRITICAL alert triggers. Then it's silenced for 5 seconds. The captain acknowledges by pressing a button or sending `ACK` over serial.

Reasoning: A continuous buzzer is panic-inducing and makes it harder to think. A single beep gets attention. The visual alert (banner on screen) persists until the condition clears. The captain needs to *think* about the problem, not *react* to the noise.

### RPM-gated alerts
Oil pressure and battery voltage are only evaluated when the engine is running (RPM > 500). When the engine is off, oil pressure is zero and battery voltage is resting. Evaluating against running thresholds produces false alerts every time the engine shuts down.

### Prediction vs threshold (future work)
The current system uses fixed thresholds. The agent's long-term goal is to implement predictive alerts — when the observed value deviates significantly from the *expected* value (based on a model), even if it hasn't crossed a threshold. The thermostat incident (June 2026) proved this approach's value: the 89°C reading was within spec but abnormal for the conditions.

## Fuel Level Sender Calibration

The standard marine fuel tank sender is a 0-190 ohm float arm. It is brutally non-linear — the float moves faster at the top of the tank (where the arm is horizontal) than at the bottom. We use a 5-point calibration table:

| Ohms | % Full |
|------|--------|
| 0 | 100 (short = full, per SAE standard) |
| 30 | 75 |
| 90 | 50 |
| 150 | 25 |
| 190 | 0 (empty) |

This is a piecewise-linear interpolation. It's not perfect, but it's better than the linear mapping that most gauges use, which reads "half full" when the tank is actually 60% full.
