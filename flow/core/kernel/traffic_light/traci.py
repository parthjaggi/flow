"""Script containing the TraCI traffic light kernel class."""

from collections import defaultdict
from flow.core.kernel.traffic_light import KernelTrafficLight
from flow.core.util import convert_lanes_to_edges
import traci.constants as tc
from traci._trafficlight import Phase, Logic


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

    def set_program_logic(self, node_id, cycle_phases, program_id='0'):
        """
        Set a new program logic to the given traffic light.

        Args:
            node_id (str): traffic light ID.
            cycle_phases (list[dict]): phases in the cycle with their durations and states.
            program_id (str): program ID. Defaults to '0'.
        """
        phases = []
        for phase in cycle_phases:
            phases.append(Phase(duration=phase["duration"], state=phase["state"]))
        
        logic = Logic(programID=program_id, type=0, currentPhaseIndex=0, phases=phases)
        self.kernel_api.trafficlight.setCompleteRedYellowGreenDefinition(node_id, logic)
        self.kernel_api.trafficlight.setProgram(node_id, program_id)
        self.kernel_api.trafficlight.setPhase(node_id, 0)
        self.kernel_api.trafficlight.setPhaseDuration(node_id, phases[0].duration)
    
    def get_program_logics(self, node_id: str) -> list:
        return self.kernel_api.trafficlight.getAllProgramLogics(node_id)

    def get_program_logic(self, node_id: str, program_idx=0):
        """
        Ger the program logic of a traffic light. Returns are in the generic format.

        Args:
            node_id (str): traffic light ID.
            program_idx (int, optional): traffic light program index. Defaults to 0.

        Returns:
            list[dict]: program logic in the form of a list of phases. Including state and durations.
        """
        logic = self.kernel_api.trafficlight.getAllProgramLogics(node_id)[program_idx]
        phases = []
        for phase in logic.getPhases():
            phases.append({
                "colors": phase.state,
                "duration": phase.duration
            })
        
        return phases

    def get_incoming_lanes(self, node_id: str):
        """
        Returns incoming (controlled) lanes for the given intersection.
        Removes duplicates in case some lanes used for multiple movements.

        Args:
            node_id (str): Intersection ID
        """
        lanes = list(dict.fromkeys(self.kernel_api.trafficlight.getControlledLanes(node_id)))
        return lanes

    def get_incoming_edges(self, node_id: str):
        """
        Returns incoming (controlled) edges for the given intersection.
        This method provides the same edge order as get_incoming_lanes

        Args:
            node_id (str): Intersection ID
        """
        lanes = self.kernel_api.trafficlight.getControlledLanes(node_id)
        edges = convert_lanes_to_edges(lanes)
        return edges
        
    def get_incoming_edge_lanes(self, node_id: str):
        """
        Returns incoming (controlled) edges with controlled lanes for the given intersection.

        Args:
            node_id (str): Intersection ID

        Returns:
            dict: [description]
        """
        lanes = list(dict.fromkeys(self.kernel_api.trafficlight.getControlledLanes(node_id)))
        edge_lanes = defaultdict(list)
        for lane in lanes:
            edge_lanes[lane.rsplit('_')[0]].append(lane)
        return edge_lanes
    