from ..multiagentenv import MultiAgentEnv
from operator import attrgetter
from copy import deepcopy
# from absl import flags
import numpy as np
# import pygame
import sys
import os
import math
import time
import numpy as np
import pathlib
import yaml

from wolf.world.environments.traffic.agents.connectors.action.exchange_change_phase import EXTEND
from wolf.world.environments.traffic.traffic_env import TrafficEnv
from wolf.world.environments.traffic.grid_env import SimpleGridEnv
from wolf.utils.configuration.registry import R


class TrafficGridEnv(MultiAgentEnv):
    def __init__(self, **kwargs):
        if 'SUMO_HOME' in os.environ:
            tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
            sys.path.append(tools)

        self.env = self.make(kwargs)
        
        self.n_agents = kwargs['n'] * kwargs['m']
        self.agents = self.env.get_agents()
        self.any_agent = next(iter(self.agents.values()))

        self.episode_limit = self.env.env_params.horizon
        self.state = kwargs.get('state', 'vector') # type of state

        self.rewards = [] # debugging
        self.debug = False
        self.obs = None

    def make(self, kwargs):
        test_env = kwargs.get('test_env', None)
        if test_env:
            return self.get_test_env(kwargs)
        else:
            return self.build_env(kwargs)

    def get_test_env(self, kwargs):
        create_env = R.env_factory(kwargs['test_env'])
        env_config = self.load_env_config_yaml()
        env = create_env(env_config)
        return env

    def load_env_config_yaml(self):
        filename = 'env_config.yaml'
        path = pathlib.Path(__file__).parent/filename
        with open(path, 'r') as stream:
            env_config = yaml.load(stream).get('env_config', {})
        return env_config

    def build_env(self, kwargs):
        simulator = "traci"
        sim_params = {
            "restart_instance": True,
            "sim_step": 1,
            "print_warnings": False,
            "render": kwargs['render'],
        }

        env_state_params = None
        groups_agent_params = None
        multi_agent_config_params = {"name": "single_policy", "params": {}}
        detector_positions = [5, 295]
        noop_action = {'add_noop_action': kwargs.get('add_noop_action', False)}

        agents_params = {
            "name": "all_the_same",
            "params": {
                "global_reward": True,
                "default_policy": None,
                "action_params": {
                    "name": "ExtendChangePhaseConnector",
                    "params": noop_action,
                },
                "obs_params": {
                    "name": "TDTSEConnector",
                    "params": {
                        "obs_params": {
                            "num_history": 60,
                            "detector_position": detector_positions,
                        },
                        "phase_channel": True,
                        **noop_action,
                    },
                },
                "reward_params": {
                    "name": "QueueRewardConnector",
                    "params": {"stop_speed": 2},
                },
            },
        }

        assert agents_params['name'] == "all_the_same", "Observation shape for all agents should be the same."

        env = TrafficEnv.create_env(
            cls=SimpleGridEnv,
            agents_params=agents_params,
            env_state_params=env_state_params,
            groups_agent_params=groups_agent_params,
            multi_agent_config_params=multi_agent_config_params,
            n=kwargs['n'],
            m=kwargs['m'],
            inflow_type='platoon',
            inflow_params={'WE': (10, 20), 'EW': (0, 30), 'NS': (0, 30), 'SN': (0, 30)},
            horizon=kwargs['horizon'],
            simulator=simulator,
            sim_params=sim_params,
            detector_params={"positions": detector_positions, "frequency": 100},
            tl_params={"initialization": "fixed"}
        )
        return env

    def step(self, actions):
        """ Returns reward, terminated, info """
        # TODO: is the actions recieved in order of self.agents.
        actions = {agent_id: int(actions[idx]) for idx, agent_id in enumerate(self.agents)}
        observation, reward, done, info = self.env.step(actions)

        self.obs = observation
        reward = sum(reward.values())
        self.rewards.append(reward)
        done = done['__all__']
        info = {}
        return reward, done, info

    def get_obs(self):
        """ Returns all agent observations in a list. """
        obs = [self.get_obs_agent(agent_id) for agent_id in self.obs]
        return obs

    def get_obs_agent(self, agent_id):
        """ Returns observation for agent_id. """
        obs = self.obs[agent_id]['tdtse'].squeeze(0)
        return obs

    def get_obs_size(self):
        """ Returns the shape of the observation """
        obs_shape = self.any_agent.obs_space()['tdtse'].shape  # (1, 4, 60, 3)
        return obs_shape[1:]  # (4, 60, 3)

    def get_state(self):
        # TODO: Compose the state using env kernel methods. Update get_state_size method.
        if self.state == 'image':
            obs = self._get_state_as_image()
        elif self.state == 'vector':
            obs = self._get_state_as_vector()
        else:
            raise NotImplementedError(self.state)
        return obs

    def _get_state_as_vector(self):
        obs = list(map(lambda x: x['tdtse'].flatten(), self.obs.values()))
        obs = np.concatenate(obs)
        return obs

    def _get_state_as_image(self):
        obs = np.concatenate(list(map(lambda x: x['tdtse'], self.obs.values())))
        return obs

    def get_state_size(self):
        """ Returns the shape of the state"""
        obs_shape = self.any_agent.obs_space()['tdtse'].shape
        n_agents = len(self.agents)
        
        if self.state == 'image':
            state_shape = (n_agents, *obs_shape[1:])
        elif self.state == 'vector':
            state_shape = int(np.prod(obs_shape) * n_agents)
        else:
            raise NotImplementedError(self.state)
        
        return state_shape

    def get_avail_actions(self):
        """
        Gives a representation of which actions are available to each agent.
        Returns nested list of shape: n_agents * n_actions_per_agent.
        Each element in boolean. If 1 it means that action is available to agent.
        """
        avail_actions = np.array(list(map(lambda x: x['action_mask'], self.obs.values())))
        return avail_actions

    def get_avail_agent_actions(self, agent_id):
        """ 
        Returns the available actions for agent_id.
        Returns a list of shape: n_actions of agent.
        Each element in boolean. If 1 it means that action is available to agent.
        """
        avail_actions = self.obs[agent_id]['action_mask']
        return avail_actions

    def get_total_actions(self):
        """
        Returns the total number of actions an agent could ever take.
        Should be integer of number of actions of an agent. Assumed that all agents have same number of actions.
        """
        return self.any_agent.action_space().n

    def get_stats(self):
        return {}

    def get_agg_stats(self, stats):
        return {}

    def reset(self):
        """ Returns initial observations and states"""
        if self.debug: 
            print(f'Episode end reward sum: {sum(self.rewards)}')
        self.obs = self.env.reset()
        self.rewards = []
        return self.get_obs(), self.get_state()

    def render(self):
        self.env.render()

    def close(self):
        self.env.close()

    def seed(self):
        pass

    def save_replay(self):
        pass

    def get_env_info(self):
        env_info = {
            "state_shape": self.get_state_size(),
            "obs_shape": self.get_obs_size(),
            "n_actions": self.get_total_actions(),
            "n_agents": self.n_agents,
            "episode_limit": self.episode_limit,
        }
        return env_info
