from ws_client import WebSocketOrderBookClient
from orderbook import OrderBook
from simulator import TradeSimulator
from impact_analysis import OrderBookImpactAnalyzer, MarketParameters
from market_impact_models import AlmgrenChrissParameters
import asyncio
import time
import json
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from websocket import create_connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ORDERBOOK_URL = "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP"

orderbook = OrderBook()
simulator = TradeSimulator(orderbook)
impact_analyzer = OrderBookImpactAnalyzer(orderbook)

impact_analyzer.update_market_parameters(
    volatility=0.03,  # 3% daily volatility for BTC
    volume=5000       # Estimated daily volume in BTC
)

impact_analyzer.ac_params = AlmgrenChrissParameters(
    permanent_impact=0.15,
    temporary_impact=0.2,
    temporary_decay=0.6,
    risk_aversion=1.5,
    volatility=0.03,
    initial_price=0.0
)

impact_analyzer._initialize_ac_model()

message_counter = 0

async def handle_message(data):
    global message_counter
    asks = data.get("asks", [])
    bids = data.get("bids", [])
    orderbook.update(asks, bids)
    message_counter += 1
    if message_counter % 10 == 0:
        best_ask = orderbook.get_best_ask()
        best_bid = orderbook.get_best_bid()
        mid_price = orderbook.get_mid_price()
        spread = best_ask - best_bid if best_ask and best_bid else None
        
        print(f"\n--- Order Book Update at {time.strftime('%H:%M:%S')} ---")
        print(f"Best Ask: {best_ask}")
        print(f"Best Bid: {best_bid}")
        print(f"Mid Price: {mid_price}")
        print(f"Spread: {spread} ({(spread/mid_price)*10000 if mid_price else 0:.2f} bps)")
        
        avg_price = simulator.estimate_cost('buy', 10)
        if avg_price:
            print(f"\n--- Basic Simulation ---")
            print(f"Estimated avg price for 10 BTC buy: {avg_price}")
            print(f"Slippage: {((avg_price/mid_price)-1)*10000 if mid_price else 0:.2f} bps")
        print(f"\n--- Market Impact Analysis ---")
        impact = impact_analyzer.estimate_market_impact(50, 'buy')
        print(f"Market impact for 50 BTC buy: {impact['impact_percentage']:.4f}%")
        print(f"Maker/Taker split: {impact['maker_proportion']*100:.1f}% / {impact['taker_proportion']*100:.1f}%")
        strategy = impact_analyzer.optimal_execution_strategy(100, 'buy', 1.0, 4)
        print(f"\n--- Optimal Execution Strategy for 100 BTC ---")
        print(f"Schedule: {[f'{x:.2f}' for x in strategy['execution_schedule']]}")
        print(f"Expected shortfall: {strategy['expected_shortfall_bps']:.2f} bps")
        slippage = impact_analyzer.estimate_slippage(30, 'buy')
        print(f"\n--- Slippage Estimation ---")
        print(f"Estimated slippage for 30 BTC buy: {slippage:.2f} bps")
        print("-" * 50)

class TradingSimulator:
    def __init__(self, orderbook, analyzer):
        self.orderbook = orderbook
        self.analyzer = analyzer
        self.positions = []
        self.trades = []
        self.pnl = 0.0

    def simulate_trade(self, quantity: float, side: str):
        try:
            # Get current market state
            mid_price = self.orderbook.get_mid_price()
            if not mid_price:
                return None
            impact = self.analyzer.estimate_market_impact(quantity, side)
            
            # Calculate execution price with impact
            execution_price = mid_price * (1 + impact['impact_percentage']/100) if side == 'buy' else \
                            mid_price * (1 - impact['impact_percentage']/100)
            trade = {
                'timestamp': datetime.now(),
                'side': side,
                'quantity': quantity,
                'price': execution_price,
                'impact': impact['impact_percentage'],
                'cost': impact['estimated_cost']
            }
            self.trades.append(trade)
            
            # Update PnL
            if side == 'buy':
                self.pnl -= execution_price * quantity
            else:
                self.pnl += execution_price * quantity
            
            return trade
            
        except Exception as e:
            logger.error(f"Error simulating trade: {str(e)}")
            return None

