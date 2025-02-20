from abc import ABC, abstractmethod
from .constants import JSONType

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

