"""
Script containing objects used to store vehicle information in Aimsun.
"""

def to_dict(struct, valid_keys, keys):
    """
    Formats the data held in an Aimsun struct into a Python dictionary

    Arguments
    ---------
        struct : Aimsun struct
           The object returned by some Aimsun API calls (holding a collection
           of data), for example 'get static vehicle info in section'
        valid_keys : tuple of strings
           A tuple of attribute names for the struct, for error-checking.
           Tuples of valid keys for the various structs are copied down below
        keys : tuple of strings
           The desired attributes from the struct

    Returns
    -------
        dict
           A dictionary with keys given by *keys and values given by extracting
           the corresponding attribute from struct

    Precondition
    ------------
        Each key should match the name of its corresponding attribute in the Aimsun struct
    """
    if struct.report != 0:
        print('[aimsun_struct.py] aimsun_info_struct returned with an error (report != 0)')
        raise RuntimeError
    results = {key: None for key in keys}
    for key in keys:
        if key not in valid_keys:
            print(f'[aimsun_struct.py] Obtained an invalid key ({key})')
            raise KeyError
        results[key] = getattr(struct, key)
    return results


# ======================================================================
# ======================================================================
# Dynamic information for a vehicle in Aimsun.
# Returned by
#     * AKIVehGetInf (vehs called by id - slow, searches for vehicle in the network)
#     * AKIVehTracketGetInf (vehs called by id - faster, but has to be tracked)
#     * AKIVehStateGetVehicleInfSection (vehs indexed by section)
#     * AKIVehStateGetVehicleInfJunction (vehs indexed by junction)

"""
Attributes
----------
report : int
    0, OK, else error code
idVeh : int
    Vehicle identifier
type : int
    Vehicle type (car, bus, truck, etc.)

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
PreviousSpeed : float
    The speed in the previous simulation step

TotalDistance : float
    Total distance travelled (metres or feet)

SystemGenerationT : float
    The absolute generation time of the vehicle into the system. If no
    virtual queue is found in its entrance section, it will be the same
    as SystemEntranceT
SystemEntranceT : float
    The absolute entrance time of the vehicle into the system, that is
    into its entrance section. If no virtual queue found in its entrance
    section it will be the same as the SystemGenerationT
SectionEntranceT : float
    The absolute entrance time of the vehicle into the current section

CurrentStopTime : float
    The current stop time
stopped : float
    True if the vehicle remains stopped
mNbLostTurnings : int
    The number of lost turnings
"""

keys_dynamic_veh_info = (
    'report',
    'idVeh',
    'type',
    # Information in Vehicle when it is in a section
    'idSection',
    'segment',
    'numberLane',

    # Information in Vehicle when it is in a node
    'idJunction',
    'idSectionFrom',
    'idLaneFrom',
    'idSectionTo',
    'idLaneTo',

    'CurrentPos',
    'distance2End',
    'xCurrentPos', 'yCurrentPos', 'zCurrentPos',
    'xCurrentPosBack', 'yCurrentPosBack', 'zCurrentPosBack',
    'CurrentSpeed', 'PreviousSpeed',

    'TotalDistance',
    'SystemGenerationT',
    'SystemEntranceT',
    'SectionEntranceT',
    'CurrentStopTime',
    'stopped',
#    'mNbLostTurnings', Excluded because returned as uint. Uncomment if needed and convert to int.
)


# ======================================================================
# ======================================================================
# Static information for a vehicle in Aimsun.
# Returned by
#     * AKIVehGetStaticInf (vehs called by id - slow)
#     * AKIVehTrackedGetStaticInf (vehs called by id - faster)
#     * AKIVehGetVehicleStaticInfSection (vehs indexed by section)
#     * AKIVehGetVehicleStaticInfJunction (vehs indexed by junction)

