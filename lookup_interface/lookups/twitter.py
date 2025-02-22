import requests
import json
import os
import threading
from dotenv import load_dotenv
from .logger import main_logger
from .constants import TWITTER_URL, HEADERS_DICT, TwitAPI_URL, JSONType
from .lookup_class_interface import LookupsInterface
from .update_script import call_update
from lookup_interface.models import LookupInstances
from lookup_interface.handle_cache import update_cache
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

load_dotenv()

class TwitterLookups(LookupsInterface):
    def __init__(self):
        '''
            The crucial params/headers will be set here.
        '''
        self._headers = {**HEADERS_DICT,
                        'x-rapidapi-host' : os.getenv('TWITTER_APIHost')}


    def send_request(self, url: str) -> JSONType:
        '''
            We send the request to the Twitter API to get the User data.
            This method will probably be written in a mixin class, considering
            that every single lookup class must implement this.
        '''
        
        response = requests.get(url, headers = self._headers, timeout = 7)
        try:
            return response.json()
        except Exception as err:
            main_logger.error(err)

    def lookup(self, target: str, api: bool, lock: threading.Lock) -> dict:
        '''
            The main method. This is defined in the formal interface, as all of
            them must have different implementations.
        '''    
        url = TwitAPI_URL.format(username = target)
        data = self.send_request(url)
        finalized_url = TWITTER_URL.format(target_name = target)
        status = "Account is private or doesn't exist!"
        if data:
            results = data.get('user').get('result')
            status = 'Account found!'
            profile_pic = results.get('legacy').get('profile_image_url_https')
            LookupInstances.objects.create(username = target, status = status, profile_pic_url = profile_pic,
                                           profile_url = finalized_url)
            LookupsInterface.send_lookups({finalized_url: status}, cached = False)
            call_update(api, lock, instance)
            print({finalized_url : 'Account found!'})
            return {finalized_url : 'Account found!'}
        else:
            instance = LookupInstances.objects.create(username = target, status = status, profile_pic_url = None,
                                           profile_url = finalized_url)
            LookupsInterface.send_lookups({finalized_url: status}, cached = False)
            call_update(api, lock, instance)
            return {finalized_url : 'Account doesnt exist!'}
