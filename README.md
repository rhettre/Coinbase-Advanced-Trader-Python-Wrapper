# Coinbase Advanced Trade API Python Client

This is the unofficial Python client for the Coinbase Advanced Trade API. It allows users to interact with the API to manage their cryptocurrency trading activities on the Coinbase platform.

## Features

- Easy-to-use Python wrapper for the Coinbase Advanced Trade API
- Supports the new Coinbase Cloud authentication method
- Built on top of the official [Coinbase Python SDK](https://github.com/coinbase/coinbase-advanced-py) for improved stability
- Supports all endpoints and methods provided by the official API
- Added support for trading strategies covered on the [YouTube channel](https://rhett.blog/youtube)

## Setup

1. Install the required packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

2. Obtain your API key and secret from the Coinbase Developer Platform. 

Download the api key in Coinbase.  Move `cdp_api_key.json` into project folder. Python code will read keys from this file.  You may rename `cdp_api_key.json` to something like strategy1.json to seperate different keys/logic.
   ```

## Authentication

Here's an example of how to authenticate using the new method:
```
from coinbase_advanced_trader.enhanced_rest_client import EnhancedRESTClient
from include import load_api_credentials

# Load API credentials
api_key, api_secret = load_api_credentials()    # Default case opens cdp_api_key.json
#api_key, api_secret = load_api_credentials( 'foo.json' )    # Optional case opens a file name given, different keys to open different CB portfolios

# use loaded keys
client = EnhancedRESTClient(api_key=api_key, api_secret=api_secret)
```

## Using the Official SDK

The `EnhancedRESTClient` inherits from the Coinbase SDK's `RESTClient`, which means you can use all the functions provided by the official SDK. Here's an example of how to use the `get_product` function:

```python
product_info = client.get_product(product_id="BTC-USDC")

print(product_info)
```

## Using Wrapper Strategies

Here's an example of how to use the strategies package to buy $10 worth of Bitcoin. By making assumptions about limit price in [trading_config.py](coinbase_advanced_trader/trading_config.py) we are able to simplify the syntax for making orders:

```python
# Perform a market buy
client.fiat_market_buy("BTC-USDC", "10")

#Place a $10 buy order for BTC-USD near the current spot price of BTC-USDC
client.fiat_limit_buy("BTC-USDC", "10")

#Place a $10 buy order for BTC-USD at a limit price of $10,000
client.fiat_limit_buy("BTC-USDC", "10", "10000")

#Place a $10 buy order for BTC-USD at a 10% discount from the current spot price of BTC-USDC
client.fiat_limit_buy("BTC-USDC", "10", price_multiplier=".90")

#Place a $10 sell order for BTC-USD at a limit price of $100,000
client.fiat_limit_sell("BTC-USDC", "10", "100000")

#Place a $10 sell order for BTC-USD near the current spot price of BTC-USDC
client.fiat_limit_sell("BTC-USDC", "5")

#Place a $10 sell order for BTC-USD at a 10% premium to the current spot price of BTC-USDC
client.fiat_limit_sell("BTC-USDC", "5", price_multiplier="1.1")
```

### Account Balance Operations

The `EnhancedRESTClient` provides methods to retrieve account balances for cryptocurrencies. These methods are particularly useful for managing and monitoring your cryptocurrency holdings on Coinbase.

#### Listing All Non-Zero Crypto Balances

To get a dictionary of all cryptocurrencies with non-zero balances in your account:

```python
balances = client.list_held_crypto_balances()
print(balances)
```

#### Getting a Specific Crypto Balance

To get the available balance of a specific cryptocurrency in your account (returns 0 if the specified cryptocurrency is not found in the account):

```python
balance = client.get_crypto_balance("BTC")
print(balance)
```

Note: Both methods use a caching mechanism to reduce API calls. The account data is cached for one hour before a fresh fetch is made from Coinbase.

### Usage of Fear and Greed Index

The client uses the [fear-and-greed-crypto](https://github.com/rhettre/fear-and-greed-crypto) package to fetch the current Fear and Greed Index value. This index helps determine market sentiment and automate trading decisions.

```python
# Trade based on Fear and Greed Index
client.trade_based_on_fgi("BTC-USDC", "10")
```

You can customize the trading behavior by updating the Fear and Greed Index schedule:

```python
# Get current FGI schedule
current_schedule = client.get_fgi_schedule()

# Update FGI schedule with custom thresholds and actions
new_schedule = [
    {'threshold': 15, 'factor': 1.2, 'action': 'buy'},   # Buy more in extreme fear
    {'threshold': 37, 'factor': 1.0, 'action': 'buy'},   # Buy normal amount in fear
    {'threshold': 35, 'factor': 0.8, 'action': 'sell'},  # Sell some in greed
    {'threshold': 45, 'factor': 0.6, 'action': 'sell'}   # Sell more in extreme greed
]
client.update_fgi_schedule(new_schedule)
```

The schedule determines:
- When to buy or sell based on the Fear and Greed Index value
- How much to adjust the trade amount (using the factor)
- What action to take at each threshold

For example, with the above schedule:
- If FGI is 10 (Extreme Fear), it will buy with 1.2x the specified amount
- If FGI is 50 (Neutral), no trade will be executed
- If FGI is 80 (Extreme Greed), it will sell with 0.6x the specified amount

## AlphaSquared Integration

This client now includes integration with AlphaSquared, allowing you to execute trading strategies based on AlphaSquared's risk analysis.

### Setup

1. Obtain your AlphaSquared API key from [AlphaSquared](https://alphasquared.io/).

2. Initialize the AlphaSquared client along with the Coinbase client:

```python
from coinbase_advanced_trader import EnhancedRESTClient, AlphaSquaredTrader
from alphasquared import AlphaSquared

# Initialize Coinbase client
coinbase_api_key = "YOUR_COINBASE_API_KEY"

coinbase_api_secret = "YOUR_COINBASE_API_SECRET"

coinbase_client = EnhancedRESTClient(api_key=coinbase_api_key, api_secret=coinbase_api_secret)

# Initialize AlphaSquared client
alphasquared_api_key = "YOUR_ALPHASQUARED_API_KEY"

alphasquared_client = AlphaSquared(alphasquared_api_key, cache_ttl=60)

# Create AlphaSquaredTrader
trader = AlphaSquaredTrader(coinbase_client, alphasquared_client)
```

### Executing AlphaSquared Strategies

To execute a trading strategy based on AlphaSquared's risk analysis:

```python
# Set trading parameters
product_id = "BTC-USDC"

# Your custom strategy name from AlphaSquared
strategy_name = "My Custom Strategy"

# Execute strategy
trader.execute_strategy(product_id, strategy_name)
```

This will:
1. Fetch the current risk level for the specified asset from AlphaSquared.
2. Determine the appropriate action (buy/sell) and value based on the custom strategy defined in AlphaSquared and the current risk.
3. Execute the appropriate trade on Coinbase if the conditions are met.

> **Note:** Make sure to handle exceptions and implement proper logging in your production code. This integration only works with custom strategies; it does not work with the default strategies provided by AlphaSquared.

### Customizing Strategies

You can create custom strategies by modifying the `execute_strategy` method in the `AlphaSquaredTrader` class. This allows you to define specific trading logic based on the risk levels provided by AlphaSquared.

## AWS Lambda Compatibility

When using this package in AWS Lambda, ensure your Lambda function is configured to use Python 3.12. The cryptography binaries in the Lambda layer are compiled for Python 3.12, and using a different Python runtime version will result in compatibility issues.

To configure your Lambda function:
1. Set the runtime to Python 3.12
2. Use the provided Lambda layer from the latest release
3. If building custom layers, ensure they are built using the same Python version as the Lambda runtime.

## Legacy Support

The legacy authentication method is still supported but moved to a separate module. It will not receive the latest updates from the Coinbase SDK. To use the legacy method:

```python
from coinbase_advanced_trader.legacy.legacy_config import set_api_credentials
from coinbase_advanced_trader.legacy.strategies.limit_order_strategies import fiat_limit_buy

legacy_key = "your_legacy_key"
legacy_secret = "your_legacy_secret"

set_api_credentials(legacy_key, legacy_secret)

# Use legacy functions
limit_buy_order = fiat_limit_buy("BTC-USDC", 10)
```

## Documentation

For more information about the Coinbase Advanced Trader API, consult the [official API documentation](https://docs.cdp.coinbase.com/advanced-trade/docs/welcome).

## License

This project is licensed under the MIT License. See the LICENSE file for more information.

## Author

Rhett Reisman

Email: rhett@rhett.blog

GitHub: https://github.com/rhettre/coinbase-advancedtrade-python

## Disclaimer

This project is not affiliated with, maintained, or endorsed by Coinbase. Use this software at your own risk. Trading cryptocurrencies carries a risk of financial loss. The developers of this software are not responsible for any financial losses or damages incurred while using this software. Nothing in this software should be seen as an inducement to trade with a particular strategy or as financial advice.
