import requests
import sqlite3
from flask import Flask, flash, render_template, redirect, url_for, g, request

app = Flask(__name__)
app.secret_key = "secret"

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

def find_token(token):
    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        SELECT ApiId, DisplayName, CurrentPrice
        FROM CoinPrices
        WHERE LOWER(ApiId) = LOWER(?) OR LOWER(Name) = LOWER(?) OR LOWER(DisplayName) = LOWER(?)
    ''', (token, token, token))

    result = cursor.fetchone()
    return result if result else None

def insert_wallet_data(token, holdings):
    db = get_db()
    cursor = db.cursor()

    print(f"Inserting {token} with holdings {holdings}")
    
    coin_data = find_token(token)
    
    if coin_data:
        name = coin_data[1]
        price = coin_data[2]
        print(f"Token found: {price}, Price: {price}") # Debugging Line
        cursor.execute('''INSERT OR REPLACE INTO Wallet (Token, Price, Holdings)
                        VALUES (?, ?, ?)''', (name, price, holdings))
        print(f'Inserted {token}, at {price} with the amount {holdings}')
        db.commit()
    else:
        print(f"Token {token} not found in CoinPrices") # Debugging Line
        return f"Token {token} not found in CoinPrices"

# Insert staking data
def insert_staking_data(token, holdings, deposited_amount, project, chain):
    db = get_db()
    cursor = db.cursor()

    
    price = find_token(token)[2]
    name = find_token(token)[1]

    if price:
        print(f"Inserting {holdings} {token} at {price}")
        cursor.execute('''INSERT OR REPLACE INTO Staking (Token, Price, Holdings, DepositedAmount, Project, Chain)
                          VALUES (?, ?, ?, ?, ?, ?)''', (name, price, holdings, deposited_amount, project, chain))
        db.commit()
    else:
        print(f"Token {token} not found in CoinPrices.")
        return f"Token {token} not found in CoinPrices."

def insert_farming_data(pool, token_a, token_b, holdings_a, holdings_b, protocol, chain, deposited_amount_a, deposited_amount_b):
    db = get_db()
    cursor = db.cursor()
    
    # Fetch current prices
    
    price_a = find_token(token_a)[2]
    name_a = find_token(token_a)[1]
    price_b = find_token(token_b)[2]
    name_b = find_token(token_b)[1]
    
    cursor.execute('''
        INSERT OR REPLACE INTO Farming (Pool, TokenA, TokenB, HoldingsA, HoldingsB, PriceA, PriceB, Protocol, Chain, DepositedAmountA, DepositedAmountB)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (pool, name_a, name_b, holdings_a, holdings_b, price_a, price_b, protocol, chain, deposited_amount_a, deposited_amount_b))
    db.commit()

def insert_leveraged_farming_data(pool, token_a, token_b, holdings_a, holdings_b, debt_a, debt_b, protocol, chain, deposited_amount_a, deposited_amount_b):
    db = get_db()
    cursor = db.cursor()
    
    # Fetch current prices
    price_a = find_token(token_a)[2]
    price_b = find_token(token_b)[2]
    
    cursor.execute('''
        INSERT OR REPLACE INTO LeveragedFarming (Pool, TokenA, TokenB, HoldingsA, HoldingsB, DebtA, DebtB, PriceA, PriceB, Protocol, Chain, DepositedAmountA, DepositedAmountB)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (pool, token_a, token_b, holdings_a, holdings_b, debt_a, debt_b, price_a, price_b, protocol, chain, deposited_amount_a, deposited_amount_b))
    db.commit()


def insert_lending_borrowing_data(protocol, chain, asset, type, amount, deposited_amount):
    db = get_db()
    cursor = db.cursor()
    
    # Fetch current price
    
    price = find_token(asset)
    
    cursor.execute('''
        INSERT OR REPLACE INTO LendingBorrowing (Protocol, Chain, Asset, Type, Amount, Price, DepositedAmount)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (protocol, chain, asset, type, amount, price, deposited_amount))
    db.commit()



