# Wiring Diagram Generator

## What It Does

The dynamic compiler generates both the firmware code AND the physical wiring diagram from the same config. If you change the config, both update. The twin's wiring IS the human's wiring.

## Output Format

The diagram is generated as:
1. ASCII art (in README.md — viewable on any device)
2. JSON (machine-readable — for the agent to understand)
3. SVG (printable — for the human to take to the boat)

## What It Shows

For each device in the system:
- Physical pin assignments (GPIO numbers, ADC channels)
- Wire colors (standard marine: red=power, black=ground, yellow=data, blue=analog)
- Connector types (Dupont, screw terminal, soldered)
- Power requirements (voltage, current, fuse rating)
- Physical placement suggestions (engine room, helm station, bilge)

## The Twin Principle

The agent's digital twin and the captain's physical boat share one source of truth: the config file. When the captain changes a sensor, the config updates, the firmware regenerates, the diagram redraws, the voice agent learns the new sensor name. One change propagates everywhere. The twin and the boat are always in sync because they're generated from the same specification.
