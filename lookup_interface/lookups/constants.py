''' All of the placeholder URLs will be stored here, so that when the user
    sends a request, the URL will be displayed on the web interface. '''
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

INSTAGRAM_URL = 'www.instagram.com/{target_name}'
TWITTER_URL = 'www.x.com/{target_name}'
TIKTOK_URL = 'www.tiktok.com/@{target_name}'
SNAPCHAT_URL = 'www.snapchat.com/add/{target_name}'
HEADERS_DICT = {'User-Agent' : os.getenv('UserAgent'), 
                'x-rapidapi-key' : os.getenv('RapidKEY')}
TIKTOKAPI_URL =  'https://tiktok-api23.p.rapidapi.com/api/user/info'
TwitAPI_URL = "https://twitter-aio.p.rapidapi.com/user/by/username/{username}"
SnapAPI_URL = 'https://snapchat3.p.rapidapi.com/getProfile'
JSONType = Dict[str, Any]