import itertools
from torch import nn, optim, distributions
import torch


class ValueNetwork(nn.Module):
    def __init__(self, state_size, hidden_size=128):
        super(ValueNetwork, self).__init__()
        self.fc1 = nn.Linear(state_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, 1)
        self.optimizer = optim.Adam(self.parameters(), lr=1e-4)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x


def build_mlp(
    state_size: int,
    action_size: int,
    hidden_size: int,
    n_layers: int,  # number of layers excluding head
):

    layers = []
    in_size = state_size
    for _ in range(n_layers):
        layers.append(nn.Linear(in_size, hidden_size))
        layers.append(nn.ReLU())
        in_size = hidden_size

    layers.append(nn.Linear(in_size, action_size))

    return nn.Sequential(*layers)


def get_device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


class PolicyNetwork:
    def __init__(
        self,
        state_size: int,
        action_size: int,
        n_layers: int = 4,
        hidden_size: int = 128,
        learning_rate=1e-4,
        training=False,
        epsilon=1,
        # nn_baseline=False,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.state_size = state_size
        self.action_size = action_size

        self.n_layers = n_layers
        self.hidden_size = hidden_size

        self.learning_rate = learning_rate
        self.training = training
        self.epsilon = epsilon
        # self.nn_baseline = nn_baseline

        # NETWORK
        self.mean_net = build_mlp(
            state_size=self.state_size,
            action_size=self.action_size,
            hidden_size=self.hidden_size,
            n_layers=self.n_layers,
        )

        device = get_device()
        self.mean_net.to(device)

        self.logstd = nn.Parameter(
            torch.zeros(self.action_size, dtype=torch.float32, device=device)
        )

        self.logstd.to(device)
        self.optimizer = optim.Adam(
            itertools.chain([self.logstd], self.mean_net.parameters()),
            self.learning_rate,
        )

    def forward(self, state: torch.FloatTensor):
        mean = self.mean_net(state)
        std = torch.exp(self.logstd)
        return distributions.Normal(mean, std)

    def get_action(self, state: torch.FloatTensor):
        dists = self.forward(state)
        if self.training:
            action = dists.sample()
        else:
            action = dists.mean

        logprob = dists.log_prob(action).sum(axis=-1)
        return action, logprob


# epsilon_noise = torch.randn_like(action) * self.epsilon
# action_with_noise = action + epsilon_noise
# logprob = dists.log_prob(action_with_noise).sum(axis=-1)
# return action_with_noise, logprob
