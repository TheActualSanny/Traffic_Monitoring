import signal
import threading
import argparse
import os
import subprocess
import socket
from datetime import datetime
import json
from typing import Optional
from dataclasses import dataclass, field
from kafka import KafkaConsumer, KafkaProducer
from scapy.all import  wrpcap, sniff, raw, Ether, IP, UDP, TCP, ARP, srp
from .kafka_components.kafka_methods import create_consumer, create_producer
from .targets import TargetManager
from tools.models import PacketInstances, TargetInstances


@dataclass
class Server:
    ip: str
    event: threading.Event
    target_manager: TargetManager
    packets_per_file: int 
    kafka_consumer : KafkaConsumer
    kafka_producer: KafkaProducer
    kafka_topic: str
    kafka_directory: str
    shutdown_event: threading.Event = field(default_factory = threading.Event)
    running: bool = True
    packet_caught: bool = False
    packet_count: int = 0
    available_macs: list = field(default_factory = list)

    
    def update_kafka(self, new_broker: str, new_topic: str, new_group_id: str,
                     new_kafka_directory: str) -> None:
        '''
            Whenever user terminates the sniffer and restarts it
            with completely new kafka parameters, this will be ran.
        '''
        self.kafka_topic = new_topic
        self.kafka_directory = f'{os.getcwd()}/{new_kafka_directory}'
        self.kafka_consumer = create_consumer(kafka_broker = new_broker, kafka_topic = new_topic,
                                              group_id = new_group_id)
        self.kafka_producer = create_producer(kafka_broker = new_broker, kafka_topic = new_topic)
        

    def fetch_macs(self) -> list:
        '''
            By utilizing the argparse library, this will execute the "arp-scan -l" command
            and fetch all of the found MAC addresses.
            Even though the ARP Scan can be done by using scapy, as it usually doesn't
            fetch all of the MAC addresses, using this command is the best way to have access to them.
        '''

        result = subprocess.run(['sudo', 'arp-scan', '-l'], capture_output = True, text = True)
        seperated_lines = result.stdout.split('\n')
        local_info = seperated_lines[0]
        beginning = None 
        self.available_macs = []

        for i in range(len(local_info)):
            if local_info[i : i + 3]  == 'MAC':
                beginning = i + 5
                break
        
        local_mac = {'mac' : local_info[beginning : beginning + 17],
                    'selected ': False, 'loaded' : False} # We get the local host's MAC address.
        self.available_macs.append(local_mac)

        for i in range(2, len(seperated_lines) - 4):
            instance_fields = seperated_lines[i].split()
            mac_instance = {'mac' : instance_fields[1], 'selected' : False,
                            'loaded' : False}
            self.available_macs.append(mac_instance)
        
        return self.available_macs

    def add_mac(self, mac_address: str) -> None:
        '''
            This will be used to write a new entry into our list
        '''
        finalized_instance = {'mac' : mac_address, 'selected' : False, 
                              'loaded' : False}
        self.available_macs.append(finalized_instance)


    def send_kafka_message(self, message: dict) -> None:
        '''
            Sends packet data as a message to our kafka broker.
        '''
        try:
            self.kafka_producer.send(self.kafka_topic, message)
            print(f'Sent message to kafka: {message}')
        except Exception as err:
            print(f'Exception occured during execution: {err}')

    def consume_kafka_messages(self):
        message_count = 0  
        for message in self.kafka_consumer:
            try:
                message_value = message.value
                print(f"Received: {message_value}")

                # Ensure the directory exists before saving the message
                file_dir = os.path.dirname(os.path.join(self.kafka_directory, f"message_{message_count}.json"))
                os.makedirs(file_dir, exist_ok=True)

                # Store the received message in the file
                file_name = os.path.join(self.kafka_directory, f"message_{message_count}.json")
                with open(file_name, 'w') as file:
                    json.dump(message_value, file, indent=4)

                message_count += 1
            except Exception as e:
                print(f"Error processing Kafka message: {e}")

    def write_record(self, mac_address, dst_mac, source_ip, destination_ip, data) -> None:
        '''
            This will write every target packet to the PacketInstances model, which will then be used
            to render all of them on the client side using node.js
        '''
        target_mac = TargetInstances.objects.get(mac_address = mac_address)
        PacketInstances.objects.create(corresponding_target = target_mac, dst_mac = dst_mac, src_ip = source_ip,
                                       dst_ip = destination_ip, packet_data = data)

    def write(self, packet):
        '''
            The wrpcap method will be called in here
        '''
        wrpcap(f'{self.target_manager.storage_directory}/{packet[Ether].src}.pcap', packet, append = True)

    def stop_filter(self, _):
        if self.shutdown_event.is_set():
            return True
        else:
            return False

    def packet_handler(self, packet):
        ''' 

            This will be called for every single packet instance caught by the sniffer
            PACKETS_PER_FILE variable will be set according to user input on the web app
            Also, will change the implementation so that once we store the requested ammount of packets,
            both sniffer and server threads will terminate, so that we avoid unneccesary payload

        '''
        if not self.shutdown_event.is_set():
            if packet.haslayer(IP) and (packet.haslayer(UDP) or packet.haslayer(TCP)):
                mac_address, ip_address = packet[Ether].src, packet[IP].src
                contains = False
                with self.target_manager.lock:
                    if mac_address in self.target_manager.macs and self.packet_count < self.packets_per_file:
                        print(f'Found packet!: {mac_address}')
                        packet_data = {
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'mac_address': mac_address,
                            'packet_summary': str(packet.summary())
                        }
            
                        self.send_kafka_message(packet_data)
                        if self.target_manager.store_locally:
                            self.write(packet)
                        self.write_record(mac_address, packet[Ether].dst, ip_address, packet[IP].dst, raw(packet))


    def sniff_packets(self, interface):
        '''
            The iface will change according to user input (or it will be filled automatically, will write in the web app)
            for each packet instance the custom handler is called and packets with the target MAC source address
            are stored in found_packets

        '''
        sniff(prn = self.packet_handler, store = 0, iface = interface, stop_filter = self.stop_filter)
        

    def start(self, interface):
        '''
            Main method responsible for instantiating the sniffer thread and *server*
            I will implement a way to check if the user ended the sniffing process
        '''
        try:
            sniffer_thread = threading.Thread(target = self.sniff_packets, args = (interface,))
            sniffer_thread.daemon = True
            kafka_consumer = threading.Thread(target = self.consume_kafka_messages)
            kafka_consumer.daemon = True
            kafka_consumer.start()
            sniffer_thread.start()
        except KeyboardInterrupt:
            self.shutdown_handler()


        
    def start_server(self):
        '''
            If a user adds or deletes a new target MAC address, the request is sent to the socket instantiated in
            this method (which will be a daemon thread), which will then parse it. Obviously, on the web app,
            there will be a list of target mac addresses which will have a widget that call the delete_mac() method.

            PORT_NUM will be an input value by the user, and since we will get it from a HTML Form, 
            we will typecast it as an integer here

            BUFFER_SIZE will also be an input value by the user
            
            I have now begun to question reality. The whole server/client part probably isn't necessary when it comes to
            creating a web API for the monitoring. Instead of having the sockets to parse user inputs, everything will
            be controlled using web widgets in HTML and Django Forms. the sniffer must still be a daemon thread tho

        '''


    def parse_client_request(self, request) -> str:
        '''
            The methods necessary for parsing command line args will not be necessary in the web app
            Hence, we will prob only use this method instead of creating a whole new Client class
            dont know for sure, but this is most likely the case
        
        '''
        cmd = request.get('cmd')
        mac_address = request.get('mac')

        if cmd == 'add':
            return self.target_manager.add_target(mac_address)
        elif cmd == 'del':
            return self.target_manager.delete_target(mac_address)
        
    

    def shutdown_handler(self):
        '''
            For now, this only clears the shutdown_event and sets running as False
            There will be a system for this

        '''
        print('\n Shutting down...')
        self.running = False
        self.shutdown_event.set()

    