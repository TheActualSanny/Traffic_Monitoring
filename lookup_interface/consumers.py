import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

class LookupConsumer(WebsocketConsumer):
    '''
        Consumer class which will handle lookup channels. 
    '''

    def connect(self):
        self.accept()
        async_to_sync(self.channel_layer.group_add)('lookups', self.channel_name)
        self.send(text_data = json.dumps({'msg' : 'success'}))

    def disconnect(self, code):
        self.channel_layer.group_discard('lookups', self.channel_name)

    def send_lookups(self, event):
        new_lookups = event['lookup_data']
        self.send(text_data = json.dumps({'lookup_data' : new_lookups}))