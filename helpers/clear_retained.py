"""
Quick helper (runs on normal CPython, not MicroPython): subscribes to `#`
(all topics) on the broker from config.dev.json, records every topic a
retained message arrives on, then republishes an empty retained payload
to each one to clear it from the broker.

Usage:
    python helpers/clear_retained.py
"""
import json
import os
import ssl
import time

import paho.mqtt.client as mqtt

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.dev.json")
LISTEN_SECONDS = 5


def load_mqtt_config():
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    return config["mqtt"]


def main():
    mqtt_config = load_mqtt_config()
    seen_topics = set()

    def on_connect(client, userdata, flags, reason_code, properties=None):
        print("connected, reason:", reason_code)
        client.subscribe("#")

    def on_message(client, userdata, msg):
        if msg.retain and msg.topic not in seen_topics:
            seen_topics.add(msg.topic)
            print("retained message found on:", msg.topic)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(mqtt_config["user"], mqtt_config["password"])
    if mqtt_config.get("ssl"):
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(mqtt_config["server"], mqtt_config["port"])
    client.loop_start()

    print(f"listening for {LISTEN_SECONDS}s to collect retained topics...")
    time.sleep(LISTEN_SECONDS)

    print(f"clearing {len(seen_topics)} retained topic(s)...")
    for topic in seen_topics:
        client.publish(topic, payload=None, qos=1, retain=True)
        print("cleared:", topic)

    time.sleep(1)
    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
