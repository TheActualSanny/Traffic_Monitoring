from dataclasses import dataclass, field
import threading
from typing import Any
import os
import sys
import json
import socket
import signal
from datetime import datetime
from scapy.all import sniff, wrpcap, Ether, IP, UDP, TCP
from config import SERVER_PORT, BUFFER_SIZE, INTERFACE, TRAFFIC_DIRECTORY, PACKETS_PER_FILE
from target_manager import TargetManager

@dataclass
class Server:
    ip_address: str
    event: threading.Event
    target_manager: TargetManager
    shutdown_event: threading.Event = field(default_factory=threading.Event)
    data: Any = None
    running: bool = True
    pkt_count: int = 0

    def packet_handler(self, packet):
        if packet.haslayer(IP) and (packet.haslayer(UDP) or packet.haslayer(TCP)):
            source_mac, source_ip = packet[Ether].src, packet[IP].src
            data_dict = {source_mac: source_ip}

            with self.target_manager.lock:
                if source_mac in self.target_manager.macs and self.pkt_count <  int(PACKETS_PER_FILE):
                    ip_directory = self.target_manager.mac_directories[source_mac]
                    datetime_now = datetime.now()
                    datetime_directory = datetime_now.strftime("%Y-%m-%d")
                    print("Received packet data:", data_dict)

                    pcap_directory = os.path.join(ip_directory, datetime_directory)
                    os.makedirs(pcap_directory, exist_ok=True)

                    pcap_filename = f"{source_ip}_{datetime_now}.pcap"
                    wrpcap(os.path.join(pcap_directory, pcap_filename), packet, append=True)
                    self.pkt_count += 1
                elif self.pkt_count == PACKETS_PER_FILE:
                    self.running = False
                    print(f"Reached {PACKETS_PER_FILE} packets. Stopping further packet capture.")

    def sniff_packets(self):
        sniff(prn=self.packet_handler, store=0, iface=INTERFACE)

    def start_server(self, my_data):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((self.ip_address, SERVER_PORT))
        print(my_data)
        print(f"Server data: {self.data}")
        print(f"UDP Server up and listening at {self.ip_address}:{SERVER_PORT}")

        while not self.shutdown_event.is_set():
            try:
                message, client_address = server_socket.recvfrom(BUFFER_SIZE)
                print(f"Message from Client {client_address}: {message.decode()}")
                data = json.loads(message.decode())
                response_message = self.process_client_command(data)

                if response_message:
                    server_socket.sendto(response_message.encode(), client_address)

            except socket.error as e:
                print(f"Socket error: {e}")

    def process_client_command(self, data):
        command = data.get("cmd")
        mac = data.get("mac")
        if command and mac:
            if command == "add":
                return self.target_manager.add_target(mac)
            elif command == "del":
                return self.target_manager.remove_target(mac)

        return "Invalid command. Please use 'add' or 'del'."

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
