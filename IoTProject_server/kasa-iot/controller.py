import asyncio
from kasa import SmartPlug
import warnings
# Ignore all DeprecationWarning messages
warnings.filterwarnings("ignore", category=DeprecationWarning)
from kasa import Discover


async def main():
    dev = await Discover.discover_single("10.118.231.203", username="m.sabramooz77@gmail.com", password="mohammadreza1717")
    await dev.turn_on()
    await dev.update()

    return dev

async def turnOff(dev):
    await dev.turn_off()
    await dev.update()
    print("Device turned off.")

async def turnOn(dev):
    await dev.turn_on()

    await dev.update()
    print("Device turned on.")

async def interactive_control(dev):
    while True:
        realtime_data = dev.emeter_realtime
        print(realtime_data)
        await dev.update()
        x = await asyncio.to_thread(input, "Enter 'o' to turn on, 'f' to turn off, 'q' to quit: ")
        if x == "f":
            await turnOff(dev)
        elif x == "o":
            await turnOn(dev)
        elif x == "q":
            print("Exiting...")
            break

async def main_wrapper():
    dev = await main()
    await interactive_control(dev)





asyncio.run(main_wrapper())  # Only one `asyncio.run()`
