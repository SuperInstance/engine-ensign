# Vessel MQTT Protocol

## Agent-to-Agent Communication

All devices on the vessel communicate over WiFi using MQTT. No cloud required.

### Broker
The Jetson runs an MQTT broker (mosquitto) on port 1883. All ESP32 devices connect as clients.

### Topics

```
vessel/engine/sensors        → ESP32 publishes sensor data (JSON, 1-5 Hz)
vessel/engine/alerts         → ESP32 publishes alerts (JSON, event-driven)
vessel/nav/sensors           → Nav ESP32 publishes GPS/depth/heading
vessel/voice/query           → Jetson publishes queries to ESP32s
vessel/voice/response        → ESP32s publish responses to Jetson
vessel/voice/speak           → Jetson publishes TTS output events
vessel/system/discovery      → New devices announce themselves on connect
vessel/system/status         → All devices heartbeat every 30s
```

### Message Formats

```json
// vessel/engine/sensors
{
  "device": "esp32_engine_1",
  "rpm": 1850,
  "coolant_c": 82,
  "oil_psi": 45,
  "fuel_pct": 78,
  "boost_psi": 4.5,
  "voltage": 12.4,
  "hours": 340,
  "timestamp": 1234567890
}

// vessel/voice/query
{
  "from": "jetson_voice",
  "query": "engine status",
  "target": "esp32_engine_1",
  "timestamp": 1234567890
}

// vessel/voice/response  
{
  "from": "esp32_engine_1",
  "summary": "all normal",
  "rpm": 1850,
  "coolant_c": 82,
  "oil_psi": 45,
  "timestamp": 1234567890
}
```

### Discovery

When a new ESP32 boots, it publishes to `vessel/system/discovery`:
```json
{
  "device": "esp32_engine_2",
  "type": "engine_monitor",
  "engine": "cummins_6bta",
  "sensors": ["rpm", "coolant", "oil", "fuel"],
  "display": "3.5_oled",
  "ip": "192.168.1.45"
}
```

The Jetson receives this, the agent logs it, and the dynamic compiler generates appropriate wiring config.
