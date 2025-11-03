# 🐦 Bird Scream Detector – Home Assistant Add-on

Detects loud bird screeches/screams from a UniFi (or other RTSP) camera feed using AI (YAMNet),
and publishes events to Home Assistant via MQTT.

Each detection increments a counter in HA, so you can track how many times your bird screamed today.

---

## 🔧 Features
- Connects to RTSP audio feed via `ffmpeg`
- Uses Google’s YAMNet audio classifier
- Publishes to MQTT (topic: `home/bird_scream/detected`)
- Lightweight Docker add-on — runs on amd64 or arm64
- Configurable thresholds and debounce

---

## 🐳 Installation

1. In Home Assistant, go to **Settings → Add-ons → Add-on store → ⋮ (three dots) → Repositories**
2. Add this repository URL:
   ```
   https://github.com/YOUR_USERNAME/home-assistant-bird-scream-detector
   ```
3. The **Bird Scream Detector** add-on will appear. Click **Install**.
4. Configure:
   - RTSP URL
   - MQTT broker & topic
   - Detection thresholds
5. Start the add-on. Logs will show detections as they occur.

---

## 🧠 Home Assistant setup

In `configuration.yaml`:

```yaml
counter:
  bird_screams:
    name: Bird Screams Today
    initial: 0

automation:
  - alias: Increment Bird Scream Counter
    trigger:
      - platform: mqtt
        topic: home/bird_scream/detected
    action:
      - service: counter.increment
        target:
          entity_id: counter.bird_screams

  - alias: Reset Bird Screams at Midnight
    trigger:
      - platform: time
        at: "00:00:00"
    action:
      - service: counter.reset
        target:
          entity_id: counter.bird_screams
```

---

## 🧩 Options

| Option | Description | Default |
|--------|--------------|----------|
| `rtsp_url` | Camera RTSP stream URL | `""` |
| `mqtt_broker` | MQTT broker hostname/IP | `"homeassistant.local"` |
| `mqtt_port` | MQTT port | `1883` |
| `mqtt_topic` | MQTT topic for detections | `"home/bird_scream/detected"` |
| `score_threshold` | YAMNet detection score threshold | `0.35` |
| `min_seconds_between_events` | Debounce between detections | `10` |
