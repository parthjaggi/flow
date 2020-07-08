"""Returns features of the Flow repository (e.g. version number)."""

from .version import __version__ as v

# add sumo/tools to path
import os, sys
tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
sys.path.append(tools)

# flow repo version number
__version__ = v
