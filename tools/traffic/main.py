import os
from . import server
from .targets import TargetManager
from threading import Thread, Event
from .kafka_components.kafka_methods import create_consumer, create_producer

def start_sniffing(packet_limit: int, network_interface: str, initial_dir: str, local_storage: str,
                   initial_broker: str, initial_topic: str, initial_group_id: str, initial_directory: str) -> None:
    '''
        This function will be called inside views.py to start the background sniffing thread.
        It is written in a function so that the user can first set params, and then call the function which
        will set the global main_sniffer as a Server instance, so that the user can then call methods usiong that reference.
    '''
    evnt = Event()
    kafka_directory = f'{os.getcwd()}/{initial_directory}'
    initial_consumer = create_consumer(kafka_broker = initial_broker, kafka_topic = initial_topic,
                                       group_id = initial_group_id)
    initial_producer = create_producer(kafka_broker = initial_broker, kafka_topic = initial_topic)

    manager = TargetManager(storage_directory = os.path.join(os.getcwd(), initial_dir), store_locally = local_storage)
    main_sniffer = server.Server('0.0.0.0', evnt, manager, packets_per_file = packet_limit,
                                 kafka_consumer = initial_consumer, kafka_producer = initial_producer,
                                 kafka_topic = initial_topic, kafka_directory = initial_directory)
    main_sniffer.start(network_interface)
    return main_sniffer

