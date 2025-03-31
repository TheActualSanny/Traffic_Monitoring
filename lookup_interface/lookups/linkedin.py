import os
import requests
import threading
from .custom_logger import handle_class
from .update_script import call_update
from dotenv import load_dotenv
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from lookup_interface.models import LookupInstances
from .lookup_class_interface import LookupsInterface
from .constants import HEADERS_DICT, LINKEDIN_URL, LinkedAPI_URL

load_dotenv()

@handle_class
class LinkedinLookups(LookupsInterface):
    def __init__(self):
        self._headers = {**HEADERS_DICT, 'x-rapidapi-host' : os.getenv(os.getenv('Linkedin_Host'))}

    def lookup(self, target: str, api: bool, lock: threading.Lock) -> None:
        self._params = {'username' : target}
        data = self.send_request(url = LinkedAPI_URL)
        profile_url = LINKEDIN_URL.format(target = target)
        
        if not data.get('success') is False:
            status = 'Account found!'
        else:
            status = 'Account not found or private!'
        profile_pic_url = data.get('profilePicture')
        inst = LookupInstances.objects.create(username = target, profile_pic_url = profile_pic_url,
                                        status = status, profile_url = profile_url)
        call_update(api, lock, inst)
        LookupsInterface.send_lookups({profile_url : status})
    
