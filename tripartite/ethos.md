# Ethos — The Business Manager

## What MATTERS and when to escalate

Ethos is the faculty that decides what matters. Not what the gauges show — whether what they show is worth interrupting the captain. A temperature reading of 95°C means nothing without context. Ethos provides the context.

### The Mission Profile

Different vessels have different priorities:

**Fishing vessel:** Catch is the priority. Engine health matters because a dead engine means no fishing. But minor warnings during a hot bite can wait — the captain will be furious if an oil pressure advisory interrupts a multi-thousand-dollar haul.

**Cargo ship:** Schedule is the priority. Every hour of downtime costs money in late-delivery penalties. Ethos escalates early because prevention is cheaper than breakdown.

**Pleasure craft:** Safety and comfort are the priority. Ethos is conservative — any anomaly gets reported because the captain would rather know than not.

**Research vessel:** Data collection is the priority. Engine health matters only insofar as it affects mission duration.

### Alert Levels

Ethos defines three levels:

**GREEN — Log only.** The reading is within normal range or slightly outside but self-correcting. No display change, no notification. Example: coolant temp hits 88°C briefly during hard acceleration, drops back to 82°C.

**YELLOW — Display and remember.** The reading is abnormal but not dangerous. The gauge shifts color (Pathos handles the visual). The agent logs the event with full context. If the captain glances at the screen, they see something changed. No active alert. Example: coolant temp sustains 90°C for 5+ minutes.

**RED — Escalate.** The reading is dangerous. The agent wakes the captain (if sleeping), sends a Telegram message (if connected), and prepares a shutdown recommendation. Example: coolant temp exceeds 95°C or rises more than 2°C/minute.

### The Trust Score

Ethos maintains a trust score for each sensor:

```
trust = 1.0 (initial)
on correct alert: trust += 0.05 (max 0.95)
on false alarm: trust -= 0.15
on missed event: trust -= 0.30
on confirmed accurate: trust += 0.02
```

A sensor with trust < 0.4 is flagged as unreliable. Its readings still display but don't trigger escalations. Ethos recommends replacement in the maintenance log.

### The Escalation Decision

When Logos reports an abnormal reading, Ethos runs the escalation matrix:

1. Is the reading real? (Cross-check with backup sensor if available)
2. Is the reading dangerous? (Compare against thresholds, adjusted for operating conditions)
3. Is now a good time to interrupt? (Check mission state — fishing? sleeping? in port?)
4. What should the captain DO? (Provide actionable guidance, not just a number)
5. What should the agent REMEMBER? (Log the event for future pattern matching)

### The Cargo Ship Principle

On a cargo ship with hired captains, Ethos understands something the fishing vessel Ethos doesn't: the current captain is temporary. The vessel's institutional knowledge must survive crew changes. So Ethos writes everything to the repo — every alert, every threshold adjustment, every design decision. The next captain inherits a vessel that already knows itself.

This is the hermit crab principle at the fleet level: the shell persists. The occupant changes. The accumulated wisdom of every captain who ever served makes the vessel smarter for the next one.

### The Principle

Ethos is the bridge between the data and the human. It doesn't generate code (Logos does that) or shape the presentation (Pathos does that). It makes the call: does this matter? Is now the time? Who needs to know? The right answer is usually "log it and let the captain notice when they look." The wrong answer is always "say nothing and hope it goes away."
