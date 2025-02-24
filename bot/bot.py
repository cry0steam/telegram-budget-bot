import os
import re

import requests
from dotenv import load_dotenv
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
        price = float(price_str)
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


@bot.message_handler()
def send_message(message):
    chat_id = message.chat.id

    try:
        trans_data = parse_message(message.text)

        if trans_data["currency"] != "EUR":
            forex_data = get_rate(trans_data["currency"], trans_data["price"])
            message = f"<b>Store</b>: {trans_data['store']}\n<b>Price in EUR</b>: {forex_data['amount']}\n<b>Currency</b>: EUR "
        else:
            message = f"<b>Store</b>: {trans_data['store']}\n<b>Price</b>: {trans_data['price']}\n<b>Currency</b>: {trans_data['currency']}"

    except Exception as e:
        message = f"The format is not right: {e}"

    bot.send_message(chat_id, message, "HTML")


if __name__ == "__main__":
    bot.polling()
