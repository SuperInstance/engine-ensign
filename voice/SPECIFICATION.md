# Voice Agent Specification

## The Ship's Voice

The Jetson is the ship's voice. It speaks the crew's chosen voice. It listens anywhere on the boat.

### Hardware
- NVIDIA Jetson Orin NX (or Nano for smaller vessels)
- USB microphone (waterproof, noise-canceling)
- Marine speaker system (connected via 3.5mm or I2S amplifier)
- WiFi (connects to vessel router)

### Software Stack
```
Microphone → wake_word_detector (Porcupine/Picovoice)
         → STT (whisper-small or vosk)
         → intent_parser (rule-based + optional LLM)
         → MQTT query to ESP32
         → MQTT response from ESP32
         → response_formatter (templated natural language)
         → TTS (piper-tts or coqui or elevenlabs)
         → speaker
```

### Wake Word
Default: "Ship" (configurable). The Jetson listens passively for the wake word. When detected:
1. Record audio for 5 seconds (or until silence)
2. STT the recording
3. Parse intent
4. Route to the right device via MQTT
5. Format response in natural language
6. Speak it

### Voice Selection (Pathos Decision)
The voice IS the ship's personality. Pathos selects it based on the vessel's aesthetic:
- Hermit steampunk boat: warm baritone, slight creakiness, uses "Cap" and "old girl"
- Cargo ship: neutral professional, uses "Captain" and vessel name
- Research vessel: precise, scientific, reads numbers with units

### Example Interactions
```
Captain: "Ship, what's the RPM?"
Ship:    "RPMs are eighteen-fifty, Cap. She's running sweet."

Captain: "Ship, how's the fuel?"
Ship:    "Fuel's at seventy-eight percent. About four hours at current burn rate."

Captain: "Ship, anything I should worry about?"
Ship:    "Coolant temp's been creeping up — eighty-two degrees now, 
         was seventy-nine an hour ago. Not dangerous yet, but worth 
         keeping an eye on. Oil pressure's steady at forty-five."

Captain: "Ship, engine temperature?"
Ship:    "Coolant's at eighty-two degrees. Normal range. You're fine, Cap."
```

### The Agent's Role
The voice agent doesn't just read numbers. The agent in the repo:
- Knows the engine's history (340 hours, last service at 300)
- Knows what's normal for THIS engine (this Yanmar usually runs 79-84°C)
- Knows the captain's preferences (Casey wants to know about trends, not just current values)
- Formats responses in the crew's voice and vocabulary
