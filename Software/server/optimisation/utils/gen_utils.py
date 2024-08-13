import numpy as np
from optimisation.models import Tick
from pymongo import MongoClient
import torch


def get_db():
    client = MongoClient(
        "mongodb+srv://smartgrid_user:OzVu9hnKiaJULToP@autodocs.kwrryjv.mongodb.net/?retryWrites=true&w=majority&appName=Autodocs"
    )
    db = client["smartgrid"]
    return db


def compute_returns(rewards, gamma=0.99):
    rewards = torch.tensor(rewards, dtype=torch.float32)
    returns = []
    R = 0

    for r in reversed(rewards):
        R = r + gamma * R
        returns.insert(0, R)

    returns = torch.tensor(returns, dtype=torch.float32)
    mean = returns.mean()
    std = returns.std()

    # Print the mean and standard deviation
    print("Returns before normalization:", returns)
    print("Mean of returns:", mean.item())
    print("Standard deviation of returns:", std.item())

    returns = (returns - mean) / (std + 1e-8)  # Normalize returns
    return returns


def backprop(policy_network, log_probs, returns):
    returns = torch.tensor(returns, dtype=torch.float32)

    policy_loss = 0
    policy_network.optimizer.zero_grad()
    for log_prob, R in zip(log_probs, returns):
        policy_loss += -log_prob * R

    print(policy_loss)
    policy_loss.backward()
    policy_network.optimizer.step()

    return policy_loss.item()

    # policy_loss = policy_loss.mean()


def print_release_store(amt, text):
    if amt > 0:
        print(f"Rel {text}:", round(amt, 3))
    else:
        print(f"Sto {text}:", round(amt, 3))


def get_ema(data, N):
    alpha = 2 / (N + 1)
    ema = [data[0]]  # Start with the first value
    for i in range(1, len(data)):
        ema.append(alpha * data[i] + (1 - alpha) * ema[-1])
    return ema


def cost_to_energy(cost, buy_price, sell_price):
    if cost < 0:
        return cost / buy_price
    else:
        return cost / sell_price


def import_export_to_cost(imp_exp_amt, tick):
    if imp_exp_amt < 0:
        return imp_exp_amt * tick.buy_price
    else:
        return imp_exp_amt * tick.sell_price


def costs_to_table_md(rows):
    table_md = "| Algorithm | Average Cost (per day) |\n"
    table_md += "|-----------|------------------------|\n"
    for row in rows:
        table_md += f"| {row[0]} | {round(np.mean(row[1]), 3)} |\n"
    return table_md
    # table_md += f"| Naive FW | {round(np.mean(naive_store_fw), 2)} |\n"
    # table_md += f"| Naive EE | {round(np.mean(naive_export_extra), 2)} |\n"
    # pyperclip.copy(table_md)
    # print("Table copied to clipboard")
