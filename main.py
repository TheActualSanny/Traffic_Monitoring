from threading import Thread, Event
import server
import sniffer 
import os
from config import BASE_DIRECTORY

event = Event()

if __name__ == "__main__":
    server = server.Server("127.0.0.1",event)
    server.start()
    print("Server started")
    sniffer.start_sniffer()
