#import requests
from time import sleep

import asyncio
from db.mongo_client import DBClient
from optimisation.algorithm import (
    TICK_LENGTH,
    get_sun_energy,
    load_policy_network_checkpoint,
    predict,
)
from optimisation.utils.gen_utils import get_ema
from optimisation.gen_data import getDayData, getTickData
from optimisation.models import Day, Tick
import time

from pymongo import MongoClient
from mqtt_client import MClient, Device
from external.parallel_get import get_day_and_tick
from external.sync import sync_with_server
from utils import print_preaction, print_postaction
# from models import AlgoDecisions

mqtt_client: MClient | None = None

# reduce this time if internet is slow
WAIT = 4.5
SCALE = 0.2


# ALGORITHM SETUP
filename = (
    "optimisation/checkpoints/06_e5000_r50_am2_rm0_im10_sta20_abs1_tre1.pth"
)
policy_network, min, min_epoch = load_policy_network_checkpoint(filename)

env = {"flywheel_amt": 0, "deferables": None, "history": []}
history = []
daily_costs = []
overall_cost = 0

# CONTROL VARIABLES
RUN_BROKER = True
RUN_ALGO = True
DB_LOG = True

setpoint = 0.3
prev_tick = None
prev_day = None
prev_actions = None


if __name__ == "__main__":
    if DB_LOG:
        db_client = DBClient()

    if RUN_BROKER:
        mqtt_client = MClient()

    # Sync with external server
    day, tick = get_day_and_tick(None, TICK_LENGTH)
    tmp_day, tick = sync_with_server(tick.tick, TICK_LENGTH)

    if tmp_day != None: day = tmp_day

    while True:
        # this is the start of the next tick
        start = time.time()

        if tmp_day != None: print(f"Day: {day.day}")

        if day and not env["deferables"] or tick.tick == 0:
            # print("New day")
            env["deferables"] = day.deferables
            # print(f"Cost for day: {tick.day - 1}: {sum(daily_costs)}")

        # part that runs the start of every new tick
        if RUN_ALGO:
            # print_preaction(tick, env)
            cost, actions = predict(policy_network, env, tick, history)
            # print(f"before: {actions}")
            actions["import_export"] = actions["import_export"] * SCALE
            actions["release_store"] = actions["release_store"] * SCALE * -1 * (0.5)
            actions["allocations"] = [a * SCALE * 0.2 * 0.5 for a in actions["allocations"]]
            # print(f"after: {actions}")

            # print(f"\n\n\nsending this to storage {actions['release_store']}\n\n\n")

            daily_costs.append(cost)
            # print_postaction(actions, tick, cost)



        # send data to picos
        if RUN_BROKER and mqtt_client != None and mqtt_client.manual == False:
            # divide by to convert to power
            mqtt_client.send_storage_power(actions["release_store"])

            # sending the irradiance
            mqtt_client.send_sun_data(tick.sun)

            tick.demand = tick.demand / (4 * 4)

            # Red is instant deferrable
            mqtt_client.send_load_power(Device.LOADR, tick.demand)

            # 3 extra defferables are grey, yellow, blue
            mqtt_client.send_load_power(Device.LOADB, actions["allocations"][0])
            mqtt_client.send_load_power(Device.LOADK, actions["allocations"][1])
            mqtt_client.send_load_power(Device.LOADY, actions["allocations"][2])

        # print(list(mqtt_client.db_data.keys()), len(list(mqtt_client.db_data.keys())))

        # add data to the database for each new day and algorithms decsions
        if DB_LOG and mqtt_client != None and mqtt_client.manual == False:

            # only write the previous tick data
            if prev_tick != None:
                full_tick = mqtt_client.get_full_tick(prev_tick, prev_actions["import_export"], prev_actions["release_store"], prev_actions["allocations"])
                
                try:
                    # calc cost
                    avg_import = mqtt_client._get_avg(prev_import)
                    avg_export = mqtt_client._get_avg(prev_export)
                    cost = avg_import*5*tick.sell_price + avg_export*5*tick.buy_price

                    # print(avg_import, avg_export, cost)

                    # change cost in tick_outcomes
                    if full_tick != None: full_tick.cost = cost
                    print(f"Cost: {cost}")
                except Exception as e:
                    print(f"Failed to calculate cost: {e}")


                if full_tick != None:
                    db_client.insert_tick(full_tick)
                    print(f"Written to db for tick {prev_tick.tick}")
            
            # write data for a new day
            if prev_tick != None and prev_tick.tick == 0:
                db_client.insert_day(prev_day)
            elif prev_day == None:
                db_client.insert_day(day)

            # reset the data stored from previous tick
            prev_import = mqtt_client.db_data["import_power"] if "import_power" in mqtt_client.db_data else [0]
            prev_export = mqtt_client.db_data["export_power"] if "export_power" in mqtt_client.db_data else [0]
            mqtt_client.reset_db_data()

        prev_tick = tick
        prev_day = day
        prev_actions = actions

        # Finds the exact start of the next tick
        delay = time.time() - start
        sleep(WAIT - delay)
        tmp_day, tick = sync_with_server(tick.tick, TICK_LENGTH)
        if tmp_day != None: day = tmp_day
