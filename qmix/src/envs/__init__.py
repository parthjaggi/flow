from functools import partial
import sys
import os

# from smac.env import MultiAgentEnv, StarCraft2Env
from .multiagentenv import MultiAgentEnv
# from .starcraft2 import StarCraft2Env
# from .gfootball import GoogleFootballEnv
from .trafficgrid import TrafficGridEnv


def env_fn(env, **kwargs) -> MultiAgentEnv:
    return env(**kwargs)


REGISTRY = {}
# REGISTRY["sc2"] = partial(env_fn, env=StarCraft2Env)
# REGISTRY["gf"] = partial(env_fn, env=GoogleFootballEnv)
REGISTRY["traf"] = partial(env_fn, env=TrafficGridEnv)

# if sys.platform == "linux":
#     os.environ.setdefault("SC2PATH", os.path.join(os.getcwd(), "3rdparty", "StarCraftII"))
