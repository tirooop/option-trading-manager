# Option Trading Manager

A comprehensive options trading management system that provides real-time options monitoring, strategy execution, risk management, and performance tracking for options traders.

![Option Trading Manager](https://via.placeholder.com/800x400.png?text=Option+Trading+Manager)

## 🌟 Key Features

### Real-time Options Monitoring
- **Multi-Symbol Tracking**: Monitor multiple options symbols simultaneously
- **Options Chain Analysis**: Real-time options chain data and analysis
- **Greeks Monitoring**: Live Delta, Gamma, Theta, Vega tracking
- **Implied Volatility Tracking**: IV surface analysis and monitoring

### Options Strategy Management
- **Strategy Templates**: Pre-built options strategy templates
- **Custom Strategy Builder**: Create and customize options strategies
- **Strategy Execution**: Automated strategy implementation
- **Position Tracking**: Real-time position monitoring and management

### Risk Management
- **Portfolio Risk Analysis**: Comprehensive options portfolio risk assessment
- **Greeks Risk Monitoring**: Real-time Greeks exposure tracking
- **Position Sizing**: Dynamic position sizing based on risk tolerance
- **Stop Loss Management**: Automated stop loss and profit taking

### Performance Analytics
- **P&L Tracking**: Real-time profit and loss calculation
- **Performance Metrics**: Comprehensive performance analysis
- **Risk-Adjusted Returns**: Sharpe ratio, Sortino ratio calculations
- **Strategy Comparison**: Side-by-side strategy performance comparison

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Options data access (IBKR, CBOE, etc.)
- Basic understanding of options trading
- Risk management knowledge

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/option-trading-manager.git
cd option-trading-manager
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure the system**:
```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your settings
```

## 🧠 Usage Examples

### Monitor Options Chain

```python
from option_trading_manager import OptionsMonitor

# Initialize the monitor
monitor = OptionsMonitor()

# Monitor options chain for a symbol
chain_data = monitor.get_options_chain(
    symbol="AAPL",
    expiration_date="2024-01-19"
)

print(f"Available strikes: {len(chain_data.strikes)}")
print(f"Current IV: {chain_data.current_iv:.2f}")
```

### Track Options Positions

```python
from option_trading_manager import PositionTracker

# Initialize position tracker
tracker = PositionTracker()

# Track current positions
positions = tracker.get_positions()

for position in positions:
    print(f"{position.symbol}: {position.quantity} @ {position.avg_price}")
    print(f"Current P&L: ${position.current_pnl:.2f}")
    print(f"Delta: {position.delta:.3f}, Gamma: {position.gamma:.3f}")
```

### Execute Options Strategy

```python
from option_trading_manager import StrategyExecutor

# Initialize strategy executor
executor = StrategyExecutor()

# Execute a covered call strategy
strategy = executor.execute_strategy(
    strategy_type="covered_call",
    symbol="AAPL",
    strike_price=150,
    expiration_date="2024-01-19",
    quantity=100
)

print(f"Strategy executed: {strategy.status}")
print(f"Trade ID: {strategy.trade_id}")
```

### Risk Analysis

```python
from option_trading_manager import RiskAnalyzer

# Initialize risk analyzer
analyzer = RiskAnalyzer()

# Analyze portfolio risk
risk_analysis = analyzer.analyze_portfolio_risk(
    positions=positions,
    market_scenarios=["bull", "bear", "neutral"]
)

print(f"Portfolio Delta: {risk_analysis.total_delta:.3f}")
print(f"Portfolio Gamma: {risk_analysis.total_gamma:.3f}")
print(f"Portfolio Theta: {risk_analysis.total_theta:.3f}")
print(f"Portfolio Vega: {risk_analysis.total_vega:.3f}")
```

## 📊 Options Strategies

### Income Strategies
- **Covered Call**: Generate income from stock ownership
- **Cash Secured Put**: Collect premium while waiting to buy
- **Iron Condor**: Profit from range-bound markets
- **Calendar Spread**: Benefit from time decay differences

### Directional Strategies
- **Long Call/Put**: Leveraged directional bets
- **Bull/Bear Spread**: Limited risk directional plays
- **Straddle/Strangle**: Volatility plays
- **Butterfly Spread**: Neutral strategies with defined risk

### Volatility Strategies
- **Long Straddle**: Bet on volatility increase
- **Short Straddle**: Bet on volatility decrease
- **Iron Butterfly**: Neutral volatility strategy
- **Vega Neutral**: Volatility-neutral positions

### Risk Management
- **Delta Hedging**: Neutralize directional risk
- **Gamma Scalping**: Profit from volatility
- **Theta Decay Management**: Optimize time decay
- **Vega Hedging**: Manage volatility exposure

## 🔧 Configuration

### Data Source Configuration
```yaml
# config.yaml
data_sources:
  ibkr:
    enabled: true
    host: "127.0.0.1"
    port: 7497
    client_id: 1
    
  cboe:
    enabled: false
    api_key: "your-cboe-api-key"
    
  yahoo:
    enabled: true
    cache_duration: "5m"

monitoring:
  symbols: ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
  update_frequency: "1m"
  alert_thresholds:
    delta: 0.1
    gamma: 0.01
    theta: -100
    vega: 50

risk_management:
  max_position_size: 0.1  # 10% of portfolio
  max_portfolio_delta: 0.5
  max_portfolio_gamma: 0.05
  stop_loss_percentage: 0.2
```

### Strategy Configuration
```python
# Define custom options strategy
class CustomStrategy:
    def __init__(self, name, legs, risk_params):
        self.name = name
        self.legs = legs
        self.risk_params = risk_params
    
    def calculate_payoff(self, underlying_price):
        # Calculate strategy payoff at given price
        pass
    
    def calculate_greeks(self, underlying_price, volatility, time_to_expiry):
        # Calculate strategy Greeks
        pass

# Example iron condor strategy
iron_condor = CustomStrategy(
    name="Iron Condor",
    legs=[
        {"type": "sell_put", "strike": 140, "quantity": 1},
        {"type": "buy_put", "strike": 135, "quantity": 1},
        {"type": "sell_call", "strike": 160, "quantity": 1},
        {"type": "buy_call", "strike": 165, "quantity": 1}
    ],
    risk_params={"max_loss": 500, "max_profit": 300}
)
```

## 📈 Performance Metrics

### Trading Performance
- **Total Return**: Overall strategy performance
- **Annualized Return**: Yearly return rate
- **Sharpe Ratio**: Risk-adjusted return measure
- **Maximum Drawdown**: Peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss

### Options-Specific Metrics
- **Theta Decay**: Daily time decay capture
- **Vega Exposure**: Volatility sensitivity
- **Delta Neutral**: Directional risk management
- **Gamma Scalping**: Volatility profit capture
- **Implied Volatility Edge**: IV mispricing exploitation

### Risk Metrics
- **Value at Risk (VaR)**: Potential loss at confidence level
- **Expected Shortfall**: Average loss beyond VaR
- **Greeks Exposure**: Delta, Gamma, Theta, Vega limits
- **Correlation Risk**: Portfolio correlation analysis
- **Liquidity Risk**: Options liquidity assessment

## 🛠️ Advanced Features

### Real-time Monitoring
```python
# Real-time options monitoring
realtime_monitor = RealtimeMonitor()

# Start monitoring
realtime_monitor.start_monitoring(
    symbols=["AAPL", "MSFT", "GOOGL"],
    callback=alert_callback,
    interval="30s"
)

def alert_callback(alert):
    if alert.type == "greeks_threshold":
        print(f"Greeks alert: {alert.symbol} - {alert.message}")
    elif alert.type == "iv_spike":
        print(f"IV spike: {alert.symbol} - IV: {alert.value:.2f}")
```

### Portfolio Optimization
```python
# Portfolio optimization
optimizer = PortfolioOptimizer()

# Optimize options portfolio
optimized_portfolio = optimizer.optimize_portfolio(
    current_positions=positions,
    target_return=0.15,
    max_risk=0.1,
    constraints={
        "max_delta": 0.3,
        "max_gamma": 0.02,
        "max_theta": -200
    }
)

print(f"Optimized portfolio expected return: {optimized_portfolio.expected_return:.2%}")
```

### Strategy Backtesting
```python
# Strategy backtesting
backtester = OptionsBacktester()

# Backtest options strategy
backtest_results = backtester.backtest_strategy(
    strategy=iron_condor,
    symbol="AAPL",
    start_date="2023-01-01",
    end_date="2023-12-31",
    initial_capital=10000
)

print(f"Backtest return: {backtest_results.total_return:.2%}")
print(f"Sharpe ratio: {backtest_results.sharpe_ratio:.2f}")
```

## 📁 Project Structure

```
option-trading-manager/
├── core/
│   ├── monitor.py              # Options monitoring system
│   ├── tracker.py              # Position tracking
│   ├── executor.py             # Strategy execution
│   └── analyzer.py              # Risk analysis
├── strategies/
│   ├── income_strategies.py    # Income generation strategies
│   ├── directional_strategies.py # Directional strategies
│   ├── volatility_strategies.py # Volatility strategies
│   └── risk_management.py      # Risk management strategies
├── data/
│   ├── options_data.py          # Options data handling
│   ├── market_data.py           # Market data processing
│   └── historical_data.py       # Historical data
├── analytics/
│   ├── performance.py           # Performance analysis
│   ├── risk_metrics.py          # Risk metrics calculation
│   └── optimization.py          # Portfolio optimization
├── utils/
│   ├── greeks_calculator.py     # Greeks calculations
│   ├── payoff_calculator.py     # Payoff calculations
│   └── visualization.py        # Chart and plot utilities
├── examples/
│   ├── basic_monitoring.py      # Basic monitoring examples
│   ├── strategy_execution.py    # Strategy execution examples
│   └── risk_analysis.py         # Risk analysis examples
├── tests/
│   ├── test_monitor.py          # Monitor tests
│   ├── test_strategies.py       # Strategy tests
│   └── test_analytics.py        # Analytics tests
├── config.yaml                  # Configuration file
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

## 🎯 Use Cases

### Individual Options Traders
- Monitor options positions and Greeks
- Execute options strategies
- Manage risk exposure
- Track performance and P&L

### Options Portfolio Managers
- Manage multiple options positions
- Optimize portfolio allocation
- Implement risk management
- Generate performance reports

### Options Research
- Backtest options strategies
- Analyze options market behavior
- Research volatility patterns
- Develop new strategies

## 🤝 Contributing

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes only. Do not risk money you cannot afford to lose. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.

## 📞 Contact

- Email: your.email@example.com
- GitHub: @your_username
- LinkedIn: your_username

## 🙏 Acknowledgments

Thanks to all developers and researchers who contributed to this project.

---

**⭐ If this project helps you, please give us a star!** 