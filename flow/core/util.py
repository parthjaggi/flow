"""A collection of utility functions for Flow."""

import csv
import errno
import os
from lxml import etree
from xml.etree import ElementTree


def makexml(name, nsl):
    """Create an xml file."""
    xsi = "http://www.w3.org/2001/XMLSchema-instance"
    ns = {"xsi": xsi}
    attr = {"{%s}noNamespaceSchemaLocation" % xsi: nsl}
    t = etree.Element(name, attrib=attr, nsmap=ns)
    return t


def printxml(t, fn):
    """Print information from a dict into an xml file."""
    etree.ElementTree(t).write(
        fn, pretty_print=True, encoding='UTF-8', xml_declaration=True)


def ensure_dir(path):
    """Ensure that the directory specified exists, and if not, create it."""
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
    return path


def emission_to_csv(emission_path, output_path=None):
    """Convert an emission file generated by sumo into a csv file.

    Note that the emission file contains information generated by sumo, not
    flow. This means that some data, such as absolute position, is not
    immediately available from the emission file, but can be recreated.

    Parameters
    ----------
    emission_path : str
        path to the emission file that should be converted
    output_path : str
        path to the csv file that will be generated, default is the same
        directory as the emission file, with the same name
    """
    parser = etree.XMLParser(recover=True)
    tree = ElementTree.parse(emission_path, parser=parser)
    root = tree.getroot()

    # parse the xml data into a dict
    out_data = []
    for time in root.findall('timestep'):
        t = float(time.attrib['time'])

        for car in time:
            out_data.append(dict())
            try:
                out_data[-1]['time'] = t
                out_data[-1]['CO'] = float(car.attrib['CO'])
                out_data[-1]['y'] = float(car.attrib['y'])
                out_data[-1]['CO2'] = float(car.attrib['CO2'])
                out_data[-1]['electricity'] = float(car.attrib['electricity'])
                out_data[-1]['type'] = car.attrib['type']
                out_data[-1]['id'] = car.attrib['id']
                out_data[-1]['eclass'] = car.attrib['eclass']
                out_data[-1]['waiting'] = float(car.attrib['waiting'])
                out_data[-1]['NOx'] = float(car.attrib['NOx'])
                out_data[-1]['fuel'] = float(car.attrib['fuel'])
                out_data[-1]['HC'] = float(car.attrib['HC'])
                out_data[-1]['x'] = float(car.attrib['x'])
                out_data[-1]['route'] = car.attrib['route']
                out_data[-1]['relative_position'] = float(car.attrib['pos'])
                out_data[-1]['noise'] = float(car.attrib['noise'])
                out_data[-1]['angle'] = float(car.attrib['angle'])
                out_data[-1]['PMx'] = float(car.attrib['PMx'])
                out_data[-1]['speed'] = float(car.attrib['speed'])
                out_data[-1]['edge_id'] = car.attrib['lane'].rpartition('_')[0]
                out_data[-1]['lane_number'] = car.attrib['lane'].\
                    rpartition('_')[-1]
            except KeyError:
                del out_data[-1]

    # sort the elements of the dictionary by the vehicle id
    out_data = sorted(out_data, key=lambda k: k['id'])

    # default output path
    if output_path is None:
        output_path = emission_path[:-3] + 'csv'

    # output the dict data into a csv file
    keys = out_data[0].keys()
    with open(output_path, 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(out_data)


def convert_lanes_to_edges(lanes):
    """
    Convert lanes (iterable) to edges (iterable).
    Remove lane index from the end and then remove duplicates while retaining order.
    Also works with single lane str.
    
    >>> lanes
    >>> ['1175109_0', '1175109_1', '1175109_2', '1183934_0', '1183934_1', '1183934_2']

    >>> self._get_edges_from_lanes(lanes)
    >>> {'1175109', '1183934'}
    """
    if isinstance(lanes, str):
        return lanes.rsplit('_', 1)[0]
    return list(dict.fromkeys(map(lambda x: x.rsplit('_', 1)[0], lanes)))
