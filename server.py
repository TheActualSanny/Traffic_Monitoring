import json
import socket
import signal
from config import PACKETS_PER_FILE, SERVER_PORT, BUFFER_SIZE, INTERFACE, BASE_DIRECTORY
import time
from scapy.all import *
from threading import Thread, Event
from scapy.all import sniff, ARP, UDP, IP, Ether,TCP
from datetime import datetime
import json
import os
from main import TRAFFIC_DIRECTORY

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
        self.lock = threading.Lock()
        self.shutdown = False
        # UDP server should only be responsible for adding/deleting target MACs
        # all the other operations like target storage and its respective information
        # should be handled by the main program/thread
        

    def packet_handler(self, packet):
        if packet.haslayer(UDP) or packet.haslayer(TCP):
            source_ip = packet[IP].src
            if source_ip in self.macs:
                print(".", end="", flush=True)
                ip_directory = self.mac_directories[source_ip]
                wrpcap(f"{ip_directory}/file{self.file_desc}.pcap", packet, append=True)
                self.pkt_count += 1
                if self.pkt_count == PACKETS_PER_FILE:
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
            response_message = None

            with self.lock:
                if data["cmd"] == "add":
                    print(f"Adding {data['ip']} to the list")
                    if data["ip"] not in self.macs:
                        self.macs.append(data["ip"])
                        mac_directory = os.path.join(TRAFFIC_DIRECTORY, data["ip"].replace(':', '_'))
                        os.makedirs(mac_directory, exist_ok=True)
                        self.mac_directories[data["ip"]] = mac_directory
                        response_message = f"IP {data['ip']} successfully added."
                    else:
                        response_message = f"IP {data['ip']} already exists."
                elif data["cmd"] == "del":
                    print(f"Deleting {data['ip']} from the list")
                    if data["mac"] in self.macs:
                        self.macs.remove(data["ip"])
                        mac_directory = self.mac_directories.pop(data["ip"])
                        response_message = f"IP {data['ip']} successfully removed."
                    else:
                        response_message = f"IP {data['ip']} not found in the list."
                else:
                    response_message = "Invalid command. Please use 'add' or 'del'."
            # self.event.set()
            # if self.event.is_set():
            #     print("Event is set")
                  
            if response_message is not None:
                server_socket.sendto(response_message.encode(), client_address)

    def start(self):
        
        server_thread = Thread(target=self.start_server, args=(self.data,))
        server_thread.daemon = True
        server_thread.start()

        sniff_thread = Thread(target=self.sniff_packets)
        sniff_thread.daemon = True
        sniff_thread.start()

        print("Server and Sniffer threads started")

        server_thread.join()
        sniff_thread.join()


if __name__ == "__main__":
    server_instance = Server(INTERFACE, None)
    server_instance.start()

###################
# General comments
###################
# - Target adding mechanism must be separate from the rest of the code logic
# - You should have a "gracefull shutdown" mechanism
# - You should have your target adding mechanism atomic and all of their                               
#   data should be stored in a single place