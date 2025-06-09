"""
Configuration module for the Crypto Trade Simulator application.
This module centralizes configuration settings to make the application more extensible.
"""

# WebSocket URLs for different exchanges and trading pairs
WEBSOCKET_URLS = {
    "OKX": {
        "BTC-USDT-SWAP": "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP",
        "ETH-USDT-SWAP": "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/ETH-USDT-SWAP",
        "SOL-USDT-SWAP": "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/SOL-USDT-SWAP"
    }
}

# Default configuration
DEFAULT_EXCHANGE = "OKX"
DEFAULT_ASSET = "BTC-USDT-SWAP"

# Available symbols for each exchange
SYMBOLS = {
    "OKX": ["BTC-USDT-SWAP", "ETH-USDT-SWAP", "SOL-USDT-SWAP"]
}

# Fee tiers for different exchanges
FEE_TIERS = {
    "OKX": {
        "Tier 1 (0.08%/0.1%)": {
            "maker": 0.0008,  # 0.08%
            "taker": 0.001    # 0.1%
        },
        "Tier 2 (0.07%/0.09%)": {
            "maker": 0.0007,  # 0.07%
            "taker": 0.0009   # 0.09%
        },
        "Tier 3 (0.06%/0.08%)": {
            "maker": 0.0006,  # 0.06%
            "taker": 0.0008   # 0.08%
        }
    }
}

# Available order types for each exchange
ORDER_TYPES = {
    "OKX": ["Market", "Limit", "Stop", "Stop Limit", "Post Only", "IOC", "FOK"]
}

# Default fee tier
DEFAULT_FEE_TIER = "Tier 1 (0.08%/0.1%)"

# Available exchanges
EXCHANGES = ["OKX"]

# Default order type
DEFAULT_ORDER_TYPE = "Market"

# Default quantity (in USD)
DEFAULT_QUANTITY = 1000

# Default volatility (in percentage)
DEFAULT_VOLATILITY = 3.0

# WebSocket reconnection settings
WS_RECONNECT_DELAY = 5  # seconds
WS_MAX_RECONNECT_ATTEMPTS = 5

# UI update interval (in milliseconds)
UI_UPDATE_INTERVAL = 1000

# Performance monitoring settings
PERFORMANCE_MONITORING = {
    "enabled": True,
    "log_interval": 100,  # Log every 100 updates
    "metrics_window": 1000  # Keep last 1000 metrics
}

# UI settings
UI_REFRESH_RATE_MS = 500  # Refresh rate for UI updates in milliseconds
MAX_ORDERBOOK_ROWS = 20   # Maximum number of rows to display in orderbook

# Market impact model settings
MARKET_IMPACT_SETTINGS = {
    "default_volatility": 0.03,  # 3% daily volatility
    "min_market_depth": 100,     # Minimum market depth in USD
    "max_slippage": 0.05,        # Maximum allowed slippage (5%)
    "impact_threshold": 0.02,    # Market impact threshold (2%)
}

# Performance settings
PERFORMANCE_SETTINGS = {
    "max_processing_time_ms": 100,  # Maximum allowed processing time
    "cache_size": 1000,             # Size of prediction cache
    "batch_size": 100,              # Number of orders to process in batch
    "retry_attempts": 3,            # Number of retry attempts for failed operations
}

# Risk management settings
RISK_SETTINGS = {
    "max_position_size": 100000,    # Maximum position size in USD
    "max_daily_trades": 100,        # Maximum number of trades per day
    "max_drawdown": 0.05,           # Maximum allowed drawdown (5%)
    "stop_loss": 0.02,              # Default stop loss (2%)
    "take_profit": 0.04,            # Default take profit (4%)
}

UI_SETTINGS = {
    "refresh_rate": 1000  # milliseconds
}