import json
from django.core.cache import cache
from django.conf import settings
from .models import LookupInstances

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
    print(f'Name: {username} \n  Data-Type: {type(cached_data)}  \n Data: {len(cached_data)} \n URL: {lookup_instance.profile_url}')


def load_cache(username: str) -> list:
    '''
        If data about a certain lookup is cached already,
        we call this function. It will loop through the cached dictionaries
        and respond a list of corresponding LookupInstances that we can then pass to the front-end.
    '''
    cached_data = json.loads(cache.get(username))
    final_lookups = []
    for elem in cached_data:
        record = LookupInstances.objects.get(id = elem['id'])
        final_lookups.append(record)
    return final_lookups


