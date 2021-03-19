"""
Script used to control and interact with Aimsun through a TCP socket. Executed with the Aimsun interpreter.
This is the version of the script that runs in a console (that is, without GUI).
"""
import sys
import os
import socket
import struct
import flow.config as config

sys.path.append(os.path.join(config.AIMSUN_NEXT_PATH,
                             'programming', 'Aimsun Next API',
                             'python', 'private', 'Micro'))
# The following modules are only accessible to the Aimsun interpreter
# (their contents are described in the Aimsun scripting guide)
import AAPI as aimsun_api
from AAPI import *

from PyANGBasic import *
from PyANGKernel import *

import flow.utils.aimsun.constants as ac
import flow.utils.aimsun.aimsun_struct as aimsun_struct
from TCP_comms import (send_formatted_message,
                       get_formatted_message)
from flow.config import (HOST,
                         RUN_API_ID,
                         STATRESP,
                         STATRESP_LEN)

model = GKSystem.getSystem().getActiveModel()

# Kinds of struct formats:
# 'i'    : Integer
# 'f'    : Float
# '?'    : Bool
# 'str'  : String
# 'dict' : Dictionary

# Codes for simulation orders (ANGSetSimulationOrder)
# 0 : None
# 1 : Cancel
# 2 : Rewind
# 3 : Stop
# 4 : StopAt

col_port = model.getColumn('GKModel::PORT')
PORT = model.getDataValue(col_port)[0]
sim_reset = False

entered_vehicles = []
exited_vehicles = []

