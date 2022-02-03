REGISTRY = {}

from .rnn_agent import RNNAgent
from .cnn_agent import CNNAgent
from .latent_ce_dis_rnn_agent import LatentCEDisRNNAgent

REGISTRY["rnn"] = RNNAgent
REGISTRY["cnn"] = CNNAgent
REGISTRY["latent_ce_dis_rnn"] = LatentCEDisRNNAgent
