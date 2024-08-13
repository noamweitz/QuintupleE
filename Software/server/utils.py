from optimisation.algorithm import get_sun_energy


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
