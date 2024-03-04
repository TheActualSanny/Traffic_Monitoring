import os

SERVER_PORT = 12345
BUFFER_SIZE = 1024
INTERFACE = "wlo1"
BASE_DIRECTORY = "/home/user/Work/Traffic_Monitoring"
PACKETS_PER_FILE = 50


TRAFFIC_DIRECTORY = os.path.join(BASE_DIRECTORY, "Traffic")
if not os.path.exists(TRAFFIC_DIRECTORY):
    os.makedirs(TRAFFIC_DIRECTORY)