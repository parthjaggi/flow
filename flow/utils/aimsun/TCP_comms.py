"""
Utility functions for TCP communication.
"""
import socket
import struct
import json

from flow.config import (TRANSFER_DONE,         # Signals communicating the status of a transfer
                         TRANSFER_CONTINUE,
                         STATRESP,              # The standard bytestring sent as a status response
                         STATRESP_LEN,          # Length of a status response bytestring
                         PACKET_SIZE)           # Number of characters in a packet when sending a string
# Kinds of formats:
# 'i'   : Integer
# 'f'   : Float
# 'str' : String
# '?'   : Boolean

def send_formatted_message(conn, format, *values):
    """
    Send a message in the specified format.

    If the message is a string, it is sent in segments of length PACKET_SIZE
    (if the string is longer than such) and concatenated on the receiving end.
    When sending a collection of strings, the values are concatenated on the
    sending end, and sent as a single string.

    Parameters
    ----------
    conn : socket.socket
        The sending socket
    format : str
        Format of the message
    *values : collection of Any
        Values to be encoded and sent to the receiving socket
    """
    if format == 'str':
        # Concatenate the input strings (and encode as a bytestring for TCP)
        message = ''.join(*values).encode()

        # When the message is too large, send value in segments
        # and inform the client that additional information will be sent.
        # The value will be concatenated on the other end
        while len(message) > PACKET_SIZE:
            # send the next set of data
            conn.send(message[:PACKET_SIZE])
            message = message[PACKET_SIZE:]

            # wait for a reply, then send a CONTINUE signal, and finally get
            # an acknowledgement that the CONTINUE was received
            conn.recv(STATRESP_LEN)
            conn.send(TRANSFER_CONTINUE)
            conn.recv(STATRESP_LEN)

        # send the remaining components of the message (which is of length less
        # than or equal to PACKET_SIZE) (encode as bytestring for TCP)
        conn.send(message)

        # wait for a reply, then send a DONE signal, and get acknowledgement
        # that DONE was received
        conn.recv(STATRESP_LEN)
        conn.send(TRANSFER_DONE)
        conn.recv(STATRESP_LEN)
    else:
        packer = struct.Struct(format=format)
        packed_data = packer.pack(*values)
        conn.send(packed_data)


def get_formatted_message(conn, format):
    """
    Retrieve a message in the specified format

    Parameters
    ----------
    conn : socket.socket
        The receiving socket
    format : str or None
        Format of the message

    Returns
    -------
    Any
        Received message
    """

    # collect the return values
    if format is None:
        return None

    if format == 'str':
        done = False
        unpacked_data = ''
        while not done:
            # get the next bunch of data
            data = conn.recv(PACKET_SIZE)

            # concatenate the results
            unpacked_data += data.decode('utf-8')

            # ask for a status check (just by sending any command)
            conn.send(STATRESP)

            # Check if done
            done = ( conn.recv(STATRESP_LEN) == TRANSFER_DONE )

            # Acknowledge that the status message was received
            conn.send(STATRESP)
    else:
        unpacker = struct.Struct(format=format)
        data = conn.recv(unpacker.size)
        unpacked_data = unpacker.unpack(data)

    return unpacked_data


def send_dict(conn, dict):
    """
    Send a dictionary (converted to a JSON string, then to a bytestring)

    Parameters
    ----------
    conn : socket.socket
        The sending socket (either client or server)
    dict : dictionary
        Python dictionary to be sent
    """
    json_message = json.dumps(dict)
    send_formatted_message(conn, 'str', json_message)


def get_dict(conn):
    """
    Receive a dictionary (as a JSON string encoded into a bytestring)

    Parameters
    ----------
    conn : socket.socket
        The receiving socket (either client or server)

    Returns
    -------
        The received dictionary
    """
    json_string = get_formatted_message(conn, 'str')
    return json.loads(json_string)
