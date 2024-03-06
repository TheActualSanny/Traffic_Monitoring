
###################
# General comments
###################
# - Target adding mechanism must be separate from the rest of the code logic
# - You should have your target adding mechanism atomic and all of their                               
              

#TODO Revert to mac address as target. create a dictionary to store mac and ip address, where it will be tracket if ip address of mac is change,
#If ip address of mac is change, then the traffic will be stored in a same directory with the new ip address name and time. 
#In short monitor traffic using IP.

#Threading part should be done using airflow. airflow should upload the pcap file to google cloud storage.

import json
import socket
import signal
import threading
import os
from scapy.all import *
import sys
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
from config import TRAFFIC_DIRECTORY

import threading
import json
import socket
import signal
from config import PACKETS_PER_FILE, SERVER_PORT, BUFFER_SIZE, INTERFACE, BASE_DIRECTORY
from scapy.all import *
from threading import Thread, Event
from datetime import datetime
import os
from config import TRAFFIC_DIRECTORY


class Server:
    def __init__(self, ip_address, event):
        self.shutdown_event = threading.Event()
        self.macs = set()
        self.ip_address = ip_address
        self.data = None
        self.running = True
        self.pkt_count = 0
        self.mac_directories = {}
        self.lock = threading.Lock()

    def packet_handler(self, packet):
        if packet.haslayer(IP) and (packet.haslayer(UDP) or packet.haslayer(TCP)):
            source_mac = packet[Ether].src
            source_ip = packet[IP].src
            dicti = {source_mac:source_ip}
            
            with self.lock:
                if source_mac in self.macs:
                    ip_directory = self.mac_directories[source_mac]
                    datetime_now = datetime.now()
                    datetime_directory = datetime_now.strftime("%Y-%m-%d")
                    
                    if self.pkt_count != 1000:
                        print("aaa", dicti)
                        
                        pcap_directory = os.path.join(ip_directory, datetime_directory)
                        os.makedirs(pcap_directory, exist_ok=True)
                        
                        wrpcap(f"{pcap_directory}/{source_ip} {datetime_now}.pcap", packet, append=True)
                        self.pkt_count += 1
                    else:
                        self.running = False
                        print("Reached 10 packets. Stopping further packet capture.")
                        return

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
                    print(f"Adding {data['mac']} to the list")
                    if data["mac"] not in self.macs:
                        self.macs.add(data["mac"])
                        mac_directory = os.path.join(TRAFFIC_DIRECTORY, data["mac"].replace(':', '_'))
                        os.makedirs(mac_directory, exist_ok=True)
                        self.mac_directories[data["mac"]] = mac_directory
                        response_message = f"MAC {data['mac']} successfully added."
                    else:
                        response_message = f"MAC {data['mac']} already exists."
                elif data["cmd"] == "del":
                    print(f"Deleting {data['mac']} from the list")
                    if data["mac"] in self.macs:
                        self.macs.remove(data["mac"])
                        mac_directory = self.mac_directories.pop(data["mac"])
                        response_message = f"MAC {data['mac']} successfully removed."
                    else:
                        response_message = f"MAC {data['mac']} not found in the list."
                else:
                    response_message = "Invalid command. Please use 'add' or 'del'."

            if response_message is not None:
                server_socket.sendto(response_message.encode(), client_address)

    def start(self):
        signal.signal(signal.SIGTERM, self.shutdown_handler)
        signal.signal(signal.SIGINT, self.shutdown_handler)

        server_thread = threading.Thread(target=self.start_server, args=(self.data,))
        server_thread.daemon = True
        server_thread.start()

        sniff_thread = threading.Thread(target=self.sniff_packets)
        sniff_thread.daemon = True
        sniff_thread.start()

        print("Server and Sniffer threads started")

        try:
            server_thread.join()
            sniff_thread.join()
        except KeyboardInterrupt:
            self.shutdown_handler(signal.SIGINT, None)

    def shutdown_handler(self, signum, frame):
        print(f"Received signal {signal.Signals(signum).name}. Shutting down gracefully...")
        self.running = False
        self.shutdown_event.set()
        sys.exit(0)

if __name__ == "__main__":
    server_instance = Server(INTERFACE, None)
    server_instance.start()

###################
# General comments
###############
# - Target adding mechanism must be separate from the rest of the code logic
# - You should have your target adding mechanism atomic and all of their                               