def calculate_total_value(table_name=None):
    db = get_db()
    cursor = db.cursor()

    if table_name:

        if table_name in ['Wallet', 'Staking', 'LendingBorrowing']:
            # Calculate total for a specific table
            cursor.execute(f'SELECT COALESCE(SUM(Value), 0) FROM {table_name}')
            return cursor.fetchone()[0]
        else:
            # Calculate total for a specific table
            cursor.execute(f'SELECT COALESCE(SUM(TotalValue), 0) FROM {table_name}')
            return cursor.fetchone()[0]

    else:
        # Calculate total across all tables
        cursor.execute('SELECT COALESCE(SUM(Value), 0) FROM Wallet')
        wallet_total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COALESCE(SUM(Value), 0) FROM Staking')
        staking_total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COALESCE(SUM(TotalValue), 0) FROM Farming')
        farming_total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COALESCE(SUM(TotalValue), 0) FROM LeveragedFarming')
        leveraged_farming_total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COALESCE(SUM(Value), 0) FROM LendingBorrowing')
        lending_borrowing_total = cursor.fetchone()[0]
        
        return wallet_total + staking_total + farming_total + leveraged_farming_total + lending_borrowing_total
    
def fetch_single_coin_price(api_id):
    url = f'https://api.coingecko.com/api/v3/coins/{api_id}'
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None

def insert_or_update_coin(api_id):
    coin_data = fetch_single_coin_price(api_id)

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
            ApiId, Name, DisplayName, CurrentPrice, MarketCap, MarketCapRank, TotalVolume, High24h, Low24h,
            PriceChange24h, PriceChangePercentage24h, MarketCapChange24h, MarketCapChangePercentage24h, PriceChangePercentage1h
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
            api_id,
            name,
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

## Page Routes **

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
    if sort_by not in ['Name', 'CurrentPrice', 'MarketCap', 'MarketCapRank', 'TotalVolume', 'High24h', 'Low24h', 'PriceChange24h', 'PriceChangePercentage24h']:
        sort_by = 'MarketCap'
    
    # Query Data based on args
    if order == 'asc':
        query = f'SELECT * FROM CoinPrices ORDER BY {sort_by} ASC'
    else:
        query = f'SELECT * FROM CoinPrices ORDER BY {sort_by} DESC'
    
    
    # Set variable for next sort
    next_sort_order = 'asc' if order == 'desc' else 'desc'

    cursor.execute(query)
    coins = cursor.fetchall()

    return render_template('coin_prices.html', coins=coins, sort_by=sort_by, order=next_sort_order)

