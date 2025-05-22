import json
import asyncio

from modules.core.sse import BaseSSEConsumer
import yfinance as yf


yf_ws: yf.AsyncWebSocket | None = None


class LiveStocksSSEConsumer(BaseSSEConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_queue = asyncio.Queue()
        self.tickers = None

    def yf_handler(self, data: dict[str, any]) -> None:
        """Synchronous handler for yfinance - puts data in queue"""
        print(f"Received data from yfinance: {data}")
        try:
            self.data_queue.put_nowait(data)
        except:
            pass

    async def send_initial_message(self, params):
        """Parse symbols and start background data processor"""
        symbols = params.get("symbols", [""])[0]
        
        print(f"Starting SSE for symbols: {symbols}")

        asyncio.create_task(self.process_data_queue())
        asyncio.create_task(self.start_yfinance_live(symbols))

        await super().send_initial_message()

    async def start_yfinance_live(self, symbols: str):
        """Start yfinance live data streaming in background"""
        try:
            self.tickers = yf.Tickers(symbols)
            await asyncio.get_event_loop().run_in_executor(
                None, self.tickers.live, self.yf_handler
            )
        except Exception as e:
            print(f"Error starting yfinance live data: {e}")

    async def process_data_queue(self):
        """Process data from the queue and send via SSE"""
        while self._should_continue:
            try:
                data = await asyncio.wait_for(self.data_queue.get(), timeout=1.0)
                await self.send_sse_event(data)
            except asyncio.TimeoutError:
                # print("No data in queue, continuing to wait...")
                continue
            except Exception as e:
                print(f"Error processing data queue: {e}")
                break

    async def get_data(self, params: dict[str, str]):
        """Fallback method - return None since we handle data via queue"""
        return None

    async def disconnect(self):
        print("Disconnecting LiveStocksSSEConsumer")
        if yf_ws is not None:
            await yf_ws.close()
        else:
            print("No active yfinance WebSocket to close.")
        super().disconnect()
