"""Script containing the TraCI detector kernel class."""
import traceback

from flow.core.kernel.detector import KernelDetector

# TODO: see use of these exceptions
from traci.exceptions import FatalTraCIError, TraCIException

# TODO: any way to get data based on the frequency provided in detector params


class TraCIDetector(KernelDetector):
    """
    Induction Loop Detector Traci: https://sumo.dlr.de/docs/TraCI/Induction_Loop_Value_Retrieval.html
    Lane Area Detector Traci: https://sumo.dlr.de/docs/TraCI/Lane_Area_Detector_Value_Retrieval.html
    """

    def __init__(self, master_kernel):
        """DocString
        """
        KernelDetector.__init__(self, master_kernel)

        # name of detectors
        self.__ids = []

        # induction loop detectors
        self.__e1_ids = []

        # lane area detectors
        self.__e2_ids = []

        # number of detectors
        self.num_detectors = 0

        # static info about detectors
        self.__detector_infos = {}

        # last step's vehicle data. updated every step
        self.__detector_obs = {}

    def pass_api(self, kernel_api):
        """See parent class.
        """
        KernelDetector.pass_api(self, kernel_api)
        self._initialize()

    def _initialize(self):
        # retrieve ids of detectors
        self.__e1_ids = self.kernel_api.inductionloop.getIDList()
        self.__e2_ids = self.kernel_api.lanearea.getIDList()
        self.__ids = self.__e1_ids + self.__e2_ids

        # add static detector info to self.__detector_infos
        for e1_id in self.__e1_ids:
            detector_info = {
                'position': self.kernel_api.inductionloop.getPosition(e1_id),
                'lane_id': self.kernel_api.inductionloop.getLaneID(e1_id),
            }
            self.__detector_infos[e1_id] = detector_info

        # e2_lengths = self.kernel_api.lanearea.getLength(self.__e1_ids)

        # number of lane area detectors
        self.num_detectors = len(self.__ids)

    def update(self, reset):
        """See parent class."""
        det_obs = {}
        for detector_id in self.__e1_ids:
            det_obs = self.kernel_api.inductionloop.getVehicleData(detector_id)
            self.__detector_obs[detector_id] = det_obs.copy()

    def get_ids(self):
        """See parent class."""
        return self.__ids

    def get_number_of_entered_vehicles(self, detector_id):
        """See parent class."""
        return self.kernel_api.inductionloop.getLastStepVehicleNumber(detector_id)

    def get_mean_speed(self, detector_id):
        """See parent class."""
        return self.kernel_api.inductionloop.get_mean_speed(detector_id)

    def get_vehicle_ids(self, detector_id):
        """See parent class."""
        return self.kernel_api.inductionloop.getLastStepVehicleIDs(detector_id)

    def get_occupany(self, detector_id):
        """See parent class."""
        return self.kernel_api.inductionloop.getLastStepOccupancy(detector_id)

    def get_mean_length(self, detector_id):
        """See parent class."""
        return self.kernel_api.inductionloop.getLastStepMeanLength(detector_id)

    def get_time_since_detection(self, detector_id):
        """See parent class."""
        return self.kernel_api.inductionloop.getTimeSinceDetection(detector_id)
