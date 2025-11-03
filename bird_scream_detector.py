import json, os, time, subprocess, numpy as np, tensorflow as tf, tensorflow_hub as hub, requests, csv, paho.mqtt.client as mqtt

CONFIG_PATH = "/data/options.json"
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH) as f:
        opts = json.load(f)
else:
    opts = {}

RTSP_URL = opts.get("rtsp_url", os.getenv("RTSP_URL", ""))
MQTT_BROKER = opts.get("mqtt_broker", os.getenv("MQTT_BROKER", "mqtt.local"))
MQTT_PORT = int(opts.get("mqtt_port", os.getenv("MQTT_PORT", 1883)))
MQTT_TOPIC = opts.get("mqtt_topic", os.getenv("MQTT_TOPIC", "home/bird_scream/detected"))
SCORE_THRESHOLD = float(opts.get("score_threshold", os.getenv("SCORE_THRESHOLD", 0.30)))
MIN_SECONDS_BETWEEN_EVENTS = float(opts.get("min_seconds_between_events", os.getenv("MIN_SECONDS_BETWEEN_EVENTS", 10)))

SAMPLE_RATE = 16000
WINDOW_SECONDS = 1.0
CHUNK_BYTES = int(SAMPLE_RATE * WINDOW_SECONDS * 2)
KEYWORDS = ["bird", "screech", "scream", "alarm", "chirp", "squawk"]
YAMNET_CLASS_MAP_URL = "https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv"

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

print("Loading YAMNet model...")
yamnet_model = hub.load("https://tfhub.dev/google/yamnet/1")

r = requests.get(YAMNET_CLASS_MAP_URL)
classes = [row[1] for row in csv.reader(r.text.splitlines()) if row and row[0] != "mid"]
target_indices = [i for i, name in enumerate(classes) if any(k in name.lower() for k in KEYWORDS)]

def publish_event(score, match):
    import json
    client.publish(MQTT_TOPIC, json.dumps({"timestamp": time.time(), "score": score, "match": match}))
    print(f"Published MQTT event: {match} ({score:.3f})")

def main():
    cmd = ["ffmpeg", "-rtsp_transport", "tcp", "-i", RTSP_URL, "-vn", "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "s16le", "-hide_banner", "-loglevel", "error", "pipe:1"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10**7)
    last_time = 0
    while True:
        raw = p.stdout.read(CHUNK_BYTES)
        if len(raw) < CHUNK_BYTES:
            continue
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        scores, _, _ = yamnet_model(audio)
        scores = scores.numpy().mean(axis=0)
        sub = scores[target_indices]
        i = np.argmax(sub)
        if sub[i] >= SCORE_THRESHOLD and time.time() - last_time >= MIN_SECONDS_BETWEEN_EVENTS:
            last_time = time.time()
            publish_event(float(sub[i]), classes[target_indices[i]])

if __name__ == "__main__":
    main()
