# Cryptocurrency Trading Simulator

A sophisticated cryptocurrency trading simulator that provides a realistic environment for testing trading strategies, analyzing market behavior, and practicing risk management in the crypto market.

## 🌟 Key Features

### Advanced Trading Capabilities
- **Multi-Cryptocurrency Support**: Trade BTC, ETH, SOL, and AVAX with real-time price tracking
- **Comprehensive Order Types**:
  - Market orders for immediate execution
  - Limit orders for price-specific entries
  - Stop-loss orders for risk management
  - Take-profit orders for securing profits
- **Portfolio Management**: Track positions, balance, and performance metrics

### Technical Analysis Tools
- **Multiple Technical Indicators**:
  - Relative Strength Index (RSI)
  - Moving Average Convergence Divergence (MACD)
  - Bollinger Bands
  - Simple and Exponential Moving Averages
- **Customizable Parameters**: Adjust indicator settings for optimal strategy development
- **Signal Generation**: Automated trading signals based on technical analysis

### Risk Management System
- **Position Sizing**: Calculate optimal position sizes based on risk percentage
- **Stop-Loss Management**: Automated stop-loss order placement and tracking
- **Portfolio Diversification**: Tools for maintaining balanced exposure
- **Performance Metrics**:
  - Maximum drawdown tracking
  - Sharpe ratio calculation
  - Win rate analysis
  - Risk-adjusted returns

### User Interface
- **Modern Dashboard**: Clean, intuitive interface built with Streamlit
- **Real-time Charts**: Interactive price charts with technical indicators
- **Portfolio Analytics**: Comprehensive performance visualization
- **Trade History**: Detailed record of all trading activities

## 🛠️ Technical Stack

- **Backend**: Python 3.8+
- **Web Framework**: Streamlit
- **Data Processing**: Pandas, NumPy
- **Technical Analysis**: TA-Lib
- **Data Visualization**: Plotly
- **API Integration**: Binance API for real-time market data

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/crypto-trading-simulator.git
cd crypto-trading-simulator
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run main.py
```

## 💡 Usage

1. Launch the application using the command above
2. Access the web interface at `http://localhost:8501`
3. Configure your trading parameters in the settings panel
4. Start simulating trades with real-time market data

## 🔧 Configuration

The simulator can be configured through `config.py`:
- Trading pairs
- Risk parameters
- Technical indicator settings
- API credentials (for real-time data)

## 📊 Performance Metrics

The simulator tracks various performance metrics:
- Total return
- Sharpe ratio
- Maximum drawdown
- Win rate
- Risk-adjusted returns
- Portfolio diversification

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- Your Name - Initial work

## 🙏 Acknowledgments

- Binance API for market data
- TA-Lib for technical analysis
- Streamlit for the web interface

## Project Structure

```
crypto-trade-simulator/
├── app.py                    # Main application entry point
├── main.py                     # Streamlit application setup
├── config.py                  # Configuration settings and parameters
├── ui.py                      # User interface components and layouts
├── simulator.py               # Core trading simulation logic
├── performance_monitor.py     # Performance tracking and analytics
├── orderbook.py              # Order book management and processing
├── ws_client.py              # WebSocket client for real-time data
├── impact_analysis.py        # Market impact analysis tools
├── market_impact_models.py   # Market impact modeling algorithms
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

### Key Components

- **Main Application**
  - `main.py`: Entry point for the trading simulator
  - `app.py`: Streamlit web application configuration
  - `ui.py`: User interface implementation and components

- **Core Trading Logic**
  - `simulator.py`: Trading simulation engine
  - `orderbook.py`: Order management system
  - `ws_client.py`: Real-time market data integration

- **Analysis & Monitoring**
  - `performance_monitor.py`: Performance tracking and metrics
  - `impact_analysis.py`: Market impact analysis
  - `market_impact_models.py`: Advanced market impact modeling

- **Configuration**
  - `config.py`: System configuration and parameters
  - `requirements.txt`: Project dependencies

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.

## Roadmap

- [ ] Add more technical indicators
- [ ] Implement backtesting functionality
- [ ] Add social trading features
- [ ] Support for more exchanges
- [ ] Mobile application development