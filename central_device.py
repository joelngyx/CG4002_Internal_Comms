import asyncio
from tokenize import String
import pybricksdev
from bleak import BleakClient
from aioconsole import ainput
from bleak import discover
import time


write_characteristic = "0000dfb1-0000-1000-8000-00805f9b34fb"
# read_characteristic = "0000dfb0-0000-1000-8000-00805f9b34fb"
address = "80:30:DC:D9:1F:A9"
test_string = "2"
encoded_string = test_string.encode()
write_value1 = bytearray([0xA])
write_value2 = bytearray([0xB])

async def main(address):
    # devices = await discover()
    # for i in devices:
    #     print(i)
    async with BleakClient(address) as client:
        if client.is_connected:
            print("Connected")
            await client.write_gatt_char(write_characteristic, write_value1)
            time.sleep(5)
            print("5 seconds have passed!")
            test_var = await client.read_gatt_char(write_characteristic)
            print(test_var)
            # await client.write_gatt_char(write_characteristic, write_value2)
            # a = await client.read_gatt_char(write_characteristic)
            # print(a)
            # await client.disconnect()

            
            

asyncio.run(main(address))
