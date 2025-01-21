import signal
import threading
import socket
import json
from dataclasses import dataclass, field
from scapy.all import  wrpcap, sniff, raw, Ether, IP, UDP, TCP
from .targets import TargetManager
from tools.models import PacketInstances, TargetInstances

@dataclass
class Server:
    ip: str
    event: threading.Event
    target_manager: TargetManager
    packets_per_file: int 
    shutdown_event: threading.Event = field(default_factory = threading.Event)
    running: bool = True
    packet_caught: bool = False
    packet_count: int = 0
    found_packets: list = field(default_factory = list)


    def write_record(self, mac_address, dst_mac, source_ip, destination_ip, data) -> None:
        '''
            This will write every target packet to the PacketInstances model, which will then be used
            to render all of them on the client side using node.js
        '''
        target_mac = TargetInstances.objects.get(mac_address = mac_address)
        PacketInstances.objects.create(corresponding_target = target_mac, src_ip = source_ip,
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
                with self.target_manager.lock:
                    if mac_address in self.target_manager.macs and self.packet_count < self.packets_per_file:
                        print(f'Found packet!: {mac_address}')
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