def simulation_step(s):
    """
    Receives commands to carry out from a TCP Wolf server. Runs every simulation step.

    Parameters
    ----------
    s : socket.socket
        Socket for the TCP connection
    """
    step_done = False
    while not step_done:
        try:
            # Signal that the client is ready to receive the next command
            s.send(STATRESP)

            # Receive the next command
            command = s.recv(STATRESP_LEN)
            # Convert the bytestring command to an integer (cf. constants.py)
            command = int(command)

        except socket.error:
            # If the pipe is broken, cancel the experiment to avoid process leaks
            cur_sim_time = int(aimsun_api.AKIGetCurrentSimulationTime())
            aimsun_api.ANGSetSimulationOrder(1, cur_sim_time)
            break


        if command == ac.SIMULATION_STEP:
            # Send acknowledgement to server
            s.send(STATRESP)

	    # Get status response to indicate no optional data sent
            s.recv(STATRESP_LEN)

            step_done = True

        elif command == ac.SIMULATION_RESET:
            s.send(STATRESP)

            s.recv(STATRESP_LEN)

            step_done = True
            global sim_reset
            sim_reset = True
            cur_sim_time = int(aimsun_api.AKIGetCurrentSimulationTime())
            aimsun_api.ANGSetSimulationOrder(2, cur_sim_time)
            # Command 2 restarts the replication, and reloads the Aimsun API

        elif command == ac.SIMULATION_TERMINATE:
            s.send(STATRESP)

            # Status response to indicate no optional data sent
            s.recv(STATRESP_LEN)

            step_done = True
            cur_sim_time = int(aimsun_api.AKIGetCurrentSimulationTime())
            aimsun_api.ANGSetSimulationOrder(1, cur_sim_time)
            # Command 1 cancels the replication and experiment.

        elif command == ac.GET_EDGE_NAME:
            s.send(STATRESP)

            # get the edge ID in flow
            edge = get_formatted_message(s, 'str')

            edge_aimsun = model.getCatalog().findByName(
                edge, model.getType('GKSection'))

            aimsun_edge_name = edge_aimsun.getId() if edge_aimsun else -1

            send_formatted_message(s, 'i',
                                   aimsun_edge_name)

        elif command == ac.ADD_VEHICLE:
            s.send(STATRESP)

            edge, lane, type_id, pos, speed, next_section, tracking = \
                get_formatted_message(s, 'i i i f f i ?')

            veh_id = aimsun_api.AKIPutVehTrafficFlow( \
                edge, lane+1, type_id, pos, speed, next_section,
                tracking)

            send_formatted_message(s, 'i',
                                   veh_id)

        elif command == ac.REMOVE_VEHICLE:
            s.send(STATRESP)

            veh_id, = get_formatted_message(s, 'i')
            aimsun_api.AKIVehTrackedRemove(veh_id)
            send_formatted_message(s, 'i',
                                   0)

        elif command == ac.VEH_SET_SPEED:
            s.send(STATRESP)
            veh_id, speed = get_formatted_message(s, 'i f')
            new_speed = speed * 3.6
            # aimsun_api.AKIVehTrackedForceSpeed(veh_id, new_speed)
            aimsun_api.AKIVehTrackedModifySpeed(veh_id, new_speed)
            send_formatted_message(s, 'i',
                                   0)

        elif command == ac.VEH_SET_LANE:
            s.send(STATRESP)
            veh_id, target_lane = get_formatted_message(s, 'i i')
            aimsun_api.AKIVehTrackedModifyLane(veh_id, target_lane)
            send_formatted_message(s, 'i',
                                   0)

        elif command == ac.VEH_SET_ROUTE:
            s.send(STATRESP)
            # TODO
            s.recv(STATRESP_LEN)
            send_formatted_message(s, 'i',
                                   0)

        elif command == ac.VEH_SET_COLOR:
            s.send(STATRESP)
            veh_id, r, g, b = get_formatted_message(s, 'i i i i')
            # TODO
            s.recv(STATRESP_LEN)
            send_formatted_message(s, 'i',
                                   0)

        elif command == ac.VEH_GET_ENTERED_IDS:
            global entered_vehicles
            s.send(STATRESP)

            # get a status response instead of optional arguments
            s.recv(STATRESP_LEN)

            # send entered_vehicles list to client
            if entered_vehicles:
                output = ':'.join([str(veh) for veh in entered_vehicles])
            else:
                output = '-1'

            send_formatted_message(s, 'str',
                                   output)

            entered_vehicles = []

        elif command == ac.VEH_GET_EXITED_IDS:
            global exited_vehicles
            s.send(STATRESP)

            s.recv(STATRESP_LEN)

            if exited_vehicles:
                output = ':'.join([str(veh) for veh in exited_vehicles])
            else:
                output = '-1'

            send_formatted_message(s, 'str',
                                   output)

            exited_vehicles = []

        elif command == ac.VEH_GET_TYPE_ID:
            s.send(STATRESP)

            # get the type ID in flow
            type_id = get_formatted_message(s, 'str')

            # convert the edge name to an edge name in Aimsun
            type_vehicle = model.getType("GKVehicle")
            vehicle = model.getCatalog().findByName(type_id, type_vehicle)
            aimsun_type = vehicle.getId()
            aimsun_type_pos = AKIVehGetVehTypeInternalPosition(aimsun_type)

            send_formatted_message(s, 'i',
                                   aimsun_type_pos)

        elif command == ac.VEH_GET_STATIC:
            s.send(STATRESP)

            config_dict = get_formatted_message(s, 'dict')
            veh_id = config_dict['veh_id']
            tracked = config_dict['tracked']

            static_info = aimsun_api.AKIVehTrackedGetStaticInf(veh_id) if tracked else \
                          aimsun_api.AKIVehGetStaticInf(veh_id) # slow

            valid_keys = aimsun_struct.keys_static_veh_info
            keys = config_dict['keys'] or valid_keys

            try:
                output = aimsun_struct.to_dict(
                    static_info,
                    valid_keys,
                    keys
                )
            except (RuntimeError, KeyError):
                output = {'report': -1}

            send_formatted_message(s, 'dict', output)

        elif command == ac.VEH_GET_DYNAMIC:
            s.send(STATRESP)

            config_dict = get_formatted_message(s, 'dict')
            veh_id = config_dict['veh_id']
            tracked = config_dict['tracked']

            dynamic_info = aimsun_api.AKIVehTrackedGetInf(veh_id) if tracked else \
                           aimsun_api.AKIVehGetInf(veh_id) # slow

            valid_keys = aimsun_struct.keys_dynamic_veh_info
            keys = config_dict['keys'] or valid_keys

            try:
                output = aimsun_struct.to_dict(
                    dynamic_info,
                    valid_keys,
                    keys
                )
            except (RuntimeError, KeyError):
                output = {'report': -1}

            send_formatted_message(s, 'dict', output)

        elif command == ac.VEH_GET_ACC:
            s.send(STATRESP)

            config_dict = get_formatted_message(s, 'dict')
            veh_id = config_dict['veh_id']
            tracked = config_dict['tracked']

            acc_info = aimsun_api.AKIVehTrackedGetStaticInfACCParams(veh_id) if tracked else \
                       aimsun_api.AKIVehGetStaticInfACCParams(veh_id) # slow

            valid_keys = aimsun_struct.keys_acc_veh_info
            keys = config_dict['keys'] or valid_keys

            try:
                output = aimsun_struct.to_dict(
                    acc_info,
                    valid_keys,
                    keys
                )
            except (RuntimeError, KeyError):
                output = {'report': -1}

            send_formatted_message(s, 'dict', output)

        elif command == ac.VEH_GET_LEADER:
            s.send(STATRESP)
            veh_id, = get_formatted_message(s, 'i')
            leader = aimsun_api.AKIVehGetLeaderId(veh_id)
            send_formatted_message(s, 'i',
                                   leader)

        elif command == ac.VEH_GET_FOLLOWER:
            s.send(STATRESP)
            veh_id, = get_formatted_message(s, 'i')
            follower = aimsun_api.AKIVehGetFollowerId(veh_id)
            send_formatted_message(s, 'i',
                                   follower)

        elif command == ac.VEH_GET_NEXT_SECTION:
            s.send(STATRESP)
            veh_id, section = get_formatted_message(s, 'i i')
            next_section = AKIVehInfPathGetNextSection(veh_id, section)
            send_formatted_message(s, 'i',
                                   next_section)

        elif command == ac.VEH_GET_ROUTE:
            s.send(STATRESP)
            # veh_id, = retrieve_message(s, 'i')
            # TODO

        # FIXME can probably be done more efficiently cf. VEH_GET_TYPE_ID
        elif command == ac.VEH_GET_TYPE_NAME:
            s.send(STATRESP)

            veh_id, = get_formatted_message(s, 'i')

            static_info = aimsun_api.AKIVehGetStaticInf(veh_id)
            typename = aimsun_api.AKIVehGetVehTypeName(static_info.type)
            anyNonAsciiChar = aimsun_api.boolp()
            output = str(aimsun_api.AKIConvertToAsciiString(
                typename, True, anyNonAsciiChar))

            send_formatted_message(s, 'str',
                                   output)

        elif command == ac.VEH_GET_LENGTH:
            s.send(STATRESP)

            veh_id, = get_formatted_message(s, 'i')

            static_info = aimsun_api.AKIVehGetStaticInf(veh_id)
            output = static_info.length

            send_formatted_message(s, 'f',
                                   output)

        elif command == ac.VEH_SET_TRACKED:
            s.send(STATRESP)

            veh_id, = get_formatted_message(s, 'i')

            aimsun_api.AKIVehSetAsTracked(veh_id)

            send_formatted_message(s, 'i',
                                   0)

        elif command == ac.VEH_SET_NO_TRACKED:
            s.send(STATRESP)

            veh_id, = get_formatted_message(s, 'i')

            aimsun_api.AKIVehSetAsNoTracked(veh_id)

            send_formatted_message(s, 'i',
                                   0)

        elif command == ac.TL_GET_IDS:
            s.send(STATRESP)

            # Status response to indicate no optional arguments
            s.recv(STATRESP_LEN)

            num_meters = aimsun_api.ECIGetNumberMeterings()
            if num_meters == 0:
                output = '-1'
            else:
                meter_ids = []
                for i in range(1, num_meters + 1):
                    struct_metering = ECIGetMeteringProperties(i)
                    meter_ids.append(struct_metering.Id)
                output = ':'.join([str(e) for e in meter_ids])

            send_formatted_message(s, 'str',
                                   output)

        elif command == ac.TL_SET_STATE:
            s.send(STATRESP)

            meter_aimsun_id, link_index, state = get_formatted_message(s, 'i i i')

            time = AKIGetCurrentSimulationTime()  # simulation time
            sim_step = AKIGetSimulationStepTime()
            identity = 0
            ECIChangeStateMeteringById(
                meter_aimsun_id, state, time, sim_step, identity)

            send_formatted_message(s, 'i',
                                   0)

        elif command == ac.TL_GET_STATE:
            s.send(STATRESP)

            meter_aimsun_id = get_formatted_message(s, 'i')

            lane_id = 1  # TODO double check
            state = ECIGetCurrentStateofMeteringById(
                meter_aimsun_id, lane_id)

            send_formatted_message(s, 'i',
                                   state)

        # in case the message is unknown, return -1001
        else:
            send_formatted_message(s, 'i',
                                   -1001)
            print("Message unknown")

    return 0



