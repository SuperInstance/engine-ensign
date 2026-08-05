# Engine Ensign

*The ESP32 is the holo-emitter. The agent is the Doctor. The repo is sickbay.*

---

Engine Ensign is a git-native agent repo for ESP32-based marine engine monitoring. The application IS the concept of "an ESP32 displaying engine sensor data on a screen" — but the agent lives in the repo alongside the firmware it writes. It doesn't just run code. It remembers why the code exists.

## The Architecture

Four layers, each with a distinct role:

```
┌──────────────────────────────────────────────────────┐
│                    THE AGENT                         │
│    Identity · Memory · Design Decisions · History    │
│    (the Doctor — lives in the repo, animated)        │
├────────────┬────────────────────┬────────────────────┤
│  FIRMWARE  │   DASHBOARDS       │   TRIPARTITE       │
│  (driver)  │   (presentation)   │   (interface)      │
│            │                    │                    │
│  C code    │  JSON configs      │  Pathos/Logos/Ethos│
│  for ESP32 │  screen layouts    │  decision framework│
│            │                    │                    │
│  Reads     │  Renders           │  Reasons           │
│  sensors   │  the display       │  about both        │
├────────────┴────────────────────┴────────────────────┤
│                                                      │
│              HARDWARE (the ship)                     │
│                                                      │
│  ESP32 ← sensors (NMEA2000, analog, temp senders)   │
│    ↓                                                 │
│  Display (TFT / OLED / LCD / IPS)                    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Layer 1: Firmware (the driver)

Real C code that compiles with PlatformIO for ESP32. Each configuration targets a specific engine/sensor/screen combination:

| Config | Engine | Sensors | Display |
|--------|--------|---------|---------|
| `firmware/yanmar_4lh-ste/` | Yanmar 4LH-STE | 6× NMEA2000 | 7" TFT |
| `firmware/cummins_6bta/` | Cummins 6BTA | Analog + temp senders | 3.5" OLED |
| `firmware/generic_diesel/` | Generic diesel | RPM + temp + oil pressure | 2.4" LCD |
| `firmware/dual_outboard/` | Twin outboard | NMEA2000 network | 5" IPS |

Each firmware config contains `main.c`, `sensors.h`, `display.h`, `config.h`, `platformio.ini`, and a `README.md` with wiring guide.

### Layer 2: Dashboards (the presentation)

Screen layouts are JSON configs — not hardcoded. The agent can modify what appears on screen by editing a dashboard file:

```json
{
  "gauge": {
    "type": "analog_dial",
    "label": "RPM",
    "data_source": "engine.rpm",
    "position": { "x": 120, "y": 160 },
    "radius": 80,
    "min": 0, "max": 4000,
    "redline": 3400,
    "color": "white"
  }
}
```

### Layer 3: The Agent (the Doctor)

The agent layer is what makes this more than a microcontroller project. It's a crew member:

- `agent/identity.md` — who the agent IS, its vessel, its history
- `agent/configurations/` — memory of every config generated
- `agent/alerts/` — history of alerts raised and resolved
- `agent/maintenance_log.md` — the ship's engine maintenance history
- `agent/preferences.md` — what the captain likes
- `agent/design_decisions.md` — WHY each threshold is what it is

### Layer 4: The Tripartite Interface

Three faculties govern how the agent interacts with the system:

| Faculty | Layer | Role |
|---------|-------|------|
| **Pathos** | Presentation | How the dashboard *feels*. Colors, sounds, urgency. |
| **Logos** | Firmware | How the driver *works*. Math, calibration, timing. |
| **Ethos** | Business | *Whether* to act. Trust, escalation, judgment. |

## Tools

### `tools/generate_config.py`

Generates a new firmware configuration from a specification:

```bash
python tools/generate_config.py \
  --engine "perkins_6354" \
  --sensors "rpm:inductive,temp:thermistor,oil:analog_0-5v,volt:analog_0-5v" \
  --display "3.5inch_tft_ili9488" \
  --platform "esp32" \
  --output firmware/perkins_6354/
```

### `tools/dashboard_designer.py`

Modifies dashboard layouts programmatically:

```bash
# List available dashboards
python tools/dashboard_designer.py --list

# Swap gauge positions
python tools/dashboard_designer.py --dashboard yanmar_7inch_tft --swap rpm oil_temp

# Set day/night theme
python tools/dashboard_designer.py --dashboard yanmar_7inch_tft --theme night

# Add a new gauge
python tools/dashboard_designer.py --dashboard yanmar_7inch_tft --add-gauge '{"type":"bar","label":"Boost","data_source":"engine.boost","x":200,"y":300}'
```

## Building

### Prerequisites

- [PlatformIO Core](https://platformio.org/install) installed
- ESP32 development board
- USB cable for flashing

### Build a configuration

```bash
cd firmware/yanmar_4lh-ste
pio run          # build
pio run -t upload # flash to ESP32
pio device monitor # serial monitor
```

### Wire it up

See each firmware config's `README.md` for the wiring diagram specific to that engine/sensor/screen combination.

## The Key Insight

The firmware and the dashboard are BOTH dynamic. The agent can:

1. Change alert thresholds based on learned engine behavior
2. Reconfigure the dashboard based on what the captain actually looks at
3. Generate new firmware configs for new engine/sensor/screen combos
4. Remember every alert and what caused it
5. Learn which sensors are noisy and which are reliable

A temperature reading of 95°C means nothing to the ESP32. It displays "95" and moves on. But the agent that lives in this repo knows:

- 95°C is 5° above the normal operating range for this engine
- The last time it hit 95°C was three weeks ago — failed thermostat
- The thermostat was replaced with part #XYZ (see maintenance log)
- The engine has 340 hours since last service
- The captain's preference is to shut down at 90°C, not 95°C

The ESP32 displays a number. The agent tells a story. Same data, different dimension.

## Philosophy

This repo is a *sickbay*. The agent is the EMH — the Emergency Medical Hologram. It runs on the ship's computer (the cloud, a laptop, wherever). The ESP32 is the holo-emitter — its hands and eyes in the engine room. When the ESP32 sends data, it's the agent feeling its own fingers. When the dashboard updates, it's the agent speaking.

The agent that monitors the engines today is the same agent that helped design the monitoring system. It knows why threshold X is set to value Y because it was in the room when that decision was made.

For the full vision, see [THE DOCTOR LIVES IN THE_REPO](https://github.com/SuperInstance/engine-ensign/blob/main/PHILOSOPHY.md).

## License

MIT — see [LICENSE](LICENSE).
