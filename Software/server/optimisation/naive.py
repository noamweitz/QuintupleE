from copy import deepcopy

import numpy as np

from optimisation.algorithm import (
    MAX_FLYWHEEL_CAPACITY,
    MAX_IMPORT_ENERGY,
    PRICE_THRESHOLD,
    get_sun_energy,
    MAX_ALLOCATION_TOTAL,
)
import matplotlib.pyplot as plt
import math

from optimisation.utils.deferables_utils import (
    satisfy_deferables,
    satisfy_deferables_start,
)
from optimisation.utils.gen_utils import cost_to_energy, import_export_to_cost

PRICE_TREND = [
    35,
    35,
    35,
    35,
    35,
    35,
    35,
    35,
    35,
    35,
    35,
    42,
    50,
    57,
    65,
    72,
    70,
    67,
    65,
    62,
    61,
    52,
    44,
    36,
    30,
    24,
    19,
    15,
    13,
    11,
    10,
    11,
    13,
    15,
    19,
    24,
    30,
    36,
    44,
    52,
    61,
    70,
    80,
    90,
    100,
    110,
    110,
    110,
    110,
    110,
    110,
    102,
    95,
    87,
    80,
    72,
    65,
    57,
    50,
    42,
]


# PRICE_THRESHOLD = 30
EXPORT_THRESHOLD = 146


def trend_prediction(
    day,
    ticks,
    max_alloc_total=MAX_ALLOCATION_TOTAL,
    price_threshold=PRICE_THRESHOLD,
    export_threshold=None,
):
    # 0-10: buy
    # 10-20: sell
    costs = []
    flywheel_amt = 0
    day = deepcopy(day)
    deferables = deepcopy(day.deferables)

    all_allocations = []
    sun_energies = []
    flywheel_usage = []
    imp_exp = []
    # print("\nTREND PREDICTION")

    for tick in ticks:
        sun_energy = get_sun_energy(tick)
        sun_energies.append(sun_energy)

        # Energy = sun + flywheel
        total_energy = sun_energy + flywheel_amt
        flywheel_used = flywheel_amt
        flywheel_amt = 0

        # Import / Export amount
        imp_exp_amt = 0
        exporting = False
        if export_threshold != None and tick.sell_price > export_threshold:
            # print("Exporting due to high prices")
            exporting = True
            imp_exp_amt = max(-total_energy, -MAX_IMPORT_ENERGY)
            total_energy -= abs(imp_exp_amt)

        # print("Imp Exp Amt Before:", imp_exp_amt)
        total_energy -= tick.demand

        # Start buying if end of deferable is reaching
        allocations = satisfy_deferables(tick, deferables, max_alloc_total)
        energy_left = total_energy - sum(allocations) + MAX_IMPORT_ENERGY

        for i, a in enumerate(allocations):
            if energy_left <= 0:
                break
            if allocations[i] != 0:
                continue

            d = deferables[i]
            if (
                tick.sell_price < price_threshold
                and d.start < tick.tick
                and d.end > tick.tick
            ):
                allocations[i] = min(energy_left, d.energy)
                d.energy -= allocations[i]
                energy_left -= allocations[i]

        total_energy -= sum(allocations)

        cost = 0
        if total_energy < 0:
            if int(total_energy) < -MAX_IMPORT_ENERGY:
                print()
                print("Sun E:", sun_energy)
                print("Flywheel Used:", flywheel_used)
                print("Inst D:", tick.demand)
                print("Total energy:", total_energy)
                print("Allocations:", allocations)
                print("Exceeded max import energy")
            imp_exp_amt += -total_energy

        else:
            if flywheel_amt + total_energy > MAX_FLYWHEEL_CAPACITY:
                imp_exp_amt -= flywheel_amt + total_energy - MAX_FLYWHEEL_CAPACITY
                # cost = (
                #     -(flywheel_amt + total_energy - MAX_FLYWHEEL_CAPACITY)
                #     * tick.buy_price
                # )

            flywheel_amt = min(MAX_FLYWHEEL_CAPACITY, flywheel_amt + total_energy)

        # print("Imp Exp Amt After:", imp_exp_amt)
        # if exporting:
        #     print("Actual imp/exp:", imp_exp_amt)
        total_energy -= sum(allocations)
        all_allocations.append(allocations)

        cost = import_export_to_cost(imp_exp_amt, tick)

        flywheel_usage.append(flywheel_used - flywheel_amt)
        imp_exp.append(cost_to_energy(cost, tick.buy_price, tick.sell_price))
        costs.append(cost)

    # plt.plot([tick.sell_price for tick in ticks], label="Sell Price")
    # plt.plot(np.array(costs) / 10, label="Cost")
    # plt.plot([tick.sell_price for tick in ticks], label="Sell Price")
    # plt.plot([a[0] for a in all_allocations], label="Deferable 1")
    # plt.plot([a[1] for a in all_allocations], label="Deferable 2")
    # plt.plot([a[2] for a in all_allocations], label="Deferable 3")
    # plt.legend()
    # plt.show()

    # plt.plot(sun_energies, label="Sun Energy")
    # plt.plot([tick.sell_price for tick in ticks], label="Sell Price")
    # plt.plot(flywheel_usage, label="Flywheel Usage")
    # plt.plot(imp_exp, label="Import / Export")
    # plt.legend()
    # plt.show()
    return costs


def simulate_day_naive(
    day,
    ticks,
    satisfy_end=True,
    use_flywheel=False,
    export_extra=False,
    max_alloc_total=MAX_ALLOCATION_TOTAL,
):
    costs = []
    flywheel_amt = 0
    day = deepcopy(day)
    deferables = deepcopy(day.deferables)

    for tick in ticks:
        sun_energy = get_sun_energy(tick)
        total_energy = sun_energy

        if use_flywheel:
            total_energy += flywheel_amt
            flywheel_amt = 0

        total_energy -= tick.demand

        if not satisfy_end:
            allocations = satisfy_deferables_start(
                tick, deferables, total_energy, MAX_IMPORT_ENERGY
            )
            total_energy -= sum(allocations)
        else:
            allocations = satisfy_deferables(tick, deferables, max_alloc_total)
            total_energy -= sum(allocations)

        cost = 0

        if total_energy < 0:
            if total_energy < -MAX_IMPORT_ENERGY:
                print("Exceeded max import energy")
            cost = -total_energy * tick.sell_price

        elif use_flywheel:
            if flywheel_amt + total_energy > MAX_FLYWHEEL_CAPACITY:
                cost = (
                    -(flywheel_amt + total_energy - MAX_FLYWHEEL_CAPACITY)
                    * tick.buy_price
                )
            flywheel_amt = min(MAX_FLYWHEEL_CAPACITY, flywheel_amt + total_energy)
        elif export_extra:
            cost = -total_energy * tick.buy_price  # Export extra energy

        costs.append(cost)
        # import_amount = cost_to_energy(cost, tick.buy_price, tick.sell_price)

    return sum(costs)
