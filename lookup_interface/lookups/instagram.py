import requests
import json
import os
import threading
from typing import Dict, Any
from dotenv import load_dotenv
from .logger import main_logger
from .constants import INSTAGRAM_URL, HEADERS_DICT, JSONType
from .lookup_interface import LookupsInterface
from lookup_interface.models import LookupInstances
from lookup_interface.handle_cache import update_cache

load_dotenv()

class InstagramLookups(LookupsInterface):
    def __init__(self):
        '''
            We set the initial parameters that we will need to send the requests to the API
        '''
        self._headers = {**HEADERS_DICT, 
                        'x-rapidapi-host' : os.getenv('INSTAGRAM_APIHost')}
        self._url = os.getenv('InstaURL')


    
    def send_request(self, username: str) -> JSONType:
        '''
            Fetches the User data if found.

            username: The user will pass the target username via the Django view
        '''

        response = requests.get(self._url, headers = self._headers, params = { 'username_or_id_or_url' : username},
                                timeout = 7)
        try:
            return response.json()
        except Exception as err:
            main_logger.error(f'An exception was raised during the fetching process: {err}')

        
    def lookup(self, target: str, api: bool, lock: threading.Lock) ->  None:
        '''
            The main method which will parse the JSON data returned by send_request.

            target: This will be the target that the user inputs, which will be then passsed to send_request to get
            the data.

            For now this just returns a dictionary containing the User's URL and a string value.
            However, I will refactor this to return some data about the user if found which we will then
            display on the page dynamically via serializing it as JSON data and passing it onto the front-end.
        '''

        json_data = self.send_request(target)
        potential = json_data.get('detail')
        finalized_url = INSTAGRAM_URL.format(target_name = target)
        if potential == 'Private account':
            status = "Account found but it's private."
            instance = LookupInstances.objects.create(username = target, status = status, profile_pic_url = None,
                                                      profile_url = finalized_url)
            if not api:
                update_cache(isinstance)
            return {finalized_url : "Account found but it's private."}
        elif potential:
            status = "Account not found!"
            instance = LookupInstances.objects.create(username = target, status = status,profile_pic_url = None,
                                                      profile_url = finalized_url)
            if not api:
                update_cache(isinstance)
            return {finalized_url : 'Account not found!'}
        else:
            status = "Account found!"
            actual_data = json_data.get('data')
            pic_url = actual_data.get('profile_pic_url')
            instance = LookupInstances.objects.create(username = target, status = status, profile_pic_url = pic_url,
                                                      profile_url = finalized_url)
            print({finalized_url : "Account found!"})
            if not api:
                with lock:
                    update_cache(instance)
            return {finalized_url : "Account found!"}           
