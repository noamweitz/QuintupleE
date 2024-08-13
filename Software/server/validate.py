from random import randint
import sys
import os
import numpy as np


current_directory = os.getcwd()
parent_directory = os.path.dirname(current_directory)
sys.path.insert(0, parent_directory)


from optimisation.train_test_utils import get_naive_label, run_validation
from optimisation.naive import simulate_day_naive
from optimisation.gen_data import getDayData, getTickData, getTicksForDay
from optimisation.algorithm import (
    STATE_SIZE,
    ACTION_SIZE,
    load_policy_network_checkpoint,
)
from optimisation.algorithm import predict
from server.optimisation.utils.gen_utils import costs_to_table_md, get_ema

import matplotlib.pyplot as plt
from IPython.display import display, Markdown
from random import randint

basename = "e1000_r10_amul2_rmul3_sta20_fut10"
filename = f"server/optimisation/checkpoints/{basename}.pth"
policy_network, min, min_epoch = load_policy_network_checkpoint(filename)
start = randint(5000000, 6000000)
print("Training min: ", round(min, 3))
print("Min epoch: ", min_epoch)
print("Start:", start)
print()

env = {"deferables": None, "flywheel_amt": 0}

history_ticks = []


number_of_days = 1000

naive_params = {"satisfy_end": True, "use_flywheel": True}

rl_costs, naive_costs = run_validation(
    start, number_of_days, policy_network, naive_params
)

ema_amount = 100
plt.plot(get_ema(rl_costs, ema_amount), label="RL")
plt.plot(get_ema(naive_costs, ema_amount), label=get_naive_label(naive_params))

mid_y = (
    max(get_ema(naive_costs, ema_amount)) - max(get_ema(rl_costs, ema_amount))
) // 2 + max(get_ema(rl_costs, ema_amount))
plt.text(
    0,
    mid_y,
    f"""Average RL cost: {round(np.mean(rl_costs), 2)}
Average Naive cost: {round(np.mean(naive_costs), 2)}""",
    bbox=dict(facecolor="white", alpha=0.5),
)

plt.xlabel("Days")
plt.ylabel("Cost")
plt.title("Cost over days (ema=100)")
plt.legend()
plt.savefig(f"plots/{basename}_val.png", dpi=500)
plt.show()