"""
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
safetyMarginFactor : double
    Safety margin factor
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

laneChangingCooperation : bool
    The vehicle is currently co-operating with another vehicle's lane change manouevre
laneChangingAggressivenessLevel : float
    The aggressiveness factor for this vehicle in lane changing, where 0% means the
    full safety gap is required for the lane change and 100% means the minimum gap
    is accepted in the lane change
distanceZoneFactor : float
    The multiplier this vehicle applies applies to the zone 1, 2, 3 distances which
    control when it starts to consider a forthcoming lane change. A value > 1 implies
    it tries to get into lane earlier than normal and < 1 imlpies to get into lane
    later than normal.

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

keys_static_veh_info = (
    'report',
    'idVeh',
    'type',
    'length',
    'width',
    'maxDesiredSpeed',
    'maxAcceleration',
    'normalDeceleration',
    'maxDeceleration',
    'speedAcceptance',
    'minDistanceVeh',
    'giveWayTime',
    'guidanceAcceptance',
    'enrouted',
    'tracked',

    'keepfastLane',
    'safetyMarginFactor',
    'headwayMin',
    'sensitivityFactor',
    'reactionTime',
    'reactionTimeAtStop',
    'reactionTimeAtTrafficLight',

    'laneChangingCooperation',
    'laneChangingAggressivenessLevel',
    'distanceZoneFactor',

    'centroidOrigin',
    'centroidDest',
    'idsectionExit',

    'idLine',
)


# ======================================================================
# ======================================================================
# Adaptive Cruise Control information for a vehicle in Aimsun.
# Returned by
#     * AKIVehGetStaticInfACCParams (vehs called by id - slow)
#     * AKIVehTrackedGetStaticInfACCParams (vehs called by id - faster)
#     * AKIVehGetVehicleStaticInfACCParamsSection (vehs indexed by section)
#     * AKIVehGetVehicleStaticInfACCParamsJunction (vehs indexed by junction)

"""
Common attributes
-----------------
report : int
    Error code returned (0 means success)
idVeh : int
    The simulated vehicle's ID
accType : int
    The simulated vehicle's ACC module
    (0: None, 1: ACC, 2: CACC)

ACC Parameters
--------------
minClearanceDistance : float
    The lower threshold for the space between the rear bumper
    of a vehicle and the front bumper of the following (meters)
maxClearanceDistance : float
    The upper threshold for the space between the rear bumper
    of a vehicle and the front bumper of the following (meters)
speedGainFreeFlow : float
    The gain on the speed difference between the free flow speed
    and the subject vehicle's current speed (1/s)
distanceGain : float
    The gain on the position difference between the preceding
    vehicle and the subject vehicle (1/s^2)
speedGainPrec : float
    The gain on the speed difference between the preceding vehicle
    and the subject vehicle (1/s)
desiredTimeGap : float
    The desired time gap of the ACC controller (s)

CACC Parameters
---------------
connectedDistanceGain : float
    The gain on the position difference between the preceding connected
    vehicle and the subject CACC vehicle (1/s)
connectedSpeedGain : float
    The gain on the speed difference between the preceding connected vehicle
    and the subject CACC vehicle
minTimeGapThreshold : float
    The lower threshold for the time gap (s)
maxTimeGapThreshold : float
    The upper threshold for the time gap (s)
followerTimeGap : float
    The constant time gap between the last vehicle of the preceding connected
    string and the subject CACC vehicle (s)
leaderTimeGap : float
    The constant time gap between the last vehicle of the preceding connected
    string and the subject CACC vehicle (s)
"""

keys_acc_veh_info = (
    'report',
    'idVeh',
    'accType',

    # ACC Model Parameters (-1 when module disabled)
    'minClearanceDistance',
    'maxClearanceDistance',
    'speedGainFreeFlow',
    'distanceGain',
    'speedGainPrec',
    'desiredTimeGap',

    # CACC Model Parameters (-1 when module disabled)
    'connectedDistanceGain',
    'connectedSpeedGain',
    'minTimeGapThreshold',
    'maxTimeGapThreshold',
    'followerTimeGap',
    'leaderTimeGap',
)
