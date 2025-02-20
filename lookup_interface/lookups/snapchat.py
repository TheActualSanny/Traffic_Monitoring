import os
import json
import requests
import threading
from lookup_interface.models import LookupInstances
from dotenv import load_dotenv
from .lookup_interface import LookupsInterface
from .constants import SnapAPI_URL, HEADERS_DICT, SNAPCHAT_URL
from .logger import main_logger
from lookup_interface.handle_cache import update_cache

class SnapchatLookups(LookupsInterface):
    '''
        Manages lookups for snapchat accounts.
    '''
    def __init__(self):
        self._headers = {**HEADERS_DICT, 'x-rapidapi-host' : os.getenv('SNAPCHAT_APIHost')}

    def send_request(self, target: str) -> dict:
        response = requests.get(SnapAPI_URL, headers = self._headers, params = {'username' : target})
        try:
            return response.json()
        except:
            raise ValueError('Response returned none type.')
        
    def lookup(self, target: str, api: bool, lock: threading.Lock) -> None:
        data = self.send_request(target)
        url = SNAPCHAT_URL.format(target_name = target)
        if data.get('success'):
            user_data = data.get('data').get('info')
            profile_pic = user_data.get('profilePictureUrl')
            instance = LookupInstances.objects.create(username = target, profile_pic_url = profile_pic,
                                           profile_url = url, status = 'Account found!')
        else:
            instance = LookupInstances.objects.create(username = target, profile_pic_url = None,
                                           profile_url = url, status = "Account doesn't exist!")
        if not api:
            with lock:
                update_cache(instance)
            