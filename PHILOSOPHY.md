# Philosophy: The Doctor Lives in the Repo

*The ESP32 is the tricorder. The repo is sickbay. The agent is the Doctor.*

---

An ESP32 is strong enough to read engine sensors and display them on a screen. That's what it does today — alone, in a loop: read pin, update display, repeat. No memory between loops. No context across sessions. No understanding of what the numbers mean.

Give that ESP32's I/O to an agent with a workspace, and the ESP32 becomes a tricorder. The agent doesn't run on the ESP32 — the ESP32 can't run a language model. The agent runs in the cloud, or on the laptop, or wherever it lives. But the ESP32 is its hands and eyes. The agent reads the sensor data through the ESP32's API, interprets it, raises alerts, logs trends, and — critically — remembers.

## The EMH Parallel

The EMH on Star Trek: Voyager is a holographic program. It runs on the ship's computer. Its hands and eyes are the holographic emitters in sickbay. When the emitters are off, the Doctor still exists — as a program, dormant, in the computer's memory. When the emitters turn on, he's there. Working.

The Doctor didn't just treat patients. He helped design sickbay. He wrote the medical protocols. He trained the nurse. He knew the ship's medical history because he WAS the ship's medical history.

Our agent is the same. The agent that monitors engine sensors lives in this repo, which contains:

- The firmware that runs on the ESP32
- The dashboard layout specification
- The alert threshold configuration
- The maintenance schedule
- The history of every alert ever raised
- The design decisions that explain why each threshold is what it is

The agent isn't a separate thing that looks at the repo. The agent IS the repo, animated.

## Same Data, Different Dimension

A temperature reading of 95°C means nothing to the ESP32. It displays "95" and moves on. But the agent that lives in the repo knows:

- 95°C is 5 degrees above the normal operating range
- The last time it hit 95°C was three weeks ago, and it was a failed thermostat
- The thermostat was replaced with part #XYZ from the maintenance log
- The engine has 340 hours since last service
- The captain's preference is to shut down at 90°C, not 95°C

The ESP32 displays a number. The agent tells a story. Same data, different dimension.

## Every Device Is a Station

This generalizes to every device with I/O:

- **ESP32 + engine sensors** = engine room station
- **Raspberry Pi + camera** = lookout station
- **Phone + GPS** = chartplotter station
- **Weather station + API** = meteorology station
- **Bilge pump + float switch** = damage control station

Each device is a tricorder for a different ensign. Each ensign lives in a repo. The repo IS the ensign.

---

*Adapted from "The Doctor Lives in the Repo" by Casey DiGennaro.*
