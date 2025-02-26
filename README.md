# Telegram Budget Bot

## Features:
- Parsing expense data from the message, including currency, POS and sum.
- Getting up-to-date currency rates to save all data in one main currency.
- User-friendly way to add category to an expense.
- Integration with Google Sheets to save and retrieve expenses data.

## Screenshots


## Commands
- `/start` – Get hello message
- `/last` – Get 5 last expenses entries


## Setup
1. Get your Telegram bot token from [@BotFather](https://t.me/BotFather)
2. Get [CurrencyAPI Key](https://currencyapi.com/docs)
3. Enable the Googel Cloud API and [get credentials](https://developers.google.com/sheets/api/quickstart/python)
4. Add all the tokens and keys to `.env` file as per `.env.example`
5. Install all the dependencies and run bot: `python bot/bot.py`


## Additional Materials:
[Short Presentation about the Bot](https://docs.google.com/presentation/d/1K-jGGov0jMcF4FSwA3KH2HLjgak8jCUogDQswpMcZPo/edit?usp=sharing)

## Made by:
[Cryosteam](https://github.com/cry0steam)
