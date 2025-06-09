"""
OrderBook module for managing cryptocurrency order book data.
"""

class OrderBook:
    """
    A class to manage and process order book data from cryptocurrency exchanges.
    Maintains asks (sell orders) and bids (buy orders) with their prices and quantities.
    """
    
    def __init__(self):
        """Initialize an empty order book with asks and bids."""
        self.asks = {}  # Price -> Quantity mapping for sell orders
        self.bids = {}  # Price -> Quantity mapping for buy orders
    
    def update(self, asks, bids):
        """
        Update the order book with new ask and bid data.
        
        Args:
            asks (list): List of [price, quantity] pairs for ask orders
            bids (list): List of [price, quantity] pairs for bid orders
        """
        # Update asks
        for price, quantity in asks:
            price = float(price)
            quantity = float(quantity)
            
            if quantity > 0:
                self.asks[price] = quantity
            else:
                # Remove the price level if quantity is 0
                if price in self.asks:
                    del self.asks[price]
        
        # Update bids
        for price, quantity in bids:
            price = float(price)
            quantity = float(quantity)
            
            if quantity > 0:
                self.bids[price] = quantity
            else:
                # Remove the price level if quantity is 0
                if price in self.bids:
                    del self.bids[price]
    
    def get_best_ask(self):
        """Get the lowest ask price (best selling price)."""
        if not self.asks:
            return None
        return min(self.asks.keys())
    
    def get_best_bid(self):
        """Get the highest bid price (best buying price)."""
        if not self.bids:
            return None
        return max(self.bids.keys())
    
    def get_asks(self):
        """Get all ask orders sorted by price (ascending)."""
        return sorted([(price, qty) for price, qty in self.asks.items()])
    
    def get_bids(self):
        """Get all bid orders sorted by price (descending)."""
        return sorted([(price, qty) for price, qty in self.bids.items()], reverse=True)
    
    def get_spread(self):
        """Calculate the spread between the best ask and best bid."""
        best_ask = self.get_best_ask()
        best_bid = self.get_best_bid()
        
        if best_ask is None or best_bid is None:
            return None
        
        return best_ask - best_bid
    
    def get_mid_price(self):
        """Calculate the mid price between best ask and best bid."""
        best_ask = self.get_best_ask()
        best_bid = self.get_best_bid()
        
        if best_ask is None or best_bid is None:
            return None
        
        return (best_ask + best_bid) / 2