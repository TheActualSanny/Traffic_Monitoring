import os
import requests
import threading
from dotenv import load_dotenv
from .constants import JSONType, HEADERS_DICT, TIKTOK_URL, TIKTOKAPI_URL
from lookup_interface.models import LookupInstances
from .lookup_class_interface import LookupsInterface
from .update_script import call_update
from lookup_interface.handle_cache import update_cache
from .logger import main_logger
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

load_dotenv()

class TikTokLookups(LookupsInterface):
    '''
        Manages the lookups for TikTok accounts.
    '''

    def __init__(self):
        self._headers = {**HEADERS_DICT, 'x-rapidapi-host' : os.getenv('TIKTOK_APIHost')}

        
    def send_request(self, username: str) -> JSONType:
        response = requests.get(TIKTOKAPI_URL, headers = self._headers, params = {'uniqueId' : username})
        try:
            return response.json()
        except err as err:
            main_logger.error(f'Exception has been raised: {err}')
    
    def lookup(self, target: str, api: bool, lock : threading.Lock) -> None:
        '''
            The main method responsible for parsing.
            Doesn't return a value as the purpose of the method is to create a new record in the LookupInstances model.
        '''
        data = self.send_request(target)
        user_data = data.get('userInfo')
        finalized_url = TIKTOK_URL.format(target_name = target)
        profile_pic = None
        if user_data:
            profile_pic = user_data.get('user').get('avatarThumb')
        status = 'Account found!' if profile_pic else "Account private or doesn't exist!"
        LookupsInterface.send_lookups({finalized_url : status})
        instance = LookupInstances.objects.create(username = target, status = status, profile_pic_url = profile_pic,
                                                  profile_url = finalized_url)
        call_update(api, lock, instance)
        