# =======================================================================
# ========================== Aimsun API =================================

def AAPILoad():
    """Execute commands while the Aimsun template is loading."""
    global s

    # Set up TCP/IP connection with Wolf
    connected = False
    while not connected:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))

            # Send an initializing message containing
            # the client identifier
            s.send(RUN_API_ID)

            # Receive a status response from the server
            # acknowledging the connection
            s.recv(STATRESP_LEN)

            connected = True
        except socket.error:
            connected = False
    print("[run.py] Client socket created")
    return 0


def AAPIInit():
    """Execute commands while the Aimsun instance is initializing."""
    # Set the simulation time to be very large
    # (to avoid checking whether the replication terminated;
    #  the replication may be terminated by sinding the
    #  ac.SIMULATION_TERMINATE command from the client)
    aimsun_api.AKISetEndSimTime(2e6)
    return 0


def AAPISimulationReady():
    """Execute commands while the Aimsun replication is initialized."""
    return 0


def AAPIManage(time, timeSta, timeTrans, acycle):
    """Execute commands before an Aimsun simulation step."""
    if not sim_reset:
        return simulation_step(s)
    # Carry out commands sent by the Wolf server
    else:
        return 0
    # Ignore the additional simulation step taken after a reset

def AAPIPostManage(time, timeSta, timeTrans, acycle):
    """Execute commands after an Aimsun simulation step."""
    return 0


