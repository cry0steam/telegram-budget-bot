# Telegram Budget Bot

## Features:
- Parsing expense data from messages, including currency, POS, and total amount.
- Retrieving up-to-date currency exchange rates to store all data in a single currency.
- Providing a user-friendly way to assign categories to expenses.
- Integration with Google Sheets to save and retrieve expense data.
- Basic tests and logging.

## Screenshots
<div align="left">
<img src="https://i.postimg.cc/4xBTZKfm/2025-02-26-22-20-31.jpg" align="center" style="width: 20%" />
<img src="https://i.postimg.cc/jSsrG6rp/2025-02-26-22-20-34.jpg" align="center" style="width: 20%" />
<img src="https://i.postimg.cc/B61WxMxK/2025-02-26-22-20-37.jpg" align="center" style="width: 20%" />
</div>

## Commands
- `/start` – Get *hello* message
- `/last` – Get last 5 expenses entries


## Setup
1. Get your Telegram bot token from [@BotFather](https://t.me/BotFather)
2. Get [CurrencyAPI Key](https://currencyapi.com/docs)
3. Enable the Google Cloud API and [get credentials](https://developers.google.com/sheets/api/quickstart/python)
4. Add all the tokens and keys to `.env` file as per `.env.example`
5. Install all the dependencies and run bot: `python bot/bot_main.py`


## Additional Materials:
[Short Presentation about the Bot](https://docs.google.com/presentation/d/1K-jGGov0jMcF4FSwA3KH2HLjgak8jCUogDQswpMcZPo/edit?usp=sharing)

## Made by:
[Cryosteam](https://github.com/cry0steam)
