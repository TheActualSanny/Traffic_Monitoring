import os
import shutil
import threading
from dataclasses import dataclass, field
from utils.config import TRAFFIC_DIRECTORY

class TargetManager:

    def __init__(self):
        self.macs = {} 
        self.mac_dir = os.path.join(os.getcwd(), TRAFFIC_DIRECTORY)  
        self.lock = threading.Lock()  
        self.target_count = 0  

        if os.path.isdir(self.mac_dir):
            shutil.rmtree(self.mac_dir)

    def add_target(self, mac: str) -> str:
        with self.lock:
            if mac not in self.macs:
                self.target_count += 1
                self.macs[mac] = self.target_count
                os.makedirs(self.mac_dir, exist_ok=True)  
                return f"MAC {mac} successfully added."
            else:
                return f"MAC {mac} already exists."

    def remove_target(self, mac: str) -> str:
        with self.lock:
            if mac in self.macs:
                os.remove(f'{self.mac_dir}/target{self.macs[mac]}.pcap')
                del self.macs[mac]
                return f"MAC {mac} successfully removed."
            else:
                return f"MAC {mac} not found in the list."

    def get_targets(self) -> list:
        with self.lock:
            return list(self.macs)