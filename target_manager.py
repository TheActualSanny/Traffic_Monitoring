import os
import threading
from dataclasses import dataclass, field
from config import TRAFFIC_DIRECTORY


@dataclass
class TargetManager:
    """
    Manages a set of target MAC addresses and their associated directories.

    Attributes:
        macs (set): Set of target MAC addresses.
        mac_directories (dict): Dictionary mapping MAC addresses to their corresponding directories.
        lock (threading.Lock): Thread lock for ensuring thread safety.

    Methods:
        add_target(mac: str) -> str: Add a target MAC address to the manager.
        remove_target(mac: str) -> str: Remove a target MAC address from the manager.
        get_targets() -> List[str]: Get a list of current target MAC addresses.
    """

    macs: set = field(default_factory=set)
    mac_directories: dict = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def add_target(self, mac: str) -> str:
        """
        Add a target MAC address to the manager.

        Args:
            mac (str): The MAC address to be added.

        Returns:
            str: A message indicating the success or failure of the operation.
        """
        with self.lock:
            if mac not in self.macs:
                self.macs.add(mac)
                mac_directory = os.path.join(TRAFFIC_DIRECTORY)
                os.makedirs(mac_directory, exist_ok=True)
                self.mac_directories[mac] = mac_directory
                return f"MAC {mac} successfully added."
            else:
                return f"MAC {mac} already exists."

    def remove_target(self, mac: str) -> str:
        """
        Remove a target MAC address from the manager.

        Args:
            mac (str): The MAC address to be removed.

        Returns:
            str: A message indicating the success or failure of the operation.
        """
        with self.lock:
            if mac in self.macs:
                self.macs.remove(mac)
                self.mac_directories.pop(mac)
                return f"MAC {mac} successfully removed."
            else:
                return f"MAC {mac} not found in the list."

    def get_targets(self) -> list:
        """
        Get a list of current target MAC addresses.

        Returns:
            List[str]: A list of target MAC addresses.
        """
        with self.lock:
            return list(self.macs)
