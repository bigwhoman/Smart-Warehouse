import asyncio
import json
import time

import requests
from kasa import Discover


# find ip using kasa discover
async def discover_device():
    dev = await Discover.discover_single(
        "10.68.147.203",
        username="m.sabramooz77@gmail.com",
        password="mohammadreza1717",
    )
    await dev.turn_on()
    await dev.update()
    return dev


async def PowerConsumption(dev):
    timer = 0
    total_energy = 0
    while True:
        realtime_data = dev.emeter_realtime
        current = realtime_data["current"]
        power = 110.0 * current
        energy = power / 3600
        total_energy = total_energy + energy
        await dev.update()
        await asyncio.sleep(
            1
        )  # Using asyncio.sleep instead of time.sleep in async function
        timer = timer + 1
        if timer == 10:
            # Send to server
            try:
                payload = {"code": "AAs12", "energy": total_energy}
                response = requests.post(
                    "http://10.68.147.191:8080/sendenergy", json=payload
                )
                print(f"Data sent to server: {payload}")
                print(f"Server response: {response.status_code}")
            except Exception as e:
                print(f"Error sending data to server: {e}")

            timer = 0
            print(f"Total energy: {total_energy}")
            total_energy = 0


async def main_wrapper():
    dev = await discover_device()
    await PowerConsumption(dev)


if __name__ == "__main__":
    asyncio.run(main_wrapper())  # Only one `asyncio.run()`
