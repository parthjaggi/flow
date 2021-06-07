"""Environment for training multi-agent experiments."""

from copy import deepcopy
import numpy as np
import random
import traceback
import operator
from gym.spaces import Box

from traci.exceptions import FatalTraCIError
from traci.exceptions import TraCIException

from ray.rllib.env import MultiAgentEnv

from flow.envs.base import Env
from flow.utils.exceptions import FatalFlowError
from flow.core.util import update_dict_using_dict, update_all_dict_values, compactify_episode, first, save_episode_using_numpy


class MultiEnv(MultiAgentEnv, Env):
    """Multi-agent version of base env. See parent class for info."""

    def step(self, rl_actions):
        """
        Check self._step_helper for documentation.
        """
        if self._action_repeat:
            assert len(self._agents) == 1, 'AR not yet tested on multi-agent scenarios.'

            if self._action_repeat_type == 'last_action':
                return self._action_repeat_helper(rl_actions)
            elif self._action_repeat_type == 'extend_action':
                return self._extend_action_repeat_helper(rl_actions)
            elif self._action_repeat_type == 'ff':
                return self._fast_forward_action_repeat_helper(rl_actions)
            else:
                raise NotImplementedError(self._action_repeat_type)
        else:
            return self._step_helper(rl_actions)

    def _action_repeat_helper(self, rl_actions):
        """
        For self._repeat_count number of steps, the given rl_actions is performed over the environment repeatedly.
        Reward returned is the aggregate of rewards during the self._repeat_count number of steps.
        State returned is the final state. 
        Check self._step_helper for more documentation.
        """
        done_all = False
        current_step = 0
        total_reward = {}

        while (current_step < self._repeat_count) and not done_all:
            states, reward, done, infos = self._step_helper(rl_actions)
            total_reward = update_dict_using_dict(total_reward, reward, operator.add)
            done_all = done['__all__']
            current_step += 1

        return states, total_reward, done, infos

    def _extend_action_repeat_helper(self, rl_actions):
        """
        Executes the given rl_actions in the first timestep.
        For future timesteps until the self._repeat_count is reached, EXTEND action is performed.
        Only supported for ExtendChangePhaseConnector action selector for now.
        Check self._step_helper for more documentation.
        """
        EXTEND = 0
        for agent in self._agents.values():
            is_extend_change = type(agent._action_connector).__name__ == 'ExtendChangePhaseConnector'
            assert is_extend_change, 'Action selector should be extend change'

        done_all = False
        current_step = 0
        total_reward = {}

        while (current_step < self._repeat_count) and not done_all:
            if current_step > 0:
                rl_actions = update_all_dict_values(rl_actions, EXTEND)
            states, reward, done, infos = self._step_helper(rl_actions)
            total_reward = update_dict_using_dict(total_reward, reward, operator.add)
            done_all = done['__all__']
            current_step += 1

        return states, total_reward, done, infos

    def _fast_forward_action_repeat_helper(self, rl_actions):
        """
        Executes given rl_actions. If next timestep is not actionable, the same action is repeated until actionable timestep is encountered.
        SecondBasedTrafficLight will ensure only reasonable actions are executed on the environment during non-actionable timesteps.
        For future actionable timesteps, EXTEND action is performed until self._repeat_count is reached.
        Check self._step_helper for more documentation.
        """
        EXTEND = 0
        for agent in self._agents.values():
            is_extend_change = type(agent._action_connector).__name__ == 'ExtendChangePhaseConnector'
            assert is_extend_change, 'Action selector should be extend change'

        done_all = False
        current_step = 0
        total_reward = {}

        while (current_step < self._repeat_count) and not done_all:
            if current_step > 0:
                rl_actions = update_all_dict_values(rl_actions, EXTEND)

            is_actionable = False
            while not is_actionable and not done_all:
                states, reward, done, infos = self._step_helper(rl_actions)
                is_actionable = next(iter(states.values()))['actionable'].all()
                total_reward = update_dict_using_dict(total_reward, reward, operator.add)
                done_all = done['__all__']

            current_step += 1
        return states, total_reward, done, infos

    def _step_helper(self, rl_actions):
        """Advance the environment by one step.

        Assigns actions to autonomous and human-driven agents (i.e. vehicles,
        traffic lights, etc...). Actions that are not assigned are left to the
        control of the simulator. The actions are then used to advance the
        simulator by the number of time steps requested per environment step.

        Results from the simulations are processed through various classes,
        such as the Vehicle and TrafficLight kernels, to produce standardized
        methods for identifying specific network state features. Finally,
        results from the simulator are used to generate appropriate
        observations.

        Parameters
        ----------
        rl_actions : array_like
            an list of actions provided by the rl algorithm

        Returns
        -------
        observation : dict of array_like
            agent's observation of the current environment
        reward : dict of floats
            amount of reward associated with the previous state/action pair
        done : dict of bool
            indicates whether the episode has ended
        info : dict
            contains other diagnostic information from the previous action
        """
        for _ in range(self.env_params.sims_per_step):
            self.time_counter += 1
            self.step_counter += 1

            # perform acceleration actions for controlled human-driven vehicles
            if len(self.k.vehicle.get_controlled_ids()) > 0:
                accel = []
                for veh_id in self.k.vehicle.get_controlled_ids():
                    accel_contr = self.k.vehicle.get_acc_controller(veh_id)
                    action = accel_contr.get_action(self)
                    accel.append(action)
                self.k.vehicle.apply_acceleration(
                    self.k.vehicle.get_controlled_ids(), accel)

            # perform lane change actions for controlled human-driven vehicles
            if len(self.k.vehicle.get_controlled_lc_ids()) > 0:
                direction = []
                for veh_id in self.k.vehicle.get_controlled_lc_ids():
                    target_lane = self.k.vehicle.get_lane_changing_controller(
                        veh_id).get_action(self)
                    direction.append(target_lane)
                self.k.vehicle.apply_lane_change(
                    self.k.vehicle.get_controlled_lc_ids(),
                    direction=direction)

            # perform (optionally) routing actions for all vehicle in the
            # network, including rl and sumo-controlled vehicles
            routing_ids = []
            routing_actions = []
            for veh_id in self.k.vehicle.get_ids():
                if self.k.vehicle.get_routing_controller(veh_id) is not None:
                    routing_ids.append(veh_id)
                    route_contr = self.k.vehicle.get_routing_controller(veh_id)
                    routing_actions.append(route_contr.choose_route(self))
            self.k.vehicle.choose_routes(routing_ids, routing_actions)

            self.apply_rl_actions(rl_actions)

            # If applicable, generate lane arrivals scheduled for this simstep
            if self.network.net_params.arrivals_remaining:
                self.network.net_params.arrivals_remaining = self.gen_lane_arrivals()

            self.additional_command()

            # advance the simulation in the simulator by one step
            self.k.simulation.simulation_step()

            # store new observations in the vehicles and traffic lights class
            self.k.update(reset=False)

            # update the colors of vehicles
            if self.sim_params.render:
                self.k.vehicle.update_vehicle_colors()

            # crash encodes whether the simulator experienced a collision
            crash = self.k.simulation.check_collision()
            crash = 0

            # stop collecting new simulation steps if there is a collision
            if crash:
                break

        states = self.get_state()
        done = {key: key in self.k.vehicle.get_arrived_ids()
                for key in states.keys()}
        if crash or (self.time_counter >= self.env_params.sims_per_step *
                     (self.env_params.warmup_steps + self.env_params.horizon)):
            done['__all__'] = True
        else:
            done['__all__'] = False
        infos = {key: {} for key in states.keys()}

        # compute the reward
        if self.env_params.clip_actions:
            rl_actions = self.clip_actions(rl_actions)
            reward = self.compute_reward(rl_actions, fail=crash)
        else:
            reward = self.compute_reward(rl_actions, fail=crash)

        for rl_id in self.k.vehicle.get_arrived_rl_ids():
            done[rl_id] = True
            reward[rl_id] = 0
            states[rl_id] = None  # TODO: Nicolas did this instead of this "np.zeros(self.observation_space.shape[0])"
        
        if self.env_params.store_transitions:
            self._save_transition(states, reward, rl_actions, done)

        return states, reward, done, infos

    def _save_transition(self, obs, reward, action, done):
        """
        Appends incoming transition to self.transitions list.
        On episode end, compactifies and saves the episode.

        Args:
            obs (dict): Observation dictionary.
            reward (dict): Reward dictionary.
            action (dict): Action dictionary.
            done (dict): Done dictionary.
        """
        if getattr(self, 'transitions', None) is None:
            self.transitions = []
            self.intersection_id = next(iter(obs.keys()))
            assert not len(obs.keys()) > 1, 'currently only single intersection storage is supported'
        
        self.transitions.append({'observation': obs, 'reward': reward, 'action': action})

        if done['__all__']:
            episode = compactify_episode(self.transitions, self.intersection_id)
            save_episode_using_numpy(episode, '{}_detector_custom'.format(self.env_params.subfolder), self.env_params.subfolder)
            self.transitions = []

    def reset(self, new_inflow_rate=None, perform_extra_work=None):
        """Reset the environment.

        This method is performed in between rollouts. It resets the state of
        the environment, and re-initializes the vehicles in their starting
        positions.

        If "shuffle" is set to True in InitialConfig, the initial positions of
        vehicles is recalculated and the vehicles are shuffled.

        Returns
        -------
        observation : dict of array_like
            the initial observation of the space. The initial reward is assumed
            to be zero.
        """
        # reset the time counter
        self.time_counter = 0

        # Now that we've passed the possibly fake init steps some rl libraries
        # do, we can feel free to actually render things
        if self.should_render:
            self.sim_params.render = True
            # got to restart the simulation to make it actually display anything
            self.restart_simulation(self.sim_params)

        # warn about not using restart_instance when using inflows
        if len(self.net_params.inflows.get()) > 0 and \
                not self.sim_params.restart_instance:
            print(
                "**********************************************************\n"
                "**********************************************************\n"
                "**********************************************************\n"
                "WARNING: Inflows will cause computational performance to\n"
                "significantly decrease after large number of rollouts. In \n"
                "order to avoid this, set SumoParams(restart_instance=True).\n"
                "**********************************************************\n"
                "**********************************************************\n"
                "**********************************************************"
            )

        if self.sim_params.restart_instance or \
                (self.step_counter > 2e6 and self.simulator != 'aimsun'):
            self.step_counter = 0
            # issue a random seed to induce randomness into the next rollout
            self.sim_params.seed = random.randint(0, 1e5)

            self.k.vehicle = deepcopy(self.initial_vehicles)
            self.k.vehicle.master_kernel = self.k
            # restart the sumo instance
            self.restart_simulation(self.sim_params)

        # perform shuffling (if requested)
        elif self.initial_config.shuffle:
            self.setup_initial_state()

        # clear all vehicles from the network and the vehicles class
        if self.simulator == 'traci':
            for veh_id in self.k.kernel_api.vehicle.getIDList():  # FIXME: hack
                try:
                    self.k.vehicle.remove(veh_id)
                except (FatalTraCIError, TraCIException):
                    print(traceback.format_exc())

        # clear all vehicles from the network and the vehicles class
        # FIXME (ev, ak) this is weird and shouldn't be necessary
        for veh_id in list(self.k.vehicle.get_ids()):
            # do not try to remove the vehicles from the network in the first
            # step after initializing the network, as there will be no vehicles
            if self.step_counter == 0:
                continue
            try:
                self.k.vehicle.remove(veh_id)
            except (FatalTraCIError, TraCIException):
                print("Error during start: {}".format(traceback.format_exc()))

        # do any additional resetting of the vehicle class needed
        self.k.vehicle.reset()

        # reintroduce the initial vehicles to the network
        for veh_id in self.initial_ids:
            type_id, edge, lane_index, pos, speed = \
                self.initial_state[veh_id]

            try:
                self.k.vehicle.add(
                    veh_id=veh_id,
                    type_id=type_id,
                    edge=edge,
                    lane=lane_index,
                    pos=pos,
                    speed=speed)
            except (FatalTraCIError, TraCIException):
                # if a vehicle was not removed in the first attempt, remove it
                # now and then reintroduce it
                self.k.vehicle.remove(veh_id)
                if self.simulator == 'traci':
                    self.k.kernel_api.vehicle.remove(veh_id)  # FIXME: hack
                self.k.vehicle.add(
                    veh_id=veh_id,
                    type_id=type_id,
                    edge=edge,
                    lane=lane_index,
                    pos=pos,
                    speed=speed)

        # Reset vehicle lane arrivals
        if self.network.net_params.lane_arrival_sched is not None:
            self.network.net_params.lane_arrivals_iter = iter(self.network.net_params.lane_arrival_sched)
            self.network.net_params.arrivals_remaining = True

        # TODO [nicolas added this]
        if perform_extra_work:
            perform_extra_work()

        # advance the simulation in the simulator by one step
        self.k.simulation.simulation_step()

        # update the information in each kernel to match the current state
        self.k.update(reset=True)

        # update the colors of vehicles
        if self.sim_params.render:
            self.k.vehicle.update_vehicle_colors()

        # check to make sure all vehicles have been spawned
        if len(self.initial_ids) > self.k.vehicle.num_vehicles:
            missing_vehicles = list(
                set(self.initial_ids) - set(self.k.vehicle.get_ids()))
            msg = '\nNot enough vehicles have spawned! Bad start?\n' \
                  'Missing vehicles / initial state:\n'
            for veh_id in missing_vehicles:
                msg += '- {}: {}\n'.format(veh_id, self.initial_state[veh_id])
            raise FatalFlowError(msg=msg)

        # perform (optional) warm-up steps before training
        for _ in range(self.env_params.warmup_steps):
            observation, _, _, _ = self.step(rl_actions=None)

        # render a frame
        self.render(reset=True)

        return self.get_state()

    def clip_actions(self, rl_actions=None):
        """Clip the actions passed from the RL agent.

        If no actions are provided at any given step, the rl agents default to
        performing actions specified by sumo.

        Parameters
        ----------
        rl_actions : array_like
            list of actions provided by the RL algorithm

        Returns
        -------
        rl_clipped : array_like
            The rl_actions clipped according to the box
        """
        # ignore if no actions are issued
        if rl_actions is None:
            return None

        # clip according to the action space requirements
        # [TODO] nicolas removed this because it would assume all agents share the same action space.
        # if isinstance(self.action_space, Box):
        #     for key, action in rl_actions.items():
        #         rl_actions[key] = np.clip(
        #             action,
        #             a_min=self.action_space.low,
        #             a_max=self.action_space.high)
        return rl_actions

    def apply_rl_actions(self, rl_actions=None):
        """Specify the actions to be performed by the rl agent(s).

        If no actions are provided at any given step, the rl agents default to
        performing actions specified by sumo.

        Parameters
        ----------
        rl_actions : dict of array_like
            dict of list of actions provided by the RL algorithm
        """
        # ignore if no actions are issued
        if rl_actions is None:
            return

        # clip according to the action space requirements
        clipped_actions = self.clip_actions(rl_actions)
        self._apply_rl_actions(clipped_actions)

    def gen_lane_arrivals(self):
        """
        If a schedule of lane arrivals is attached to the environment,
        generates the vehicles according to the attached schedule.
        Returns a bool that determines if this function is called again
        on the following simulation step
        """
        if self.network.net_params.lane_arrivals_iter is None:
            return False    # No vehicle arrivals scheduled

        try:
            cur_step_arrivals = next(self.network.net_params.lane_arrivals_iter)
        except StopIteration:
            return False    # No more vehicles to be generated

        # Generate a vehicle for each lane that is on the schedule
        # for the current simulation step
        for lane_id, veh_id in cur_step_arrivals:
            edge_id = lane_id[:-2]
            lane = lane_id[-1]
            self.k.vehicle.add(veh_id, 'human', edge_id, 0, lane, 10)

        # If got here, call this function again on the next sim step
        return True

