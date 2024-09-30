import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import requests

# Connect to SQLite
conn = sqlite3.connect('crypto_portfolio.db')
cursor = conn.cursor()

# Create tables
def create_tables():
    cursor.execute('PRAGMA foreign_keys = ON')
    cursor.execute('''CREATE TABLE IF NOT EXISTS CoinPrices (
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
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS Wallet (
        Token TEXT PRIMARY KEY,
        Price REAL NOT NULL,
        Holdings REAL NOT NULL,
        Value REAL GENERATED ALWAYS AS (Holdings * Price) VIRTUAL,
        PercentOfTotal REAL,
        FOREIGN KEY (Token) REFERENCES CoinPrices(Name)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS Staking (
        Pool TEXT PRIMARY KEY,
        Token TEXT NOT NULL,
        Price REAL NOT NULL,
        Holdings REAL NOT NULL,
        Value REAL GENERATED ALWAYS AS (Holdings * Price) VIRTUAL,
        PercentOfTotal REAL,
        FOREIGN KEY (Token) REFERENCES CoinPrices(Name)
    )''')
    conn.commit()

# Fetch coin prices from API
def fetch_coin_prices():
    url = 'https://api.coingecko.com/api/v3/coins/markets'
    all_coins = []
    total_top_coins = 500
    coins_per_page = 100
    for page in range(1, (total_top_coins // coins_per_page) + 1):
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': coins_per_page,
            'page': page,
            'sparkline': 'false',
            'price_change_percentage': '1h,24h'
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            coins = response.json()
            all_coins.extend(coins)
        else:
            messagebox.showerror("Error", f"Error fetching data from page {page}: {response.status_code}")
            break
    return all_coins

# Update coin prices in the database
def update_coin_prices():
    coins = fetch_coin_prices()
    if coins:
        for coin in coins:
            cursor.execute('''INSERT OR REPLACE INTO CoinPrices (
                Name, CurrentPrice, MarketCap, MarketCapRank, TotalVolume, High24h, Low24h,
                PriceChange24h, PriceChangePercentage24h, MarketCapChange24h, MarketCapChangePercentage24h, PriceChangePercentage1h
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                coin['name'], coin['current_price'], coin['market_cap'], coin['market_cap_rank'], 
                coin['total_volume'], coin['high_24h'], coin['low_24h'], coin['price_change_24h'], 
                coin['price_change_percentage_24h'], coin['market_cap_change_24h'], 
                coin['market_cap_change_percentage_24h'], coin['price_change_percentage_1h_in_currency']
            ))
        conn.commit()
        messagebox.showinfo("Success", "Coin prices updated successfully!")
    else:
        messagebox.showerror("Error", "Failed to update coin prices.")

# Insert wallet data
def insert_wallet_data(token, holdings):
    cursor.execute('SELECT CurrentPrice FROM CoinPrices WHERE Name = ?', (token.lower(),))
    price = cursor.fetchone()
    if price:
        cursor.execute('''INSERT OR REPLACE INTO Wallet (Token, Price, Holdings)
                          VALUES (?, ?, ?)''', (token, price[0], holdings))
        conn.commit()
    else:
        messagebox.showerror("Error", f"Token {token} not found in CoinPrices.")

# Insert staking data
def insert_staking_data(pool, token, holdings):
    cursor.execute('SELECT CurrentPrice FROM CoinPrices WHERE Name = ?', (token,))
    price = cursor.fetchone()
    if price:
        cursor.execute('''INSERT OR REPLACE INTO Staking (Pool, Token, Price, Holdings)
                          VALUES (?, ?, ?, ?)''', (pool, token, price[0], holdings))
        conn.commit()
    else:
        messagebox.showerror("Error", f"Token {token} not found in CoinPrices.")

# Calculate the toal value for Wallet or Staking
def calculate_total_value(table_name):
    cursor.execute(f'SELECT SUM(Value) From {table_name}')
    total_value = cursor.fetchone()[0]
    if total_value is None:
        total_value = 0
    return total_value

# Display tables and update total value label
def display_table(table_name):
    cursor.execute(f'SELECT * FROM {table_name}')
    rows = cursor.fetchall()
    columns = {'CoinPrices': ['Name', 'CurrentPrice', 'MarketCap', 'MarketCapRank', 'TotalVolume', 
                              'High24h', 'Low24h', 'PriceChange24h', 'PriceChangePercentage24h', 
                              'MarketCapChange24h', 'MarketCapChangePercentage24h', 'PriceChangePercentage1h'],
               'Wallet': ['Token', 'Price', 'Holdings', 'Value'],
               'Staking': ['Pool', 'Token', 'Price', 'Holdings', 'Value']}

    # Clear previous data
    for item in tree.get_children():
        tree.delete(item)

    # Insert new data
    for row in rows:
        tree.insert('', tk.END, values=row)

    # Update total value label if table is Wallet or Staking
    if table_name in ['Wallet', 'Staking']:
        total_value = calculate_total_value(table_name)
        total_value_label.config(text=f"Total Value: ${total_value:.2f}")
    else:
        total_value_label.config(text="")
    


def update_view(view):
    global tree
    for widget in frame.winfo_children():
        widget.destroy()

    tree = ttk.Treeview(frame, columns=('col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8', 'col9', 'col10', 'col11', 'col12'), show='headings')
    
    columns = {'CoinPrices': ['Name', 'CurrentPrice', 'MarketCap', 'MarketCapRank', 'TotalVolume',
                              'High24h', 'Low24h', 'PriceChange24h', 'PriceChangePercentage24h',
                              'MarketCapChange24h', 'MarketCapChangePercentage24h', 'PriceChangePercentage1h'],
               'Wallet': ['Token', 'Price', 'Holdings', 'Value'],
               'Staking': ['Pool', 'Token', 'Price', 'Holdings', 'Value']}[view]
    
    tree["columns"] = columns
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    
    tree.pack(fill=tk.BOTH, expand=True)
    display_table(view)

def switch_view(view):
    if view == 'CoinPrices':
        btn_update_prices.pack(side=tk.TOP, fill=tk.X)
        total_value_label.config(text="")
    else:
        btn_update_prices.pack_forget()
        total_value = calculate_total_value(view)
        total_value_label.config(text=f"Total Value: ${total_value:.2f}")
    update_view(view)

def add_wallet_entry():
    token = token_entry.get()
    holdings = holdings_entry.get()
    if token and holdings:
        insert_wallet_data(token, float(holdings))
        update_view('Wallet')
        token_entry.delete(0, tk.END)
        holdings_entry.delete(0, tk.END)
    else:
        messagebox.showwarning("Input Error", "Please fill in all fields")

def add_staking_entry():
    pool = pool_entry.get()
    token = token_entry.get()
    holdings = holdings_entry.get()
    if pool and token and holdings:
        insert_staking_data(pool, token, float(holdings))
        update_view('Staking')
        pool_entry.delete(0, tk.END)
        token_entry.delete(0, tk.END)
        holdings_entry.delete(0, tk.END)
    else:
        messagebox.showwarning("Input Error", "Please fill in all fields")

def show_wallet_form():
    hide_all_forms()
    form_frame.pack(side=tk.BOTTOM, fill=tk.X)
    btn_add_wallet.pack(side=tk.LEFT)
    token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    holdings_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

def show_staking_form():
    hide_all_forms()
    form_frame.pack(side=tk.BOTTOM, fill=tk.X)
    btn_add_staking.pack(side=tk.LEFT)
    pool_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    holdings_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

def hide_all_forms():
    btn_add_wallet.pack_forget()
    btn_add_staking.pack_forget()
    token_entry.pack_forget()
    holdings_entry.pack_forget()
    pool_entry.pack_forget()

# Initialize App
app = tk.Tk()
app.title("Cryptocurrency Portfolio Manager")

frame = tk.Frame(app)
frame.pack(fill=tk.BOTH, expand=True)

# Label for displaying total value
total_value_label = tk.Label(app, text="", font=('Helvetice', 12, 'bold'))
total_value_label.pack(side=tk.TOP, anchor=tk.E, padx=20, pady=10)

# Buttons
btn_view_coin_prices = tk.Button(app, text="View Coin Prices", command=lambda: switch_view('CoinPrices'))
btn_view_coin_prices.pack(side=tk.TOP, fill=tk.X)

btn_view_wallet = tk.Button(app, text="View Wallet", command=lambda: switch_view('Wallet'))
btn_view_wallet.pack(side=tk.TOP, fill=tk.X)

btn_view_staking = tk.Button(app, text="View Staking", command=lambda: switch_view('Staking'))
btn_view_staking.pack(side=tk.TOP, fill=tk.X)

btn_update_prices = tk.Button(app, text="Update Prices", command=update_coin_prices)

btn_update_wallet = tk.Button(app, text="Update Wallet", command=show_wallet_form)
btn_update_wallet.pack(side=tk.TOP, fill=tk.X)

btn_update_staking = tk.Button(app, text="Update Staking", command=show_staking_form)
btn_update_staking.pack(side=tk.TOP, fill=tk.X)

# Form for adding wallet or staking entries
form_frame = tk.Frame(app)
token_entry = tk.Entry(form_frame)
holdings_entry = tk.Entry(form_frame)
pool_entry = tk.Entry(form_frame)

btn_add_wallet = tk.Button(form_frame, text="Add to Wallet", command=add_wallet_entry)
btn_add_staking = tk.Button(form_frame, text="Add to Staking", command=add_staking_entry)

# Create tables and start the app
create_tables()
app.mainloop()
