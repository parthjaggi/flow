"""Used as an example of sugiyama experiment.
This example consists of 22 OVM cars on a ring creating shockwaves.
"""

from flow.controllers import IDMController, ContinuousRouter,BCMController, PNSController, OVMController, LACController, PISaturation, FollowerStopper
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


def sugiyama_example1(render=True, x=0,cont='LAC'):
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
                            emission_path='\OVM_{}/{}OVM_{}{}'.format(cont,22-x,x,cont))
    if render is not None:
        sim_params.render = render

    if cont == "FS":
        controller = FollowerStopper
    if cont == "LAC":
        controller = LACController    
    if cont == "PI":
        controller = PISaturation
    if cont == "BCM":
        controller = BCMController
    if cont == "PNS":
        controller = PNSController 

    vehicles = VehicleParams()
    vehicles.add(
        veh_id="OVM",
        acceleration_controller=(OVMController, {"noise":0.1}),
        routing_controller=(ContinuousRouter, {}),
        num_vehicles=22-x)
    vehicles.add(
        veh_id="{}".format(cont),
        acceleration_controller=(controller, {}),
        routing_controller=(ContinuousRouter, {}),
        num_vehicles=x)
    
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
        exp1 = sugiyama_example1(x = x,cont='LAC', render=False)
        exp1.run(1, 6000, convert_to_csv=True)
        print('{} left'.format(23-x)) 
        print('done') 
        del exp1
    for x in range(23):
        exp1 = sugiyama_example1(x = x,cont='PI', render=False)
        exp1.run(1, 6000, convert_to_csv=True)
        print('{} left'.format(23-x)) 
        print('done') 
        del exp1
    for x in range(23):
        exp1 = sugiyama_example1(x = x,cont='FS', render=False)
        exp1.run(1, 6000, convert_to_csv=True)
        print('{} left'.format(23-x)) 
        print('done') 
        del exp1
    for x in range(23):
        exp1 = sugiyama_example1(x = x,cont='BCM', render=False)
        exp1.run(1, 6000, convert_to_csv=True)
        print('{} left'.format(23-x)) 
        print('done') 
        del exp1
    for x in range(23):
        exp1 = sugiyama_example1(x = x,cont='PNS', render=False)
        exp1.run(1, 6000, convert_to_csv=True)
        print('{} left'.format(23-x)) 
        print('done') 
        del exp1