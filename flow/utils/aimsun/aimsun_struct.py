"""
Script containing objects used to store vehicle information in Aimsun.
"""

INFOS_ATTR_BY_INDEX = [
    'CurrentPos', 'distance2End', 'xCurrentPos', 'yCurrentPos', 'zCurrentPos',
    'xCurrentPosBack', 'yCurrentPosBack', 'zCurrentPosBack', 'CurrentSpeed', 'TotalDistance',
    'SectionEntranceT', 'CurrentStopTime', 'stopped', 'idSection', 'segment',
    'numberLane', 'idJunction', 'idSectionFrom', 'idLaneFrom', 'idSectionTo',
    'idLaneTo'
]
NUM_ATTRS = len(INFOS_ATTR_BY_INDEX)

class InfVeh(object):
    """Dynamics (tracking) information for vehicles in Aimsun.

    Attributes
    ----------
    CurrentPos : float
        Position inside the section. The distance (metres or feet, depending on
        the units defined in the network) from the beginning of the section or
        position inside the junction given as the distance from the entrance to
        the junction
    distance2End : float
        Distance to end of the section (metres or feet, depending on the units
        defined in the network) when the vehicle is located in a section or the
        distance to the end of the turn when the vehicle is in a junction
    xCurrentPos : float
        x coordinates of the middle point of the front bumper of the vehicle
    yCurrentPos : float
        y coordinates of the middle point of the front bumper of the vehicle
    zCurrentPos : float
        z coordinates of the middle point of the front bumper of the vehicle
    xCurrentPosBack : float
        x coordinates of the middle point of the rear bumper of the vehicle
    yCurrentPosBack : float
        y coordinates of the middle point of the rear bumper of the vehicle
    zCurrentPosBack : float
        z coordinates of the middle point of the rear bumper of the vehicle
    CurrentSpeed : float
        Current speed (in km/h or mph, depending on the units defined in the
        network)
    TotalDistance : float
        Total distance travelled (metres or feet)
    SectionEntranceT : float
        The absolute entrance time of the vehicle into the current section
    CurrentStopTime : float
        The current stop time
    stopped : float
        True if the vehicle remains stopped
    idSection : int
        The section identifier
    segment : int
        Segment number of the section where the vehicle is located (from 0 to
        n-1)
    numberLane : int
        Lane number in the segment (from 1, the rightmost lane, to N, the
        leftmost lane)
    idJunction : int
        The junction identifier
    idSectionFrom : int
        Origin section identifier when the vehicle is in a node
    idLaneFrom : int
        Origin sections lane where the vehicle enters the junction from. 1
        being the rightmost lane and N the leftmost lane, being N the number of
        lanes in the origin section
    idSectionTo : int
        Destination section identifier when the vehicle is in a node
    idLaneTo : int
        Destination sections lane where the vehicle exits the junction to. 1
        being the rightmost lane and N the leftmost lane, being N the number of
        lanes in the destination section
    """

    def __init__(self,
                 CurrentPos = None,
                 distance2End = None,
                 xCurrentPos = None,
                 yCurrentPos = None,
                 zCurrentPos = None,
                 xCurrentPosBack = None,
                 yCurrentPosBack = None,
                 zCurrentPosBack = None,
                 CurrentSpeed = None,
                 TotalDistance = None,
                 SectionEntranceT = None,
                 CurrentStopTime = None,
                 stopped = None,
                 idSection = None,
                 segment = None,
                 numberLane = None,
                 idJunction = None,
                 idSectionFrom = None,
                 idLaneFrom = None,
                 idSectionTo = None,
                 idLaneTo = None ):
        """Instantiate InfVeh."""
        self.CurrentPos = CurrentPos
        self.distance2End = distance2End
        self.xCurrentPos = xCurrentPos
        self.yCurrentPos = yCurrentPos
        self.zCurrentPos = zCurrentPos
        self.xCurrentPosBack = xCurrentPosBack
        self.yCurrentPosBack = yCurrentPosBack
        self.zCurrentPosBack = zCurrentPosBack
        self.CurrentSpeed = CurrentSpeed
        self.TotalDistance = TotalDistance
        self.SectionEntranceT = SectionEntranceT
        self.CurrentStopTime = CurrentStopTime
        self.stopped = stopped

        # Information in Vehicle when it is in a section
        self.idSection = idSection
        self.segment = segment
        self.numberLane = numberLane

        # Information in Vehicle when it is in a node
        self.idJunction = idJunction
        self.idSectionFrom = idSectionFrom
        self.idLaneFrom = idLaneFrom
        self.idSectionTo = idSectionTo
        self.idLaneTo = idLaneTo

    def __str__(self):
        return(f"CurrentPos = {self.CurrentPos}, "
               f"distance2End = {self.distance2End}, "
               f"xCurrentPos = {self.xCurrentPos}, "
               f"yCurrentPos = {self.yCurrentPos}, "
               f"zCurrentPos = {self.zCurrentPos}, "
               f"xCurrentPosBack = {self.xCurrentPosBack}, "
               f"yCurrentPosBack = {self.yCurrentPosBack}, "
               f"zCurrentPosBack = {self.zCurrentPosBack}, "
               f"CurrentSpeed = {self.CurrentSpeed}, "
               f"TotalDistance = {self.TotalDistance}, "
               f"SectionEntranceT = {self.SectionEntranceT}, "
               f"CurrentStopTime = {self.CurrentStopTime}, "
               f"stopped = {self.stopped}, "
               f"idSection = {self.idSection}, "
               f"segment = {self.segment}, "
               f"numberLane = {self.numberLane}, "
               f"idJunction = {self.idJunction}, "
               f"idSectionFrom = {self.idSectionFrom}, "
               f"idLaneFrom = {self.idLaneFrom}, "
               f"idSectionTo = {self.idSectionTo}, "
               f"idLaneTo = {self.idLaneTo}")

    def __eq__(self, other):
    # Some of the entries are floats, so round to two decimal places (ints are rounded to themselves)
    # Because of the usage of a bitmap/bitmask, some attributes may be set to None

        self_none_indices = [i for i in range(NUM_ATTRS) if getattr(self, INFOS_ATTR_BY_INDEX[i]) is None]
        other_none_indices = [i for i in range(NUM_ATTRS) if getattr(other, INFOS_ATTR_BY_INDEX[i]) is None]

        if self_none_indices != other_none_indices:
            return False   # Some of the attributes are None in one class and not None in another

        # Remove Nones
        indices = [i for i in range(21) if i not in self_none_indices]

        rounded_self_attrs  = [ round(getattr(self, INFOS_ATTR_BY_INDEX[i]), 2) for i in indices]
        rounded_other_attrs = [ round(getattr(other, INFOS_ATTR_BY_INDEX[i]), 2) for i in indices]

        return rounded_self_attrs == rounded_other_attrs

    def __ne__(self, other):
        return not self.__eq__(other)

    def tuple(self):
        return (getattr(self, INFOS_ATTR_BY_INDEX[i]) for i in range(NUM_ATTRS))



