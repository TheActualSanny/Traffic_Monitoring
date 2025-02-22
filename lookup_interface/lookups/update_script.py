from threading import Lock
from lookup_interface.handle_cache import update_cache
from lookup_interface.models import LookupInstances

def call_update(api: bool, lock: Lock, instance: LookupInstances) -> None:
        '''
            This method will be called to call the update_cache() method
            in manager classes.
        '''
        try:
            if not api:
                with lock:
                    update_cache(instance)
        except Exception as err:
            print(err)