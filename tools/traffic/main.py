import os
from . import server
from .targets import TargetManager
from threading import Thread, Event

def start_sniffing(packet_limit, network_interface, initial_dir) -> None:
    '''
        This function will be called inside views.py to start the background sniffing thread.
        It is written in a function so that the user can first set params, and then call the function which
        will set the global main_sniffer as a Server instance, so that the user can then call methods usiong that reference.
    '''
    evnt = Event()
    manager = TargetManager(storage_directory = os.path.join(os.getcwd(), initial_dir))
    main_sniffer = server.Server('0.0.0.0', evnt, manager, packets_per_file = packet_limit)
    main_sniffer.start(network_interface)
    return main_sniffer

