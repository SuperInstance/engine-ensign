# Captain's Preferences

*What the captain likes. What the captain doesn't like.*

---

## Display

- **Units:** Metric (°C, bar, L/h, km). Not imperial. Definitely not Fahrenheit.
- **Day mode brightness:** 220/255 — bright enough to read in direct sunlight
- **Night mode brightness:** 60/255 — dim enough to preserve night vision at 0300
- **Dim timeout:** 30 seconds of inactivity — long enough to read, short enough to save the display
- **Color scheme:** Green = normal, Yellow = caution, Red = critical. No purple, no blue, no decorative colors.
- **RPM gauge:** Analog dial preferred over digital. Glanceable.
- **Temperature:** Digital readout is fine. Bar gauge is better.
- **Night mode:** Dim orange text on black. NOT red — Casey's eyes can't focus on pure red.

## Alerts

- **Buzzer:** One beep (150ms) for new warnings. NOT continuous. The captain will not panic; he will think.
- **Alert text:** Specific. "HIGH COOLANT TEMP" not "WARNING." Say what's wrong.
- **Acknowledgment:** Button press or serial `ACK` command. Alert stays on screen until condition clears, even after ack.
- **Silence period:** 5 seconds after beep. If the condition persists or worsens, it beeps again.
- **Quiet hours:** No buzzer between 2300-0500 unless CRITICAL. Visual alert only.

## Engine

- **Cruise RPM:** 2200-2400 (sweet spot for fuel economy and noise)
- **Max sustained RPM:** 2800 (for long crossings)
- **WOT:** Only for emergencies and sea trials
- **Shutdown temp preference:** 90°C — Casey wants to shut down before the redline, not at it. (Agent's yellow threshold reflects this.)
- **Oil change interval:** 350 hours (Yanmar says 250; Casey runs synthetic and extends to 350 with the agent monitoring oil condition trends)

## Fuel

- **Tank capacity:** 400 L (M/V Aurora, standard tank)
- **Reserve:** Never below 15% (60L) in protected waters, never below 25% (100L) on open crossings
- **Fuel log:** Agent tracks cumulative fuel consumed vs. refuel events. Discrepancy > 5% triggers an INFO alert (possible fuel theft or leak).

## Communication

- **Serial JSON:** The captain likes JSON status output. He pipes it to a logger on the chartplotter Raspberry Pi.
- **Verbose logging:** Agent logs all alerts and state changes to serial. Casey reads them later.
- **No wireless:** The ESP32's WiFi is disabled. Casey doesn't want anything on the boat's network that doesn't need to be there. The serial port is the only interface.

## What Casey Doesn't Like

- He doesn't like alerts that fire and immediately clear (transient spikes). The agent should hold an alert for at least 2 consecutive readings before raising it.
- He doesn't like the display flickering between modes. Transitions should be smooth.
- He doesn't like undocumented thresholds. Every number in config.h must have a design_decisions.md entry explaining why.
