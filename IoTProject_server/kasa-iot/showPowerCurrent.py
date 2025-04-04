import asyncio
from kasa import Discover
import time

async def main():
    dev = await Discover.discover_single("10.118.231.203", username="m.sabramooz77@gmail.com", password="mohammadreza1717")
    await dev.turn_on()
    await dev.update()

    return dev


async def printPowerConsumption(dev):
    while True:
        realtime_data = dev.emeter_realtime
        print(realtime_data["current"])
        await dev.update()
        time.sleep(1)



async def main_wrapper():
    dev = await main()
    await printPowerConsumption(dev)


asyncio.run(main_wrapper())  # Only one `asyncio.run()`
