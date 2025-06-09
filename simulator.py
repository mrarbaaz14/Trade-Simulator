class TradeSimulator:
    def __init__(self, orderbook):
        self.orderbook = orderbook
 
    def estimate_cost(self, side, quantity):
        if side == 'buy':
            return self.orderbook.get_best_ask()
        else:
            return self.orderbook.get_best_bid() 