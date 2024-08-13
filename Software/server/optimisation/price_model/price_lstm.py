from copy import deepcopy
from torch import nn
import torch
import os


def init_price_lstm(input_size=1):
    # input_size = 1  # price
    dir = os.path.dirname(__file__)
    model = PriceLSTM(input_size)

    model.load_state_dict(torch.load(os.path.join(dir, "model.pth")))
    model.eval()
    return model


def create_input(dataset: list, lookback):
    X = []
    for i in range(len(dataset) - lookback + 1):
        X.append([[x.tick, x.sell_price] for x in dataset[i : i + lookback]])
    return torch.FloatTensor(X)


def predict_future(model, ticks, lookahead):
    # Ticks should be of size 10

    predictions = []
    ticks = deepcopy(ticks[-model.lookback :])
    x_test = create_input(ticks, model.lookback)
    input = x_test[0]

    with torch.no_grad():
        for i in range(lookahead):
            y_pred = model(input.unsqueeze(0)).squeeze().numpy()
            predictions.append(y_pred.item())
            latest_tick = input[-1]
            next_tick = torch.tensor([latest_tick[0] + 1, y_pred], dtype=input.dtype)
            new_input = torch.cat((input[1:], next_tick.unsqueeze(0)), dim=0)
            input = new_input

    return predictions


class PriceLSTM(nn.Module):
    def __init__(self, input_size, hidden_size=50, output_size=1, lookback=20):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.lookback = lookback
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
        )
        self.linear = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x, _ = self.lstm(x)
        last_time_step = x[:, -1, :]
        out = self.linear(last_time_step)
        return out
