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
# '?'   : Boolean
# 'str' : String
# 'dict': Dictionary

def send_formatted_message(conn, format, *values):
    """
    Send a message in the specified format.

    If the message is a string, it is sent in segments of length PACKET_SIZE
    (if the string is longer than such) and concatenated on the receiving end.

    If the message is a dictionary, it is first converted to a JSON string.

    When sending a collection of strings, the values are concatenated on the
    sending end, and sent as a single string.

    When sending a collection of dicts, the dictionaries are combined into a
    single one. In case of key conflicts, the latest dictionary's value is the
    one that gets recorded.

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
        # Concatenate the input strings if necessary
        if len(values) == 1:
            message = values[0]
        else:
            message = ''.join(*values)
        # Encode as a bytestring for TCP
        message = message.encode()

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

    elif format == 'dict':
        # Combine the input dictionaries if necessary
        if len(values) == 1:
            message = values[0]
        else:
            message = {}
            for d in values:
                message.update(d)

        # Convert to a JSON string and send
        json_message = json.dumps(message)
        send_formatted_message(conn, 'str', json_message)

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

    elif format == 'dict':
        # Receive a JSON string and decode
        json_string = get_formatted_message(conn, 'str')
        unpacked_data = json.loads(json_string)

    else:
        unpacker = struct.Struct(format=format)
        data = conn.recv(unpacker.size)
        unpacked_data = unpacker.unpack(data)

    return unpacked_data
