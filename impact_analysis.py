import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple
from market_impact_models import AlmgrenChrissParameters

@dataclass
class MarketParameters:
    volatility: float
    volume: float
    avg_trade_size: float = 1.0
    market_depth: float = 1000000.0

class OrderBookImpactAnalyzer:
    def __init__(self, orderbook):
        self.orderbook = orderbook
        self.ac_params = None
        self.market_params = None
        self._initialize_ac_model()

    def update_market_parameters(self, volatility: float, volume: float):
        self.market_params = MarketParameters(
            volatility=volatility,
            volume=volume,
            avg_trade_size=volume / 1000,
            market_depth=self._estimate_market_depth()
        )

    def _estimate_market_depth(self) -> float:
        try:
            asks = self.orderbook.get_asks()
            bids = self.orderbook.get_bids()
            ask_depth = sum(float(price) * float(size) for price, size in asks[:10])
            bid_depth = sum(float(price) * float(size) for price, size in bids[:10])
            return (ask_depth + bid_depth) / 2
        except Exception:
            return 1000000.0

    def _initialize_ac_model(self):
        if not self.ac_params:
            self.ac_params = AlmgrenChrissParameters(
                permanent_impact=0.15,
                temporary_impact=0.2,
                temporary_decay=0.6,
                risk_aversion=1.5,
                volatility=0.03,
                initial_price=0.0
            )

    def estimate_market_impact(self, quantity: float, side: str) -> Dict:
        try:
            if not self.market_params:
                self.update_market_parameters(0.03, 5000)
            base_impact = (quantity / self.market_params.market_depth) * 100
            vol_adjustment = self.market_params.volatility * 2
            impact = base_impact * (1 + vol_adjustment)
            maker_prop = max(0.2, 1 - (quantity / self.market_params.avg_trade_size) * 0.1)
            taker_prop = 1 - maker_prop
            return {
                'impact_percentage': impact,
                'maker_proportion': maker_prop,
                'taker_proportion': taker_prop,
                'estimated_cost': impact * quantity / 100
            }
        except Exception as e:
            print(f"Error in market impact estimation: {str(e)}")
            return {
                'impact_percentage': 0.0,
                'maker_proportion': 0.5,
                'taker_proportion': 0.5,
                'estimated_cost': 0.0
            }

    def optimal_execution_strategy(self, quantity: float, side: str, 
                                 time_horizon: float, num_periods: int) -> Dict:
        try:
            if not self.market_params:
                self.update_market_parameters(0.03, 5000)
            tau = time_horizon / num_periods
            kappa = np.sqrt(self.ac_params.risk_aversion * 
                          self.ac_params.volatility**2 / 
                          self.ac_params.temporary_impact)
            t = np.linspace(0, time_horizon, num_periods + 1)
            x = quantity * np.sinh(kappa * (time_horizon - t)) / np.sinh(kappa * time_horizon)
            v = np.diff(x) / tau
            market_impact = self.ac_params.temporary_impact * np.sum(v**2) * tau
            permanent_impact = (self.ac_params.permanent_impact - 
                              self.ac_params.temporary_impact/2) * quantity**2
            volatility_cost = (self.ac_params.risk_aversion * 
                             self.ac_params.volatility**2 * 
                             np.sum(x[1:]**2) * tau)
            total_cost = market_impact + permanent_impact + volatility_cost
            return {
                'execution_schedule': x.tolist(),
                'trading_rates': v.tolist(),
                'expected_shortfall_bps': (total_cost / (quantity * self.ac_params.initial_price)) * 10000
            }
        except Exception as e:
            print(f"Error in optimal execution strategy: {str(e)}")
            return {
                'execution_schedule': [0.0 for _ in range(num_periods+1)],
                'expected_shortfall_bps': 0.0
            }

    def estimate_slippage(self, quantity: float, side: str) -> float:
        try:
            if not self.market_params:
                self.update_market_parameters(0.03, 5000)
            base_slippage = (quantity / self.market_params.market_depth) * 10000
            vol_adjustment = self.market_params.volatility * 100
            slippage = base_slippage * (1 + vol_adjustment)
            return slippage
        except Exception as e:
            print(f"Error in slippage estimation: {str(e)}")
            return 0.0 