from flask import Blueprint, render_template, request, flash, redirect, url_for
from services.wallet_service import WalletService


wallet_routes = Blueprint('wallet_routes', __name__)

@wallet_routes.route('/wallet')
def wallet():
    sort_by = request.args.get('sort_by', 'Value')
    order = request.args.get('order', 'desc')
    
    response = WalletService.get_wallet_items(sort_by,order)
    if not response['success']:
        flash(response['error'], 'error')
        wallet_items = []
    else:
        wallet_items = response['data']
    
    total_wallet_value = WalletService.calculate_total_value()
    total_portfolio_value = WalletService.calculate_total_portfolio_value()

    wallet_with_percent = []
    for item in wallet_items:
        percent_of_total = item.calculate_percent_of_total(total_portfolio_value)
        wallet_with_percent.append((item,percent_of_total))
    
    return render_template('wallet.html',
                            wallet_data=wallet_with_percent,
                            total_value=total_wallet_value,
                            total_portfolio_value=total_portfolio_value,
                            sort_by=sort_by,
                            order=('asc' if order == 'desc' else 'desc'))

@wallet_routes.route('/update_token', methods=['POST'])
def update_token():
    token_name = request.form.get('token_name')
    holdings = request.form.get('holdings')

    if not token_name or not holdings:
        flash('Token name and holdings are required', 'error')
        return redirect(url_for('wallet_routes.wallet'))

    try:
        holdings = float(holdings)
    except ValueError:
        flash('Holdings must be a number', 'error')
        return redirect(url_for('wallet_routes.wallet'))
    
    result = WalletService.add_token(token_name, holdings)
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('wallet_routes.wallet'))



@wallet_routes.route('/update_wallet_and_prices', methods=['GET'])
def update_wallet_and_prices():
    result = WalletService.update_wallet_and_prices()
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['error'], 'error')
    return redirect(url_for('wallet_routes.wallet'))