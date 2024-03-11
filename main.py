from threading import Thread, Event
import server
import sniffer 
import os
from config import LOOPBACK_ADDRESS
from target_manager import TargetManager

event = Event()

if __name__ == "__main__":
    target_manager_instance = TargetManager()
    server = server.Server(LOOPBACK_ADDRESS, event, target_manager_instance)
    server.start()
    print("Server started")
    sniffer.start_sniffer()
    


    