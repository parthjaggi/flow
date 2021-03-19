"""
Script used to control and interact with Aimsun through a TCP socket.
Executed with the Aimsun interpreter. GUI version.
"""
import sys
import os
import socket
import struct
import flow.config as config


sys.path.append(os.path.join(config.AIMSUN_NEXT_PATH,
                             'programming/Aimsun Next API/python/private/Micro'))
# The following modules are only accessible from a script launched from the Aimsun process
# (their contents are described in the Aimsun scripting guide)
import AAPI as aimsun_api
from AAPI import *
from PyANGKernel import *
from PyANGGui import *

import flow.utils.aimsun.constants as ac
import flow.utils.aimsun.aimsun_struct as aimsun_struct
from flow.utils.aimsun.TCP_comms import (send_formatted_message,
                                         get_formatted_message, get_dict)
from flow.config import (HOST,
                         RUN_API_ID,
                         STATRESP,
                         STATRESP_LEN)

model = GKSystem.getSystem().getActiveModel()
gui   = GKGUISystem.getGUISystem().getActiveGui()

# Kinds of formats:
# 'i'   : Integer
# 'f'   : Float
# '?'   : Bool
# 'str' : String
# 'dict': Dictionary

entered_vehicles = []
exited_vehicles = []


def simulation_step(s):
    """
    Receives commands from a TCP Wolf server. Runs every simulation step.

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

            # receive the next command
            command = s.recv(STATRESP_LEN)
        except socket.error:
            cur_sim_time = int(aimsun_api.AKIGetCurrentSimulationTime())
            aimsun_api.ANGSetSimulationOrder(1, cur_sim_time)
            # Cancel the experiment
            print('[run.py] ERROR: Broken pipe, ending the experiment')
            break

        # convert to the integer command code (cf. constants.py)
        command = int(command)

        if command == ac.SIMULATION_STEP:
            # send acknowledgement to client
            s.send(STATRESP)
	    # get status response to indicate no optional data sent
            s.recv(STATRESP_LEN)

            step_done = True

        elif command == ac.SIMULATION_RESET:
            s.send(STATRESP)

            s.recv(STATRESP_LEN)

            step_done = True
            cur_sim_time = aimsun_api.AKIGetCurrentSimulationTime()
            cur_sim_time = int(cur_sim_time)
            aimsun_api.ANGSetSimulationOrder(2, cur_sim_time)
            # Codes for simulation orders
            # 0 : None
            # 1 : Cancel
            # 2 : Rewind
            # 3 : Stop
            # 4 : StopAt
            # Command 2 restarts the replication, and reloads
            # the Aimsun API

        elif command == ac.SIMULATION_TERMINATE:
            s.send(STATRESP)

            # Status response to indicate no optional data sent
            s.recv(STATRESP_LEN)

            step_done = True
            cur_sim_time = aimsun_api.AKIGetCurrentSimulationTime()
            cur_sim_time = int(cur_sim_time)
            aimsun_api.ANGSetSimulationOrder(1, cur_sim_time)
            # Command 1 camcels the replication and experiment.
            # (Please see ac.SIMULATION_RESTART for the simulation codes)

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
            if entered_vehicles:    # entered_vehicles is not empty
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

            if exited_vehicles:    # exited_vehicles is not empty
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

            config = get_formatted_message(s, 'dict')

            veh_id = config['veh_id']
            static_info = aimsun_api.AKIVehGetStaticInf(veh_id)

            valid_keys = aimsun_struct.keys_static_veh_in_section
            keys = config['keys'] or valid_keys

            results = aimsun_struct.to_dict(
                static_info,
                valid_keys,
                keys,
            )
            send_formatted_message(s, 'dict', results)

        elif command == ac.VEH_GET_TRACKING:
            s.send(STATRESP)

            info_bitmap = get_formatted_message(s, 'str')

            # The bitmap is built as follows:
            #   the id of the vehicle
            #   a ':' character
            #   21 bits representing what information is to be returned
            #   a bit representing whether or not the vehicle is tracked

            # retrieve the tracked boolean
            info_bitmap = info_bitmap[:-1]
            tracked = info_bitmap[-1]

            # separate the actual bitmap from the vehicle id
            veh_id, info_bitmap = info_bitmap.split(':')
            veh_id = int(veh_id)

            # retrieve the tracking info of the vehicle
            tracking_info = aimsun_api.AKIVehTrackedGetInf(veh_id) if tracked else \
                            aimsun_api.AKIVehGetInf(veh_id)

            # The commented out attributes are no longer in InfVeh
            # for whatever reason
            data = (  #tracking_info.report,
                      #tracking_info.idVeh,
                      #tracking_info.type,
                      tracking_info.CurrentPos,
                      tracking_info.distance2End,
                      tracking_info.xCurrentPos,
                      tracking_info.yCurrentPos,
                      tracking_info.zCurrentPos,
                      tracking_info.xCurrentPosBack,
                      tracking_info.yCurrentPosBack,
                      tracking_info.zCurrentPosBack,
                      tracking_info.CurrentSpeed,
                      #tracking_info.PreviousSpeed,
                      tracking_info.TotalDistance,
                      #tracking_info.SystemGenerationT,
                      #tracking_info.SystemEntranceT,
                      tracking_info.SectionEntranceT,
                      tracking_info.CurrentStopTime,
                      tracking_info.stopped,
                      tracking_info.idSection,
                      tracking_info.segment,
                      tracking_info.numberLane,
                      tracking_info.idJunction,
                      tracking_info.idSectionFrom,
                      tracking_info.idLaneFrom,
                      tracking_info.idSectionTo,
                      tracking_info.idLaneTo )

            # form the output and output format according to the bitmap
            output = []
            in_format = ''
            for i in range(len(info_bitmap)):
                if info_bitmap[i] == '1':
                    in_format += 'f ' if i <= 12 else 'i '
                    output.append(data[i])
            if in_format == '':
                output = None
            else:
                in_format = in_format[:-1]    # Remove the last space

            send_formatted_message(s, in_format,
                                   *output)

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

col_port = model.getColumn('GKModel::PORT')
PORT = int(model.getDataValue(col_port)[0])

def AAPILoad():
    """Execute commands while the Aimsun template is loading."""
    global s

    # TCP/IP connection from the Aimsun process
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
    return simulation_step(s)    # Carry out commands sent by the server
                                 # through the TCP connection

def AAPIPostManage(time, timeSta, timeTrans, acycle):
    """Execute commands after an Aimsun simulation step."""
    plugin = GKSystem.getSystem().getPlugin('GGetram').getSimulator().getSimulationControl()
    print(plugin.getName())
    print(type(plugin))
    print(len(plugin.__dict__.keys()))

#    print(plugin.verify())
#    sim = plugin.getSimulator()
#    print(sim)
#    simulator = plugin.getCreateSimulator()
#    sim = get_simulator(model)
#    a = sim.getSimulationControl()
#    a.run()
    print(":   )")
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
