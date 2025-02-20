from threading import Thread, Lock
from .instagram import InstagramLookups
from .twitter import TwitterLookups
from .tiktok import TikTokLookups
from .snapchat import SnapchatLookups
from dotenv import load_dotenv
from dataclasses import dataclass, field

load_dotenv()

@dataclass
class LookupManager:
    '''
        The main manager class which will be used to do each lookup on seperate threads.

        The implementation of displaying all of these to the users will similar to the implementation of displaying packets.
        In the main.py module we will instantiate a Mutex lock and pass it to each one of the objects.
        Each lookup method will have access to our lookups model and will write new records into it if user data was found.
        Every second or so the front-end will fetch new lookup data and load it onto the website.
        
        {media}_manager: Refrences the lookup class object of the given media class, for now there are only instagram
                        and twitter managers, but there will be seperate classes for most of the social media website.

    '''
    instagram_manager: InstagramLookups
    twitter_manager: TwitterLookups
    tiktok_manager: TikTokLookups
    snapchat_manager: SnapchatLookups
    lock: Lock
    
    def api_lookup(self, username: str) -> None:
        '''
            The same exact method as main_lookup, except this waits for the
            threads to join.
        '''
        

    def main_lookup(self, username: str, api: bool) -> None:
        '''
            The main method, which will call the .lookup() function of all of the managers.
        '''
        media_managers = self.__dict__.copy()
        media_managers.pop('lock')
        threads = [Thread(target = manager.lookup, args = (username, api, self.lock)) for manager in media_managers.values()]
        for thread in threads:
            thread.start()
        if api:
            for thread in threads:
                thread.join()
