import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import GradientBoostingRegressor
from dataclasses import dataclass
from typing import List, Tuple, Optional
import pandas as pd

@dataclass
class AlmgrenChrissParameters:
    """Parameters for the Almgren-Chriss model."""
    permanent_impact: float  # Permanent price impact parameter
    temporary_impact: float  # Temporary price impact parameter
    temporary_decay: float   # Decay rate of temporary impact
    risk_aversion: float    # Risk aversion parameter
    volatility: float       # Market volatility
    initial_price: float    # Initial market price

class AlmgrenChrissModel:
    """Implementation of the Almgren-Chriss model for optimal execution."""
    
    def __init__(self, params: AlmgrenChrissParameters):
        self.params = params
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the model parameters."""
        self.eta = self.params.permanent_impact
        self.gamma = self.params.temporary_impact
        self.rho = self.params.temporary_decay
        self.lambda_ = self.params.risk_aversion
        self.sigma = self.params.volatility
        self.S0 = self.params.initial_price
    
    def calculate_optimal_schedule(self, quantity: float, time_horizon: float, num_periods: int):
        """Calculate optimal execution schedule using Almgren-Chriss model."""
        # Calculate time step
        tau = time_horizon / num_periods
        
        # Calculate model parameters
        kappa = np.sqrt(self.lambda_ * self.sigma**2 / self.gamma)
        
        # Calculate optimal schedule
        t = np.linspace(0, time_horizon, num_periods + 1)
        x = quantity * np.sinh(kappa * (time_horizon - t)) / np.sinh(kappa * time_horizon)
        
        # Calculate trading rates
        v = np.diff(x) / tau
        
        return x, v

    def optimal_execution_strategy(self, total_quantity: float, 
                                 time_horizon: float, 
                                 num_periods: int) -> dict:
        """
        Calculate the optimal execution strategy using the Almgren-Chriss model.
        
        Args:
            total_quantity: Total quantity to execute
            time_horizon: Time horizon in days
            num_periods: Number of periods to split the execution
            
        Returns:
            Dictionary containing execution schedule and expected costs
        """
        # Time step
        tau = time_horizon / num_periods
        
        # Calculate model parameters
        kappa = np.sqrt(self.lambda_ * self.sigma**2 / self.gamma)
        eta_tilde = self.eta - self.gamma/2
        
        # Calculate optimal trading schedule
        t = np.linspace(0, time_horizon, num_periods + 1)
        x = total_quantity * np.sinh(kappa * (time_horizon - t)) / np.sinh(kappa * time_horizon)
        
        # Calculate trading rates
        v = np.diff(x) / tau
        
        # Calculate expected costs
        market_impact = self.gamma * np.sum(v**2) * tau
        permanent_impact = eta_tilde * total_quantity**2
        volatility_cost = self.lambda_ * self.sigma**2 * np.sum(x[1:]**2) * tau
        
        total_cost = market_impact + permanent_impact + volatility_cost
        
        return {
            'execution_schedule': x.tolist(),
            'trading_rates': v.tolist(),
            'market_impact': market_impact,
            'permanent_impact': permanent_impact,
            'volatility_cost': volatility_cost,
            'total_cost': total_cost,
            'expected_shortfall_bps': (total_cost / (total_quantity * self.S0)) * 10000
        }

class SlippageModel:
    """Regression models for slippage estimation."""
    
    def __init__(self, base_slippage: float = 0.0001):
        self.base_slippage = base_slippage
    
    def estimate_slippage(self, quantity: float, market_depth: float) -> float:
        """Estimate slippage based on order size and market depth."""
        return self.base_slippage * (quantity / market_depth)
        
    def predict(self, order_book: dict) -> Tuple[float, float]:
        """Predict slippage using both linear and quantile regression models.
        
        Args:
            order_book: Dictionary containing 'asks' and 'bids' lists
            
        Returns:
            Tuple of (linear_prediction, quantile_prediction) in basis points
        """
        try:
            if not order_book['asks'] or not order_book['bids']:
                return 0.0, 0.0
                
            # Calculate market depth
            ask_depth = sum(float(price) * float(size) for price, size in order_book['asks'][:10])
            bid_depth = sum(float(price) * float(size) for price, size in order_book['bids'][:10])
            market_depth = (ask_depth + bid_depth) / 2
            
            # Calculate mid price
            best_ask = float(order_book['asks'][0][0])
            best_bid = float(order_book['bids'][0][0])
            mid_price = (best_ask + best_bid) / 2
            
            # Linear prediction (simplified)
            linear_pred = self.base_slippage * (100 / market_depth) * 10000  # Convert to bps
            
            # Quantile prediction (simplified)
            spread = (best_ask - best_bid) / mid_price
            quantile_pred = (self.base_slippage + spread) * 10000  # Convert to bps
            
            return linear_pred, quantile_pred
            
        except Exception as e:
            print(f"Error in slippage prediction: {str(e)}")
            return 0.0, 0.0

class MakerTakerModel:
    """Logistic regression model for maker/taker proportion prediction."""
    
    def __init__(self, maker_fee: float = 0.001, taker_fee: float = 0.002):
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee

    def estimate_fees(self, quantity: float, is_maker: bool) -> float:
        """Estimate trading fees based on order type."""
        return quantity * (self.maker_fee if is_maker else self.taker_fee)
        
    def predict(self, order_book: dict) -> float:
        """Predict maker/taker proportion based on order book state.
        
        Args:
            order_book: Dictionary containing 'asks' and 'bids' lists
            
        Returns:
            Predicted maker proportion (0.0 to 1.0)
        """
        try:
            if not order_book['asks'] or not order_book['bids']:
                return 0.5
                
            # Calculate spread
            best_ask = float(order_book['asks'][0][0])
            best_bid = float(order_book['bids'][0][0])
            mid_price = (best_ask + best_bid) / 2
            spread = (best_ask - best_bid) / mid_price
            
            # Calculate depth imbalance
            ask_depth = sum(float(price) * float(size) for price, size in order_book['asks'][:10])
            bid_depth = sum(float(price) * float(size) for price, size in order_book['bids'][:10])
            depth_ratio = min(ask_depth, bid_depth) / max(ask_depth, bid_depth)
            
            # Predict maker proportion based on spread and depth
            # Higher spread and balanced depth favor maker orders
            maker_prop = 0.5 + (spread * 10) * depth_ratio
            
            # Clamp between 0.2 and 0.8
            return max(0.2, min(0.8, maker_prop))
            
        except Exception as e:
            print(f"Error in maker/taker prediction: {str(e)}")
            return 0.5 