# Wallet Route
@app.route('/wallet')
def wallet():
    db = get_db()
    cursor = db.cursor()
    
    sort_by = request.args.get('sort_by', 'Value')
    order = request.args.get('order', 'desc')
    
    query = f'SELECT * FROM Wallet ORDER BY {sort_by} {order}'
    cursor.execute(query)
    wallet_data = cursor.fetchall()
    
    total_wallet_value = calculate_total_value('Wallet')
    total_portfolio_value = calculate_total_value()
    wallet_with_percent = []
    
    for row in wallet_data:
        token, price, holdings, value = row
        percent_of_total = (value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        wallet_with_percent.append((token, price, holdings, value, percent_of_total))
    
    return render_template('wallet.html',
                            wallet_data=wallet_with_percent,
                            total_value=total_wallet_value,
                            total_portfolio_value=total_portfolio_value,
                            sort_by=sort_by,
                            order=('asc' if order == 'desc' else 'desc'))

# Staking Route
@app.route('/staking')
def staking():
    db = get_db()
    cursor = db.cursor()
    
    sort_by = request.args.get('sort_by', 'Value')
    order = request.args.get('order', 'desc')

    query = f'SELECT * FROM Staking ORDER BY {sort_by} {order}'
    cursor.execute(query)
    staking_data = cursor.fetchall()
    
    total_portfolio_value = calculate_total_value()
    total_staking_value = calculate_total_value('Staking')
    staking_with_percent = []
    
    for row in staking_data:
        value = row[3]  # Assuming Value is at index 3
        percent_of_total = (value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        staking_with_percent.append(row + (percent_of_total,))
    
    return render_template('staking.html',
                            staking_data=staking_with_percent,
                            total_value=total_portfolio_value,
                            total_staking_value=total_staking_value,
                            sort_by=sort_by,
                            order=('asc' if order == 'desc' else 'desc'))

@app.route('/farming')
def farming():
    db = get_db()
    cursor = db.cursor()
    
    sort_by = request.args.get('sort_by', 'TotalValue')
    order = request.args.get('order', 'desc')

    valid_columns = ['Pool', 'TokenA', 'TokenB', 'HoldingsA', 'HoldingsB', 'ValueA', 'ValueB', 'DepositedAmountA', 'DepositedAmountB','Protocol','Chain']
    if sort_by not in valid_columns:
        sort_by = 'TotalValue'

    query = f'''
        SELECT * FROM Farming
        ORDER BY {sort_by} {'DESC' if order == 'desc' else 'ASC'}
    '''

    cursor.execute(query)
    farming_data = cursor.fetchall()
    
    total_portfolio_value = calculate_total_value()
    total_farming_value = calculate_total_value('Farming')
    farming_with_percent = []
    
    next_order = 'asc' if order == 'desc' else 'desc'

    for row in farming_data:
        total_value = row[9]  # Assuming TotalValue is at index 9
        percent_of_total = (total_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        farming_with_percent.append(row + (percent_of_total,))
    
    return render_template('farming.html',
                            farming_data=farming_with_percent,
                            total_value=total_portfolio_value,
                            total_farming_value=total_farming_value,
                            sort_by=sort_by,
                            order=next_order)

# Leveraged Farming Route
@app.route('/leveraged_farming')
def leveraged_farming():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM LeveragedFarming')
    leveraged_farming_data = cursor.fetchall()
    
    total_portfolio_value = calculate_total_value()
    leveraged_farming_with_percent = []
    
    for row in leveraged_farming_data:
        total_value = row[11]  # Assuming TotalValue is at index 11
        percent_of_total = (total_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        leveraged_farming_with_percent.append(row + (percent_of_total,))
    
    return render_template('leveraged_farming.html', leveraged_farming_data=leveraged_farming_with_percent, total_value=total_portfolio_value)

@app.route('/lending_borrowing')
def lending_borrowing():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM LendingBorrowing')
    lending_borrowing_data = cursor.fetchall()
    
    total_portfolio_value = calculate_total_value()
    lending_borrowing_with_percent = []
    
    for row in lending_borrowing_data:
        value = row[6]  # Assuming Value is at index 6
        percent_of_total = (value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        lending_borrowing_with_percent.append(row + (percent_of_total,))
    
    return render_template('lending_borrowing.html', lending_borrowing_data=lending_borrowing_with_percent, total_value=total_portfolio_value)

@app.route('/coin_exposure')
def coin_exposure():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM CoinExposure ORDER BY TotalValue DESC')
    coin_exposure_data = cursor.fetchall()
    
    total_portfolio_value = calculate_total_value()
    coin_exposure_with_percent = []
    
    for row in coin_exposure_data:
        total_value = row[1]  # Assuming TotalValue is at index 1
        percent_of_total = (total_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        coin_exposure_with_percent.append(row + (percent_of_total,))
    
    return render_template('coin_exposure.html', coin_exposure_data=coin_exposure_with_percent, total_value=total_portfolio_value)

##############################
## Update / Function Routes ##
##############################



@app.route('/add_farming', methods=['POST'])
def add_farming():
    pool = request.form['pool']
    token_a = request.form['token-a']
    token_b = request.form['token-b']
    holdings_a = float(request.form['holdings-a'])
    holdings_b = float(request.form['holdings-b'])
    protocol = request.form['protocol']
    chain = request.form['chain']
    deposited_amount_a = float(request.form['deposited-amount-a'])
    deposited_amount_b = float(request.form['deposited-amount-b'])
    insert_farming_data(pool, token_a, token_b, holdings_a, holdings_b, protocol, chain, deposited_amount_a, deposited_amount_b)
    flash('Farming position added successfully', 'success')
    return redirect(url_for('farming'))

@app.route('/add_leveraged_farming', methods=['POST'])
def add_leveraged_farming():
    pool = request.form['pool']
    token_a = request.form['token-a']
    token_b = request.form['token-b']
    holdings_a = float(request.form['holdings-a'])
    holdings_b = float(request.form['holdings-b'])
    debt_a = float(request.form['debt-a'])
    debt_b = float(request.form['debt-b'])
    protocol = request.form['protocol']
    chain = request.form['chain']
    deposited_amount_a = float(request.form['deposited-amount-a'])
    deposited_amount_b = float(request.form['deposited-amount-b'])
    insert_leveraged_farming_data(pool, token_a, token_b, holdings_a, holdings_b, debt_a, debt_b, protocol, chain, deposited_amount_a, deposited_amount_b)
    flash('Leveraged farming position added successfully', 'success')
    return redirect(url_for('leveraged_farming'))

@app.route('/add_lending_borrowing', methods=['POST'])
def add_lending_borrowing():
    protocol = request.form['protocol']
    chain = request.form['chain']
    asset = request.form['asset']
    type = request.form['type']
    amount = float(request.form['amount'])
    deposited_amount = float(request.form['deposited_amount'])
    insert_lending_borrowing_data(protocol, chain, asset, type, amount, deposited_amount)
    flash('Lending/Borrowing position added successfully', 'success')
    return redirect(url_for('lending_borrowing'))


# Add staking route
@app.route('/add_staking', methods=['POST'])
def add_staking():
    token = request.form['token']
    holdings = request.form['holdings']
    deposited_amount = request.form['deposited-amount']
    project = request.form['project']
    chain = request.form['chain']

    message = insert_staking_data(token, holdings, deposited_amount, project, chain)
    if message:
        flash(message)
    return redirect(url_for('staking'))

@app.route('/add_wallet', methods=['POST'])
def add_wallet():
    token = request.form['token']
    holdings = request.form['holdings']
    print(f"Token: {token}, Holdings: {holdings}") # Debug Line
    insert_wallet_data(token, holdings)
    return redirect(url_for('wallet'))


@app.route('/update_coin_prices', methods=['GET'])
def update_coin_prices():
    coins = fetch_coin_prices()
    if isinstance(coins, str):
        flash(f"Error fetching coin prices: {coins}", "error")
        return redirect(url_for('coin_prices'))
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

        missing_apis = []
        for coin_name in missing_coins:
            cursor.execute(f'SELECT ApiId FROM CoinPrices WHERE Name = {str(coin_name)}')
            missing_apis.append(cursor.fetchone())
        
        # Fetch prices for the missing coins
        for api in missing_apis:
            coin_data = fetch_single_coin_price(str(api))
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
                print(f"Token {api} not found in API, maunal update needed")
        db.commit()
        return redirect(url_for('coin_prices')) # Redirect back to coin price page
    return "Failed to update coin prices."

# Route handling Display Name change
@app.route('/update_display_name', methods=['POST'])
def update_display_name():
    coin_name = request.form['coin-name']
    display_name = request.form['display-name']

    db = get_db()
    cursor = db.cursor()

    cursor.execute('UPDATE CoinPrices SET DisplayName = ? WHERE Name = ?', (display_name, coin_name))
    db.commit()

    return redirect(url_for('coin_prices'))

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

    
    

@app.route('/edit_staking', methods=['POST'])
def edit_staking():
    token = request.form['token']
    holdings = float(request.form['holdings'])
    deposited_amount = float(request.form['deposited-amount'])
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('UPDATE Staking SET Holdings = ?, DepositedAmount = ? WHERE Token = ?',
                   (holdings, deposited_amount, token))
    db.commit()
    
    flash(f'Staking position for {token} updated successfully', 'success')
    return redirect(url_for('staking'))

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
