import websocket
import json
import threading
import time
import logging
from datetime import datetime

class WebSocketOrderBookClient:
    def __init__(self, url, callback):
        self.url = url
        self.callback = callback
        self.ws = None
        self.running = False
        self.thread = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('WebSocketClient')
    
    def on_message(self, ws, message):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            
            # Process order book data
            if isinstance(data, dict) and 'asks' in data and 'bids' in data:
                # Sort asks and bids
                asks = sorted(data['asks'], key=lambda x: float(x[0]))  # Sort by price ascending
                bids = sorted(data['bids'], key=lambda x: float(x[0]), reverse=True)  # Sort by price descending
                
                # Print order book snapshot
                print(f"\n=== Order Book Update at {timestamp} ===")
                print("Top 5 Asks:")
                for price, size in asks[:5]:
                    print(f"  Price: {price:>10}, Size: {size:>10}")
                print("\nTop 5 Bids:")
                for price, size in bids[:5]:
                    print(f"  Price: {price:>10}, Size: {size:>10}")
                
                # Calculate and print spread
                if asks and bids:
                    best_ask = float(asks[0][0])
                    best_bid = float(bids[0][0])
                    spread = best_ask - best_bid
                    spread_bps = (spread / best_bid) * 10000
                    print(f"\nSpread: {spread:.2f} ({spread_bps:.2f} bps)")
                
                # Call the callback function with the processed data
                if self.callback:
                    self.callback({'asks': asks, 'bids': bids})
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse message: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
    
    def on_error(self, ws, error):
        """Handle WebSocket errors."""
        self.logger.error(f"WebSocket error: {str(error)}")
        self.reconnect_attempts += 1
        
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.logger.info(f"Attempting to reconnect in {self.reconnect_delay} seconds...")
            time.sleep(self.reconnect_delay)
            self.reconnect()
        else:
            self.logger.error("Max reconnection attempts reached. Giving up.")
            self.running = False
    
    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection close."""
        self.logger.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        if self.running:  # Only attempt reconnect if we're still supposed to be running
            self.reconnect()
    
    def on_open(self, ws):
        """Handle WebSocket connection open."""
        self.logger.info("WebSocket connection established")
        self.running = True
        self.reconnect_attempts = 0  # Reset reconnect attempts on successful connection
    
    def reconnect(self):
        """Attempt to reconnect to the WebSocket server."""
        if self.ws:
            self.ws.close()
        self._run_websocket()
    
    def run(self):
        """Run the WebSocket client in a separate thread."""
        self.thread = threading.Thread(target=self._run_websocket)
        self.thread.daemon = True
        self.thread.start()
    
    def _run_websocket(self):
        """Internal method to run the WebSocket connection."""
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            self.url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        self.ws.run_forever()
    
    def stop(self):
        """Stop the WebSocket client."""
        self.running = False
        if self.ws:
            self.ws.close()
        if self.thread:
            self.thread.join() 