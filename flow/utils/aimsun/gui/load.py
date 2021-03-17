7# flake8: noqa
"""
Script to load an Aimsun instance from a template. Executed with the Aimsun interpreter.
This is the version of the script that runs with GUI.
"""
import os, sys
import socket
import flow.config as config
from flow.utils.aimsun.gui.scripting_api import AimsunTemplate
from flow.utils.aimsun.TCP_comms import (send_formatted_message,
                                         get_formatted_message,
                                         send_dict, get_dict)

def load_network():
    """Load the whole network into a dictionary and returns it."""
    sections = model.sections
    nodes = model.nodes
    turnings = model.turnings
    cen_connections = model.cen_connections

    network_data = get_dict_from_objects(sections,
                                         nodes,
                                         turnings,
                                         cen_connections)
    print(network_data)
    return network_data

def load_subnetwork(subnetwork, scenario):
    """Load subnetwork into a dictionary and returns it."""
    # get all objects in subnetwork
    objs = list(subnetwork.classify_objects(scenario.id))

    sections = model.find_all_by_type(objs, 'GKSection')
    nodes = model.find_all_by_type(objs, 'GKNode')
    turnings = model.find_all_by_type(objs, 'GKTurning')
    cen_connections = model.find_all_by_type(objs, 'GKCenConnection')

    network_data = get_dict_from_objects(sections,
                                         nodes,
                                         turnings,
                                         cen_connections)
    return network_data


def get_dict_from_objects(sections, nodes, turnings, cen_connections):
    """Load all relevant data into dictionaries."""
    network_data = {
        'sections': {},
        'nodes': {},
        'turnings': {},
        'centroids': {},
        'connections': {}
    }
    """
    # load centroids
    # TODO use centroids when we don't have a centroid configuration
    centroids = [o for o in objs if o.getTypeName() == 'GKCentroid']
    # FIXME doesn't handle centroids that are both in and out
    # maybe no need to distinguish them since it is done
    # later with centroid connections
    centroid_config_name = aimsun_config['centroid_config_name']
    centroid_config = model.find_by_name(model.centroid_configurations,
                                         centroid_config_name)
    if not centroid_config:
        print('[load.py] ERROR: Centroid configuration ' +
              centroid_config_name + ' does not exist.')
    else:
        # load origin centroids only if they exist
        if centroid_config.origin_centroids:
            for c in centroid_config.origin_centroids:
                network_data['centroids'][c.id] = {'type': 'in'}

        # load destination centroids only if they exist
        if centroid_config.destination_centroids:
            for c in centroid_config.destination_centroids:
                network_data['centroids'][c.id] = {'type': 'out'}
    """
    # load sections
    for s in sections:
        network_data['sections'][s.id] = {
            'name': s.name,
            'numLanes': s.nb_full_lanes,
            'length': s.length2D(),
            'speed': s.speed
        }

    # load nodes
    for n in nodes:
        network_data['nodes'][n.id] = {
            'name': n.name,
            'nb_turnings': len(n.turnings)
        }

    # load turnings
    for t in turnings:
        network_data['turnings'][t.id] = {
            'name': t.name,
            'length': t.polygon.length2D() / 2,  # FIXME not totally accurate
            'origin_section_name': t.origin.name,
            'origin_section_id': t.origin.id,
            'dest_section_name': t.destination.name,
            'dest_section_id': t.destination.id,
            'node_id': t.node.id,
            'max_speed': t.speed,
            'origin_from_lane': t.origin_from_lane,
            'origin_to_lane': t.origin_to_lane,
            'dest_from_lane': t.destination_from_lane,
            'dest_to_lane': t.destination_to_lane
        }

    # load centroid connections
    for c in cen_connections:
        from_id = c.owner.id
        from_name = c.owner.name
        to_id = c.connection_object.id
        to_name = c.connection_object.name

        # invert from and to if connection is reversed
        if c.connection_type == 1:  # TODO verify this
            from_id, to_id = to_id, from_id
            from_name, to_name = to_name, from_name

        network_data['connections'][c.id] = {
            'from_id': from_id,
            'from_name': from_name,
            'to_id': to_id,
            'to_name': to_name
        }

    return network_data

