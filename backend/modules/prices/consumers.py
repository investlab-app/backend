import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer

class PriceStreamConsumer(AsyncWebsocketConsumer):
    names = []

    async def connect(self):
        if not self.scope['user'].is_authenticated:
            await self.close()
            return

        self.names = self.scope['url_route']['kwargs']['name'].split(',')
        self.names = [n.strip().upper() for n in self.names]
        self.layer = get_channel_layer()
        await self.layer.group_add('tickers_broadcast', self.channel_name)
        await self.accept()

    async def broadcast_receive(self, event):
        print(event)
        selected_tickers = [event['data'][ticker] for ticker in self.names if ticker in event['data']]
        print(selected_tickers)
        await self.send(text_data=json.dumps({"message": selected_tickers}))
