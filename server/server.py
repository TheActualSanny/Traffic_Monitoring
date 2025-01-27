import os
import sys
import json
import socket
import signal
import threading
import logging
from typing import Any
from datetime import datetime
from traffic_monitoring.target_manager import TargetManager
from scapy.all import sniff, wrpcap, Ether, raw, IP, UDP, TCP, srp, ARP
from utils.config import SERVER_PORT, BUFFER_SIZE, INTERFACE, PACKETS_PER_FILE, TRAFFIC_DIRECTORY, KAFKA_BROKER, KAFKA_TOPIC
from kafka_components.kafka_consumer import create_kafka_consumer
from kafka import KafkaProducer

logger = logging.getLogger(__name__)

class Server:
    def __init__(self, ip_address: str, event: threading.Event, target_manager: TargetManager, data: Any = None):
        self.ip_address = ip_address
        self.event = event
        self.target_manager = target_manager
        self.shutdown_event = threading.Event()  
        self.data = data
        self.running = True
        self.pkt_count = 0


        self.consumer = create_kafka_consumer(KAFKA_BROKER, KAFKA_TOPIC)  
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')  
        )

    def create_directory(self, mac_address: str):
        """Utility function to create necessary directories for storing packets."""
        mac_dir = os.path.join(TRAFFIC_DIRECTORY, mac_address)
        os.makedirs(mac_dir, exist_ok=True)

        current_date = datetime.now().strftime("%Y/%m/%d")
        date_dir = os.path.join(mac_dir, current_date)
        os.makedirs(date_dir, exist_ok=True)

        return date_dir

    def write(self, packet, mac_address):
        """Save the captured packet in the specified directory."""
        date_dir = self.create_directory(mac_address)
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        pcap_file_path = os.path.join(date_dir, f"{mac_address}_{current_time}.pcap")
        wrpcap(pcap_file_path, packet, append=True)

    def send_message_to_kafka(self, message):
        """Send a message to Kafka topic."""
        try:
            self.producer.send(KAFKA_TOPIC, message)
            logger.info(f"Sent message to Kafka: {message}")
        except Exception as e:
            logger.error(f"Error sending message to Kafka: {e}")

    def consume_and_store_messages(self):
        """Consume messages from Kafka topic and store them in files."""
        print("Listening for Kafka messages...")

        message_count = 0  
        for message in self.consumer:
            try:
                message_value = message.value
                logger.info(f"Received: {message_value}")

                # Ensure the directory exists before saving the message
                file_dir = os.path.dirname(os.path.join(TRAFFIC_DIRECTORY, f"message_{message_count}.json"))
                os.makedirs(file_dir, exist_ok=True)

                # Store the received message in the file
                file_name = os.path.join(TRAFFIC_DIRECTORY, f"message_{message_count}.json")
                with open(file_name, 'w') as file:
                    json.dump(message_value, file, indent=4)

                message_count += 1
            except Exception as e:
                logger.error(f"Error processing Kafka message: {e}")


    def packet_handler(self, packet):
        """Process packets and send them to Kafka if necessary."""
        if packet.haslayer(IP) and (packet.haslayer(UDP) or packet.haslayer(TCP)):
            source_mac = packet[Ether].src
            if source_mac in self.target_manager.macs:
                logger.info(f"Captured packet from {source_mac}")
                packet_data = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'mac_address': source_mac,
                    'packet_summary': str(packet.summary())
                }
                self.send_message_to_kafka(packet_data)  
                self.write(packet, source_mac)

    def sniff_packets(self):
        """Sniff network packets and handle them."""
        sniff(prn=self.packet_handler, store=0, iface=INTERFACE)

    def start_server(self):
        """Start the UDP server to listen for incoming commands."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((self.ip_address, SERVER_PORT))
        logger.info("ENTER TARGET MAC ADDRESS TO MONITOR: ")

        while not self.shutdown_event.is_set():
            try:
                message, client_address = server_socket.recvfrom(BUFFER_SIZE)
                data = json.loads(message.decode())
                response_message = self.process_client_command(data)

                if response_message:
                    server_socket.sendto(response_message.encode(), client_address)

            except socket.error as e:
                logger.error(f"Socket error: {e}")

    def process_client_command(self, data):
        """Process a client command based on the provided data."""
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
        Start the server, packet sniffing threads, and Kafka consumer thread.
        Handle shutdown signals.
        """
        signal.signal(signal.SIGTERM, self.shutdown_handler)
        signal.signal(signal.SIGINT, self.shutdown_handler)

        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True
        server_thread.start()

        sniff_thread = threading.Thread(target=self.sniff_packets)
        sniff_thread.daemon = True
        sniff_thread.start()

        kafka_thread = threading.Thread(target=self.consume_and_store_messages)
        kafka_thread.daemon = True
        kafka_thread.start()

        try:
            server_thread.join()
            sniff_thread.join()
            kafka_thread.join()
        except KeyboardInterrupt:
            self.shutdown_handler(signal.SIGINT, None)

    def shutdown_handler(self, signum, frame):
        """Graceful shutdown."""
        logger.info(f"Received signal {signal.Signals(signum).name}. Shutting down gracefully...")
        self.running = False
        self.shutdown_event.set()
        self.producer.close()  
        sys.exit(0)