"""
Contains the Wolf <-> Aimsun API manager.
A lightly modified and expanded version of the FlowAimsunAPI.

A major difference with the former API is that the client and
server locations are switched: the server socket is opened
from the Wolf process, and the client socket is opened from
the Aimsun subprocess.

[The reason for making this change is to avoid recreating
the server socket on every replication (run.py is reloaded
on every replication), and also be able to use the server
for data transfer in load.py and generate.py.]

Executed within the Wolf process.
"""
import socket
import logging
import struct

import flow.utils.aimsun.constants as ac
import flow.utils.aimsun.aimsun_struct as aimsun_struct

from flow.utils.aimsun.aimsun_struct import INFOS_ATTR_BY_INDEX
from flow.utils.aimsun.TCP_comms import ( send_formatted_message,
                                          get_formatted_message )
from flow.config import ( RUN_API_ID,
                          STATRESP,
                          STATRESP_LEN )


def accept_aimsun_connection(server):
    """
    Accepts a connection from an Aimsun client socket
    to the provided server socket. Expects an initial
    message with identifier RUN_API_ID from flow.config

    Arguments
    ---------
        server : socket.socket
            The server socket

    Returns
    -------
        socket : socket
            The connection
    """
    # Wait for the client with the expected identifier
    # and create the connection
    connected = False
    while not connected:
        try:
            conn, address = server.accept()
            connected = ( conn.recv(STATRESP_LEN) == RUN_API_ID )
        except socket.error:
            connected = False

    # Send a status response acknowledging
    # the connection
    conn.send(STATRESP)

    return conn


