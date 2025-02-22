from lookup_interface.models import LookupInstances
from threading import Lock
from abc import ABC, abstractmethod
from .constants import JSONType
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class LookupsInterface(ABC):
    '''
        This will be the formal interface for all of our lookup classes.
        it Includes main methods such as send_request() and lookup() 
    '''
    @abstractmethod
    def send_request(self):
        pass

    @abstractmethod
    def lookup(self):
        pass
        
    @staticmethod   
    def send_lookups(lookup_data: dict, cached: bool) -> None:
        '''
            This will be a static method that will be called 
            whenever the managers finish the lookup data fetching.
            This will send the essential data to the client socket
            for it to dynamically load the data onto the website.
        '''
        layer = get_channel_layer()
        if not cached:
            data = {
                'type' : 'send_lookups',
                'lookup_data' : lookup_data
            }
        else:
            data = {
                'type' : 'send_cached_lookups',
                'cached_lookup_data' : lookup_data
            }

        async_to_sync(layer.group_send)(
            'lookups',
            data
        )