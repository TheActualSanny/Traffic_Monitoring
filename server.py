import json
import socket
from config import SERVER_PORT, BUFFER_SIZE, INTERFACE, BASE_DIRECTORY
import time
from scapy.all import *
from threading import Thread, Event
from scapy.all import sniff, ARP, UDP, IP, Ether
from datetime import datetime
import json
import os

MACS_DIRECTORY = os.path.join(BASE_DIRECTORY, "MACS")
if not os.path.exists(MACS_DIRECTORY):
    os.makedirs(MACS_DIRECTORY)
    
# This is not recommended practice, you should habdle that outside of this class
# probably somewhere where you start the whole program    

# You should have a "gracefull shutdown" mechanism
# for your program, so you can stop the server and the sniffer
# The usual way to do this is to handel signals like SIGTERM and SIGINT

class Server:
    def __init__(self, ip_address, event):
        self.macs = []
        self.ip_address = ip_address
        self.data = None
        self.event = event
        self.running = True
        self.pkt_count = 0
        self.file_desc = 0
        # You should not store the information about the same thing in
        # a few different places, it will be hard to maintain and debug
        self.mac_directories = {}
        # UDP server should only be responsible for adding/deleting target MACs
        # all the other operations like target storage and its respective information
        # should be handled by the main program/thread

    def packet_handler(self, packet):
        # You must also habdle TCP traffic
        if packet.haslayer(UDP):
            source_mac = packet[Ether].src.lower()
            # unused variable
            now = datetime.now()
            # Why "stringing" twice?
            str_mac = str(source_mac)
            # Project descirption specified that you must store the traffic
            # based on IP adress of the target not the mac
            if str_mac in self.macs:
                print(".", end="", flush=True)
                # Use proper logging
                mac_directory = self.mac_directories[str_mac]
                # Wrpcap
                wrpcap(f"{mac_directory}/file{self.file_desc}.pcap", packet, append=True)
                self.pkt_count += 1
                # The number of packets per file should be coming from config
                if self.pkt_count == 50:
                    self.pkt_count = 0
                    self.file_desc += 1

    def sniff_packets(self):
        sniff(prn=self.packet_handler, store=0, iface=INTERFACE)

    def start_server(self, my_data):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((self.ip_address, SERVER_PORT))

        print(my_data)
        print(f"Server data: {self.data}")
        print(f"UDP Server up and listening at {self.ip_address}:{SERVER_PORT}")

        while self.running:
            message, client_address = server_socket.recvfrom(BUFFER_SIZE)
            print(f"Message from Client {client_address}: {message.decode()}")
            data = json.loads(message.decode())
            if data["cmd"] == "add":
                print(f"Adding {data['mac']} to the list")
                if data["mac"] not in self.macs:
                    # Use proper locking mechanism for the shared resource
                    # Adding target should be atomic
                    self.macs.append(data["mac"])
                    mac_directory = os.path.join(MACS_DIRECTORY, data["mac"].replace(':', '_'))
                    os.makedirs(mac_directory, exist_ok=True)
                    self.mac_directories[data["mac"]] = mac_directory
                    response_message = f"MAC {data['mac']} successfully added."
                else:
                    response_message = f"MAC {data['mac']} already exists."
            elif data["cmd"] == "del":
                print(f"Removing {data['mac']} from the list")
                if data["mac"] in self.macs:
                    self.macs.remove(data["mac"])
                    mac_directory = self.mac_directories.pop(data["mac"])
                    response_message = f"MAC {data['mac']} successfully removed."
                else:
                    response_message = f"MAC {data['mac']} not found in the list."

            # There is no purpose for this three lines of code
            self.event.set()
            if self.event.is_set():
                print("Event is set")
            # Response message should be set outside of the if block
            # Or in if block there sshould an else clause
            # for handling the case when the command is not add or del
            server_socket.sendto(response_message.encode(), client_address)

    def start(self):
        # You should handle your child threads properly
        # They should not be let to libe as zombie threads
        t = Thread(target=self.start_server, args=(self.data,))
        t.start()

        sniff_thread = Thread(target=self.sniff_packets)
        sniff_thread.start()

        print("Server and Sniffer started")
        t.join()
        sniff_thread.join()


###################
# General comments
###################
# - Target adding mechanism must be separate from the rest of the code logic
# - You should have a "gracefull shutdown" mechanism
# - You should have your target adding mechanism atomic and all of their                               
#   data should be stored in a single place