class WolfAimsunAPI():
    """
    An API used to interact with Aimsun via a TCP connection.
    """
    def __init__(self, server):
        """
        Instantiate the API

        Parameters
        ----------
        server : socket.socket
            The server socket used in Wolf (initialized in the master kernel)
        """
        self.server = server
        self.conn = accept_aimsun_connection(self.server)

    def _send_command(self, command_type, *values, in_format, out_format):
        """Send an arbitrary command via the connection.

        Commands are sent in two stages. First, the server sends the command
        type (e.g. ac.REMOVE_VEHICLE) and waits for a conformation message from
        the client. Once the confirmation is received, the server sends an
        encoded binary packet that the client will be prepared to decode, and
        will then receive some return value (either the value the client was
        requesting or a 0 signifying that the command has been executed. This
        value is then returned by this method.

        Parameters
        ----------
        command_type : flow.utils.aimsun.constants.*
            The command the server would like Aimsun to execute
        in_format : str or None
            Format of the input structure
        values : Collection of Any or None
            Commands to be encoded and issued to the client
        out_format : str or None
            Format of the output structure

        Returns
        -------
        Any
            The final message received from the Aimsun client
        """
        # Receive ready signal from the client
        self.conn.recv(STATRESP_LEN)

        # Send the command identifier to the client
        self.conn.send(str(command_type).encode())

        # Wait for a status response
        self.conn.recv(STATRESP_LEN)

        # Send the optional command parameters
        if in_format is not None:
            send_formatted_message(self.conn, in_format, *values)
        else:
            # if no additional parameters are needed,
            # just send a status response
            self.conn.send(STATRESP)

        # collect the return values
        if out_format is not None:
            return get_formatted_message(self.conn, out_format)


    def simulation_step(self):
        """
        Advance the replication by one step
        """
        self._send_command(ac.SIMULATION_STEP,
                           None,
                           in_format=None,
                           out_format=None)

    def simulation_reset(self):
        """
        Reset the replication to the beginning.
        The simulation time within Wolf, as well as the initial vehicle positions
        and various other initializations, have to be updated separately.
        """
        self._send_command(ac.SIMULATION_RESET,
                           None,
                           in_format=None,
                           out_format=None)
        self.conn.close()
        # The replication will restart, and the Aimsun API will
        # be initialized again, so we need to reconnect
        self.conn = accept_aimsun_connection(self.server)

    def stop_simulation(self):
        """
        Terminate the replication
        """
        self._send_command(ac.SIMULATION_TERMINATE,
                           None,
                           in_format=None,
                           out_format=None)

    def get_edge_name(self, edge):
        """
        Get the name of an edge in Aimsun.

        Parameters
        ----------
        edge : str
            Name of the edge in Flow (Corresponding to the 'Name' field of a
            Section in Aimsun)

        Returns
        -------
        int
            name of the edge in Aimsun
            -1 if no edge with that name is found
        """
        return self._send_command(ac.GET_EDGE_NAME,
                                  edge,
                                  in_format='str',
                                  out_format='i')[0]

    def add_vehicle(self, edge, lane, type_id, pos, speed, next_section, tracking=True):
        """
        Add a vehicle to the network.

        Parameters
        ----------
        edge : int
            name of the start edge in Aimsun (an integer that identifies the Aimsun object)
        lane : int
            start lane
        type_id : int or string
            vehicle type (id or name)
            Ex. 1 or 'Car'
        pos : float
            starting position
        speed : float
            starting speed
        next_section : int
            the edge number the vehicle should move towards after the current
            edge it is one. If set to -1, the vehicle takes the next feasible
            route
        tracking : bool
             True if vehicle is tracked, False otherwise

        Returns
        -------
        int
            name of the new vehicle in Aimsun
        """
        # if type_id is a string, retrieve the id of the type in Aimsun
        # for example, 'Car' -> 1
        if isinstance(type_id, str):
            type_id = self._send_command(ac.VEH_GET_TYPE_ID,
                                         type_id,
                                         in_format='str',
                                         out_format='i')[0]
        # TODO maybe put back the type conversion dict
        # to avoid useless API calls

        veh_id, = self._send_command(
            ac.ADD_VEHICLE,
            edge, lane, type_id, pos, speed, next_section, tracking,
            in_format='i i i f f i ?',
            out_format='i')

        return veh_id

    def remove_vehicle(self, veh_id):
        """
        Remove a vehicle from the network.

        Parameters
        ----------
        veh_id : int
            identifier of the vehicle in Aimsun
        """
        self._send_command(ac.REMOVE_VEHICLE,
                           veh_id,
                           in_format='i',
                           out_format='i')

    def set_speed(self, veh_id, speed):
        """
        Set the speed of a specific vehicle.

        Parameters
        ----------
        veh_id : int
            name of the vehicle in Aimsun
        speed : float
            target speed
        """
        self._send_command(ac.VEH_SET_SPEED,
                           veh_id, speed,
                           in_format='i f',
                           out_format='i')

    def apply_lane_change(self, veh_id, direction):
        """
        Set the lane change action of a specific vehicle.

        Parameters
        ----------
        veh_id : int
            name of the vehicle in Aimsun
        direction : int
            target direction (could be positive or negative)

        Returns
        -------
        float
            status (should be 0)
        """
        return self._send_command(ac.VEH_SET_LANE,
                                  veh_id, direction,
                                  in_format='i i',
                                  out_format='i')

    def set_route(self, veh_id, route):
        """
        Set the route of a specific vehicle.

        Parameters
        ----------
        veh_id : int
            name of the vehicle in Aimsun
        route : list of int
            list of edges the vehicle should traverse

        Returns
        -------
        float
            status (should be 0)
        """
        raise NotImplementedError
        return self._send_command(ac.VEH_SET_ROUTE,
                                  veh_id, route)

    def set_color(self, veh_id, color):
        """
        Set the color of a specific vehicle.

        Parameters
        ----------
        veh_id : int
            name of the vehicle in Aimsun
        color : (int, int, int)
            red, green, blue values
        """
        raise NotImplementedError
        r, g, b = color
        return self._send_command(ac.VEH_SET_COLOR,
                                  veh_id, r, g, b,
                                  in_format='i i i i',
                                  out_format='i')

    def get_entered_ids(self):
        """
        Return the ids of all vehicles that entered the network.
        """
        veh_ids = self._send_command(ac.VEH_GET_ENTERED_IDS,
                                     None,
                                     in_format=None,
                                     out_format='str')

        if veh_ids == '-1':
            return []
        else:
            veh_ids = veh_ids.split(':')
            return [int(v) for v in veh_ids]

    def get_exited_ids(self):
        """
        Return the ids of all vehicles that exited the network.
        """
        veh_ids = self._send_command(ac.VEH_GET_EXITED_IDS,
                                     None,
                                     in_format=None,
                                     out_format='str')

        if veh_ids == '-1':
            return []
        else:
            veh_ids = veh_ids.split(':')
            return [int(v) for v in veh_ids]

    def get_vehicle_type_id(self, flow_id):
        """
        Get the Aimsun type number of a Flow vehicle types.

        Parameters
        ----------
        flow_id : str
            Flow-specific vehicle type (e.g. 'Car')

        Returns
        -------
        int
            Aimsun-specific vehicle type, value from 1 to AKIVehGetNbVehTypes()
            If returned value is negative, the vehicle type is not being used
        """
        return self._send_command(ac.VEH_GET_TYPE_ID,
                                  flow_id,
                                  in_format='str',
                                  out_format='i')[0]

    def get_vehicle_static_info(self, veh_id):
        """
        Return the static information of the specified vehicle.

        Parameters
        ----------
        veh_id : int
            name of the vehicle in Aimsun

        Returns
        -------
        flow.utils.aimsun.struct.StaticInfVeh
            static info object
        """
        static_info = aimsun_struct.StaticInfVeh()

        (static_info.report,
         static_info.idVeh,
         static_info.type,
         static_info.length,
         static_info.width,
         static_info.maxDesiredSpeed,
         static_info.maxAcceleration,
         static_info.normalDeceleration,
         static_info.maxDeceleration,
         static_info.speedAcceptance,
         static_info.minDistanceVeh,
         static_info.giveWayTime,
         static_info.guidanceAcceptance,
         static_info.enrouted,
         static_info.equipped,
         static_info.tracked,
         static_info.keepfastLane,
         static_info.headwayMin,
         static_info.sensitivityFactor,
         static_info.reactionTime,
         static_info.reactionTimeAtStop,
         static_info.reactionTimeAtTrafficLight,
         static_info.centroidOrigin,
         static_info.centroidDest,
         static_info.idsectionExit,
         static_info.idLine) = self._send_command(
            ac.VEH_GET_STATIC,
            veh_id,
            in_format='i',
            out_format='i i i f f f f f f f '
                       'f f f i i i ? f f f '
                       'f f i i i i'
        )

        return static_info

    def get_vehicle_tracking_info(self, veh_id, info_bitmap, tracked=True):
        """
        Return the tracking information of the specified vehicle.

        Parameters
        ----------
        veh_id : int
            name of the vehicle in Aimsun
        info_bitmap : str
            bitmap representing the tracking info to be returned
            (cf function make_bitmap_for_tracking in vehicle/aimsun.py)
        tracked : boolean (defaults to True)
            whether the vehicle is tracked in Aimsun.

        Returns
        -------
        flow.utils.aimsun.struct.InfVeh
            tracking info object
        """

        # build the output format from the bitmap
        out_format = ''
        for i in range(len(info_bitmap)):
            if info_bitmap[i] == '1':
                out_format += ('f ' if i <= 12 else 'i ')
        if out_format == '':
            return
        else:
            out_format = out_format[:-1]    # remove the last space

        # append tracked boolean and vehicle id to the bitmap
        # so that the command only has one parameter
        val = str(veh_id) + ":" + info_bitmap + ("1" if tracked else "0")

        # retrieve the vehicle tracking info specified by the bitmap
        info = self._send_command(
            ac.VEH_GET_TRACKING,
            val,
            in_format='str',
            out_format=out_format)

        # place these tracking info into a struct
        ret = aimsun_struct.InfVeh()
        count = 0
        for map_index in range(len(INFOS_ATTR_BY_INDEX)):
            if info_bitmap[map_index] == '1':
                setattr(ret, INFOS_ATTR_BY_INDEX[map_index], info[count])
                count += 1
        return ret

    def get_vehicle_leader(self, veh_id):
        """
        Return the leader of a specific vehicle.

        Parameters
        ----------
        veh_id : int
            name of the vehicle in Aimsun

        Returns
        -------
        int
            name of the leader in Aimsun
            Negative if no leader exists
        """
        leader = self._send_command(ac.VEH_GET_LEADER,
                                    veh_id,
                                    in_format='i',
                                    out_format='i')[0]
        if leader >= 0:
            return leader
        else:
            return None

    def get_vehicle_follower(self, veh_id):
        """
        Return the follower of a specific vehicle.

        Parameters
        ----------
        veh_id : int
            name of the vehicle in Aimsun

        Returns
        -------
        int
            name of the follower in Aimsun
            Negative if no follower exists
        """
        follower = self._send_command(ac.VEH_GET_FOLLOWER,
                                      veh_id,
                                      in_format='i',
                                      out_format='i')[0]
        if follower >= 0:
            return follower
        else:
            return None

    def get_next_section(self, veh_id, section):
        """
        Return the headway of a specific vehicle.

        Parameters
        ----------
        veh_id : int
            name of the vehicle in Aimsun
        section : int
            name of a section in the vehicle's path

        Returns
        -------
        int
            next section
        """
        return self._send_command(ac.VEH_GET_NEXT_SECTION,
                                  veh_id, section,
                                  in_format='i i',
                                  out_format='i')[0]

    def get_route(self, veh_id):
        """
        Return the route of a specific vehicle.

        Parameters
        ----------
        veh_id : int
            name of the vehicle in Aimsun

        Returns
        -------
        list of int
            list of edge names in Aimsun
        """
        raise NotImplementedError
        return self._send_command(ac.VEH_GET_ROUTE,
                                  veh_id)

    def get_vehicle_type_name(self, veh_id):
        """
        Get the Aimsun type name of an Aimsun vehicle.

        Parameters
        ----------
        veh_id : int
            id of the vehicle in Aimsun

        Returns
        -------
        str
            Aimsun-specific vehicle type name
        """
        return self._send_command(ac.VEH_GET_TYPE_NAME,
                                  veh_id,
                                  in_format='i',
                                  out_format='str')

    def get_vehicle_length(self, veh_id):
        """
        Get the length of an Aimsun vehicle.

        Parameters
        ----------
        veh_id : int
            id of the vehicle in Aimsun

        Returns
        -------
        float
            length of the vehicle in Aimsun
        """
        return self._send_command(ac.VEH_GET_LENGTH,
                                  veh_id,
                                  in_format='i',
                                  out_format='f')[0]

    def set_vehicle_tracked(self, veh_id):
        """
        Set a vehicle as tracked in Aimsun.

        This thus allows for faster tracking information retrieval.

        Parameters
        ----------
        veh_id : int
            name of the vehicle in Aimsun
        """
        self._send_command(ac.VEH_SET_TRACKED,
                           veh_id,
                           in_format='i',
                           out_format='i')

    def set_vehicle_no_tracked(self, veh_id):
        """
        Set a tracked vehicle as untracked in Aimsun.

        Parameters
        ----------
        veh_id : int
            name of the vehicle in Aimsun
        """
        self._send_command(ac.VEH_SET_NO_TRACKED,
                           veh_id,
                           in_format='i',
                           out_format='i')

    def get_traffic_light_ids(self):
        """
        Return the ids of all traffic lights in the network.
        """
        tl_ids = self._send_command(ac.TL_GET_IDS,
                                    None,
                                    in_format=None,
                                    out_format='str')
        if tl_ids == '-1':
            return []
        else:
            tl_ids = tl_ids.split(':')
            return [int(t) for t in tl_ids]

    def set_traffic_light_state(self, tl_id, link_index, state):
        """
        Set the state of the specified traffic light(s).

        Parameters
        ----------
        tl_id : int
            name of the traffic light node in Aimsun
        link_index : TODO
            TODO
        state : str
            TODO
        """
        self._send_command(ac.TL_SET_STATE,
                           tl_id, link_index, state,
                           in_format='i i i',
                           out_format='i')

    def get_traffic_light_state(self, tl_id):
        """
        Get the traffic light state of a specific set of traffic light(s).

        Parameters
        ----------
        tl_id : int
            name of the traffic light node in Aimsun

        Returns
        -------
        str
            traffic light state of each light on that node
        """
        return self._send_command(ac.TL_GET_STATE,
                                  tl_id,
                                  in_format='i',
                                  out_format='i')[0]
