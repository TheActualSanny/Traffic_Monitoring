import socket
from scapy.all import sniff, ARP, UDP,IP, Ether
from scapy.all import *
from config import SERVER_PORT, INTERFACE
from datetime import datetime

def write(pkt):
    wrpcap('filtered.pcap', pkt, append=True) 

def packet_handler(packet):
    if packet.haslayer(UDP):
        source_mac = packet[Ether].src.lower()
        now = datetime.now()
        write(packet)

def start_sniffer():
    sniff(prn=packet_handler, store=0, iface="wlo1") 
