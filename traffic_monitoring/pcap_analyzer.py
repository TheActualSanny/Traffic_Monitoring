from scapy.all import rdpcap, IP, TCP, UDP
import pandas as pd

class PcapAnalyzer:
    def __init__(self, pcap_file):
        self.pcap_file = pcap_file
        self.packets = self.load_pcap()

    def load_pcap(self):
        try:
            return rdpcap(self.pcap_file)
        except Exception as e:
            print(f"Error loading pcap file: {e}")
            return []

    def packet_summary(self):
        print(f"Total number of packets: {len(self.packets)}")
        for i, packet in enumerate(self.packets[:5]):
            print(f"Packet {i+1}: {packet.summary()}")

    def analyze_packets(self):
        packet_data = []
        for pkt in self.packets:
            if pkt.haslayer(IP):  
                data = {
                    "Source IP": pkt[IP].src,
                    "Destination IP": pkt[IP].dst,
                    "Protocol": pkt[IP].proto
                }

                if pkt.haslayer(TCP):
                    data["Source Port"] = pkt[TCP].sport
                    data["Destination Port"] = pkt[TCP].dport
                elif pkt.haslayer(UDP):
                    data["Source Port"] = pkt[UDP].sport
                    data["Destination Port"] = pkt[UDP].dport
                else:
                    data["Source Port"] = None
                    data["Destination Port"] = None

                packet_data.append(data)
        return packet_data

    def export_to_csv(self, output_file):
        packet_data = self.analyze_packets()
        if packet_data:
            df = pd.DataFrame(packet_data)
            df.to_csv(output_file, index=False)
            print(f"Analysis exported to {output_file}")
        else:
            print("No data to export.")

pcap_file = "/home/user/Work/Personal/Working_Traffic_Monitoring/Github_Version (another copy)/zzz/78:44:76:c8:bd:20/2025/01/22/78:44:76:c8:bd:20_2025-01-22_17-10-02.pcap"

analyzer = PcapAnalyzer(pcap_file)

analyzer.packet_summary()

analyzer.export_to_csv("/home/user/Work/Personal/Working_Traffic_Monitoring/Github_Version (another copy)/Traffic_Monitoring/utils/packet_analysis.csv")
