import os
import threading
import shutil
from dataclasses import dataclass, field
from .config import TRAFFIC_DIR

@dataclass
class TargetManager:
    storage_directory: str 
    macs: set = field(default_factory = set)
    lock: threading.Lock = field(default_factory = threading.Lock)

    @staticmethod
    def finalized_path(dir_name):
        '''
            This will be used to get the finalized path to our directory
        '''
        return os.path.join(os.getcwd(), dir_name) 

    def add_target(self, mac: str) -> str:
        '''
            Method which adds a new MAC address to the macs set
            and creates a new directory for it
        '''
        with self.lock:
            if mac not in self.macs:
                self.macs.add(mac)
                # os.makedirs(self.storage_directory, exist_ok = True)
                return f'MAC {mac} has been added to the target list.'
            else:
                return f'MAC {mac} is already set as a target.'

    def delete_target(self, mac):
        '''
            Deletes a certain MAC address from the set and removes the pcap file for it.
        '''
        with self.lock:
            if mac in self.macs:
                # os.remove(f'{self.storage_directory}/{mac}.pcap')
                self.macs.remove(mac)
                return f'MAC {mac} has been removed from the target list.'
            else:
                return f'MAC {mac} is not a target.'
            
    def update_dir(self, new_dir):
        '''
            This method will be called whenever the user calls the terminate_sniffer view
        '''
        shutil.rmtree(self.storage_directory)
        self.storage_directory = self.finalized_path(new_dir)