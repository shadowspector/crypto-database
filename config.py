class Config:
    SECRET_KEY = "secret"
    MORALIS_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjIzNGI1YzJhLTEwNTgtNDExNi1iZjhmLWUyZjQyMjE4MzgzOCIsIm9yZ0lkIjoiNDExMTY1IiwidXNlcklkIjoiNDIyNTM1IiwidHlwZUlkIjoiMTYwOWZiMmEtYjc0Mi00ZWE1LTkwZDAtZGZlNmYyM2ViZjMxIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3Mjg1MjU3NjAsImV4cCI6NDg4NDI4NTc2MH0.2y4lJE7yrszEUx9dOoD0krIjDkeAE6OtntVBjy-laQ4'
    MORALIS_BASE_URL = 'https://deep-index.moralis.io/api/v2'
    CG_API_KEY = 'CG-crAB46kbWL5h2Jk1MQk7MJRw'
    DEPOSIT_TOKENS = ['Aave Optimism wstETH','peahalla', 'Aave Optimism Variable Debt DAI',
                        'Metronome Synth vaETH-Deposit', 'Metronome Synth ETH-Debt', 'Metronome Synth USD-Debt',
                        'Aave Optimism Variable Debt USDCn', 'Sturdy Interest Bearing WETH (Renzo Restaked ETH) - 1',
                        'max EQB', 'esVKA', 'staked Equilibria Pendle', 'GammaSwap Revenue Share', 'pfLODE',
                        'Smilee Share', 'pfCMLT-LP', 'pfxGRAIL', 'GRAIL-USDC Camelot Neutral Wide Jones LP Token',
                        'aWETH-USDC', 'Staked PEASPod', 'Smilee Share', 'Staked Dinero', 'Staked OHM Pod', '(Re)cycler Staked Tokemak',
                        'Staked peahalla']
    SPAM_TOKENS = ['Lizardo Pepez', 'MINKY', 'toby', 'MikeAI', 'BoysClub', 'WOLFO', 'Peepo', 'Based USA', 'Oh no',
                    'Oomer', 'Wild Goat Coin', 'OX Coin', 'Boysclub', 'BASED USA', 'Oh No']
    DATABASE = 'crypto_portfolio.db'
    # List of Chains for API Query
    CHAINS_TO_QUERY = ['eth', 'polygon', 'avalanche', 'arbitrum', 'optimism', 'base']
    WALLET_ADDRESS = '0xbF133C1763c0751494CE440300fCd6b8c4e80D83'
