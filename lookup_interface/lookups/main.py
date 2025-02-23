import threading
from .lookup_manager import LookupManager
from .instagram import InstagramLookups
from .twitter import TwitterLookups
from .tiktok import TikTokLookups
from .snapchat import SnapchatLookups

lock = threading.Lock()

def target_lookup(target: str, api: bool) -> LookupManager:
    '''
        This is the function which will be called in views.
        It will return a lookup manager so that the user can do lookups again without reloading the page.
    '''
    
    instagram = InstagramLookups()
    twitter = TwitterLookups()
    tiktok = TikTokLookups()
    snapchat = SnapchatLookups()
    lookup_manager = LookupManager(instagram_manager = instagram, twitter_manager = twitter,
                                   tiktok_manager = tiktok, snapchat_manager = snapchat, lock = lock)

    lookup_manager.main_lookup(target, api = api)

    return lookup_manager
