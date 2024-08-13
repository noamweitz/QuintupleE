import time

import numpy as np

# from gen_data import getTicksForDay
from optimisation.models import Tick
from optimisation.policy import PolicyNetwork, ValueNetwork

from optimisation.price_model.price_lstm import init_price_lstm, predict_future


from optimisation.utils.deferables_utils import satisfy_deferables
from optimisation.utils.gen_utils import import_export_to_cost

import torch
import matplotlib.pyplot as plt

MAX_DEFERABLES = 3
MPP = 4
GAMMA = 0.99
MAX_FLYWHEEL_CAPACITY = 25
MAX_IMPORT_EXPORT = 25
MAX_IMPORT_ENERGY = 40
MAX_ALLOCATION_TOTAL = MAX_IMPORT_ENERGY - 30  # max import / export - ~max inst demand

# Action size: 1 for buy/sell, 1 for store/release, 1 for each deferable


# Allocation
TICK_LENGTH = 5
SUN_TICK_LENGTH = 5

# HYPERPARAMETERS
FUTURE_TICKS = 0
STACKED_NUM = 20
HIST_SIZE = 1
STATE_SIZE = (
    MAX_DEFERABLES * 3 + 1 + 4 + STACKED_NUM * HIST_SIZE + FUTURE_TICKS
)  # 1 for flywheel_amt, 5 for cur tick info, 3 for each past tick, 1 for each future price

ACTION_SIZE = 1 + 1 + MAX_DEFERABLES  # Make it 1 action for allocations
# ACTION_SIZE = 1 + 1 + 1  # 1 for import/export, 1 for store/release, 1 allocation total

# ALLOCATION_ABSOLUTE = 1
HANDLE_OVERFLOW = 1
ALLOCATION_BIAS = 0
ALLOCATION_ABSOLUTE = 1

RELEASE_STORE_MULTIPLIER = 0
# Try 2 & 5
ALLOCATION_MULTIPLIER = 2
IMPORT_EXPORT_MULTIPLIER = 10
PRICE_THRESHOLD = 11
USE_TREND_FOR_ALLOCATION = 1

price_lstm = init_price_lstm(input_size=2)


def future_ticks_to_vect(ticks):
    # Ticks should be of size 10
    if len(ticks) < price_lstm.lookback or None in ticks:
        return [0] * FUTURE_TICKS

    lookback_ticks = ticks[-price_lstm.lookback :]
    predictions = predict_future(price_lstm, lookback_ticks, FUTURE_TICKS)
    return predictions


def cur_tick_to_vect(tick):
    sun_energy = get_sun_energy(tick)
    return [tick.tick, tick.demand, sun_energy, tick.sell_price]


def hist_tick_to_vect(tick):
    sun_energy = get_sun_energy(tick)
    return [tick.sell_price]


def history_ticks_to_vect(history, STACKED_NUM):
    hist = []
    for i in range(STACKED_NUM):
        index = -1 - i
        if index < -len(history) or history[index] is None:
            hist.extend([0] * HIST_SIZE)
        else:
            hist.extend(hist_tick_to_vect(history[index]))
    return hist


def get_sun_energy(tick):
    return (tick.sun / 100) * MPP * SUN_TICK_LENGTH


def update_flywheel_amt(day_state, release_store_amt):
    cur_flywheel_amt = day_state["flywheel_amt"]
    penalty = 0

    # If release amount > flywheel amount, set release amount to flywheel amount and penalise
    if release_store_amt > cur_flywheel_amt:
        release_store_amt = cur_flywheel_amt

    # Else if store amount + cur_flywheel_amt > capacity, set release_store_amt to capacity - cur_flywheel_amt and penalise
    elif (
        release_store_amt < 0
        and -release_store_amt + cur_flywheel_amt > MAX_FLYWHEEL_CAPACITY
    ):
        release_store_amt = -(MAX_FLYWHEEL_CAPACITY - cur_flywheel_amt)

    # If release_store > 0, draw energy and subtract from flywheel_amt
    day_state["flywheel_amt"] -= release_store_amt

    return release_store_amt, penalty


