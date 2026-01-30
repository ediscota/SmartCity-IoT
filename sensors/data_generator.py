import paho.mqtt.client as mqtt
import random
import time
import configparser
import threading
import json
import os
from collections import deque

# Config
config = configparser.ConfigParser()
config.read('config.ini')

broker_env = os.getenv('MQTT_BROKER')
client_address = broker_env if broker_env else config['mqtt']['client_address']
port = int(config['mqtt']['port'])

mqtt_user = os.getenv('MQTT_USER')
mqtt_password = os.getenv('MQTT_PASSWORD')

sensor_list = config['data_generation']['sensors'].split('|')
district_names = config['data_generation']['districts'].split('|')

# Build city map from configuration: district -> list of streets
city_map = {}
for d in district_names:
    section = f"district_{d}"
    if section in config:
        city_map[d] = config[section]['streets'].split('|')

global_settings = {
    "time_sleep": float(config['data_generation']['time_sleep'])
}

# MQTT 
mqtt_client = mqtt.Client()
offline_queue = deque()
is_connected = False
lock = threading.Lock()

if mqtt_user and mqtt_password:
    mqtt_client.username_pw_set(mqtt_user, mqtt_password)

def on_connect(client, userdata, flags, rc):
    global is_connected
    if rc == 0:
        print(f"Connected to MQTT broker at {client_address}")
        is_connected = True
        client.subscribe("smartcity/config")

        # Flush buffered messages after successful reconnection (resilience)
        with lock:
            while offline_queue:
                topic, payload = offline_queue.popleft()
                client.publish(topic, json.dumps(payload))
            print("Offline buffer flushed")

def on_disconnect(client, userdata, rc):
    global is_connected
    is_connected = False
    print("Disconnected from MQTT broker, buffering messages")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if "time_sleep" in payload:
            global_settings["time_sleep"] = float(payload["time_sleep"])
            print(f"Sleep time updated to {global_settings['time_sleep']}s")
    except:
        pass

mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_message = on_message

mqtt_client.connect(client_address, port=port)
mqtt_client.loop_start()

def safe_publish(topic, payload):
    with lock:
        if is_connected:
            mqtt_client.publish(topic, json.dumps(payload))
        else:
            offline_queue.append((topic, payload))
            print(f"Buffered: {topic}")

def reconnect_loop():
    while True:
        if not is_connected:
            try:
                print("Trying to reconnect to MQTT broker...")
                mqtt_client.reconnect()
            except:
                pass
        time.sleep(5)

threading.Thread(target=reconnect_loop, daemon=True).start()

# Sensor Logic
def generate_value(sensor):
    section = f"sensor_{sensor}"
    if section not in config:
        raise ValueError(f"Sensor '{sensor}' not defined in config.ini")

    min_v = float(config[section]['min'])
    max_v = float(config[section]['max'])
    return round(random.uniform(min_v, max_v), 2)

def publish_street_data(district, street):
    while True:
        for sensor in sensor_list:
            value = generate_value(sensor)
            topic = f"smartcity/{district}/{street}/{sensor}"

            payload = {
                "value": value,
                "timestamp": time.time()
            }

            safe_publish(topic, payload)
            print(f"[{topic}] {value}")

        time.sleep(global_settings["time_sleep"])

# Create and start a simulation thread for each street in the city map
for district, streets in city_map.items():
    for street in streets:
        threading.Thread(
            target=publish_street_data,
            args=(district, street),
            daemon=True
        ).start()

# Keep main thread alive while simulation threads are running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping simulation...")
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
