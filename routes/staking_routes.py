from flask import Blueprint, render_template, request, flash, redirect, url_for
from services.staking_service import StakingService
from services.wallet_service import WalletService # For total portfolio value - temporary
from utils.logging_config import setup_logger, log_function_call

logger = setup_logger(__name__)
staking_routes = Blueprint('staking_routes', __name__)

@staking_routes.route('/staking')
@log_function_call(logger)
def staking():
    """Display the staking page with all staked positions."""
    sort_by = request.args.get('sort_by', 'Value')
    order = request.args.get('order', 'desc')

    # Get staked positions
    reponse = StakingService.get_staked_positions(sort_by,order)
    if not reponse['success']:
        flash(reponse['error'], 'error')
        logger.error('No response recieved from get_staked_positions')
        staking_positions = []
    else:
        staking_positions = reponse['data']
        logger.debug(f'Response data: {staking_positions}')
    
    # Calculate totals
    total_staking_value = StakingService.calculate_total_staking_value()
    total_portfolio_value = WalletService.calculate_total_portfolio_value()

    # Calculate percentages and create display data
    staking_with_percent = []
    for position in staking_positions:
        percent_of_total = position.calculate_percent_of_total(total_staking_value)
        staking_with_percent.append((position, percent_of_total))
    
    return render_template('staking.html',
                           staking_data=staking_with_percent,
                           total_value=total_portfolio_value,
                           total_staking_value=total_staking_value,
                           sort_by=sort_by,
                           order=('asc' if order== 'desc' else 'desc'))

@staking_routes.route('/add_staking', methods=['POST'])
@log_function_call(logger)
def add_staking():
    """Add a new staked position."""
    pool = request.form.get('pool')
    token = request.form.get('token')
    holdings = request.form.get('holdings')
    deposited_amount= request.form.get('deposited-amount')
    project = request.form.get('project')
    chain = request.form.get('chain')

    # validate inputs
    if not all([pool, token, holdings, deposited_amount, project, chain]):
        flash('All fields are required', 'error')
        return redirect(url_for('staking_routes.staking'))

    try:
        holdings = float(holdings)
        deposited_amount = float(deposited_amount)
    except ValueError:
        flash('Holdings and deposited amounts must be numbers', 'error')
        return redirect(url_for('staking_routes.staking'))
    
    # Add the position
    result = StakingService.add_staked_position(
        pool=pool,
        token=token,
        holdings=holdings,
        deposited_amount=deposited_amount,
        project=project,
        chain=chain
    )
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('staking_routes.staking'))

@staking_routes.route('/edit_staking', methods=['POST'])
@log_function_call(logger)
def edit_staking():
    """Update an existing staked position"""
    pool = request.form.get('pool')
    token = request.form.get('token')
    holdings = request.form.get('holdings')
    deposited_amount = request.form.get('deposited-amount')

    # Validate inputs
    if not all([pool, token, holdings, deposited_amount]):
        flash('Token, holdings, and deposited amount are required', 'error')
        return redirect(url_for('staking_routes.staking'))
    
    try:
        holdings =float(holdings)
        deposited_amount = float(deposited_amount)
    except ValueError:
        flash('Holdings and deposited amount must be numbers', 'error')
        return redirect(url_for('staking_routes.staking'))
    
    # Update the position
    result = StakingService.update_staked_postion(
        current_pool=pool,
        token=token,
        holdings=holdings,
        deposited_amount=deposited_amount
    )

    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('staking_routes.staking'))