# Cryptocurrency Portfolio Tracker - Detailed Project Structure Overview

## Main Application
- `app.py`: 
  - Entry point of the application
  - Sets up Flask app
  - Registers blueprints (coin_routes, wallet_routes)
  - Defines the main menu route

## Configuration
- `config.py`: 
  - Contains configuration settings including:
    - API keys (Moralis, CoinGecko)
    - Database settings
    - Chains to query
    - Deposit tokens to ignore

## Database
- `crypto_portfolio.db`: SQLite database file storing all application data
  - Tables: CoinPrices, Wallet, Staking, Farming, LeveragedFarming, LendingBorrowing, CoinExposure

## Services
Located in the `services/` directory:

- `database.py`: 
  - Handles database connections
  - Provides methods for query execution

- `wallet_service.py`: 
  - Business logic for wallet-related operations
  - Methods: get_wallet_items, update_token, update_wallet_and_prices, find_coin_by_name

- `coin_price_service.py`: 
  - Manages coin price data and updates
  - Methods: get_all_coins, update_coin_prices, update_coin_names, find_token, insert_or_update_coin

- `moralis_service.py`: 
  - Interfaces with the Moralis API for blockchain data
  - Methods: get_wallet_balances_and_prices

- `coin_gecko_service.py`: 
  - Interfaces with the CoinGecko API for coin data
  - Methods: fetch_coin_prices, fetch_single_coin_price

## Routes
Located in the `routes/` directory:

- `coin_routes.py`: 
  - Handles routes related to coin prices and updates
  - Routes: coin_prices, update_coin_prices, update_coin_name, update_manual_token, add_coin

- `wallet_routes.py`: 
  - Manages routes for wallet operations
  - Routes: wallet, update_token, update_wallet_and_prices

## Models
Located in the `models/` directory:

- `coin.py`: 
  - Defines the Coin data model
  - Attributes: Name, CurrentPrice, MarketCap, MarketCapRank, etc.

- `wallet.py`: 
  - Defines the WalletItem data model
  - Attributes: token, price, holdings, value

## Templates
Located in the `templates/` directory:

- `index.html`: Main menu template
- `wallet.html`: Wallet page template
- `coin_prices.html`: Coin prices page template
- `staking.html`: Staking information template
- `farming.html`: Farming information template
- `leveraged_farming.html`: Leveraged farming information template
- `lending_borrowing.html`: Lending/Borrowing information template

## Static Files
Located in the `static/` directory:
- `style.css`: Main CSS file for styling the application

## Utilities
Located in the `utils/` directory:

- `logging_config.py`: 
  - Centralized logging configuration
  - Defines setup_logger and log_function_call decorator

- `response.py`: 
  - Standardized response handling
  - Defines ResponseHandler class with success and error methods

## Key Functionalities and Their Locations:

1. Wallet Management:
   - Adding/Updating tokens: `wallet_service.py`, `wallet_routes.py`
   - Displaying wallet: `wallet_routes.py`, `wallet.html`
   - Updating from blockchain: `wallet_service.py`, `moralis_service.py`

2. Coin Price Management:
   - Fetching prices: `coin_price_service.py`, `coin_gecko_service.py`
   - Displaying prices: `coin_routes.py`, `coin_prices.html`
   - Updating prices: `coin_price_service.py`, `coin_routes.py`

3. Blockchain Data Updates:
   - Fetching blockchain data: `moralis_service.py`
   - Updating wallet based on blockchain data: `wallet_service.py`

4. Database Operations:
   - All database interactions: `database.py`
   - Used in: `wallet_service.py`, `coin_price_service.py`

5. Logging:
   - Centralized logging setup: `logging_config.py`
   - Used throughout all service and route files

6. Staking, Farming, and Lending:
   - Templates: `staking.html`, `farming.html`, `leveraged_farming.html`, `lending_borrowing.html`
   - (Note: Backend services for these features are not fully implemented in the provided code)

## Flow of Data:
1. User interacts with frontend (HTML templates)
2. Requests handled by route files (coin_routes.py, wallet_routes.py)
3. Route files call appropriate service methods (wallet_service.py, coin_price_service.py)
4. Services interact with the database (via database.py) or external APIs (via coin_gecko_service.py, moralis_service.py) as needed
5. Results are passed back through services to routes to frontend

