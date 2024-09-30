import requests
import sqlite3
from flask import Flask, render_template, redirect, url_for, g, request

app = Flask(__name__)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('crypto_portfolio.db')
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def fetch_coin_prices():
    url = 'https://api.coingecko.com/api/v3/coins/markets'
    all_coins = []
    total_top_coins = 500
    coins_per_page = 100

    for page in range(1, (total_top_coins // coins_per_page) + 1):
        params = {
            'vs_currency': 'usd',
            'order' : 'market_cap_desc',
            'per_page' : coins_per_page,
            'page' : page,
            'sparkline' : 'false',
            'price_change_percentage' : '1h,24h',
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            coins = response.json()
            all_coins.extend(coins)
        else:
            return "Error fetching data from CoinGecko."
    return all_coins


def insert_wallet_data(token, holdings):
    db = get_db()
    cursor = db.cursor()

    

    print(f"Inserting {token} with holdings {holdings}")

    cursor.execute('SELECT Name, CurrentPrice FROM CoinPrices WHERE Name = ?', (token,))
    coin_data = cursor.fetchone()

    
    if coin_data:
        name, price = coin_data
        print(f"Token found: {price}, Price: {price}") # Debugging Line
        cursor.execute('''INSERT OR REPLACE INTO Wallet (Token, Price, Holdings)
                        VALUES (?, ?, ?)''', (name, price, holdings))
        print(f'Inserted {token}, at {price} with the amount {holdings}')
        db.commit()
    else:
        print(f"Token {token} not found in CoinPrices") # Debugging Line
        return f"Token {token} not found in CoinPrices"

# Insert staking data
def insert_staking_data(pool, token, holdings):
    db = get_db()
    cursor = db.cursor()

    cursor.execute('SELECT CurrentPrice FROM CoinPrices WHERE Name = ?', (token.lower()))
    price = cursor.fetchone()
    if price:
        cursor.execute('''INSERT OR REPLACE INTO Staking (Pool, Token, Price, Holdings)
                          VALUES (?, ?, ?, ?)''', (pool, token, price[0], holdings))
        db.commit()
    else:
        return f"Token {token} not found in CoinPrices."

def calculate_total_value(table_name):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(f'SELECT SUM(Value) FROM {table_name}')
    total_value = cursor.fetchone()[0]
    if total_value:
        return total_value
    else:
        return 0
    
def fetch_single_coin_price(token):
    url = f'https://api.coingecko.com/api/v3/coins/{token}'
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None

def insert_or_update_coin(token):
    coin_data = fetch_single_coin_price(token)

    if coin_data:
        db = get_db()
        cursor = db.cursor()

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
        price_change_percentage_1h_in_currency = coin_data['market_data']['price_change_percentage_1h_in_currency']['usd']

        cursor.execute('''INSERT OR REPLACE INTO CoinPrices (
            Name, CurrentPrice, MarketCap, MarketCapRank, TotalVolume, High24h, Low24h,
            PriceChange24h, PriceChangePercentage24h, MarketCapChange24h, MarketCapChangePercentage24h, PriceChangePercentage1h
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
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
            price_change_percentage_1h_in_currency
        ))
        db.commit()
        return "Coin updated successfully"
    return "Coin not found"
        
        
############################
#         Routes           #
############################

# Main Menu Route
@app.route('/')
def main_menu():
    return render_template('index.html')

# Coin Prices Route
@app.route('/coin_prices')
def coin_prices():
    db = get_db()
    cursor = db.cursor()

    # Default Sorting set to MarketCap Descending
    sort_by = request.args.get('sort_by', 'MarketCap') 
    order = request.args.get('order', 'desc')

    # Default to MarketCap if args not valid
    if sort_by not in ['Name', 'CurrentPrice', 'MarketCap', 'High24h', 'Low24h', 'PriceChange24h', 'PriceChangePercentage24h']:
        sort_by = 'MarketCap'
    
    # Query Data based on args
    if order == 'asc':
        query = f'SELECT * FROM CoinPrices ORDER BY {sort_by} ASC'
    else:
        query = f'SELECT * FROM CoinPrices ORDER BY {sort_by} DESC'
    
    
    # Set variable for next sort
    if order == 'asc':
        next_sort_order = 'desc'
    else:
        next_sort_order = 'asc'

    cursor.execute(query)
    coins = cursor.fetchall()

    return render_template('coin_prices.html', coins=coins, sort_by=sort_by, order=next_sort_order)

@app.route('/update_coin_prices', methods=['GET'])
def update_coin_prices():
    coins = fetch_coin_prices()
    if coins:
        db = get_db()
        cursor = db.cursor()

        # Update prices for top 500 coins
        for coin in coins:
            cursor.execute('''INSERT OR REPLACE INTO CoinPrices (
                Name, CurrentPrice, MarketCap, MarketCapRank, TotalVolume, High24h, Low24h,
                PriceChange24h, PriceChangePercentage24h, MarketCapChange24h, MarketCapChangePercentage24h, PriceChangePercentage1h
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
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
        
        # Fetch all coins
        cursor.execute('SELECT Name FROM CoinPrices')
        all_db_coins = {row[0] for row in cursor.fetchall()}

        # Find coins that are in database but not in top 500
        top_500_coins = {coin['name'] for coin in coins}
        missing_coins = all_db_coins - top_500_coins

        # Fetch prices for the missing coins
        for coin_name in missing_coins:
            coin_data = fetch_single_coin_price(coin_name.lower())
            if coin_data:
                cursor.execute('''INSERT OR REPLACE INTO CoinPrices (
                    Name, CurrentPrice, MarketCap, MarketCapRank, TotalVolume, High24h, Low24h,
                    PriceChange24h, PriceChangePercentage24h, MarketCapChange24h, MarketCapChangePercentage24h, PriceChangePercentage1h
                ) Values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                    coin_data['name'],
                    coin_data['market_data']['current_price']['usd'],
                    coin_data['market_data']['market_cap']['usd'],
                    coin_data['market_cap_rank'],
                    coin_data['market_data']['total_volume']['usd'],
                    coin_data['market_data']['high_24h']['usd'],
                    coin_data['market_data']['low_24h']['usd'],
                    coin_data['market_data']['price_change_24h'],
                    coin_data['market_data']['price_change_percentage_24h'],
                    coin_data['market_data']['market_cap_change_24h'],
                    coin_data['market_data']['market_cap_change_percentage_24h'],
                    coin_data['market_data']['price_change_percentage_1h_in_currency']['usd']
                ))
            else:
                print(f"Token {coin_name} not found in API, maunal update needed")
        db.commit()
        return redirect(url_for('coin_prices')) # Redirect back to coin price page
    return "Failed to update coin prices."

@app.route('/update_manual_token', methods=['POST'])
def update_manual_token():
    token_name = request.form['token_name']
    token_price = request.form['token_price']

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute('SELECT * FROM CoinPrices WHERE Name = ?', (token_name,))
        existing_token = cursor.fetchone()

        if existing_token:
            # Update existing
            cursor.execute('''
                UPDATE CoinPrices
                SET CurrentPrice = ?,
                    PriceChange24h = ?,
                    PriceChangePercentage24h = ?
                WHERE Name = ?
            ''', (token_price, 0, 0, token_name))
        else:
            # Insert new token
            cursor.execute('''
                INSERT INTO CoinPrices (Name, CurrentPrice, MarketCap, MarketCapRank, TotalVolume,
                                        High24h, Low24h, PriceChange24h, PriceChangePercentage24h,
                                        MarketCapChange24h, MarketCapChangePercentage24h, PriceChangePercentage1h)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (token_name, token_price, 0, 0, 0, token_price, token_price, 0, 0, 0, 0, 0))
        db.commit()
        return redirect(url_for('coin_prices'))
    except Exception as e:
        print(f"Error updating manual token: {e}")
        db.rollback()
        return "Error updating token", 500

# Add Coin Price Route
@app.route('/add_coin', methods=['POST'])
def add_coin():
    coin_name = request.form['coin_name']
    print(f"Adding coin: {coin_name}")

    message = insert_or_update_coin(coin_name)
    print(message)
    return redirect(url_for('coin_prices'))

# Wallet Route
@app.route('/wallet')
def wallet():
    db = get_db()
    cursor = db.cursor()

    sort_by = request.args.get('sort_by', 'Value')
    order = request.args.get('order', 'desc')

    if order == 'desc':
        query = f'SELECT * FROM Wallet ORDER BY {sort_by} DESC'
    else:
        query = f'SELECT * FROM Wallet ORDER BY {sort_by} ASC'
    cursor.execute(query)

    if order == 'desc':
        next_sort_order = 'asc'
    else:
        next_sort_order = 'desc'

    wallet_data = cursor.fetchall()

    # Calculate total value for wallet
    total_wallet_value = calculate_total_value('Wallet')

    # Calculate total value for Staking
    total_staking_value = calculate_total_value('Staking')

    total_value = total_wallet_value + total_staking_value

    wallet_with_percent = []

    for row in wallet_data:
        token, price, holdings, value = row[:4]

        percent_of_wallet = (value / total_wallet_value * 100)
        percent_of_total = (value / total_value * 100)

        wallet_with_percent.append((token, price, holdings, value, percent_of_wallet, percent_of_total))

    return render_template('wallet.html', wallet_data=wallet_with_percent, total_value=total_value, sort_by=sort_by, order=next_sort_order)

@app.route('/add_wallet', methods=['POST'])
def add_wallet():
    token = request.form['token']
    holdings = request.form['holdings']
    print(f"Token: {token}, Holdings: {holdings}") # Debug Line
    insert_wallet_data(token, holdings)
    return redirect(url_for('wallet'))


# Staking Route
@app.route('/staking')
def staking():
    db = get_db()
    cursor = db.cursor()

    sort_by = request.args.get('sort_by', 'Value')
    order = request.args.get('order', 'desc')

    valid_columns = ['Token', 'Price', 'Holdings', 'Value', 'DepositedAmount', 'Project', 'Chain']
    if sort_by not in valid_columns:
        sort_by = 'Value'
    
    query = f'''
        SELECT Token, Price, Holdings, Value, DepositedAmount, Project, Chain
        FROM Staking
        ORDER BY {sort_by} {'DESC' if order == 'desc' else 'ASC'}
    '''

    cursor.execute(query)
    staking_data = cursor.fetchall()

    next_sort_order = 'asc' if order == 'desc' else 'desc'

    total_staking_value = calculate_total_value('Staking')

    return render_template('staking.html', staking_data=staking_data, total_value=total_staking_value, sort_by=sort_by, order=next_sort_order)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
