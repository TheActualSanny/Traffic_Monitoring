import json
from channels.layers import get_channel_layer
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

class PacketConsumer(WebsocketConsumer):
    '''
        This consumer class will be used to accept a handshake from the client.
    '''

    def connect(self):
        self.accept()
        async_to_sync(self.channel_layer.group_add)('client', self.channel_name)
        PacketConsumer.channel_name = self.channel_name
        self.send(text_data = json.dumps({'msg' : 'success'}))

    def disconnect(self, close_code):
        self.channel_layer.group_discard('client', self.channel_name)

    def send_packets(self, event):
        packets = event['packets']
        self.send(text_data = json.dumps({'packets' : packets}))
