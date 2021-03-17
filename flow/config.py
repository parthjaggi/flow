"""Default config variables, which may be overridden by a user config."""
import os.path as osp
import os

PYTHON_COMMAND = "python"

SUMO_SLEEP = 1.0  # Delay between initializing SUMO and connecting with TraCI

PROJECT_PATH = osp.abspath(osp.join(osp.dirname(__file__), '..'))

LOG_DIR = PROJECT_PATH + "/data"

# users set both of these in their bash_rc or bash_profile
# and also should run aws configure after installing awscli
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY", None)

AWS_ACCESS_SECRET = os.environ.get("AWS_ACCESS_SECRET", None)

AWS_S3_PATH = "s3://bucket_name"


# ===========================================================================
# =========================== Aimsun config  ================================

# path to the Aimsun_Next main directory (required for Aimsun simulations)
AIMSUN_NEXT_PATH = os.environ.get("AIMSUN_NEXT_PATH", None)


# Constants for the TCP connection to Aimsun
HOST = 'localhost'
# The PORT is now a random integer between 1000 and 9999 inclusive

# Number of characters in a packet when sending a string
PACKET_SIZE = 256

# Signals for communicating the status of a transfer to the client
TRANSFER_DONE      = b'Wolf0'
TRANSFER_CONTINUE  = b'Wolf1'

# Standard length for a bytestring sent as a Status Response
STATRESP = b'StatResp'
STATRESP_LEN = 32

# Client identifiers
NETWORK_LOAD_ID   = b'load.py_and_generate.py'
RUN_API_ID        = b'run.py_and_api.py'
