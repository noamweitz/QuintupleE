from copy import deepcopy
from optimisation.gen_data import getDayData, getTickData, getTicksForDay
from optimisation.algorithm import MAX_ALLOCATION_TOTAL, predict
from optimisation.naive import simulate_day_naive, trend_prediction
from optimisation.utils.gen_utils import get_ema

import numpy as np
import matplotlib.pyplot as plt


def get_naive_label(naive_params):
    text = "Naive"
    if naive_params["use_flywheel"]:
        text += " FW"
    else:
        text += " EE"

    if naive_params["satisfy_end"]:
        text += " End"
    else:
        text += " Start"
    return text


def run_validation(start, number_of_days, policy_network, naive_params):
    env = {"deferables": None, "flywheel_amt": 0}
    rl_costs = []
    naive_costs = []
    trend_algo_costs = []
    history_ticks = []

    for day_id in range(start, start + number_of_days):
        day = getDayData(day_id)
        env["deferables"] = deepcopy(day.deferables)
        costs_for_day = []

        ticks = []
        for tick_id in range(60):
            tick = getTickData(day_id, tick_id)
            cost, actions = predict(policy_network, env, tick, history_ticks)
            ticks.append(tick)
            history_ticks.append(tick)
            costs_for_day.append(cost)

        rl_costs.append(sum(costs_for_day))

        if day_id % 250 == 0:
            emas = get_ema(rl_costs, 100)
            print(f"Day {day_id}")
            print("EMA Cost:", round(emas[-1], 3))
            print("-" * 20)

        naive_costs.append(
            simulate_day_naive(
                day,
                ticks,
                export_extra=not naive_params["use_flywheel"],
                use_flywheel=naive_params["use_flywheel"],
                satisfy_end=naive_params["satisfy_end"],
            )
        )
        trend_algo_costs.append(
            sum(
                trend_prediction(
                    deepcopy(day),
                    ticks,
                    max_alloc_total=MAX_ALLOCATION_TOTAL,
                    price_threshold=11,
                    # export_threshold=146,
                )
            )
        )

    return rl_costs, naive_costs, trend_algo_costs


def plot_test_results(results, naive_costs, trend_costs, naive_params, basename):
    rl_costs = [r["cost"] for r in results]
    ema_amount = 100
    ema_rl_costs = get_ema(rl_costs, ema_amount)
    min_cost = np.min(ema_rl_costs)
    min_epoch = np.argmin(ema_rl_costs)

    print(f"Min cost: {round(min_cost, 3)} at epoch {min_epoch}")

    plt.plot(ema_rl_costs, label="RL")
    # plt.plot(get_ema(trend_costs, ema_amount), label="Trend Prediction Costs")
    # plt.plot(get_ema(naive_costs, ema_amount), label=get_naive_label(naive_params))
    plt.xlabel("Epochs (days)")
    plt.ylabel("Cost")
    plt.title("Training cost over days (ema=100)")
    # plt.legend()
    # mid_y = max(get_ema(naive_costs, ema_amount)) // 2
    # plt.text(0, mid_y,
    # f'''Average RL cost: {round(np.mean(rl_costs), 2)}
    # Average Naive cost: {round(np.mean(naive_costs), 2)}''',
    #         bbox=dict(facecolor='white', alpha=0.5))
    plt.scatter(min_epoch, min_cost, color="red", zorder=5)
    plt.text(
        min_epoch,
        min_cost - 50,
        f"({min_epoch}, {min_cost:.2f})",
        color="red",
        ha="center",
        va="top",
    )

    plt.savefig(f"plots/{basename}_train.png", dpi=500)
    plt.show()
