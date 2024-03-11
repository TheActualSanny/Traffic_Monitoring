import os
import threading
from dataclasses import dataclass, field
from config import TRAFFIC_DIRECTORY

@dataclass
class TargetManager:
    macs: set = field(default_factory=set)
    mac_directories: dict = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def add_target(self, mac):
        with self.lock:
            if mac not in self.macs:
                self.macs.add(mac)
                mac_directory = os.path.join(TRAFFIC_DIRECTORY)
                os.makedirs(mac_directory, exist_ok=True)
                self.mac_directories[mac] = mac_directory
                return f"MAC {mac} successfully added."
            else:
                return f"MAC {mac} already exists."

    def remove_target(self, mac):
        with self.lock:
            if mac in self.macs:
                self.macs.remove(mac)
                mac_directory = self.mac_directories.pop(mac)
                return f"MAC {mac} successfully removed."
            else:
                return f"MAC {mac} not found in the list."

    def get_targets(self):
        with self.lock:
            return list(self.macs)