def plot_execution_strategy(strategy: dict, title: str = "Optimal Execution Strategy"):
    """Plot the optimal execution strategy."""
    try:
        plt.figure(figsize=(12, 6))
        
        # Plot execution schedule
        plt.subplot(2, 1, 1)
        plt.plot(strategy['execution_schedule'], label='Remaining Position')
        plt.title('Position Schedule')
        plt.xlabel('Time Period')
        plt.ylabel('Position Size')
        plt.grid(True)
        plt.legend()
        
        # Plot trading rates
        plt.subplot(2, 1, 2)
        plt.plot(strategy['trading_rates'], label='Trading Rate')
        plt.title('Trading Rate')
        plt.xlabel('Time Period')
        plt.ylabel('Rate')
        plt.grid(True)
        plt.legend()
        
        plt.tight_layout()
        plt.savefig('execution_strategy.png')
        plt.close()
        
    except Exception as e:
        logger.error(f"Error plotting execution strategy: {str(e)}")

def print_market_analysis(orderbook: OrderBook, analyzer: OrderBookImpactAnalyzer):
    """Print current market analysis."""
    try:
        mid_price = orderbook.get_mid_price()
        if not mid_price:
            return

        print("\n=== Market Analysis ===")
        print(f"Mid Price: {mid_price:.2f}")
        
        # Calculate and print spread
        if orderbook.asks and orderbook.bids:
            best_ask = float(orderbook.asks[0][0])
            best_bid = float(orderbook.bids[0][0])
            spread = best_ask - best_bid
            spread_bps = (spread / best_bid) * 10000
            print(f"Spread: {spread:.2f} ({spread_bps:.2f} bps)")
        
        # Print market depth
        if analyzer.market_params:
            print(f"Market Depth: ${analyzer.market_params.market_depth:,.2f}")
            print(f"Volatility: {analyzer.market_params.volatility:.4f}")
            print(f"Avg Trade Size: {analyzer.market_params.avg_trade_size:.2f}")
        
        print("=====================\n")
        
    except Exception as e:
        logger.error(f"Error printing market analysis: {str(e)}")

async def main():
    # Initialize components
    orderbook = OrderBook()
    analyzer = OrderBookImpactAnalyzer(orderbook)
    orderbook.analyzer = analyzer
    simulator = TradingSimulator(orderbook, analyzer)
    
    # Initialize WebSocket client with the specified endpoint
    ws_client = WebSocketOrderBookClient(ORDERBOOK_URL, orderbook.update)
    
    try:
        # Start WebSocket client
        ws_client.run()
        logger.info("WebSocket client started")
        await asyncio.sleep(2)
        while True:
            try:
                print_market_analysis(orderbook, analyzer)
                if orderbook.get_mid_price():
                    strategy = analyzer.optimal_execution_strategy(
                        quantity=1.0,
                        side='buy',
                        time_horizon=1.0,
                        num_periods=10
                    )
                    plot_execution_strategy(strategy)
                    trade = simulator.simulate_trade(1.0, 'buy')
                    if trade:
                        print("\n=== Trade Simulation ===")
                        print(f"Side: {trade['side']}")
                        print(f"Quantity: {trade['quantity']}")
                        print(f"Price: {trade['price']:.2f}")
                        print(f"Impact: {trade['impact']:.2f}%")
                        print(f"Cost: ${trade['cost']:.2f}")
                        print(f"Total PnL: ${simulator.pnl:.2f}")
                        print("=====================\n")
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                await asyncio.sleep(1)
                
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        ws_client.stop()
        logger.info("WebSocket client stopped")

if __name__ == "__main__":
    asyncio.run(main())