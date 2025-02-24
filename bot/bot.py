import os
import re

import messages
import requests
from dotenv import load_dotenv
from sheets_integration import append_values
from telebot import TeleBot

load_dotenv()

bot = TeleBot(token=os.getenv("BOT_TOKEN"))

DEFAULT_CURRENCY = "EUR"
CURRENCY_MAP = {
    "USD": [
        "usd",
        "$",
        "dollar",
        "доллар",
    ],
    "KZT": [
        "tenge",
        "kzt",
        "тенге",
    ],
}
RATES_URL = "https://www.amdoren.com/api/currency.php"
TARGET_CUR = "EUR"


def get_rate(currency, amount):
    payload = {
        "api_key": os.getenv("AMDOREN_KEY"),
        "from": currency,
        "to": TARGET_CUR,
        "amount": amount,
    }
    response = requests.get(RATES_URL, params=payload)
    return response.json()


def parse_message(message):
    pattern = re.compile(
        r"^(.*?)\s+(\d+(?:[.,]\d+)?)(?:\s*(\S+))?$",
        re.IGNORECASE,
    )
    try:
        match = pattern.match(message.strip())
    except Exception as e:
        return e

    store = match.group(1).strip()
    price_str = match.group(2).replace(",", ".")
    cur_str = match.group(3)

    try:
        price = round(float(price_str), 2)
    except ValueError:
        return None

    if cur_str is None:
        cur = DEFAULT_CURRENCY
    else:
        cur_found = False
        cur_lower = cur_str.lower().strip()

        for cur_code, synonyms in CURRENCY_MAP.items():
            if cur_lower in synonyms:
                cur = cur_code
                cur_found = True
                break

        if not cur_found:
            cur = cur_str.upper()

    return {"store": store, "price": price, "currency": cur}


def write_transaction(chat_id, trans_data):
    sheet_arr = [
        trans_data["store"],
        trans_data["price"],
        trans_data["currency"],
    ]

    if trans_data["currency"] != "EUR":
        forex_data = get_rate(trans_data["currency"], trans_data["price"])
        message = f"<b>Store</b>: {trans_data['store']}\n<b>Price in EUR</b>: {forex_data['amount']}\n<b>Currency</b>: EUR "
    else:
        append_values(sheet_arr)
        message = f"<b>Store</b>: {trans_data['store']}\n<b>Price</b>: {trans_data['price']}\n<b>Currency</b>: {trans_data['currency']}"

    bot.send_message(chat_id, message, "HTML")


@bot.message_handler(commands=["start"])
def start_message(message):
    chat_id = message.chat.id
    message = messages.WELCOME_MESSAGE
    bot.send_message(chat_id, message)


@bot.message_handler(func=lambda message: True)
def check_message_for_transaction(message):
    chat_id = message.chat.id
    try:
        trans_data = parse_message(message.text)
        write_transaction(chat_id, trans_data)
    except Exception as e:
        message = f"{messages.NOT_TRANSACTION} - {e}"
        bot.send_message(chat_id, message)


if __name__ == "__main__":
    bot.polling()
