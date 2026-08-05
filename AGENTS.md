# AGENTS.md — Engine Ensign

## What This Is

Engine Ensign is a git-native agent repo for ESP32-based marine engine monitoring. The application IS the concept of "an ESP32 displaying engine sensor data on a screen" — but the agent lives in the repo alongside the firmware it writes.

## Architecture (4 Layers)

1. **Firmware** (`firmware/`) — Real C code for ESP32, one directory per engine/sensor/display combo
2. **Dashboards** (`dashboards/`) — JSON configs defining screen layouts (not hardcoded)
3. **Agent** (`agent/`) — Identity, memory, maintenance log, design decisions, preferences, alert history
4. **Tripartite** (`tripartite/`) — Pathos (presentation), Logos (firmware math), Ethos (escalation/trust)

## Key Files

- `agent/identity.md` — Who the agent IS (written as if running for months)
- `agent/design_decisions.md` — WHY each threshold is what it is
- `agent/maintenance_log.md` — The ship's engine maintenance history
- `agent/preferences.md` — What the captain likes
- `agent/alerts/history.md` — Every alert ever raised and what was learned
- `agent/configurations/registry.md` — Memory of every firmware config generated

## Tools

- `tools/generate_config.py` — Generate new firmware configs from specs
- `tools/dashboard_designer.py` — Modify dashboard layouts programmatically

## Building

```bash
cd firmware/yanmar_4lh-ste
pio run          # build
pio run -t upload # flash
pio device monitor # serial monitor (115200 baud)
```

## Serial Protocol

The ESP32 exposes a text interface over USB serial:
- `STATUS` — all sensor values as JSON
- `ALERTS` — current alert state
- `CONFIG` — threshold configuration
- `MODE DAY` / `MODE NIGHT` — display mode
- `ACK` — acknowledge current alert
- `QUIET` — silence buzzer for 5 minutes

## Agent Conventions

- Thresholds are never arbitrary — each has a `design_decisions.md` entry
- Alerts must be RPM-gated (no oil pressure alerts at engine-off)
- One beep, not a klaxon (see `tripartite/pathos.md`)
- Trust scoring per sensor (see `tripartite/ethos.md`)
- All dashboard changes should be validated (`tools/dashboard_designer.py --validate`)

## Philosophy

The ESP32 is the holo-emitter. The agent is the Doctor. The repo is sickbay.
See `PHILOSOPHY.md` for the full vision.
