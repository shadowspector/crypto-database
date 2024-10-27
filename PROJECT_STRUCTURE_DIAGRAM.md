```mermaid
graph TD
    A[app.py] --> B[config.py]
    A --> C[Database: crypto_portfolio.db]
    A --> D[Routes]
    A --> E[Services]
    A --> F[Templates]
    A --> G[Static Files]
    A --> H[Utils]

    D --> D1[coin_routes.py]
    D --> D2[wallet_routes.py]

    E --> E1[database.py]
    E --> E2[wallet_service.py]
    E --> E3[coin_price_service.py]
    E --> E4[moralis_service.py]
    E --> E5[coin_gecko_service.py]

    F --> F1[index.html]
    F --> F2[wallet.html]
    F --> F3[coin_prices.html]
    F --> F4[staking.html]
    F --> F5[farming.html]
    F --> F6[leveraged_farming.html]
    F --> F7[lending_borrowing.html]

    G --> G1[style.css]

    H --> H1[logging_config.py]
    H --> H2[response.py]

    I[Models] --> I1[coin.py]
    I --> I2[wallet.py]

    A --> I

    E2 --> E1
    E2 --> E4
    E3 --> E1
    E3 --> E5

    D1 --> E3
    D2 --> E2

    subgraph Key Functionalities
        J[Wallet Management]
        K[Coin Price Management]
        L[Blockchain Data Updates]
        M[Database Operations]
        N[Logging]
    end

    J --> E2
    J --> D2
    K --> E3
    K --> E5
    K --> D1
    L --> E4
    L --> E2
    M --> E1
    N --> H1
```mermaid