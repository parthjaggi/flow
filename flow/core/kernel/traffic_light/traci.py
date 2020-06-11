"""Script containing the TraCI traffic light kernel class."""

from flow.core.kernel.traffic_light import KernelTrafficLight
import traci.constants as tc


class TraCITrafficLight(KernelTrafficLight):
    """Sumo traffic light kernel.

    Implements all methods discussed in the base traffic light kernel class.
    """

    def __init__(self, master_kernel):
        """Instantiate the sumo traffic light kernel.

        Parameters
        ----------
        master_kernel : flow.core.kernel.Kernel
            the higher level kernel (used to call methods from other
            sub-kernels)
        """
        KernelTrafficLight.__init__(self, master_kernel)

        self.__tls = dict()  # contains current time step traffic light data
        self.__tls_properties = dict()  # traffic light xml properties

        # names of nodes with traffic lights
        self.__ids = []

        # number of traffic light nodes
        self.num_traffic_lights = 0

    def pass_api(self, kernel_api):
        """See parent class.

        Subscriptions and vehicle IDs are also added here.
        """
        KernelTrafficLight.pass_api(self, kernel_api)

        # names of nodes with traffic lights
        self.__ids = kernel_api.trafficlight.getIDList()

        # number of traffic light nodes
        self.num_traffic_lights = len(self.__ids)

        # subscribe the traffic light signal data
        for node_id in self.__ids:
            self.kernel_api.trafficlight.subscribe(
                node_id, [tc.TL_RED_YELLOW_GREEN_STATE])

    def update(self, reset):
        """See parent class."""
        tls_obs = {}
        for tl_id in self.__ids:
            tls_obs[tl_id] = \
                self.kernel_api.trafficlight.getSubscriptionResults(tl_id)
        self.__tls = tls_obs.copy()

    def get_ids(self):
        """See parent class."""
        return self.__ids

    def set_state(self, node_id, state, link_index="all"):
        """See parent class."""
        if link_index == "all":
            # if lights on all lanes are changed
            self.kernel_api.trafficlight.setRedYellowGreenState(
                tlsID=node_id, state=state)
        else:
            # if lights on a single lane is changed
            self.kernel_api.trafficlight.setLinkState(
                tlsID=node_id, tlsLinkIndex=link_index, state=state)

    def get_state(self, node_id):
        """See parent class."""
        return self.__tls[node_id][tc.TL_RED_YELLOW_GREEN_STATE]

    def set_cycle_logic(self, node_id, cycle_phases):
        from traci._trafficlight import Phase, Logic
        phases = []
        for phase in cycle_phases:
            phases.append(Phase(duration=phase["duration"], state=phase["state"]))
        # TODO: programID may need to be dynamic
        logic = Logic(programID='0', type=0, currentPhaseIndex=0, phases=phases)
        self.kernel_api.trafficlight.setCompleteRedYellowGreenDefinition(node_id, logic)
        self.kernel_api.trafficlight.setProgram(node_id, '0')
        self.kernel_api.trafficlight.setPhase(node_id, 0)
        self.kernel_api.trafficlight.setPhaseDuration(node_id, phases[0].duration)

    def get_incoming_lanes(self, node_id: str):
        """
        Returns incoming (or controlled) lanes for the given intersection.
        Removes duplicates in case some lanes used for multiple movements.

        Args:
            node_id (str): Intersection ID
        """
        lanes = list(dict.fromkeys(self.kernel_api.trafficlight.getControlledLanes(node_id)))
        return lanes

    def get_incoming_edges(self, node_id: str):
        """
        Returns incoming (or controlled) edges for the given intersection.

        Args:
            node_id (str): Intersection ID
        """
        lanes = self.kernel_api.trafficlight.getControlledLanes(node_id)
        edges = self._get_edges_from_lanes(lanes)
        return edges

    def _get_edges_from_lanes(self, lanes):
        """
        Convert lanes (iterable) to edges (iterable).
        Remove lane index from the end and then remove duplicates while retaining order.
        
        >>> lanes
        >>> ['1175109_0', '1175109_1', '1175109_2', '1183934_0', '1183934_1', '1183934_2']

        >>> self._get_edges_from_lanes(lanes)
        >>> {'1175109', '1183934'}
        """
        return list(dict.fromkeys(map(lambda x: x.rsplit('_', 1)[0], lanes)))
        