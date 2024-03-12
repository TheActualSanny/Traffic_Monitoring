from tempfile import NamedTemporaryFile
from dataclasses import dataclass, field
import threading
from typing import Any
import io
import os
import sys
import json
import socket
import signal
from datetime import datetime
from scapy.all import sniff, wrpcap, Ether, IP, UDP, TCP, srp, ARP
from config import SERVER_PORT, CREDENTIAL_PATH, BUCKET_NAME, BUFFER_SIZE, INTERFACE, NETWORK_RANGE, BROADCAST_MAC, PACKETS_PER_FILE
from target_manager import TargetManager
from configparser import ConfigParser
from google.cloud import storage


@dataclass
class Server:
    ip_address: str
    event: threading.Event
    target_manager: TargetManager
    shutdown_event: threading.Event = field(default_factory=threading.Event)
    data: Any = None
    running: bool = True
    pkt_count: int = 0

    @staticmethod
    def get_ip_by_mac(mac_address):
        """
        Discover the IP address associated with a given MAC address using ARP requests.

        This static method sends an ARP (Address Resolution Protocol) request to the specified MAC address
        within the given network range. It then processes the ARP responses, if any, to extract and return
        the corresponding IP address.

        Parameters:
        - mac_address (str): The MAC address for which the IP address is to be discovered.
        """
        try:
            arp_request = Ether(dst=BROADCAST_MAC) / ARP(pdst=NETWORK_RANGE, hwdst=mac_address)
            arp_response = srp(arp_request, timeout=1, verbose=0)

            if arp_response:
                for packet in arp_response:
                    response_ip = packet[ARP].psrc
                    print(f"Found IP {response_ip} for MAC {mac_address}")
                    return response_ip
            else:
                print(f"No ARP response for MAC {mac_address}")

        except Exception as exception:
            print(f"Error getting IP from MAC: {exception}")

        return None


    def packet_handler(self, packet):
        """
        Handle incoming network packets.

        This method is called for each packet captured by the packet sniffing process.
        It processes the packet to extract relevant information, checks if it contains
        IP layer and either UDP or TCP layer, and uploads the packet data to cloud storage
        if the source MAC address is in the target manager's list.

        Parameters:
        - packet: The network packet captured by the packet sniffing process.

        Returns:
        - None

        Behavior:
        1. Checks if the packet has an IP layer and either UDP or TCP layer.
        2. If the conditions are met, it extracts the source MAC address and IP address from the packet.
        3. Creates a dictionary with the source MAC address as the key and the source IP address as the value.
        4. Acquires a lock on the target manager to safely access and modify its data structures.
        5. Checks if the source MAC address is in the target manager's list of MAC addresses.
        6. If the conditions are met, increments the packet count and proceeds to upload the packet data to cloud storage.
        7. Prints the received packet data for informational purposes.
        """

        if packet.haslayer(IP) and (packet.haslayer(UDP) or packet.haslayer(TCP)):
            source_mac, source_ip = packet[Ether].src, packet[IP].src
            data_dict = {source_mac: source_ip}

            with self.target_manager.lock:
                if source_mac in self.target_manager.macs and self.pkt_count < int(PACKETS_PER_FILE):
                    datetime_now = datetime.now()
                    datetime_directory = datetime_now.strftime("%Y-%m-%d")
                    print("Received packet data:", data_dict)

                    self.upload_packet_to_cloud_storage(packet, source_mac, datetime_directory)

                    self.pkt_count += 1
                

    def upload_packet_to_cloud_storage(self, packet, source_mac, datetime_directory):
        """
        Uploads network packet data to cloud storage.

        This method uploads the provided network packet data to a cloud storage bucket.
        It creates a temporary PCAP file, writes the packet data to the file, reads the file
        content, and uploads it to the specified blob in the cloud storage bucket.

        Parameters:
        - packet: The network packet data to be uploaded.
        - source_mac: The source MAC address associated with the packet.
        - datetime_directory: The directory structure for organizing the cloud storage data.

        Returns:
        - None

        Behavior:
        1. Creates a temporary PCAP file using the NamedTemporaryFile context manager.
        2. Writes the provided network packet data to the temporary PCAP file.
        3. Reads the content of the temporary PCAP file.
        4. Uploads the packet data to the specified blob in the cloud storage bucket.
        """
        try:
            storage_client = storage.Client.from_service_account_json(CREDENTIAL_PATH)
            bucket = storage_client.get_bucket(BUCKET_NAME)

            with NamedTemporaryFile(delete=False, suffix=".pcap") as temp_file:
                temp_filename = temp_file.name
                temp_file.close()  

                wrpcap(temp_filename, [packet]) 

                with open(temp_filename, "rb") as file:
                    packet_bytes = file.read()

                blob_name = f"{source_mac}/{datetime_directory}/{datetime.now()}.pcap"
                blob = bucket.blob(blob_name)
                blob.upload_from_string(packet_bytes, content_type='application/octet-stream')

                print(f"Uploaded packet data to {blob_name}")

        except Exception as e:
            print(f"Error uploading packet data: {e}")


    def sniff_packets(self):
        sniff(prn=self.packet_handler, store=0, iface=INTERFACE)
        """
        Sniff network packets and handle them using the specified packet_handler.
        """

    def start_server(self, my_data):
        """
        Start a UDP server to handle incoming messages and process client commands.

        Binds the server socket to a specific IP address and port, then continuously
        listens for incoming messages. Messages are expected to be in JSON format.

        Args:
            my_data (str): Data to be passed to the server.
        """

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((self.ip_address, SERVER_PORT))
        print("ENTER TARGET MAC ADDRESS TO MONITOR: ")

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
        """
        Process a client command based on the provided data.

        Parses the 'cmd' and 'mac' fields from the given data dictionary and performs
        the corresponding action. Supported commands are 'add' and 'del', indicating
        the addition or removal of a target MAC address.

        Args:
            data (dict): A dictionary containing 'cmd' and 'mac' fields.

        Returns:
            str: Response message indicating the result of the command.
        """
        command = data.get("cmd")
        mac = data.get("mac")
        if command and mac:
            if command == "add":
                return self.target_manager.add_target(mac)
            elif command == "del":
                return self.target_manager.remove_target(mac)

        return "Invalid command. Please use 'add' or 'del'."

    def start(self):
        """
        Start the server and packet sniffer threads, and handle shutdown signals.

        Sets up signal handlers for termination and interruption, then launches
        server and sniffer threads in the background. Waits for threads to complete
        or until interrupted.
        """
        signal.signal(signal.SIGTERM, self.shutdown_handler)
        signal.signal(signal.SIGINT, self.shutdown_handler)

        server_thread = threading.Thread(target=self.start_server, args=(self.data,))
        server_thread.daemon = True
        server_thread.start()

        sniff_thread = threading.Thread(target=self.sniff_packets)
        sniff_thread.daemon = True
        sniff_thread.start()

        # print("testing server and Sniffer threads")

        try:
            server_thread.join()
            sniff_thread.join()
        except KeyboardInterrupt:
            self.shutdown_handler(signal.SIGINT, None)

    def shutdown_handler(self, signum, frame):
        """
        Handle the shutdown of the application gracefully.

        Prints a shutdown message and sets the shutdown event to signal
        server and sniffer threads to terminate. Exits the application.
        """
        print(f"Received signal {signal.Signals(signum).name}. Shutting down gracefully...")
        self.running = False
        self.shutdown_event.set()
        sys.exit(0)