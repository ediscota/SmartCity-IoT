import paho.mqtt.client as mqtt
import random
import time
import configparser
import threading
import json
import os
from collections import deque

config = configparser.ConfigParser()
config.read('config.ini')

# If 'MQTT_BROKER' env exists (Docker), use it. Otherwise use config.ini.
broker_env = os.getenv('MQTT_BROKER')
client_address = broker_env if broker_env else config['mqtt']['client_address']
port = int(config['mqtt']['port'])
mqtt_user = os.getenv('MQTT_USER')
mqtt_password = os.getenv('MQTT_PASSWORD')
sensor_list = config['data_generation']['sensors'].split('|')

# Districts -> streets mapping
district_names = config['data_generation']['districts'].split('|')
city_map = {}

for d in district_names:
    section = f"district_{d}"
    if section in config:
        streets = config[section]['streets'].split('|')
        city_map[d] = streets
    else:
        print(f"Warning: Section [{section}] not found in config.ini")

# Global variable for dynamic config (shared by all threads)
global_settings = {
    "time_sleep": float(config['data_generation']['time_sleep'])
}

mqtt_client = mqtt.Client()
#Resilience structures 
offline_queue = deque()
is_connected = False

#Configure Authentication if credentials exist
if mqtt_user and mqtt_password:
    mqtt_client.username_pw_set(mqtt_user, mqtt_password)
    print(f"Auth configured for user: {mqtt_user}")

if mqtt_user and mqtt_password:
    mqtt_client.username_pw_set(mqtt_user, mqtt_password)
    print(f"Auth configured for user: {mqtt_user}")

def on_connect(client, userdata, flags, rc):
    global is_connected
    if rc == 0:
        is_connected = True
        print(f"Connected to Broker at {client_address}")
        client.subscribe("smartcity/config")

        if offline_queue:
            print(f"Flushing {len(offline_queue)} buffered messages...")
            while offline_queue:
                topic, payload = offline_queue.popleft()
                client.publish(topic, json.dumps(payload))
    else:
        print(f"Failed to connect, return code {rc}")

def on_disconnect(client, userdata, rc):
    global is_connected
    is_connected = False
    print("Disconnected from MQTT broker, buffering messages...")

#Handles dynamic configuration from MQTT Explorer. Expected payload: {"time_sleep": 1}
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if "time_sleep" in payload:
            new_time = float(payload["time_sleep"])
            global_settings["time_sleep"] = new_time
            print(f"!!! CONFIG UPDATED: Sleep time set to {new_time}s !!!")
    except Exception as e:
        print(f"Error parsing config: {e}")

#Guarantees RESILIENCE by buffering messages when offline
def safe_publish(topic, payload):
    """
    Publishes if connected, otherwise buffers the message.
    """
    if is_connected:
        mqtt_client.publish(topic, json.dumps(payload))
    else:
        offline_queue.append((topic, payload))
        print(f"Buffered (offline): {topic}")

#Guarantees RESILIENCE by trying to reconnect every 5 seconds
def reconnect_and_flush():
    while True:
        if not is_connected:
            try:
                print("Trying to reconnect to MQTT broker...")
                mqtt_client.reconnect()
            except:
                pass
        time.sleep(5)

mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_message = on_message
mqtt_client.connect(client_address, port=port)
mqtt_client.loop_start()
threading.Thread(target=reconnect_and_flush, daemon=True).start()

#Simulation Function
def publish_street_data(mqtt_client, sensor_list, district, street):
    """
    Simulates one street with multiple sensors.
    """
    while True:
        for sensor in sensor_list:
            data = 0
            unit = ""

            if sensor == 'temperature':
                data = round(random.uniform(15, 35), 2)
                unit = "C"
            elif sensor == 'humidity':
                data = round(random.uniform(30, 70), 2)
                unit = "%"
            elif sensor == 'noise':
                data = round(random.uniform(40, 90), 2)
                unit = "dB"
            elif sensor == 'traffic':
                data = random.randint(0, 80)
                unit = "km/h"
            elif sensor == 'pm25':
                data = round(random.uniform(5, 80), 2)
                unit = "ug/m3"
            elif sensor == 'pm10':
                data = round(random.uniform(10, 150), 2)
                unit = "ug/m3"
            elif sensor == 'co':
                data = round(random.uniform(0.1, 5.0), 2)
                unit = "ppm"
            elif sensor == 'no2':
                data = round(random.uniform(5, 200), 2)
                unit = "ppb"
            elif sensor == 'o3':
                data = round(random.uniform(10, 180), 2)
                unit = "ppb"

            #Topic with structure: smartcity/district/street/sensor
            topic = f"smartcity/{district}/{street}/{sensor}"

            payload = {
                "value": data,
                "unit": unit,
                "timestamp": time.time()
            }

            safe_publish(topic, payload)
            print(f"[{topic}] {data} {unit}")

        time.sleep(global_settings["time_sleep"])


#Thread Management
threads = []
print("Starting simulation with custom city map:")
for d, streets in city_map.items():
    print(f"  {d}: {len(streets)} streets")

for district, streets in city_map.items():
    for street in streets:
        thread = threading.Thread(
            target=publish_street_data,
            args=(mqtt_client, sensor_list, district, street)
        )
        threads.append(thread)
        thread.start()

#Keep main script alive
try:
    for thread in threads:
        thread.join()
except KeyboardInterrupt:
    print("Stopping simulation...")
    mqtt_client.loop_stop()
    mqtt_client.disconnect()