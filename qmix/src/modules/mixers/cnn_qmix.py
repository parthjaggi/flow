import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class CNNQMixer(nn.Module):
    def __init__(self, args):
        super(CNNQMixer, self).__init__()

        self.args = args
        self.n_agents = args.n_agents
        self.state_dim = int(np.prod(args.state_shape))
        self.embed_dim = args.mixing_embed_dim

        filter_size = 16
        _, n_lanes, n_history, n_channel = args.state_shape  # (n_agents, 4, 60, 3)

        # self.conv_layers = nn.Sequential(
        #     nn.Conv2d(n_channel, filter_size, [8, 1]), nn.ELU(),
        #     nn.Conv2d(filter_size, filter_size*2, [4, 1]), nn.ELU(),
        #     nn.Conv2d(filter_size*2, filter_size*2, [2, 1]), nn.ELU(),
        #     nn.Flatten()
        # )

        self.conv_layers = nn.Sequential(
            nn.Conv2d(n_channel, filter_size, [8, 1], stride=[2, 1]), nn.BatchNorm2d(filter_size), nn.ReLU(),
            nn.Conv2d(filter_size, filter_size*2, [8, 1], stride=[2, 1]), nn.BatchNorm2d(filter_size*2), nn.ReLU(),
            nn.Conv2d(filter_size*2, filter_size*2, [8, 1], stride=[2, 1]), nn.BatchNorm2d(filter_size*2), nn.ReLU(),
            nn.Flatten()
        )

        conv_input_shape = (n_channel, n_history, n_lanes)  # After transpose: (3, 60, 4)
        self.conv_output_shape = self.get_conv_output(conv_input_shape)

        self.hyper_w_1 = nn.Linear(self.conv_output_shape * self.n_agents, self.embed_dim * self.n_agents)
        self.hyper_b_1 = nn.Linear(self.conv_output_shape * self.n_agents, self.embed_dim)

        self.hyper_w_final = nn.Linear(self.conv_output_shape * self.n_agents, self.embed_dim)

        self.V = nn.Sequential(
            nn.Linear(self.conv_output_shape * self.n_agents, self.embed_dim), nn.ReLU(),
            nn.Linear(self.embed_dim, 1)
        )

    def get_conv_output(self, conv_input_shape):
        rand = torch.rand((1,) + conv_input_shape)
        out = self.conv_layers(rand)
        return out.shape[1]

    def forward(self, agent_qs, states):  # agent_qs.shape: (bs,t,n)
        bs = agent_qs.size(0)
        agent_qs = agent_qs.view(-1, 1, self.n_agents)

        # states = states.reshape(-1, self.state_dim)
        states = states.reshape(-1, *self.args.state_shape[1:])
        states = states.transpose(1, 3)
        conv_states = self.conv_layers(states)
        conv_states = conv_states.view(-1, self.conv_output_shape * self.n_agents)

        # First layer
        w1 = torch.abs(self.hyper_w_1(conv_states))
        b1 = self.hyper_b_1(conv_states)
        w1 = w1.view(-1, self.n_agents, self.embed_dim)
        b1 = b1.view(-1, 1, self.embed_dim)
        hidden = F.elu(torch.bmm(agent_qs, w1) + b1)

        # Second layer
        w_final = torch.abs(self.hyper_w_final(conv_states))
        w_final = w_final.view(-1, self.embed_dim, 1)

        # State-dependent bias
        v = self.V(conv_states).view(-1, 1, 1)

        # Compute final output
        y = torch.bmm(hidden, w_final) + v

        # Reshape and return
        q_tot = y.view(bs, -1, 1)
        return q_tot  # shape: (bs, t, 1)
