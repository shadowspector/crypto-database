from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, json
from services.coin_price_service import CoinPriceService
from utils.response import ResponseHandler

coin_routes = Blueprint('coin_routes', __name__)

@coin_routes.route('/coin_prices')
def coin_prices():
    sort_by = request.args.get('sort_by', 'MarketCap')
    order = request.args.get('order', 'desc')
    response= CoinPriceService.get_all_coins(sort_by, order)
    if not response['success']:
        flash(response['error'], 'error')
        coins = []
    else:
        coins = response['data']
    return render_template('coin_prices.html', coins=coins, sort_by=sort_by, order=order)

@coin_routes.route('/update_coin_prices', methods=['GET'])
def update_coin_prices():
    result = CoinPriceService.update_coin_prices()
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['error'], 'error')
    return redirect(url_for('coin_routes.coin_prices'))

@coin_routes.route('/update_coin_name', methods=['POST'])
def update_coin_name():
    data = request.json
    if not all ([data.get('coin_name'), data.get('display_name'), data.get('alternate_names', []), data.get('api_name')]):
        return jsonify(ResponseHandler.error("Missing input")), 400
    
    result = CoinPriceService.update_coin_names(data['coin_name'], data['alternate_names'], data['display_name'], data['api_name'])

    return jsonify(result), 200 if result['success'] else 400

    

@coin_routes.route('/update_manual_token', methods=['POST'])
def update_manual_token():
    token_name = request.form.get('token_name')
    token_price = request.form.get('token_price')
    
    if not token_name or not token_price:
        flash('Token name and price are required', 'error')
        return redirect(url_for('coin_routes.coin_prices'))
    try:
        token_price = float(token_price)
    except ValueError:
        flash('Invalid price format', 'error')
        return redirect(url_for('coin_routes.coin_prices'))
    
    result = CoinPriceService.update_manual_token(token_name, token_price)
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['error'], 'error')
    return redirect(url_for('coin_routes.coin_prices'))

@coin_routes.route('/add_coin', methods=['POST'])
def add_coin():
    coin_name = request.form.get('coin_name')
    if not coin_name:
        flash('Coin name is required', 'error')
        return redirect(url_for('coin_routes.coin_prices'))
    result = CoinPriceService.insert_or_update_coin(coin_name)
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['error'], 'error')
    return redirect(url_for('coin_routes.coin_prices'))