STATIC_INFOS_ATTR_BY_INDEX = [
    'report', 'idVeh', 'type', 'length', 'width',
    'maxDesiredSpeed', 'maxAcceleration', 'normalDeceleration', 'maxDeceleration', 'speedAcceptance',
    'minDistanceVeh', 'giveWayTime', 'guidanceAcceptance', 'enrouted', 'equipped',
    'tracked', 'keepfastLane', 'headwayMin', 'sensitivityFactor', 'reactionTime',
    'reactionTimeAtStop', 'reactionTimeAtTrafficLight', 'centroidOrigin', 'centroidDest', 'idsectionExit',
    'idLine'
]
NUM_STATIC_ATTRS = len(STATIC_INFOS_ATTR_BY_INDEX)

class StaticInfVeh(object):
    """Static information for vehicles in Aimsun.

    Attributes
    ----------
    report : int
        0, OK, else error code
    idVeh : int
        Vehicle identifier
    type : int
        Vehicle type (car, bus, truck, etc.)
    length : float
        Vehicle length (m or feet, depending on the units defined in the
        network)
    width : float
        Vehicle width (m or feet, depending on the units defined in the
        network)
    maxDesiredSpeed : float
        Maximum desired speed of the vehicle (km/h or mph, depending on the
        units defined in the network)
    maxAcceleration : float
        Maximum acceleration of the vehicle (m/s2 or ft/ s2, depending on
        the units defined in the network)
    normalDeceleration : float
        Maximum deceleration of the vehicle that can apply under normal
        conditions (m/s2 or ft/ s2, depending the units defined in the
        network)
    maxDeceleration : float
        Maximum deceleration of the vehicle that can apply under special
        conditions (m/s2 or ft/ s2, depending the units defined in the
        network)
    speedAcceptance : float
        Degree of acceptance of the speed limits
    minDistanceVeh : float
        Distance that the vehicle keeps between itself and the preceding
        vehicle (metres or feet, depending on the units defined in the
        network)
    giveWayTime : float
        Time after which the vehicle becomes more aggressive in give-way
        situations (seconds)
    guidanceAcceptance : float
        Level of compliance of the vehicle to guidance indications
    enrouted : int
        0 means vehicle will not change path enroute, 1 means vehicle will
        change path enroute depending on the percentage of enrouted
        vehicles defined
    equipped : int
        0 means vehicle not equipped, 1 means vehicle equipped
    tracked : int
        0 means vehicle not tracked, 1 means vehicle tracked
    keepfastLane : bool
        True means the vehicle keeps fast lane during overtaking
    headwayMin : float
        Minimum headway to the leader
    sensitivityFactor : float
        Estimation of the acceleration of the leader
    reactionTime : float
        Reaction time of the vehicle
    reactionTimeAtStop : float
        Reaction time at stop of the vehicle
    reactionTimeAtTrafficLight : float
        Reaction time of the vehicle when stopped the first one of the
        queue in a traffic light
    centroidOrigin : int
        Identifier of centroid origin of the vehicle, when the traffic
        conditions are defined by an OD matrix
    centroidDest : int
        Identifier of centroid destination of the vehicle, when the traffic
        conditions are defined by an OD matrix
    idsectionExit : int
        Identifier of exit section destination of the vehicle, when the
        destination centroid uses percentages as destination (otherwise is
        –1) and the traffic conditions are defined by an OD matrix
    idLine : int
        Identifier of Public Transport Line, when the vehicle has been
        generated as a public transport vehicle
    """

    def __init__(self,
                 report=None,
                 idVeh=None,
                 type=None,
                 length=None,
                 width=None,
                 maxDesiredSpeed=None,
                 maxAcceleration=None,
                 normalDeceleration=None,
                 maxDeceleration=None,
                 speedAcceptance=None,
                 minDistanceVeh=None,
                 giveWayTime=None,
                 guidanceAcceptance=None,
                 enrouted=None,
                 equipped=None,
                 tracked=None,
                 keepfastLane=None,
                 headwayMin=None,
                 sensitivityFactor=None,
                 reactionTime=None,
                 reactionTimeAtStop=None,
                 reactionTimeAtTrafficLight=None,
                 centroidOrigin=None,
                 centroidDest=None,
                 idsectionExit=None,
                 idLine=None):
        """Instantiate StaticInfVeh."""
        self.report = report
        self.idVeh = idVeh
        self.type = type
        self.length = length
        self.width = width
        self.maxDesiredSpeed = maxDesiredSpeed
        self.maxAcceleration = maxAcceleration
        self.normalDeceleration = normalDeceleration
        self.maxDeceleration = maxDeceleration
        self.speedAcceptance = speedAcceptance
        self.minDistanceVeh = minDistanceVeh
        self.giveWayTime = giveWayTime
        self.guidanceAcceptance = guidanceAcceptance
        self.enrouted = enrouted
        self.equipped = equipped
        self.tracked = tracked
        self.keepfastLane = keepfastLane
        self.headwayMin = headwayMin
        self.sensitivityFactor = sensitivityFactor
        self.reactionTime = reactionTime
        self.reactionTimeAtStop = reactionTimeAtStop
        self.reactionTimeAtTrafficLight = reactionTimeAtTrafficLight
        self.centroidOrigin = centroidOrigin
        self.centroidDest = centroidDest
        self.idsectionExit = idsectionExit
        self.idLine = idLine

    def __str__(self):
        return (f"report = {self.report}, "
                f"idVeh = {self.idVeh}, "
                f"type = {self.type}, "
                f"length = {self.length}, "
                f"width = {self.width}, "
                f"maxDesiredSpeed = {self.maxDesiredSpeed}, "
                f"maxAcceleration = {self.maxAcceleration}, "
                f"normalDeceleration = {self.normalDeceleration}, "
                f"maxDeceleration = {self.maxDeceleration}, "
                f"speedAcceptance = {self.speedAcceptance}, "
                f"minDistanceVeh = {self.minDistanceVeh}, "
                f"giveWayTime = {self.giveWayTime}, "
                f"guidanceAcceptance = {self.guidanceAcceptance}, "
                f"enrouted = {self.enrouted}, "
                f"equipped = {self.equipped}, "
                f"tracked = {self.tracked}, "
                f"keepfastLane = {self.keepfastLane}, "
                f"headwayMin = {self.headwayMin}, "
                f"sensitivityFactor = {self.sensitivityFactor}, "
                f"reactionTime = {self.reactionTime}, "
                f"reactionTimeAtStop = {self.reactionTimeAtStop}, "
                f"reactionTimeAtTrafficLight = {self.reactionTimeAtTrafficLight}, "
                f"centroidOrigin = {self.centroidOrigin}, "
                f"centroidDest = {self.centroidDest}, "
                f"idsectionExit = {self.idsectionExit}, "
                f"idLine = {self.idLine}")

    def __eq__(self, other):
        # When comparing floats, round to two decimal places
        return ( self.report == other.report and
                 self.idVeh == other.idVeh and
                 self.type == other.type and
                 round(self.length, 2) == round(other.length, 2) and
                 round(self.width, 2) == round(other.width, 2) and
                 round(self.maxDesiredSpeed, 2) == round(other.maxDesiredSpeed, 2) and
                 round(self.maxAcceleration, 2) == round(other.maxAcceleration, 2) and
                 round(self.normalDeceleration, 2) == round(other.normalDeceleration, 2) and
                 round(self.maxDeceleration, 2) == round(other.maxDeceleration, 2) and
                 round(self.speedAcceptance, 2) == round(other.speedAcceptance, 2) and
                 round(self.minDistanceVeh, 2) == round(other.minDistanceVeh, 2) and
                 round(self.giveWayTime, 2) == round(other.giveWayTime, 2) and
                 round(self.guidanceAcceptance, 2) == round(other.guidanceAcceptance, 2) and
                 self.enrouted == other.enrouted and
                 self.equipped == other.equipped and
                 self.tracked == other.tracked and
                 self.keepfastLane == other.keepfastLane and
                 round(self.headwayMin, 2) == round(other.headwayMin, 2) and
                 round(self.sensitivityFactor, 2) == round(other.sensitivityFactor, 2) and
                 round(self.reactionTime, 2) == round(other.reactionTime, 2) and
                 round(self.reactionTimeAtStop, 2) == round(other.reactionTimeAtStop, 2) and
                 round(self.reactionTimeAtTrafficLight, 2) == round(other.reactionTimeAtTrafficLight, 2) and
                 self.centroidOrigin == other.centroidOrigin and
                 self.centroidDest == other.centroidDest and
                 self.idsectionExit == other.idsectionExit and
                 self.idLine == other.idLine )

    def __ne__(self, other):
        return not self.__eq__(other)

    def tuple(self):
        return (getattr(self, STATIC_INFOS_ATTR_BY_INDEX[i]) for i in range(NUM_STATIC_ATTRS))
