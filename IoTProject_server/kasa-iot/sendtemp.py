import json
import logging
import time
from collections import deque

import paho.mqtt.client as mqtt
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("temperature_monitor.log"), logging.StreamHandler()],
)
logger = logging.getLogger("temperature_monitor")

# MQTT Configuration
MQTT_BROKER = "localhost"  # Change to your MQTT broker address
MQTT_PORT = 1883
MQTT_TOPIC = "chomp_topic"
MQTT_USERNAME = None  # Set if your broker requires authentication
MQTT_PASSWORD = None  # Set if your broker requires authentication

# API Configuration
API_ENDPOINT = "http://10.118.231.191:8080/sendtemperature"
API_CODE = "AAs12"

# Data collection
temperature_buffer = []
flame_buffer = deque(maxlen=8)  # Track last 8 flame readings
TEMP_BUFFER_SIZE = 10  # Number of temperature readings to average
FLAME_THRESHOLD = 4  # Number of flame detections to trigger alert


# Callback for when the client receives a CONNACK response from the server
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT broker successfully")
        # Subscribe to the temperature topic
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        logger.error(f"Failed to connect to MQTT broker with code: {rc}")


# Function to send temperature data to API
def send_temperature_data(temperature):
    try:
        # Prepare the data to send to the API
        api_data = {"code": API_CODE, "temperature": temperature}

        # Send the data to the API
        response = requests.post(API_ENDPOINT, json=api_data)

        # Check the response
        if response.status_code == 200:
            logger.info(
                f"Successfully sent average temperature data ({temperature}) to API: {response.text}"
            )
        else:
            logger.error(
                f"Failed to send data. Status code: {response.status_code}, Response: {response.text}"
            )

    except requests.RequestException as e:
        logger.error(f"Request error when sending data to API: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")


# Function to send flame alert
def send_flame_alert():
    try:
        # Prepare the data to send flame alert
        api_data = {"code": API_CODE, "alert": "flame_up"}

        # For this example, we'll use the same endpoint
        # In a real application, you might have a different endpoint for alerts
        response = requests.post(API_ENDPOINT, json=api_data)

        if response.status_code == 200:
            logger.info(f"Successfully sent flame alert to API: {response.text}")
        else:
            logger.error(
                f"Failed to send flame alert. Status code: {response.status_code}, Response: {response.text}"
            )

    except requests.RequestException as e:
        logger.error(f"Request error when sending flame alert: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")


# Callback for when a message is received from the server
def on_message(client, userdata, msg):
    try:
        # Decode the message payload
        payload = msg.payload.decode("utf-8")
        logger.info(f"Received message: {payload}")

        # Parse the JSON data
        data = json.loads(payload)

        # Extract the temperature value and flame status
        temperature = data.get("temperature")
        device_id = data.get("id")
        flame_detected = data.get("flame", False)

        if temperature is not None:
            # Add temperature to buffer
            temperature_buffer.append(temperature)
            logger.info(
                f"Added temperature {temperature} to buffer. Buffer size: {len(temperature_buffer)}/{TEMP_BUFFER_SIZE}"
            )

            # Add flame status to buffer
            flame_buffer.append(flame_detected)
            flame_count = sum(1 for f in flame_buffer if f)
            logger.info(
                f"Flame status: {flame_detected}. Total flames in buffer: {flame_count}/{len(flame_buffer)}"
            )

            # Check if flame threshold is exceeded
            if len(flame_buffer) >= 8 and flame_count > FLAME_THRESHOLD:
                logger.warning(
                    f"FLAME ALERT! {flame_count} flames detected in last {len(flame_buffer)} readings"
                )
                send_flame_alert()
                # Reset flame buffer after sending alert
                flame_buffer.clear()

            # Check if we have enough temperature readings to calculate average
            if len(temperature_buffer) >= TEMP_BUFFER_SIZE:
                avg_temperature = sum(temperature_buffer) / len(temperature_buffer)
                avg_temperature = round(avg_temperature, 2)  # Round to 2 decimal places

                logger.info(
                    f"Calculated average temperature: {avg_temperature} from {len(temperature_buffer)} readings"
                )

                # Send the average temperature
                send_temperature_data(avg_temperature)

                # Clear the temperature buffer after sending
                temperature_buffer.clear()

        else:
            logger.warning("Temperature value not found in the message")

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON data from MQTT message")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")


def main():
    # Create MQTT client instance
    client = mqtt.Client()

    # Set the callbacks
    client.on_connect = on_connect
    client.on_message = on_message

    # Set username and password if configured
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    try:
        # Connect to the MQTT broker
        logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)

        # Start the network loop
        logger.info("Starting MQTT client loop")
        client.loop_forever()

    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {str(e)}")
    finally:
        client.disconnect()
        logger.info("Disconnected from MQTT broker")


if __name__ == "__main__":
    main()
