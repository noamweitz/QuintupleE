from copy import deepcopy

import requests
import time
import pymongo
import asyncio

url = "http://127.0.0.1:5000"


def get_data(endpoint):
    response = requests.get(url + endpoint)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Request failed with status code:", response.status_code)


MONGO_CONN_STRING = "mongodb+srv://smartgrid_user:OzVu9hnKiaJULToP@autodocs.kwrryjv.mongodb.net/?retryWrites=true&w=majority&appName=Autodocs"
db = "smartgrid"

mongoCli = pymongo.MongoClient(MONGO_CONN_STRING)
db = mongoCli["smartgrid"]


async def insert_tick(tick_data):
    collection = db["ticks"]
    collection.insert_many(ticks)
    print("Inserted ticks for: ", tick_data[0]["day"])


async def insert_day(day_data):
    collection = db["days"]
    collection.insert_one(day_data)
    print("Inserted day", day_data["day"])


# To store in the database
# Each tick: {"day": day, "tick": tick, "sun": sun, "buy_price": buy_price, "sell_price": sell_price, "demand": demand}

prev_tick = None
count = 0
ticks = []

all = get_data("/all")
asyncio.run(insert_day(deepcopy({"day": all["day"], "deferables": all["deferables"]})))
prev_day = all["day"]
prev_tick = all["tick"]

while True:
    all = get_data("/all")
    day = all["day"]
    tick = all["tick"]

    if day == prev_day and all["tick"] == prev_tick:
        continue

    # print("Day:", day, "Tick:", tick)

    prev_tick = tick
    tick_data = deepcopy(all)
    tick_data.pop("deferables")
    ticks.append(tick_data)

    if prev_day != day:
        # Insert ticks for that day
        asyncio.run(insert_tick(deepcopy(ticks)))

        # Insert new day
        day_data = {"day": day, "deferables": all["deferables"]}
        asyncio.run(insert_day(deepcopy(day_data)))
        # print("New day:", day)

        prev_day = day
        ticks = []

    time.sleep(0.1)  # Delay for 1 second

    # sun_data = get_data("/sun")
    # price_data = get_data("/price")
    # inst_demand = get_data("/demand")  # {"day": day, "tick": tick, "demand": demand}

    # # Process sun data
    # sun = sun_data["sun"]

    # # Process price data
    # cur_day = price_data["day"]
    # if prev_day != cur_day:
    #     def_demand = get_data(
    #         "/deferables"
    #     )  # [{"start": start, "end": end, "energy": energy}]

    #     print("New day:", cur_day)
    #     print(def_demand)
    #     prev_day = cur_day

    # Process price data
