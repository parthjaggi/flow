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


def sugiyama_example1(render=None, v_des=5, l=220):
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
    sim_params = SumoParams(sim_step=0.1, render=False, emission_path='\l={}-v_des={}'.format(l,v_des) )
    if render is not None:  
        sim_params.render = render

		
    vehicles = VehicleParams()
    vehicles.add(
        veh_id="idm",
        acceleration_controller=(BCMController, {
            "v_des": v_des,
            "noise": 0.1,
        }),
        routing_controller=(ContinuousRouter, {}),
        num_vehicles=22)  

    env_params = EnvParams(additional_params=ADDITIONAL_ENV_PARAMS)
    

    additional_net_params = ADDITIONAL_NET_PARAMS.copy()
    net_params = NetParams(
    additional_params={
        'length': l, 
        'lanes': 1, 
        'speed_limit': 30, 
        'resolution': 40
    }
)

    initial_config = InitialConfig(perturbation=0, spacing='uniform')

    scenario = LoopScenario(
        name="sugiyama",
        vehicles=vehicles,
        net_params=net_params,
        initial_config=initial_config)

    env = AccelEnv(env_params, sim_params, scenario)
    	

    return Experiment(env)

"""-------------------------------------------------------------"""

if __name__ == "__main__":
    # import the experiment variable
    for v in range(5, 31):
        for l in np.arange(220, 291, 5):
            for i in range(1):
               exp1 = sugiyama_example1(v_des=v, l=l, render=False)
               exp1.run(1,3000,convert_to_csv=True) 
               del exp1

