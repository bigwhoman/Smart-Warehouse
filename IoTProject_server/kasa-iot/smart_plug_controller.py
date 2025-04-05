import asyncio
import sys
import warnings

from kasa import Discover, SmartPlug

# Ignore all DeprecationWarning messages
warnings.filterwarnings("ignore", category=DeprecationWarning)


async def control_smart_plug(action, ip, username, password):
    """
    Control a TP-Link Smart Plug

    Args:
        action (str): "on", "off", or "status"
        ip (str): IP address of the smart plug
        username (str): Username for the smart plug
        password (str): Password for the smart plug

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Discover and connect to the device
        device = await Discover.discover_single(
            ip, username=username, password=password
        )
        await device.update()

        # Check what action to take
        if action.lower() == "on":
            await device.turn_on()
            await device.update()
            print(f"Smart plug turned ON. Current state: {device.is_on}")
            return True

        elif action.lower() == "off":
            await device.turn_off()
            await device.update()
            print(f"Smart plug turned OFF. Current state: {device.is_on}")
            return True

        elif action.lower() == "status":
            print(f"Smart plug status: Power is {'ON' if device.is_on else 'OFF'}")
            print(f"Realtime data: {device.emeter_realtime}")
            return True

        else:
            print(f"Unknown action: {action}. Use 'on', 'off', or 'status'")
            return False

    except Exception as e:
        print(f"Error controlling smart plug: {str(e)}", file=sys.stderr)
        return False


if __name__ == "__main__":
    # Check arguments
    if len(sys.argv) != 5:
        print(
            "Usage: python smart_plug_controller.py <action> <ip> <username> <password>"
        )
        print("  action: 'on', 'off', or 'status'")
        sys.exit(1)

    # Get arguments
    action = sys.argv[1]
    ip = sys.argv[2]
    username = sys.argv[3]
    password = sys.argv[4]

    # Run the control function
    success = asyncio.run(control_smart_plug(action, ip, username, password))

    # Exit with appropriate code
    sys.exit(0 if success else 1)
