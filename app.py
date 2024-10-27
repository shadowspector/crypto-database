from flask import Flask, flash, render_template, redirect, url_for, request, jsonify
from config import Config
from routes.coin_routes import coin_routes
from routes.wallet_routes import wallet_routes
from routes.staking_routes import staking_routes
from utils.logging_config import setup_logger, log_function_call

logger = setup_logger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(coin_routes)
app.register_blueprint(wallet_routes)
app.register_blueprint(staking_routes)

#def insert_farming_data(pool, token_a, token_b, holdings_a, holdings_b, protocol, chain, deposited_amount_a, deposited_amount_b):
#    db = get_db()
#    cursor = db.cursor()
    
    # Fetch current prices
    
#    price_a = find_token(token_a)[2]
#    name_a = find_token(token_a)[1]
#    price_b = find_token(token_b)[2]
#    name_b = find_token(token_b)[1]
    
#    cursor.execute('''
#        INSERT OR REPLACE INTO Farming (Pool, TokenA, TokenB, HoldingsA, HoldingsB, PriceA, PriceB, Protocol, Chain, DepositedAmountA, DepositedAmountB)
#        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#    ''', (pool, name_a, name_b, holdings_a, holdings_b, price_a, price_b, protocol, chain, deposited_amount_a, deposited_amount_b))
#    db.commit()

#def insert_leveraged_farming_data(pool, token_a, token_b, holdings_a, holdings_b, debt_a, debt_b, protocol, chain, deposited_amount_a, deposited_amount_b):
#    db = get_db()
#    cursor = db.cursor()
    
    # Fetch current prices
#    price_a = find_token(token_a)[2]
#    price_b = find_token(token_b)[2]
    
#    cursor.execute('''
#        INSERT OR REPLACE INTO LeveragedFarming (Pool, TokenA, TokenB, HoldingsA, HoldingsB, DebtA, DebtB, PriceA, PriceB, Protocol, Chain, DepositedAmountA, DepositedAmountB)
#        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#    ''', (pool, token_a, token_b, holdings_a, holdings_b, debt_a, debt_b, price_a, price_b, protocol, chain, deposited_amount_a, deposited_amount_b))
#    db.commit()


#def insert_lending_borrowing_data(protocol, chain, asset, type, amount, deposited_amount):
#    db = get_db()
#    cursor = db.cursor()
    
    # Fetch current price
    
#    price = find_token(asset)
    
#    cursor.execute('''
#        INSERT OR REPLACE INTO LendingBorrowing (Protocol, Chain, Asset, Type, Amount, Price, DepositedAmount)
#        VALUES (?, ?, ?, ?, ?, ?, ?)
#    ''', (protocol, chain, asset, type, amount, price, deposited_amount))
#    db.commit()





    
        
############################
#         Routes           #
############################

## Page Routes **

# Main Menu Route
@app.route('/')
@log_function_call(logger)
def main_menu():
    logger.info('Accessed main menu')
    return render_template('index.html')

#@app.route('/farming')
#def farming():
#    db = get_db()
#    cursor = db.cursor()
    
#    sort_by = request.args.get('sort_by', 'TotalValue')
#    order = request.args.get('order', 'desc')

#    valid_columns = ['Pool', 'TokenA', 'TokenB', 'HoldingsA', 'HoldingsB', 'ValueA', 'ValueB', 'DepositedAmountA', 'DepositedAmountB','Protocol','Chain']
#    if sort_by not in valid_columns:
#        sort_by = 'TotalValue'

#    query = f'''
#        SELECT * FROM Farming
#        ORDER BY {sort_by} {'DESC' if order == 'desc' else 'ASC'}
#    '''

#    cursor.execute(query)
#    farming_data = cursor.fetchall()
    
#    total_portfolio_value = calculate_total_value()
#    total_farming_value = calculate_total_value('Farming')
#    farming_with_percent = []
    
#    next_order = 'asc' if order == 'desc' else 'desc'

#    for row in farming_data:
#        total_value = row[9]  # Assuming TotalValue is at index 9
#        percent_of_total = (total_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
#        farming_with_percent.append(row + (percent_of_total,))
    
#    return render_template('farming.html',
#                            farming_data=farming_with_percent,
#                            total_value=total_portfolio_value,
#                            total_farming_value=total_farming_value,
#                            sort_by=sort_by,
#                            order=next_order)

# Leveraged Farming Route
#@app.route('/leveraged_farming')
#def leveraged_farming():
#    db = get_db()
#    cursor = db.cursor()
    
