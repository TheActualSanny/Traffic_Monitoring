import json
from django.core.cache import cache
from django.conf import settings
from .models import LookupInstances
from .lookups.lookup_class_interface import LookupsInterface

def update_cache(lookup_instance, ip_cache: bool = False) -> None:
    '''
        This method is called during the lookup process to
        update our redis cache as new records are saved
    '''
    key = lookup_instance.username if not ip_cache else lookup_instance.ip_address

    try: 
        cached_data = json.loads(cache.get(key))
    except TypeError:
        cached_data = cache.get(key)
    lookup_data = lookup_instance.__dict__
    lookup_data.pop('_state')
    cached_data.append(lookup_data)
    updated = json.dumps(cached_data)
    cache.set(key, updated, timeout = 300)



def convert_cache(data: list, ip_cache: bool = False) -> str:
    '''
        If data about a certain lookup is cached already,
        we call this function. It will loop through the cached dictionaries
        and will transform them into the desired: url : status format and return it as a list
        for it to be sent as a context variable to the template.

    '''
    if not ip_cache:
        final_lookups = []
        for elem in data:
            url = elem['profile_url']
            status = elem['status']
            final_lookups.append({url : status})
        return json.dumps(final_lookups)
    else:
        return json.dumps(data)