def update_deferable_demands_old(
    energy_available, day_state, action, tick, print_info=False
):

    deferables = day_state["deferables"]
    energy_left = energy_available
    allocations = satisfy_deferables(
        tick, deferables, max_alloc_total=MAX_ALLOCATION_TOTAL
    )

    if ALLOCATION_ABSOLUTE == 1:
        action = abs(action[2].item())
    else:
        action = max(0, action[2].item())

    alloc_action = min(energy_left - sum(allocations), action * ALLOCATION_MULTIPLIER)
    total = 0

    end_to_indices = {}
    indices = []
    for i, a in enumerate(allocations):
        if a != 0:
            energy_left -= a
            continue
        d = deferables[i]
        if d.start <= tick.tick and d.end >= tick.tick:
            if d.end not in end_to_indices:
                end_to_indices[d.end] = []

            end_to_indices[d.end].append(i)
            indices.append(i)

    # # SIMPLE SPLITTING
    # total = sum([deferables[i].energy for i in indices])
    # if total == 0:
    #     return sum(allocations), 0, allocations

    # for i in indices:
    #     d = deferables[i]
    #     energy_used = (d.energy / total) * alloc_action
    #     allocations[i] = min(d.energy, energy_used)
    #     d.energy -= allocations[i]
    # return sum(allocations), 0, allocations

    # SPLITTING BY END TIME
    end_to_indices = dict(sorted(end_to_indices.items(), key=lambda x: x[0]))
    # print("End to indices:", end_to_indices)
    for k, v in end_to_indices.items():
        total = sum([deferables[index].energy for index in v])

        if alloc_action <= 0 or total == 0:
            break

        used = 0

        for index in v:
            d = deferables[index]
            energy_used = (d.energy / total) * alloc_action
            allocations[index] = min(d.energy, energy_used)
            d.energy -= allocations[index]
            used += allocations[index]
        alloc_action -= used

    return sum(allocations), 0, allocations


def update_deferable_demands(
    energy_available, day_state, action, tick, print_info=False
):
    deferables = day_state["deferables"]
    penalty = 0

    # allocations = []
    energy_left = energy_available
    allocations = satisfy_deferables(
        tick, deferables, max_alloc_total=MAX_ALLOCATION_TOTAL
    )
    for a in allocations:
        energy_left -= a
        if a != 0:
            # print("Default allocation not 0")
            break

    for i in range(len(deferables)):
        d = deferables[i]

        if d.start > tick.tick or allocations[i] != 0:
            continue

        allocation = (ALLOCATION_BIAS + action[i + 2].item()) * ALLOCATION_MULTIPLIER

        if ALLOCATION_ABSOLUTE == 1:
            allocation = abs(allocation)
        else:
            allocation = max(0, allocation)

        allocation = min(allocation, d.energy)
        allocation = min(allocation, energy_left)
        energy_left -= allocation

        allocations[i] = allocation
        d.energy -= allocation

    return sum(allocations), penalty, allocations


def update_deferable_demands_trend(
    energy_available, day_state, action, tick, print_info=False
):
    deferables = day_state["deferables"]
    allocations = satisfy_deferables(
        tick, deferables, max_alloc_total=MAX_ALLOCATION_TOTAL
    )

    energy_left = energy_available - sum(allocations)

    # If allocate here...
    for i, a in enumerate(allocations):
        if energy_left <= 0:
            break
        if allocations[i] != 0:
            continue

        d = deferables[i]
        if (
            tick.sell_price < PRICE_THRESHOLD
            and d.start < tick.tick
            and d.end > tick.tick
        ):
            allocations[i] = min(energy_left, d.energy)
            d.energy -= allocations[i]
            energy_left -= allocations[i]

    return sum(allocations), 0, allocations


