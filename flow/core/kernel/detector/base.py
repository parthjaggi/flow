"""Script containing the base detector kernel class."""


class KernelDetector(object):
    """Docstring
    """

    def __init__(self, master_kernel):
        """DocString
        """
        self.master_kernel = master_kernel
        self.kernel_api = None

    def pass_api(self, kernel_api):
        """DocString
        """
        self.kernel_api = kernel_api

    # State acquisition methods

    def update(self, reset):
        """DocString
        """
        raise NotImplementedError

    def get_ids(self):
        """DocString
        """
        raise NotImplementedError

    def get_number_of_entered_vehicles(self, detector_id):
        """DocString
        """
        raise NotImplementedError

    def get_mean_speed(self, detector_id):
        """DocString
        """
        raise NotImplementedError

    def get_vehicle_ids(self, detector_id):
        """DocString
        """
        raise NotImplementedError

    def get_occupany(self, detector_id):
        """DocString
        """
        raise NotImplementedError

    def get_mean_length(self, detector_id):
        """DocString
        """
        raise NotImplementedError

    def get_time_since_detection(self, detector_id):
        """DocString
        """
        raise NotImplementedError
