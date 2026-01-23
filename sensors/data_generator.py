import paho.mqtt.client as mqtt
import random
import time
import configparser
import threading
import json
import os

config = configparser.ConfigParser()
config.read('config.ini')

# If 'MQTT_BROKER' env exists (Docker), use it. Otherwise use config.ini.
broker_env = os.getenv('MQTT_BROKER')
client_address = broker_env if broker_env else config['mqtt']['client_address']
port = int(config['mqtt']['port'])

districts = int(config['data_generation']['districts'])
streets = int(config['data_generation']['streets'])
sensor_list = config['data_generation']['sensors'].split('|')

# Global variable for dynamic config (shared by all threads)
global_settings = {
    "time_sleep": int(config['data_generation']['time_sleep'])
}

mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to Broker at {client_address}")
        # Subscribe to a global config topic
        # MQTT Explorer can publish to this topic to change behavior
        client.subscribe("smartcity/config")
    else:
        print(f"Failed to connect, return code {rc}")

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

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(client_address, port=port)

# Start the network loop in a separate thread so it doesn't block simulation
mqtt_client.loop_start()

# --- Simulation Function ---
def publish_street_data(mqtt_client, sensor_list, district, street):
    """
    Simulates one street with multiple sensors.
    """
    while True:
        # Generate random sensor data
        for sensor in sensor_list:
            data = 0
            unit = ""
            
            # Smart City Data Logic
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

            
            # Topic Structure: smartcity/district_0/street_1/temperature
            topic = f"smartcity/district_{district}/street_{street}/{sensor}"
            
            # JSON Payload (Required by specs)
            payload = {
                "value": data,
                "unit": unit,
                "timestamp": time.time()
            }
            
            mqtt_client.publish(topic, json.dumps(payload))
            print(f"[{topic}] {data} {unit}")

        # Dynamic Sleep: Reads from the global settings that on_message updates
        time.sleep(global_settings["time_sleep"]) 

# --- Thread Management ---
threads = []
print(f"Starting simulation for {districts} districts and {streets} streets per district...")

for d in range(districts):
    for s in range(streets):
        thread = threading.Thread(
            target=publish_street_data, 
            args=(mqtt_client, sensor_list, d, s)
        )
        threads.append(thread)
        thread.start()

# Keep main script alive
try:
    for thread in threads:
        thread.join()
except KeyboardInterrupt:
    print("Stopping simulation...")
    mqtt_client.loop_stop()
    mqtt_client.disconnect()