# LATEST
def environment_step(action, tick, day_state, print_info=False):
    total_penalty = 0

    # 1. Get total sun energy
    sun_energy = get_sun_energy(tick)
    total_energy = sun_energy
    # print()
    # print("-" * 20)
    # print("Tick:", tick.tick)
    # print("Sun E: ", round(sun_energy, 1))

    # 2. Get energy bought/sold
    # imp_exp_amt = 0
    imp_exp_amt = min(action[0].item() * IMPORT_EXPORT_MULTIPLIER, MAX_IMPORT_ENERGY)
    total_energy += imp_exp_amt

    # print("Initial Imp/Exp: ", round(imp_exp_amt, 1))

    # 3. Get energy stored/released
    if RELEASE_STORE_MULTIPLIER == 0:
        release_store_amt = day_state["flywheel_amt"]
        day_state["flywheel_amt"] = 0
        total_energy += release_store_amt
    else:
        release_store_amt = action[1].item() * RELEASE_STORE_MULTIPLIER
        release_store_amt, penalty = update_flywheel_amt(day_state, release_store_amt)
        total_penalty += penalty
        total_energy += release_store_amt
    # print("Rel/Sto: ", round(release_store_amt, 1))

    # 4. Satisfy instantaneous demand
    total_energy -= tick.demand
    # print("Inst D: ", round(tick.demand, 1))

    # 5. Satisfy deferable demands
    energy_available = sun_energy + release_store_amt + MAX_IMPORT_ENERGY - tick.demand
    # energy_spent, penalty, allocations = update_deferable_demands(
    #     energy_available, day_state, action, tick
    # )

    energy_spent, penalty, allocations = update_deferable_demands_trend(
        energy_available, day_state, action, tick
    )
    total_penalty += penalty
    total_energy -= sum(allocations)
    # print("All: ", [round(a, 1) for a in allocations])

    # 6. Buy more energy if total energy < 0
    if total_energy < 0:
        imp_exp_amt += -total_energy
        total_energy = 0

    # print("Imp/Exp: ", round(imp_exp_amt, 1))
    if int(imp_exp_amt) > MAX_IMPORT_ENERGY:
        print("Sun E: ", round(sun_energy, 1))
        print("Rel/Sto: ", round(release_store_amt, 1))
        print("Ins D: ", round(tick.demand, 1))
        # print("Def D: ", round(sum(allocations), 1))
        print("All:", [round(a, 1) for a in allocations])
        print("Imp/Exp Action:", action[0].item())
        print("Imp/Exp: ", imp_exp_amt)
        raise Exception("Exceeded max import/export amount")
    elif imp_exp_amt < -MAX_IMPORT_ENERGY:
        # print("Orig Imp/Exp: ", imp_exp_amt)
        exceeded_amt = -imp_exp_amt - MAX_IMPORT_ENERGY
        total_energy += exceeded_amt
        imp_exp_amt = -MAX_IMPORT_ENERGY

    if total_energy > 0 and HANDLE_OVERFLOW == 1:
        if total_energy > MAX_FLYWHEEL_CAPACITY - day_state["flywheel_amt"]:
            energy_to_sell = total_energy - (
                MAX_FLYWHEEL_CAPACITY - day_state["flywheel_amt"]
            )
            imp_exp_amt -= energy_to_sell

        release_store_amt -= min(
            MAX_FLYWHEEL_CAPACITY - day_state["flywheel_amt"], total_energy
        )
        day_state["flywheel_amt"] = min(
            MAX_FLYWHEEL_CAPACITY, day_state["flywheel_amt"] + total_energy
        )

    cost = import_export_to_cost(imp_exp_amt, tick)

    # if print_info:
    #     print("Tick: ", tick.tick)
    #     print("Sun E: ", round(sun_energy, 3))
    #     print("Imp/Exp: ", round(imp_exp_amt, 3))
    #     print("Cost: ", round(cost, 5))
    #     print("Rel/Sto: ", round(release_store_amt, 3))
    #     print("Ins D: ", round(tick.demand, 3))
    #     print("Def D: ", round(energy_spent, 3))
    #     print("E left: ", round(total_energy, 3))
    #     print("Penalty: ", round(total_penalty, 3))
    #     print("-" * 20)
    #     print()

    # Check balance of energy
    balance = (
        sun_energy + imp_exp_amt + release_store_amt - tick.demand - sum(allocations)
    )
    if balance > 1e-8:
        print("Sun E: ", round(sun_energy, 1))
        print("Imp/Exp: ", round(imp_exp_amt, 1))
        print("Rel/Sto: ", round(release_store_amt, 1))
        print("Inst D: ", round(tick.demand, 1))
        print("All: ", [round(a, 1) for a in allocations])
        print("Balance: ", balance)
        raise ("Energy not balanced")

    return (
        cost,
        total_penalty,
        {
            "import_export": imp_exp_amt,
            "release_store": release_store_amt,
            "allocations": allocations,
        },
    )


def predict(policy_network, env, tick, history):

    # Add deferable demand info
    deferables = env["deferables"]
    state = []
    for j in range(len(deferables)):
        d = deferables[j]
        state.extend([d.energy, d.start, d.end])

    # Add store/release info
    state.append(env["flywheel_amt"])

    # Add cur tick
    state.extend(cur_tick_to_vect(tick))

    # Add history
    state.extend(history_ticks_to_vect(history, STACKED_NUM))

    if FUTURE_TICKS > 0:
        state.extend(future_ticks_to_vect(history + [tick]))

    # Run policy network
    action, log_prob = policy_network.get_action(torch.tensor(state))

    cost, penalty, actions = environment_step(action, tick, env, print_info=False)

    return cost, actions


def load_policy_network_checkpoint(filename):
    checkpoint = torch.load(filename)
    policy_network = PolicyNetwork(STATE_SIZE, ACTION_SIZE)
    policy_network.mean_net.load_state_dict(checkpoint["mean_net"])
    policy_network.logstd = checkpoint["logstd"]
    return policy_network, checkpoint["min"], checkpoint["min_index"]


def compute_returns(rewards, baseline_rewards, gamma=0.99):
    # rewards = (
    #     torch.tensor(rewards, dtype=torch.float32)
    #     if isinstance(rewards, torch.tensor)
    #     else rewards
    # )
    # rewards = rewards - rewards.mean()

    returns = []

    baseline_returns = []
    R = 0
    base_R = 0
    for i in range(len(rewards) - 1, -1, -1):
        R = rewards[i] + gamma * R
        returns.insert(0, R)

        base_R = baseline_rewards[i] + gamma * base_R
        baseline_returns.insert(0, base_R)

    returns = torch.tensor(returns, dtype=torch.float32) - torch.tensor(
        baseline_returns, dtype=torch.float32
    )

    mean = returns.mean()
    std = returns.std()

    returns = (returns - mean) / (std + 1e-8)  # Normalize returns

    return returns


def compute_loss(log_probs, returns):
    # returns = torch.tensor(returns)
    returns = (
        torch.tensor(returns) if not isinstance(returns, torch.Tensor) else returns
    )

    loss = 0
    for log_prob, G in zip(log_probs, returns):
        loss += -log_prob * G
    return loss
