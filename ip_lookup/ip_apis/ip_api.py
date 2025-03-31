import requests
import threading
from dotenv import load_dotenv
from ip_lookup.models import IpLookups
from lookup_interface.lookups.constants import IpAPI_URL
from lookup_interface.lookups.update_script import call_update
from lookup_interface.lookups.custom_logger import handle_class
from lookup_interface.lookups.lookup_class_interface import LookupsInterface

load_dotenv()

class IpLookup(LookupsInterface):
    '''
        Uses the exact same interface as other lookup managers
    '''

    def __init__(self):
        pass

    def lookup(self, ip_address: str, api: bool, lock: threading.Lock) -> None:
        url = IpAPI_URL.format(ip_address = ip_address)
        data = self.send_request(url = url, ip_lookup = True)
        status = data.get('status')
        lat = data.get('lat')
        lon = data.get('lon')
        location = f'{data.get('country')},  {data.get('city')}'
        isp_name = data.get('isp')
        lookup_instance = IpLookups.objects.create(status = status, latitude = lat, longitude = lon,
                                                   location = location, isp = isp_name)
        call_update(api, lock, lookup_instance, ip_cache = True)

