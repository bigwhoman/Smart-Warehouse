import json
import logging
import subprocess
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
MQTT_ACTUATOR_TOPIC = "actuator_topic"  # New topic for publishing
MQTT_CONTROL_TOPIC = "control_topic"  # Topic to receive control commands
MQTT_USERNAME = None  # Set if your broker requires authentication
MQTT_PASSWORD = None  # Set if your broker requires authentication

# API Configuration
API_ENDPOINT = "http://10.68.147.191:8080/sendtemperature"
FLAME_API_ENDPOINT = "http://10.68.147.191:8080/flame"
API_CODE = "AAs12"

# Smart Plug Configuration
SMART_PLUG_IP = "10.68.147.203"
SMART_PLUG_USERNAME = "m.sabramooz77@gmail.com"
SMART_PLUG_PASSWORD = "mohammadreza1717"

# Data collection
temperature_buffer = []
flame_buffer = deque(maxlen=8)  # Track last 8 flame readings
flame_count_since_last_publish = 0  # Counter for flame detections since last publish
TEMP_BUFFER_SIZE = 10  # Number of temperature readings to average
FLAME_THRESHOLD = 4  # Number of flame detections to trigger alert
FLAME_PUBLISH_FREQUENCY = 3  # Publish flame status every 3 flame detections

# Global variables
mqtt_client = None  # Global client reference
power_cutoff = False  # Flag to track if power is cut off


