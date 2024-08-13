from copy import deepcopy
from random import randint
import sys

import numpy as np
from optimisation.algorithm import (
    ALLOCATION_MULTIPLIER,
    MAX_ALLOCATION_TOTAL,
    get_sun_energy,
    load_policy_network_checkpoint,
    predict,
)
from optimisation.naive import simulate_day_naive, trend_prediction
from optimisation.gen_data import getDayData, getTickData
from optimisation.models import Day, Tick


import time
import matplotlib.pyplot as plt


costs = []
sun_energies = []
import_prices = []
export_prices = []
demands = []
dd1_allocations = []
dd2_allocations = []
dd3_allocations = []
import_export = []
release_store = []
ticks = []
costs_for_day = []


def print_preaction(tick, env):
    print("Day:", tick.day, "Tick:", tick.tick)
    print("Sun energy:", round(get_sun_energy(tick), 3))
    print("Flywheel Amt:", round(env["flywheel_amt"], 3))
    print("Inst D:", round(tick.demand, 3))
    print(
        "Deferrable D:",
        [[round(d.energy, 3), d.start, d.end] for d in env["deferables"]],
    )


def print_postaction(actions, tick, cost):
    print("Imp / Exp:", round(actions["import_export"], 3))
    print("Rel / Sto:", round(actions["release_store"], 3))
    print("Allocations:", [round(a, 3) for a in actions["allocations"]])
    print("Buy price:", round(tick.buy_price, 3))
    print("Sell price:", round(tick.sell_price, 3))
    print("Cost: ", cost)
    print("-" * 20)
    print()


filename = (
    "server/optimisation/checkpoints/06_e5000_r50_am2_rm0_im10_sta20_abs1_tre1.pth"
)
policy_network, min, min_epoch = load_policy_network_checkpoint(filename)

env = {
    "flywheel_amt": 0,
    "deferables": None,
}
day_id = randint(5000000, 6000000)
tick_id = 0
day: Day = getDayData(day_id)
history = []

# ALGORITHM
time.sleep(0)
day = getDayData(day_id)
env["deferables"] = deepcopy(day.deferables)
print("Deferables:", [[d.energy, d.start, d.end] for d in env["deferables"]])


for i in range(60):
    tick = getTickData(day_id, i)
    print_preaction(tick, env)
    cost, actions = predict(policy_network, env, tick, history)

    history.append(tick)
    ticks.append(tick)
    sun_energies.append(get_sun_energy(tick))
    costs_for_day.append(cost)
    import_prices.append(tick.sell_price)
    export_prices.append(tick.buy_price)
    demands.append(deepcopy(tick.demand))
    dd1_allocations.append(actions["allocations"][0])
    dd2_allocations.append(actions["allocations"][1])
    dd3_allocations.append(actions["allocations"][2])
    import_export.append(actions["import_export"])
    release_store.append(actions["release_store"])

    print_postaction(actions, tick, cost)


naive_fw_start = simulate_day_naive(
    day,
    ticks,
    use_flywheel=True,
    satisfy_end=False,
)
trend_costs = trend_prediction(deepcopy(day), ticks)


# print("Total Naive FW End:", naive_fw_end)
# print("Min cost:", min)
# print("Epochs trained:", min_epoch)
print("Total Naive FW Start:", naive_fw_start)
print("Total Trend cost:", sum(trend_costs))
print("Total RL cost: ", sum(costs_for_day))


def scale_data(data):
    data = np.array(data)
    return data / (data.max() - data.min())


plt.title("Deferable Demands allocations")
# plt.plot(demands, label="Demands")
plt.plot(scale_data(import_prices) * 5 + 5, label="Import Price (Biased)")
plt.plot(dd1_allocations, label="DD1 Allocation")
plt.plot(dd2_allocations, label="DD2 Allocation")
plt.plot(dd3_allocations, label="DD3 Allocation")
plt.legend()
plt.show()

# plt.plot(import_prices, label="Import Price")
plt.title("Import / Export and Release / Store actions (RL)")
# allocation_demands = [
#     dd1_allocations[i] + dd2_allocations[i] + dd3_allocations[i]
#     for i in range(len(dd1_allocations))
# ]
# plt.plot(allocation_demands, label="Allocation Demands")
plt.plot(demands, label="Demands")
plt.plot(sun_energies, label="Sun Energy")
plt.plot(import_export, label="Import / Export")
plt.plot(release_store, label="Release / Store")
plt.legend()
plt.show()
