import json
import logging

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


# Callback for when the client receives a CONNACK response from the server
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT broker successfully")
        # Subscribe to the temperature topic
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        logger.error(f"Failed to connect to MQTT broker with code: {rc}")


# Callback for when a message is received from the server
def on_message(client, userdata, msg):
    try:
        # Decode the message payload
        payload = msg.payload.decode("utf-8")
        logger.info(f"Received message: {payload}")

        # Parse the JSON data
        data = json.loads(payload)

        # Extract the temperature value
        temperature = data.get("temperature")
        device_id = data.get("id")
        flame_detected = data.get("flame", False)

        if temperature is not None:
            # Prepare the data to send to the API
            api_data = {"code": API_CODE, "temperature": temperature}

            # Log additional information
            logger.info(
                f"Device ID: {device_id}, Temperature: {temperature}, Flame Detected: {flame_detected}"
            )

            # Send the data to the API
            response = requests.post(API_ENDPOINT, json=api_data)

            # Check the response
            if response.status_code == 200:
                logger.info(
                    f"Successfully sent temperature data to API: {response.text}"
                )
            else:
                logger.error(
                    f"Failed to send data. Status code: {response.status_code}, Response: {response.text}"
                )
        else:
            logger.warning("Temperature value not found in the message")

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON data from MQTT message")
    except requests.RequestException as e:
        logger.error(f"Request error when sending data to API: {str(e)}")
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
