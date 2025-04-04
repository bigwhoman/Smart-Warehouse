import asyncio
from kasa import Discover
import time
# find ip using kasa discover

async def discover_device():
    dev = await Discover.discover_single("10.118.231.203", username="m.sabramooz77@gmail.com", password="mohammadreza1717")
    await dev.turn_on()
    await dev.update()

    return dev

async def PowerConsumption(dev):
    timer = 0
    total_energy=0
    while True:
        realtime_data = dev.emeter_realtime
        current = (realtime_data["current"])
        power = 110.0 * current
        energy = power / 3600
        total_energy = total_energy + energy
        await dev.update()
        time.sleep(1)
        timer = timer+1
        if timer == 60:
            # Send to server
            timer = 0
            print(total_energy)
            total_energy = 0


async def main_wrapper():
    dev = await discover_device()
    await PowerConsumption(dev)


asyncio.run(main_wrapper())  # Only one `asyncio.run()`