def AAPIFinish():
    """Execute commands while the Aimsun instance is terminating."""
    return 0


def AAPIUnLoad():
    """Execute commands while Aimsun is closing."""
    s.close()
    print("[run.py] Client socket closed")
    return 0


def AAPIPreRouteChoiceCalculation(time, timeSta):
    """Execute Aimsun route choice calculation."""
    return 0


def AAPIVehicleStartParking(idveh, idsection, time):
    """Execite command once a vehicle starts parking"""
    return 0


def AAPIEnterVehicle(idveh, idsection):
    """Execute command once a vehicle enters the Aimsun instance."""
    global entered_vehicles
    entered_vehicles.append(idveh)
    return 0


def AAPIExitVehicle(idveh, idsection):
    """Execute command once a vehicle exits the Aimsun instance."""
    global exited_vehicles
    exited_vehicles.append(idveh)
    return 0


def AAPIEnterPedestrian(idPedestrian, originCentroid):
    """Execute command once a pedestrian enters the Aimsun instance."""
    return 0


def AAPIExitPedestrian(idPedestrian, destinationCentroid):
    """Execute command once a pedestrian exits the Aimsun instance."""
    return 0


def AAPIEnterVehicleSection(idveh, idsection, atime):
    """Execute command once a vehicle section enters the Aimsun instance."""
    return 0


def AAPIExitVehicleSection(idveh, idsection, atime):
    """Execute command once a vehicle section exits the Aimsun instance."""
    return 0
