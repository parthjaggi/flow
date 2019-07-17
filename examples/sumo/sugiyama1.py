"""Used as an example of sugiyama experiment.
This example consists of 22 IDM cars on a ring creating shockwaves.
"""

from flow.controllers import IDMController, ContinuousRouter,BCMController
from flow.core.experiment import Experiment
from flow.core.params import SumoParams, EnvParams,InitialConfig, NetParams
from flow.core.params import VehicleParams
from flow.envs.loop.loop_accel import AccelEnv, ADDITIONAL_ENV_PARAMS
from flow.scenarios.loop import LoopScenario, ADDITIONAL_NET_PARAMS
from flow.core.util import emission_to_csv
from flow.controllers.base_controller import BaseController
import numpy as np 
import os 

"""------------------------BCM Model-----------------------------------"""


def sugiyama_example1(render=None, x=22):
    """
    Perform a simulation of vehicles on a ring road.
    Parameters
    ----------
    render : bool, optional
        specifies whether to use the gui during execution
    Returns
    -------
    exp: flow.core.experiment.Experiment
        A non-rl experiment demonstrating the performance of human-driven
        vehicles on a ring road.
    """
    sim_params = SumoParams(sim_step=0.1, render=False,
                            emission_path='\IDM+BCM/{}IDM_{}BCM'.format(x, 22-x))
    if render is not None:
        sim_params.render = render

    vehicles = VehicleParams()
    vehicles.add(
        veh_id="idm",
        acceleration_controller=(IDMController, {},"noise":0.1),
        routing_controller=(ContinuousRouter, {}),
        num_vehicles=x)
    vehicles.add(
        veh_id="bcm",
        acceleration_controller=(BCMController,"noise":0.1),
        routing_controller=(ContinuousRouter, {}),
        num_vehicles=22-x)

    env_params = EnvParams(additional_params=ADDITIONAL_ENV_PARAMS)

    net_params = NetParams(
        additional_params={
            'length': 260,
            'lanes': 1,
            'speed_limit': 30,
            'resolution': 40
        }
    )

    initial_config = InitialConfig(perturbation=1, spacing='uniform')

    scenario = LoopScenario(
        name="sugiyama",
        vehicles=vehicles,
        net_params=net_params,
        initial_config=initial_config)

    env = AccelEnv(env_params, sim_params, scenario)

    return Experiment(env)

"""-------------------------------------------------------------"""

import random

if __name__ == "__main__":
    # import the experiment variable
    for x in range(23):
        exp1 = sugiyama_example1(x = x, render=False)
        exp1.run(1, 6000, convert_to_csv=True)
        del exp1
