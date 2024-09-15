import sqlite3
import requests
import random

# Connect to SQLite
conn = sqlite3.connect('crypto_portfolio.db')
cursor = conn.cursor()

# Enable foreign key support
cursor.execute('PRAGMA foreign_keys = ON')

# Create tables if they don't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS CoinPrices (
    Name TEXT PRIMARY KEY,
    CurrentPrice REAL,
    MarketCap REAL,
    MarketCapRank INTEGER,
    TotalVolume REAL,
    High24h REAL,
    Low24h REAL,
    PriceChange24h REAL,
    PriceChangePercentage24h REAL,
    MarketCapChange24h REAL,
    MarketCapChangePercentage24h REAL,
    PriceChangePercentage1h REAL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Wallet (
    Token TEXT PRIMARY KEY,
    Price REAL NOT NULL,
    Holdings REAL NOT NULL,
    Value REAL GENERATED ALWAYS AS (Holdings * Price) VIRTUAL,
    PercentOfTotal REAL,
    FOREIGN KEY (Token) REFERENCES CoinPrices(Name)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Staking (
    Pool TEXT PRIMARY KEY,
    Token TEXT NOT NULL,
    Price REAL NOT NULL,
    Holdings REAL NOT NULL,
    Value REAL GENERATED ALWAYS AS (Holdings * Price) VIRTUAL,
    PercentOfTotal REAL,
    FOREIGN KEY (Token) REFERENCES CoinPrices(Name)
)
''')

conn.commit()

def fetch_coin_prices():
    url = 'https://api.coingecko.com/api/v3/coins/markets'
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 500,
        'page': 1,
        'sparkline': 'false',
        'price_change_percentage': '1h,24h'
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data: {response.status_code}")
        return None

def fetch_single_coin_price(token):
    url = f'https://api.coingecko.com/api/v3/coins/{(token.lower())}'
    headers = {"accept": "application/json"}
    response = requests.get(url, headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching single coin data: {response.status_code}")
        return None

def update_coin_prices():
    coins = fetch_coin_prices()
    
    if coins:
        for coin in coins:
            cursor.execute('''
            INSERT OR REPLACE INTO CoinPrices (
                Name, CurrentPrice, MarketCap, MarketCapRank, TotalVolume, High24h, Low24h,
                PriceChange24h, PriceChangePercentage24h, MarketCapChange24h, MarketCapChangePercentage24h, PriceChangePercentage1h
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                coin['name'],
                coin['current_price'],
                coin['market_cap'],
                coin['market_cap_rank'],
                coin['total_volume'],
                coin['high_24h'],
                coin['low_24h'],
                coin['price_change_24h'],
                coin['price_change_percentage_24h'],
                coin['market_cap_change_24h'],
                coin['market_cap_change_percentage_24h'],
                coin['price_change_percentage_1h_in_currency']
            ))
        conn.commit()
        print(f"Successfully updated {len(coins)} coin prices")
    else:
        print("Failed to update coin prices")

