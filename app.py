import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import config
from ui import MainWindow
import asyncio
import json
import logging
from config import SYMBOLS, DEFAULT_EXCHANGE, DEFAULT_ASSET


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OKXWebSocket:
    def __init__(self, symbol, callback):
        self.symbol = symbol
        self.callback = callback
        self.running = False

    async def start(self):
        try:
            ws_url = config.WEBSOCKET_URLS["OKX"][self.symbol]
            while self.running:
                try:
                    self.callback({"status": "connected"})
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"WebSocket error: {str(e)}")
                    await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")

    def stop(self):
        self.running = False

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            if 'asks' in data and 'bids' in data:
                self.callback(data)
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")

async def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    ws = OKXWebSocket(SYMBOLS["OKX"][0], window.update_order_book)
    ws.running = True
    asyncio.create_task(ws.start())
    sys.exit(app.exec())

if __name__ == "__main__":
    asyncio.run(main()) 