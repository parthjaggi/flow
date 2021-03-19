import torch
import torch.nn as nn
import torch.nn.functional as F


class CNNAgent(nn.Module):
    def __init__(self, input_shape, args):
        super(CNNAgent, self).__init__()
        self.args = args
        filter_size = 16
        n_lanes, n_history, n_channel = input_shape  # (4, 60, 3)

        # TODO: Compare with CNN model here: https://pytorch.org/tutorials/intermediate/reinforcement_q_learning.html
        self.conv_layers = nn.Sequential(
            nn.Conv2d(n_channel, filter_size, [8, 1]), nn.ELU(),
            nn.Conv2d(filter_size, filter_size*2, [4, 1]), nn.ELU(),
            nn.Conv2d(filter_size*2, filter_size*2, [2, 1]), nn.ELU(),
            nn.Flatten()
        )
        
        conv_input_shape = (n_channel, n_history, n_lanes)  # After transpose: (3, 60, 4)
        conv_output_shape = self.get_conv_output(conv_input_shape)
        self.head = nn.Linear(conv_output_shape, args.n_actions)

    def init_hidden(self):
        # make hidden states on same device as model
        # return self.fc1.weight.new(1, self.args.rnn_hidden_dim).zero_()
        return self.head.weight.new(1, self.args.rnn_hidden_dim).zero_()

    def get_conv_output(self, conv_input_shape):
        rand = torch.rand((1,) + conv_input_shape)
        out = self.conv_layers(rand)
        return out.shape[1]

    def forward(self, inputs, hidden_state):
        x = inputs.transpose(1, 3)
        x = self.conv_layers(x)
        q = self.head(x)
        return q, hidden_state