def insert_or_update_coin(token):
    # Fetch single coin data
    coin_data = fetch_single_coin_price(token)
    
    if coin_data:
        # Extract data
        name = coin_data['name']
        current_price = coin_data['market_data']['current_price']['usd']
        market_cap = coin_data['market_data']['market_cap']['usd']
        market_cap_rank = coin_data['market_cap_rank']
        total_volume = coin_data['market_data']['total_volume']['usd']
        high_24h = coin_data['market_data']['high_24h']['usd']
        low_24h = coin_data['market_data']['low_24h']['usd']
        price_change_24h = coin_data['market_data']['price_change_24h']
        price_change_percentage_24h = coin_data['market_data']['price_change_percentage_24h']
        market_cap_change_24h = coin_data['market_data']['market_cap_change_24h']
        market_cap_change_percentage_24h = coin_data['market_data']['market_cap_change_percentage_24h']
        price_change_percentage_1h = coin_data['market_data']['price_change_percentage_1h_in_currency']['usd']
        
        cursor.execute('''
        INSERT OR REPLACE INTO CoinPrices (
            Name, CurrentPrice, MarketCap, MarketCapRank, TotalVolume, High24h, Low24h,
            PriceChange24h, PriceChangePercentage24h, MarketCapChange24h, MarketCapChangePercentage24h, PriceChangePercentage1h
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name,
            current_price,
            market_cap,
            market_cap_rank,
            total_volume,
            high_24h,
            low_24h,
            price_change_24h,
            price_change_percentage_24h,
            market_cap_change_24h,
            market_cap_change_percentage_24h,
            price_change_percentage_1h
        ))
        conn.commit()
        print(f"Added or updated coin data for {token}")

def clean_and_convert_to_float(value):
    try:
        # Remove any non-numeric characters except decimal point
        cleaned_value = ''.join(char for char in value if char.isdigit() or char == '.')
        # Convert to float
        return float(cleaned_value)
    except ValueError as e:
        print(f"ValueError: Could not convert '{value}' to float. Error: {e}")
        raise

def insert_wallet_data(token, holdings):
    try:
        holdings = holdings.strip()
        # Clean and convert holdings
        holdings = clean_and_convert_to_float(holdings)
        
        cursor.execute('SELECT CurrentPrice FROM CoinPrices WHERE Name = ?', (token.lower(),))
        price = cursor.fetchone()
        
        if price:
            cursor.execute('''
            INSERT OR REPLACE INTO Wallet (Token, Price, Holdings)
            VALUES (?, ?, ?)
            ''', (token, price[0], holdings))
            conn.commit()
            print(f"Inserted {token} into Wallet with {holdings:.8f} holdings at price {price[0]:.8f}")
        else:
            print(f"Token {token} not found in CoinPrices, fetching and updating data...")
            insert_or_update_coin(token)
            # Retry inserting after updating
            cursor.execute('SELECT CurrentPrice FROM CoinPrices WHERE Name = ?', (token.lower(),))
            price = cursor.fetchone()
            cursor.execute('''
            INSERT OR REPLACE INTO Wallet (Token, Price, Holdings)
            VALUES (?, ?, ?)
            ''', (token, price[0], holdings))
            conn.commit()
            print(f"Inserted {token} into Wallet with {holdings:.8f} holdings at price {price[0]:.8f}")
    except Exception as e:
        print(f"An error occurred: {e}")

def insert_staking_data(pool, token, holdings):
    try:
        holdings = holdings.strip()
        # Clean and convert holdings
        holdings = clean_and_convert_to_float(holdings)
        
        cursor.execute('SELECT CurrentPrice FROM CoinPrices WHERE Name = ?', (token,))
        price = cursor.fetchone()
        
        if price:
            cursor.execute('''
            INSERT OR REPLACE INTO Staking (Pool, Token, Price, Holdings)
            VALUES (?, ?, ?, ?)
            ''', (pool, token, price[0], holdings))
            conn.commit()
            print(f"Inserted {pool} with {holdings:.8f} {token} holdings at price {price[0]:.8f}")
        else:
            print(f"Token {token} not found in CoinPrices, fetching and updating data...")
            insert_or_update_coin(token)
            # Retry inserting after updating
            cursor.execute('SELECT CurrentPrice FROM CoinPrices WHERE Name = ?', (token,))
            price = cursor.fetchone()
            cursor.execute('''
            INSERT OR REPLACE INTO Staking (Pool, Token, Price, Holdings)
            VALUES (?, ?, ?, ?)
            ''', (pool, token, price[0], holdings))
            conn.commit()
            print(f"Inserted {pool} with {holdings:.8f} {token} holdings at price {price[0]:.8f}")
    except Exception as e:
        print(f"An error occurred: {e}")

def display_wallet_portfolio():
    print("Wallet Portfolio:")
    cursor.execute('SELECT Token, Price, Holdings, Value FROM Wallet')
    rows = cursor.fetchall()
    print(f"{'Token':<6} {'Price':<15} {'Holdings':<20} {'Value':<20}")
    print('-' * 60)
    for row in rows:
        print(f"{row[0]:<6} {row[1]:<15.8f} {row[2]:<20.8f} {row[3]:<20.8f}")

def display_staking_portfolio():
    print("\nStaking Portfolio:")
    cursor.execute('SELECT Pool, Token, Price, Holdings, Value FROM Staking')
    rows = cursor.fetchall()
    print(f"{'Pool':<10} {'Token':<6} {'Price':<15} {'Holdings':<20} {'Value':<20}")
    print('-' * 60)
    for row in rows:
        print(f"{row[0]:<10} {row[1]:<6} {row[2]:<15.8f} {row[3]:<20.8f} {row[4]:<20.8f}")

def interactive_menu():
    while True:
        print("\n--- Cryptocurrency Portfolio Manager ---")
        print("1. Update Coin Prices")
        print("2. Add Wallet Holdings")
        print("3. Add Staking Position")
        print("4. View Wallet Portfolio")
        print("5. View Staking Portfolio")
        print("6. Exit")
        
        choice = input("Enter your choice: ")
        
        if choice == '1':
            update_coin_prices()
        elif choice == '2':
            token = input("Enter the token (e.g., Bitcoin, Ethereum): ")
            holdings = input("Enter the number of tokens held: ")
            insert_wallet_data(token, holdings)
        elif choice == '3':
            pool = input("Enter the staking pool name: ")
            token = input("Enter the token being staked (e.g., Cardano, Ethereum): ")
            holdings = input(f"Enter the number of {token} tokens staked: ")
            insert_staking_data(pool, token, holdings)
        elif choice == '4':
            display_wallet_portfolio()
        elif choice == '5':
            display_staking_portfolio()
        elif choice == '6':
            print("Exiting the program...")
            break
        else:
            print("Invalid choice! Please try again.")

# Run the interactive menu
interactive_menu()

# Close the connection when done
conn.close()