#    sort_by = request.args.get('sort_by', 'TotalValue')
#    order = request.args.get('order', 'desc')

    
#    cursor.execute('SELECT * FROM LeveragedFarming')
#    leveraged_farming_data = cursor.fetchall()
    
#    total_portfolio_value = calculate_total_value()
#    leveraged_farming_with_percent = []
    
#    for row in leveraged_farming_data:
#        total_value = row[11]  # Assuming TotalValue is at index 11
#        percent_of_total = (total_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
#        leveraged_farming_with_percent.append(row + (percent_of_total,))
    
#    return render_template('leveraged_farming.html', leveraged_farming_data=leveraged_farming_with_percent, total_value=total_portfolio_value)

#@app.route('/lending_borrowing')
#def lending_borrowing():
#    db = get_db()
#    cursor = db.cursor()
    
#    cursor.execute('SELECT * FROM LendingBorrowing')
#    lending_borrowing_data = cursor.fetchall()
    
#    total_portfolio_value = calculate_total_value()
#    lending_borrowing_with_percent = []
    
#    for row in lending_borrowing_data:
#        value = row[6]  # Assuming Value is at index 6
#        percent_of_total = (value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
#        lending_borrowing_with_percent.append(row + (percent_of_total,))
    
#    return render_template('lending_borrowing.html', lending_borrowing_data=lending_borrowing_with_percent, total_value=total_portfolio_value)

#@app.route('/coin_exposure')
#def coin_exposure():
#    db = get_db()
#    cursor = db.cursor()
    
#    cursor.execute('SELECT * FROM CoinExposure ORDER BY TotalValue DESC')
#    coin_exposure_data = cursor.fetchall()
    
#    total_portfolio_value = calculate_total_value()
#    coin_exposure_with_percent = []
    
#    for row in coin_exposure_data:
#        total_value = row[1]  # Assuming TotalValue is at index 1
#        percent_of_total = (total_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
#        coin_exposure_with_percent.append(row + (percent_of_total,))
    
#    return render_template('coin_exposure.html', coin_exposure_data=coin_exposure_with_percent, total_value=total_portfolio_value)

##############################
## Update / Function Routes ##
##############################



#@app.route('/add_farming', methods=['POST'])
#def add_farming():
#    pool = request.form['pool']
#    token_a = request.form['token-a']
#    token_b = request.form['token-b']
#    holdings_a = float(request.form['holdings-a'])
#    holdings_b = float(request.form['holdings-b'])
#    protocol = request.form['protocol']
#    chain = request.form['chain']
#    deposited_amount_a = float(request.form['deposited-amount-a'])
#    deposited_amount_b = float(request.form['deposited-amount-b'])
#    insert_farming_data(pool, token_a, token_b, holdings_a, holdings_b, protocol, chain, deposited_amount_a, deposited_amount_b)
#    flash('Farming position added successfully', 'success')
#    return redirect(url_for('farming'))

#@app.route('/add_leveraged_farming', methods=['POST'])
#def add_leveraged_farming():
#    pool = request.form['pool']
#    token_a = request.form['token-a']
#    token_b = request.form['token-b']
#    holdings_a = float(request.form['holdings-a'])
#    holdings_b = float(request.form['holdings-b'])
#    debt_a = float(request.form['debt-a'])
#    debt_b = float(request.form['debt-b'])
#    protocol = request.form['protocol']
#    chain = request.form['chain']
#    deposited_amount_a = float(request.form['deposited-amount-a'])
#    deposited_amount_b = float(request.form['deposited-amount-b'])
#    insert_leveraged_farming_data(pool, token_a, token_b, holdings_a, holdings_b, debt_a, debt_b, protocol, chain, deposited_amount_a, deposited_amount_b)
#    flash('Leveraged farming position added successfully', 'success')
#    return redirect(url_for('leveraged_farming'))

#@app.route('/add_lending_borrowing', methods=['POST'])
#def add_lending_borrowing():
#    protocol = request.form['protocol']
#    chain = request.form['chain']
#    asset = request.form['asset']
#    type = request.form['type']
#    amount = float(request.form['amount'])
#    deposited_amount = float(request.form['deposited_amount'])
#    insert_lending_borrowing_data(protocol, chain, asset, type, amount, deposited_amount)
#    flash('Lending/Borrowing position added successfully', 'success')
#    return redirect(url_for('lending_borrowing'))





# Run the app
if __name__ == '__main__':
    logger.info('Starting application')
    app.run(debug=True)
