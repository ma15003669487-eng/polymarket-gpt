# Polymarket Arbitrage Bot

This project implements a configurable arbitrage scanner and trader for Polymarket that can:

1. Scan markets for opportunities where the cost of buying both **Yes** and **No** is below 1 USDC.
2. Send Telegram alerts with deal details.
3. Wait for manual confirmation or execute automatically.
4. Place trades via the Polymarket CLOB API and report results.

## Features
- **Wallet management**: generate a new private key or load from an environment variable.
- **Market scanning**: query the Polymarket CLOB API for best ask prices on Yes/No outcomes.
- **Arbitrage filter**: configurable maximum combined price (default `0.99`) and minimum volume thresholds.
- **Telegram push**: send rich messages with inline confirm/skip links plus structured logging.
- **Manual or automatic trades**: switch between dry-run, manual confirmation, or fully automatic execution.

## Quick start
1. Create and activate a Python 3.11+ environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables (see `.env.example`).

4. Run a scan:

```bash
python app.py --auto false --poll-interval 30
```

## Environment variables
- `POLYMARKET_API_BASE` (optional): override the CLOB API base URL. Default: `https://clob.polymarket.com`.
- `POLYMARKET_API_KEY`: API key for placing orders.
- `POLYMARKET_API_SECRET`: Secret used to sign order payloads.
- `PRIVATE_KEY`: Hex-encoded private key for the trading wallet. If absent, a new key will be generated and printed.
- `TELEGRAM_BOT_TOKEN`: Telegram bot token for notifications.
- `TELEGRAM_CHAT_ID`: Chat or channel ID that will receive notifications.

## Safety notes
- Always run in `--dry-run` mode first to validate connectivity.
- Keep your private key and API secrets outside of version control.
- The bot does not store secrets on disk; they are read from the environment at runtime.

## Project layout
- `app.py`: Entry point that wires together the scanner, notifier, and trader.
- `bot/config.py`: Environment loading and validation helpers.
- `bot/polymarket_client.py`: HTTP client for market discovery and order placement.
- `bot/arbitrage.py`: Core arbitrage scanning and trading loop.
- `bot/telegram_notifier.py`: Minimal Telegram messaging helper.
- `bot/trader.py`: Wallet handling and trade execution logic.

## Testing
- Lint-free execution and import validation can be checked with:

```bash
python -m compileall .
```

Networked end-to-end trading requires funded accounts and real API credentials.
