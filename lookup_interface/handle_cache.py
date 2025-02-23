import json
from django.core.cache import cache
from django.conf import settings
from .models import LookupInstances
from .lookups.lookup_class_interface import LookupsInterface

def update_cache(lookup_instance) -> None:
    '''
        This method is called during the lookup process to
        update our redis cache as new records are saved
    '''
    username = lookup_instance.username

    try: 
        cached_data = json.loads(cache.get(username))
    except TypeError:
        cached_data = cache.get(username)
    lookup_data = lookup_instance.__dict__
    lookup_data.pop('_state')
    cached_data.append(lookup_data)
    updated = json.dumps(cached_data)
    cache.set(username, updated, timeout = 300)



def convert_cache(data: list) -> str:
    '''
        If data about a certain lookup is cached already,
        we call this function. It will loop through the cached dictionaries
        and will transform them into the desired: url : status format and return it as a list
        for it to be sent as a context variable to the template.

    '''
    final_lookups = []
    for elem in data:
        url = elem['profile_url']
        status = elem['status']
        final_lookups.append({url : status})
    return json.dumps(final_lookups)