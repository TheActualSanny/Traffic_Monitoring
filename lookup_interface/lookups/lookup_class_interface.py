import requests
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
    def send_request(self,  url: str = None, contains_target: bool = True, ip_lookup: bool = False) -> dict:

        if contains_target:
            response = requests.get(url, headers = self._headers, params = self._params)
        elif ip_lookup:
            response = requests.get(url = url)
        else:
            response = requests.get(url, headers = self._headers)
    
        try:
            return response.json()
        except requests.JSONDecodeError:
            pass

    @abstractmethod
    def lookup(self):
        pass
        
    @staticmethod   
    def send_lookups(lookup_data: dict) -> None:
        '''
            This will be a static method that will be called 
            whenever the managers finish the lookup data fetching.
            This will send the essential data to the client socket
            for it to dynamically load the data onto the website.
        '''
        layer = get_channel_layer()
        data = {
            'type' : 'send_lookups',
            'lookup_data' : lookup_data
        }
        
        async_to_sync(layer.group_send)(
            'lookups',
            data
        )