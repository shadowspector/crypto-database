from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from services.wallet_service import WalletService
from utils.logging_config import setup_logger, log_function_call
from utils.response import ResponseHandler
import datetime


logger = setup_logger(__name__)
wallet_routes = Blueprint('wallet_routes', __name__)

@wallet_routes.route('/wallet')
@log_function_call(logger)
def wallet():
    """
    Display wallet page with current holdings and values.
    Supports sorting by different columns
    """
    try:
        sort_by = request.args.get('sort_by', 'Value')
        order = request.args.get('order', 'desc')
        
        # Map URL parameters to column names
        sort_mapping = {
            'Token': 'coin_id',
            'Price': 'price',
            'Holdings': 'amount',
            'Value': 'value'
        }

        # Use mapped column name or default to 'value'
        db_sort_column = sort_mapping.get(sort_by, 'value')


        response = WalletService.get_wallet_items(db_sort_column,order)
        if not response['success']:
            flash(response['error'], 'error')
            logger.error(f'Failed to retrieve wallet items: {response["error"]}')
            wallet_items = []
        else:
            wallet_items = response['data']
            logger.debug(f'Retrieved {len(wallet_items)} wallet items')
        
        total_wallet_value = WalletService.calculate_total_value()
        total_portfolio_value = WalletService.calculate_total_portfolio_value()

        wallet_with_percent = []
        for item in wallet_items:
            percent_of_total = item.calculate_percent_of_total(total_portfolio_value)
            wallet_with_percent.append((item,percent_of_total))

        # Determine next sort order for template
        next_order = 'asc' if order == 'desc' else 'desc'
        
        return render_template('wallet.html',
                                wallet_data=wallet_with_percent,
                                total_value=total_wallet_value,
                                total_portfolio_value=total_portfolio_value,
                                sort_by=sort_by,
                                order=next_order)
    except Exception as e:
        logger.error(f'Error in wallet route: {str(e)}', exc_info=True)
        flash('An error occurred while loading wallet data', 'error')
        return render_template(
            'wallet.html',
            wallet_data=[],
            total_value=0,
            total_portfolio_value=0,
            sort_by=sort_by,
            order='desc'
        )

@wallet_routes.route('/update_token', methods=['POST'])
@log_function_call(logger)
def update_token():
    """
    Handle manual token updates.
    Expects token_name and holdings in form data.
    """
    try:    
        token_name = request.form.get('token-name')
        holdings = request.form.get('holdings')

        if not token_name or holdings is None:
            flash('Token name and holdings are required', 'error')
            logger.warning('Attempted token update with missing data')
            return redirect(url_for('wallet_routes.wallet'))

        try:
            holdings = float(holdings)
            if holdings < 0:
                raise ValueError('Holdings cannot be negative')
        except ValueError:
            flash('Holdings must be a valid positive number', 'error')
            logger.warning(f'Invalid holdings value provided: {holdings}')
            return redirect(url_for('wallet_routes.wallet'))
        
        result = WalletService.update_token(token_name, holdings)
        if result['success']:
            flash(result['message'], 'success')
            logger.info(f'Successfully updated token {token_name}')
        else:
            flash(result['error'], 'error')
            logger.error(f'Failed to update token {token_name}: {result["error"]}')
        
        return redirect(url_for('wallet_routes.wallet'))
    except Exception as e:
        logger.error(f'Error in update_token route: {str(e)}', exc_info=True)
        flash('An error occurred while updating the token', 'error')
        return redirect(url_for('wallet_routes.wallet'))



@wallet_routes.route('/update_wallet_and_prices', methods=['GET'])
@log_function_call(logger)
def update_wallet_and_prices():
    """
    Trigger wallet and price update from Moralis
    Handles the complete update process including new token discovery
    """
    try:
        logger.info('Starting wallet and prices update')
        result = WalletService.update_wallet_and_prices()

        if result['success']:
            flash(result['message'], 'success')
            logger.info('Successfully update wallet and prices')
        else:
            flash(result['error'], 'error')
            logger.error(f'Failed to update wallet and prices: {result["error"]}')
        
        return redirect(url_for('wallet_routes.wallet'))
    except Exception as e:
        logger.error(f'Error in update_wallet_and_prices route: {str(e)}', exc_info=True)
        flash('An error occurred while updating wallet data', 'error')
        return redirect(url_for('wallet_routes.wallet'))
    
@wallet_routes.route('/api/wallet/summary', methods=['GET'])
@log_function_call(logger)
def get_wallet_summary():
    """
    API endpoint for getting wallet summary data.
    Useful for AJAX updates or external services.
    """
    try:
        total_value = WalletService.calculate_total_value()
        return jsonify(ResponseHandler.success('Success', {
            'total_value': total_value,
            'update_at': datetime.datetime.now().isoformat()
        }))
    except Exception as e:
        logger.error(f'Error in wallet summary API: {str(e)}', exc_info=True)
        return jsonify(ResponseHandler.error(str(e))), 500
