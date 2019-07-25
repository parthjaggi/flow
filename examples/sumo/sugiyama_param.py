"""Used as an example of sugiyama experiment.
This example consists of 22 IDM cars on a ring creating shockwaves.
"""

from flow.controllers import IDMController, ContinuousRouter,BCMController,FollowerStopper,PISaturation,RLController,LACController
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


def sugiyama_example1(render=None, l=220,v0=5):
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
                            emission_path='\IDM_noise/l={}_vo={}'.format(l, v0))
    if render is not None:
        sim_params.render = render

    vehicles = VehicleParams()
    vehicles.add(
        veh_id="idm",
        acceleration_controller=(IDMController, {"noise":0.1,"v0":v0),
        routing_controller=(ContinuousRouter, {}),
        num_vehicles=22)
 
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
    for l in np.arrange(220,5,320):
        for v0 in np.arrange(5,1,30): 
            exp1 = sugiyama_example1(l = l,v0=v0, render=False)
            exp1.run(1, 6000, convert_to_csv=True)
            del exp1