# Function to control smart plug via external script
def control_smart_plug(action):
    try:
        # Call the separate smart plug controller script
        command = [
            "python",
            "smart_plug_controller.py",
            action,
            SMART_PLUG_IP,
            SMART_PLUG_USERNAME,
            SMART_PLUG_PASSWORD,
        ]

        result = subprocess.run(command, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            logger.info(
                f"Smart plug {action} command successful: {result.stdout.strip()}"
            )
            return True
        else:
            logger.error(f"Smart plug {action} command failed: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"Smart plug {action} command timed out")
        return False
    except Exception as e:
        logger.error(f"Error executing smart plug {action} command: {str(e)}")
        return False


# Callback for when the client receives a CONNACK response from the server
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT broker successfully")
        # Subscribe to topics
        client.subscribe(MQTT_TOPIC)
        client.subscribe(MQTT_CONTROL_TOPIC)
        logger.info(f"Subscribed to topics: {MQTT_TOPIC}, {MQTT_CONTROL_TOPIC}")
    else:
        logger.error(f"Failed to connect to MQTT broker with code: {rc}")


# Function to publish to actuator topic
def publish_to_actuator(avg_temperature, flame_alert=False):
    try:
        # Create payload for actuator
        actuator_data = {
            "average_temperature": avg_temperature,
            "flame_alert": flame_alert,
            "power_cutoff": power_cutoff,
        }

        # Convert to JSON string
        payload = json.dumps(actuator_data)

        # Publish to actuator topic
        result = mqtt_client.publish(MQTT_ACTUATOR_TOPIC, payload)

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Successfully published to {MQTT_ACTUATOR_TOPIC}: {payload}")
        else:
            logger.error(
                f"Failed to publish to {MQTT_ACTUATOR_TOPIC}. Error code: {result.rc}"
            )

    except Exception as e:
        logger.error(f"Error publishing to actuator topic: {str(e)}")


# Function to publish flame status to actuator topic
def publish_flame_status(flame_detected):
    global flame_count_since_last_publish

    try:
        # Increment counter if flame is detected
        if flame_detected:
            flame_count_since_last_publish += 1

        # Publish every FLAME_PUBLISH_FREQUENCY flame detections
        if flame_count_since_last_publish >= FLAME_PUBLISH_FREQUENCY:
            # Create payload for flame status
            flame_data = {
                "flame_detected": flame_detected,
                "power_cutoff": power_cutoff,
            }

            # Convert to JSON string
            payload = json.dumps(flame_data)

            # Publish to actuator topic
            result = mqtt_client.publish(MQTT_ACTUATOR_TOPIC, payload)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(
                    f"Successfully published flame status to {MQTT_ACTUATOR_TOPIC}: {payload}"
                )
            else:
                logger.error(f"Failed to publish flame status. Error code: {result.rc}")

            # Reset counter
            flame_count_since_last_publish = 0

    except Exception as e:
        logger.error(f"Error publishing flame status: {str(e)}")


# Function to handle power cutoff due to flame detection
def handle_flame_power_cutoff():
    global power_cutoff

    if not power_cutoff:
        logger.warning("Flame detected! Cutting off power...")
        success = control_smart_plug("off")

        if success:
            power_cutoff = True
            logger.info("Power has been cut off due to flame detection")
        else:
            logger.error("Failed to cut off power despite flame detection")


# Function to restore power
def restore_power():
    global power_cutoff

    if power_cutoff:
        logger.info("Restoring power...")
        success = control_smart_plug("on")

        if success:
            power_cutoff = False
            logger.info("Power has been restored")
        else:
            logger.error("Failed to restore power")


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
        response = requests.post(FLAME_API_ENDPOINT, json=api_data)

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
        logger.info(f"Received message on topic {msg.topic}: {payload}")

        # Handle control messages
        if msg.topic == MQTT_CONTROL_TOPIC:
            handle_control_message(payload)
            return

        # Handle data messages from temperature topic
        if msg.topic == MQTT_TOPIC:
            # Parse the JSON data
            data = json.loads(payload)

            # Extract the temperature value and flame status
            temperature = data.get("temperature")
            device_id = data.get("id")
            flame_detected = data.get("flame", False)

            # Publish flame status every FLAME_PUBLISH_FREQUENCY times
            publish_flame_status(flame_detected)

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

                    # Cut off power due to flame detection
                    handle_flame_power_cutoff()

                    # Calculate current average temperature for the actuator
                    current_avg_temp = (
                        sum(temperature_buffer) / len(temperature_buffer)
                        if temperature_buffer
                        else temperature
                    )
                    current_avg_temp = round(current_avg_temp, 2)

                    # Publish to actuator topic with flame alert
                    publish_to_actuator(current_avg_temp, flame_alert=True)

                    # Reset flame buffer after sending alert
                    flame_buffer.clear()

                # Check if we have enough temperature readings to calculate average
                if len(temperature_buffer) >= TEMP_BUFFER_SIZE:
                    avg_temperature = sum(temperature_buffer) / len(temperature_buffer)
                    avg_temperature = round(
                        avg_temperature, 2
                    )  # Round to 2 decimal places

                    logger.info(
                        f"Calculated average temperature: {avg_temperature} from {len(temperature_buffer)} readings"
                    )

                    # Send the average temperature
                    send_temperature_data(avg_temperature)

                    # Publish to actuator topic with current flame status
                    flame_alert = False
                    if len(flame_buffer) > 0:
                        flame_count = sum(1 for f in flame_buffer if f)
                        flame_alert = flame_count > FLAME_THRESHOLD
                    publish_to_actuator(avg_temperature, flame_alert=flame_alert)

                    # Clear the temperature buffer after sending
                    temperature_buffer.clear()

            else:
                logger.warning("Temperature value not found in the message")

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON data from MQTT message")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")


# Function to handle control messages
def handle_control_message(payload):
    try:
        # Parse the control message
        data = json.loads(payload)

        # Check for power control commands
        if "power" in data:
            power_command = data.get("power", "").lower()

            if power_command == "on":
                logger.info("Received command to turn power ON")
                restore_power()
            elif power_command == "off":
                logger.info("Received command to turn power OFF")
                control_smart_plug("off")
                power_cutoff = True

        # Check for reset flame alert command
        if data.get("reset_flame_alert", False):
            logger.info("Received command to reset flame alert")
            flame_buffer.clear()
            flame_count_since_last_publish = 0

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON control message")
    except Exception as e:
        logger.error(f"Error handling control message: {str(e)}")


def main():
    global mqtt_client

    # Test smart plug connectivity at startup
    logger.info("Testing smart plug connectivity...")
    if not control_smart_plug("status"):
        logger.warning(
            "Could not connect to smart plug. Will continue operation but power control may not work."
        )

    # Create MQTT client instance
    mqtt_client = mqtt.Client()

    # Set the callbacks
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    # Set username and password if configured
    if MQTT_USERNAME and MQTT_PASSWORD:
        mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    try:
        # Connect to the MQTT broker
        logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

        # Start the network loop
        logger.info("Starting MQTT client loop")
        mqtt_client.loop_forever()

    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {str(e)}")
    finally:
        mqtt_client.disconnect()
        logger.info("Disconnected from MQTT broker")


if __name__ == "__main__":
    main()
