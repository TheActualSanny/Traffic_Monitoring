from threading import Thread, Event
import socket
# Do not import something that you do not use
from scapy.all import sniff, ARP, UDP,IP, Ether
from datetime import datetime
import server
# try to import only the things you need not the whole files/modules
import sniffer 

event = Event()

if __name__ == "__main__":
    # t = Thread(target=server.start_server, args=("127.0.0.1","Hello"))
    # t.start()
    # Do not leave unneccessary comments
    server = server.Server("127.0.0.1",event)
    server.start()
    # sniff(prn=packet_handler, store=0, iface="wlo1") 
    print("Server started")
    sniffer.start_sniffer()