"""
Once the Aimsun child process is loaded, with the script load.py running
within its Python interpreter, a TCP connection between the Aimsun subprocess
and the parent Wolf / Flow process is set up. Once the connection is established,
the server sends the parameters necessary to load the Aimsun template
and replication in a python dictionary (sent as a json string).

Among the parameters sent, the parameters that are used for template loading are:

  template_path : OS Path
      Path to the Aimsun template to be loaded

  replication_name : String
      Name of the Aimsun replication to be ran

  subnetwork_name : String or None
      Name of the subnetwork to be loaded

  centroid_config_name : String or None
      Name of a centroid configuration

  sim_step : Float
      Duration of a simulation step, in seconds

  render : Boolean
      True if simulation is to be ran in full mode, and
      False if simulation is to be ran in batch mode (no animation)

After the Aimsun template is loaded, the network data is read off the
loaded network, sent back to the server, and copied over into the Wolf
(or Flow) network kernel.
"""
# Receive the PORT to be used for the TCP connection
# as a command-line argument
PORT = int(sys.argv[1])

print("PORT", PORT)

# Connect to the Wolf (or Flow) instance that launched the
# Aimsun subprocess through a TCP socket
# (Wolf acts as the server, and we are connecting as a client)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((config.HOST, PORT))

# Send an identifier, letting the server know that we
# expect to receive Aimsun params and send the Aimsun
# network data
s.send(config.NETWORK_LOAD_ID)

# Read in the Aimsun parameters from the response received
# from the server
aimsun_config = get_dict(s)
print("AIMSUN_PARAMS", aimsun_config)

# Let the server know that the message has been received,
# by sending a status response message
s.send(config.STATRESP)


# Open the template in Aimsun
template_path = aimsun_config['template_path']
model = AimsunTemplate(GKSystem, GKGUISystem)
print(f'[load.py] Loading template {template_path}')
model.load(template_path)

# Retrieve replication by name
replication_name = aimsun_config['replication_name']
replication = model.find_by_name(model.replications, replication_name)
if replication is None:
    if model.replications:
        replication = model.replications[0]
        replication_name = replication.getName()
        print(f'[load.py] ERROR: No replication with name {aimsun_config["replication_name"]}'
              f' found. Launching the first one in the list, {replication_name}, instead.')
    else:
        raise ValueError(f'[load.py] ERROR: No replications found.')

# Retrieve experiment and scenario
experiment = replication.experiment
scenario = experiment.scenario
network_data = scenario.input_data
network_data.add_extension(os.path.join(
    config.PROJECT_PATH, 'flow/utils/aimsun/gui/run.py'), True)

print("[load.py] ATTACHED API")

# If subnetwork_name was specified in the Aimsun params,
# try to only load subnetwork; it not specified or if
# subnetwork is not found, load the whole network
subnetwork_name = aimsun_config['subnetwork_name']
if subnetwork_name is not None:
    subnetwork = model.find_by_name(model.problem_nets, subnetwork_name)
    if subnetwork:
        network_data = load_subnetwork(subnetwork, scenario)
    else:
        print(f'[load.py] ERROR: Subnetwork {subnetwork_name}'
               ' could not be found. Loading the whole network.')
        network_data = load_network()
else:
    network_data = load_network()

print("[load.py] Got net data")

# The network data is ready to be sent back to Wolf (or Flow)
# Receive a message from the server telling us that it is
# ready for the network data
s.recv(config.STATRESP_LEN)
# Send the network dictionary
send_dict(s, network_data)
# Get an acknowledgement from the server that the network data
# has been received
s.recv(config.STATRESP_LEN)
# Close the client socket
s.close()

# Set new replication step value
col_sim = model.getColumn('GKExperiment::simStepAtt')
experiment.setDataValue(col_sim, aimsun_config['sim_step'])

# Store the PORT in a new column
model.getType('GKModel').addColumn('GKModel::PORT', 'PORT', GKColumn.Int)
col_port = model.getColumn('GKModel::PORT')
model.setDataValue(col_port, PORT)

# Run the replication
action = 'play' if aimsun_config['render'] else 'execute'
# play: with animation
# execute: no animation (in `batch mode')
GKSystem.getSystem().executeAction(action, replication, [], "")
