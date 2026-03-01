"""
Broker Setup and Configuration Guide
ÉTAPE 16: Complete setup instructions for broker API integration
"""

# ============================================================================
# ÉTAPE 16: BROKER API INTEGRATION SETUP GUIDE
# ============================================================================

BROKER_SETUP_INSTRUCTIONS = """
╔════════════════════════════════════════════════════════════════════════════╗
║              BROKER API INTEGRATION - COMPLETE SETUP GUIDE                ║
║                    ÉTAPE 16: Interactive Brokers Setup                     ║
╚════════════════════════════════════════════════════════════════════════════╝

=== OVERVIEW ===

This guide covers setup for Interactive Brokers (IB) API integration. 
Interactive Brokers is recommended for algo trading because of:
  ✓ Most reliable API
  ✓ Best commission structure (~$1/trade)
  ✓ Excellent execution
  ✓ Paper trading environment
  ✓ Full market data access

=== PREREQUISITES ===

1. Required Software Versions:
   - Python 3.8+
   - Interactive Brokers Account (live or paper)
   - Trader Workstation (TWS) or IB Gateway
   - pip packages: ibapi, numpy, pandas

2. System Requirements:
   - Windows/Mac/Linux
   - Network connection
   - Minimum 256MB RAM
   - Port 7497 (live) or 7498 (paper) available

=== STEP-BY-STEP SETUP ===

────────────────────────────────────────────────────────────────────────────
STEP 1: DOWNLOAD AND INSTALL TRADER WORKSTATION (TWS)
────────────────────────────────────────────────────────────────────────────

1. Go to: https://www.interactivebrokers.com/en/trading/platforms/tws.php
2. Select your operating system
3. Download TWS installer
4. Run installer and follow prompts
5. Create IB account (if not existing)

Directory typically created:
  Windows: C:\\Jts\\
  Mac: ~/Jts/
  Linux: ~/Jts/

────────────────────────────────────────────────────────────────────────────
STEP 2: CONFIGURE TWS FOR API ACCESS
────────────────────────────────────────────────────────────────────────────

1. Launch Trader Workstation
2. Navigate to: File → Global Configuration
3. Find "API" section in left menu
4. Configure settings:

   ┌─ API CONFIGURATION ──────────────────────────────┐
   │ ☑ Enable ActiveX and Socket Clients              │
   │                                                   │
   │ Socket Port (on logon):                           │
   │   ◉ Paper Trading Account → 7498                │
   │   ◉ Live Trading Account → 7497                 │
   │                                                   │
   │ ☑ Read-only API (recommended for testing)       │
   │ ☑ Master API Client ID: 1                       │
   │                                                   │
   │ Read-Only API Settings:                          │
   │   ☑ Block Non-API Orders from Account: OFF      │
   │   ☑ Trust Client Timestamp: ON                  │
   └────────────────────────────────────────────────────┘

5. Click "Apply" and "OK"
6. Restart TWS for settings to take effect

────────────────────────────────────────────────────────────────────────────
STEP 3: INSTALL PYTHON IBAPI LIBRARY
────────────────────────────────────────────────────────────────────────────

Option A: Install from PyPI (Recommended)
$ pip install ibapi

Option B: Build from source (if needed)
1. Download from GitHub: https://github.com/InteractiveBrokers/tws-api
2. Navigate to source/pythonclient directory
3. Run: python setup.py install

Verify installation:
$ python -c "from ibapi.client import EClient; print('ibapi installed successfully')"

────────────────────────────────────────────────────────────────────────────
STEP 4: VERIFY API CONNECTION
────────────────────────────────────────────────────────────────────────────

1. Start TWS with your account (paper or live)
2. Run test script:

   $ python tests/test_broker_integration.py

Expected output:
   Connection: ✓ PASS
   Account Info: ✓ PASS
   Price Fetch: ✓ PASS
   ...

════════════════════════════════════════════════════════════════════════════

=== PAPER TRADING SETUP (RECOMMENDED FOR TESTING) ===

Paper trading allows you to test strategies without risking real money.

1. Create/Access Subaccount:
   - Login to Account Management portal
   - Select Account → Paper Trading
   - Select a paper account (e.g., DU999999L)

2. Note your account ID (format: DUxxxxxx or similar)

3. In TWS:
   - File → Switch Account
   - Select your paper trading account
   - Configure API as described above for socket port 7498

4. In Python code:
   from src.trading.interactive_brokers import InteractiveBrokersConnector
   
   broker = InteractiveBrokersConnector(
       account_id="DU999999L",
       port=7498,  # Paper trading port
       client_id=1
   )
   broker.connect()

════════════════════════════════════════════════════════════════════════════

=== LIVE TRADING SETUP (AFTER PAPER TRADING VALIDATION) ===

⚠️  DO NOT proceed to live trading until:
   [✓] Paper trading validated for 30+ days
   [✓] Win rate > 45%
   [✓] Return > -5%
   [✓] All risk management rules enforced
   [✓] Manual intervention procedures documented

Live trading configuration:

1. Ensure IB account has sufficient funds
   - Minimum: $25,000 (Pattern Day Trading rule in US)
   - Recommended: $100,000+

2. In TWS:
   - Ensure you're logged into LIVE account
   - Socket port: 7497 (NOT 7498)
   - File → Global Configuration → API
   - Socket port: 7497

3. In Python code:
   broker = InteractiveBrokersConnector(
       account_id="YOUR_LIVE_ACCOUNT_ID",
       port=7497,  # Live trading port
       client_id=1
   )

4. Start with SMALL position sizes:
   - Reduce position allocation by 50% initially
   - Scale up after 5 profitable days

════════════════════════════════════════════════════════════════════════════

=== COMMON ISSUES & SOLUTIONS ===

─── Issue: "Connection refused" when connecting ─────────────────────────────

Solution:
1. Verify TWS is running: windows → bottom right tray
2. Check port configuration matches (7497 vs 7498)
3. Check firewall allows local port
4. Restart TWS
5. Check: File → Global Configuration → API → Port setting

─── Issue: "Unable to import ibapi" ──────────────────────────────────────────

Solution:
1. Verify installation: pip list | grep ibapi
2. Try reinstall: pip install --upgrade ibapi
3. Check Python version: python --version (need 3.8+)
4. For Visual Studio: Check interpreter selection

─── Issue: "Error code: 2110" (No market data) ─────────────────────────────

Solution:
1. Your IB account may not have market data subscription
2. Account may not be enabled for API data
3. Try simple position/account requests instead of price data
4. Contact IB support for data subscriptions

─── Issue: "Invalid Account" - Account ID incorrect ────────────────────────

Solution:
1. Get correct account ID from: File → Account → Account ID
2. Format is typically: DUxxxxxx or xxxxxx
3. Make sure you're in correct account in TWS before connecting

─── Issue: Orders not executing ─────────────────────────────────────────────

Solution:
1. Check account has sufficient buying power
2. Verify order size doesn't exceed limits
3. Check market is open (9:30 AM - 4:00 PM ET, Mon-Fri)
4. In paper trading: some symbols may be unavailable
5. Check order status: use get_order_status()

════════════════════════════════════════════════════════════════════════════

=== NEXT STEPS AFTER SETUP ===

1. Run integration tests:
   $ python tests/test_broker_integration.py

2. Test with paper trading:
   $ python src/analysis/paper_trading_etape15.py

3. Implement broker integration in main system:
   - Import InteractiveBrokersConnector
   - Replace MockBroker with real broker instance
   - Test all functions

4. Monitor logs for errors:
   - logs/api_errors.log
   - logs/order_execution.log

════════════════════════════════════════════════════════════════════════════

=== USEFUL IBAPI RESOURCES ===

Official Documentation:
  https://interactivebrokers.github.io/tws-api/

Community Resources:
  https://groups.io/g/ibapi
  https://github.com/InteractiveBrokers/tws-api

Error Code Reference:
  https://interactivebrokers.com/en/software/tws/usersguidebook/referencebook/error_codes.htm

Contact Support:
  Email: apihelp@interactivebrokers.com
  Phone: Available on IB website

════════════════════════════════════════════════════════════════════════════

=== ARCHITECTURE OVERVIEW ===

Your system supports multiple broker backends:

┌──────────────────────────────────────────────────────────┐
│                  Trading System                          │
│                  paper_trading_etape15.py               │
└──────────────────┬───────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
   BrokerInterface      BrokerInterface
   (Abstract)           (Abstract)
        │                     │
   ┌────┴──────┐         ┌────┴──────┐
   │            │         │            │
   ▼            ▼         ▼            ▼
MockBroker  (for testing/dev)
   InteractiveBrokersConnector (live/paper trading)
   (Future: TD Ameritrade, Alpaca, etc.)

This architecture allows:
  ✓ Easy switching between brokers
  ✓ Testing without real API
  ✓ Gradual migration to live
  ✓ Multiple broker support

════════════════════════════════════════════════════════════════════════════

=== SECURITY CONSIDERATIONS ===

⚠️  IMPORTANT: Protect your credentials!

1. Never commit account credentials to git
2. Use environment variables for sensitive data:
   export IB_ACCOUNT_ID="DU999999L"
   export IB_PORT="7498"

3. Restrict file permissions:
   chmod 600 broker_config.py

4. Don't share logs that contain account info
5. Use read-only API key when possible
6. Monitor account activity regularly
7. Set up two-factor authentication on IB account

════════════════════════════════════════════════════════════════════════════
"""


