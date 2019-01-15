from time import sleep
from iot_gh.IoTGreenhouseService import IoTGreenhouseService
from iot_gh.GHTextingService import GHTextingService

TOKEN = "your token here"
last_id = None

ghs = IoTGreenhouseService()
ts = GHTextingService(TOKEN, ghs)

while True:
    lm = ts.last_message
    if lm.id != last_id:
        print(lm.name + "   " + lm.text)
        print()

        last_id = lm.id
    sleep(.5)