# Usage example code
BROKER_USAGE_EXAMPLE = """
# ============================================================================
# USAGE EXAMPLE: Using Broker API
# ============================================================================

from src.trading.interactive_brokers import InteractiveBrokersConnector
from src.trading.broker_interface import OrderData, OrderType, OrderSide
import logging

logging.basicConfig(level=logging.INFO)

# Initialize broker for paper trading
broker = InteractiveBrokersConnector(
    account_id="DU999999L",  # Your paper trading account ID
    port=7498,               # Paper trading port
    client_id=1
)

# Connect to TWS
if not broker.connect():
    print("Failed to connect")
    exit(1)

# Get account info
account = broker.get_account_info()
print(f"Account Balance: ${account.total_value:.2f}")
print(f"Cash Available: ${account.cash:.2f}")
print(f"Buying Power: ${account.buying_power:.2f}")

# Get current prices
prices = broker.get_prices(['AAPL', 'GOOGL', 'MSFT', 'TSLA'])
for symbol, price in prices.items():
    print(f"{symbol}: ${price:.2f}")

# Place a market order to buy
buy_order = OrderData(
    order_id="",
    symbol="GOOGL",
    side=OrderSide.BUY,
    quantity=10,
    order_type=OrderType.MARKET
)

order_id = broker.place_order(buy_order)
print(f"Buy order placed: {order_id}")

# Check order status
import time
time.sleep(2)
status, filled = broker.get_order_status(order_id)
print(f"Order {order_id}: {status.value} - Filled: {filled}")

# Get positions
positions = broker.get_positions()
for pos in positions:
    print(f"{pos.symbol}: {pos.quantity} shares @ ${pos.avg_cost:.2f}")

# Close position
close_order_id = broker.close_position("GOOGL", 10)
print(f"Close order: {close_order_id}")

# Disconnect
broker.disconnect()
"""


if __name__ == "__main__":
    print(BROKER_SETUP_INSTRUCTIONS)
    print("\n" + "="*80 + "\n")
    print("USAGE EXAMPLE:")
    print("="*80)
    print(BROKER_USAGE_EXAMPLE)
