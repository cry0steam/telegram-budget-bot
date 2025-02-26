import logging
import os
import re
from datetime import date
from http import HTTPStatus

import messages
import requests
from dotenv import load_dotenv
from exceptions import (
    NoApiResponseError,
    NoCredentialsError,
    ServerResponseError,
)
from sheets_integration import append_values, get_last_values
from telebot import TeleBot, types
from telebot.util import quick_markup

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s, %(levelname)s, %(message)s",
    filename="main.log",
    filemode="a",
)

bot = TeleBot(token=os.getenv("BOT_TOKEN"))

TRANS_REGEX = r"^(.*?)\s+(\d+(?:[.,]\d+)?)(?:\s*(\S+))?$"
DEFAULT_CURRENCY = "EUR"
TARGET_CUR = "EUR"
RATES_URL = "https://api.currencyapi.com/v3/latest"
CURR_URL = "https://api.currencyapi.com/v3/currencies"

data_to_write = {}


@bot.message_handler(commands=["start"])
def start_message(message):
    chat_id = message.chat.id

    c1 = types.BotCommand(command="start", description="start the bot")
    c2 = types.BotCommand(command="last", description="last 5 expenses")
    bot.set_my_commands(commands=[c1, c2])

    message = messages.WELCOME_MESSAGE
    bot.send_message(chat_id, message)


@bot.message_handler(commands=["last"])
def last_expenses(message):
    chat_id = message.chat.id
    try:
        data = get_last_values(5)

        lines = []
        header = "<b>Date    Store    Sum    Currency    Sum in EUR    Category</b>"
        lines.append(header)

        for row in data:
            date, store, sum, currency, sum_in_eur, category = row
            line = f"{date} -- {store} -- {sum} -- {currency} -- {sum_in_eur} -- {category}"
            lines.append(line)

        message = "\n".join(lines)
        bot.send_message(chat_id, message, "HTML")
    except Exception as e:
        logging.exception(
            f"Error in last_expenses handler for chat_id={message.chat.id}. Error = {e}"
        )
        bot.send_message(
            message.chat.id,
            "An error occurred while getting the last expenses.",
        )


@bot.message_handler(regexp=TRANS_REGEX)
def check_message_for_transaction(message):
    chat_id = message.chat.id
    trans_data = parse_message(message.text)
    try:
        if trans_data["currency"] == "EUR":
            trans_data["sum_in_eur"] = trans_data["sum"]
            write_transaction(message, trans_data)
        elif trans_data["currency"] not in get_currency_codes():
            check_currency_code(message, trans_data)
        else:
            sum_in_eur = get_rate(trans_data["currency"]) * trans_data["sum"]
            trans_data["sum_in_eur"] = round(sum_in_eur, 2)
            write_transaction(message, trans_data)
    except Exception as err:
        bot.send_message(chat_id, err)


@bot.message_handler(func=lambda message: True)
def send_basic_message(message):
    bot.send_message(message.chat.id, messages.NOT_TRANSACTION)


def parse_message(message):
    pattern = re.compile(
        TRANS_REGEX,
        re.IGNORECASE,
    )
    match = pattern.match(message.strip())

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
        cur = cur_str.upper().strip()

    return {"pos": store, "sum": price, "currency": cur}


def check_currency_code(message, trans_data):
    chat_id = message.chat.id
    trans_data["currency"] = message.text.upper().strip()
    if message.text == "stop":
        bot.send_message(chat_id, messages.STOP_INPUT)
    elif trans_data["currency"] not in get_currency_codes():
        msg = bot.send_message(chat_id, messages.UNKNOWN_CURRENCY)
        bot.register_next_step_handler(
            msg,
            check_currency_code,
            trans_data,
        )
    else:
        sum_in_eur = get_rate(trans_data["currency"]) * trans_data["sum"]
        trans_data["sum_in_eur"] = round(sum_in_eur, 2)
        write_transaction(message, trans_data)


def write_transaction(message, trans_data):
    chat_id = message.chat.id
    if "category" not in trans_data:
        cat_msg = bot.send_message(
            chat_id,
            messages.CATEGORY,
            reply_markup=keyboard(),
        )
        bot.register_next_step_handler(cat_msg, get_category, trans_data)
    else:
        data_to_write[chat_id] = trans_data
        message = f"<b>Store</b>: {trans_data['pos']}\
                    <b>Price</b>: {trans_data['sum']}\
                    <b>Currency</b>: {trans_data['currency']}\
                    <b>Sum in EUR</b>: {trans_data['sum_in_eur']}\
                    <b>Category</b>: {trans_data['category']}"

        markup = quick_markup(
            {
                "Yes": {"callback_data": "approve"},
                "No": {"callback_data": "decline"},
            },
            row_width=2,
        )

        bot.send_message(
            chat_id,
            message,
            "HTML",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        bot.send_message(
            chat_id,
            "Is everything correct?",
            "HTML",
            reply_markup=markup,
        )


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    trans_data = data_to_write.get(chat_id)
    if call.data == "decline":
        bot.answer_callback_query(call.id, "Declined")
        trans_data.pop(chat_id, None)
        bot.delete_message(chat_id, call.message.id)
        bot.send_message(
            chat_id,
            messages.TRANSACTION_DELETED,
        )
    if call.data == "approve":
        trans_date = date.today()
        sheet_arr = [
            trans_date.strftime("%d/%m/%Y"),
            trans_data["pos"],
            trans_data["sum"],
            trans_data["currency"],
            trans_data["sum_in_eur"],
            trans_data["category"],
        ]
        append_values(sheet_arr)
        trans_data.pop(chat_id, None)
        bot.answer_callback_query(call.id, "Approved")
        bot.delete_message(chat_id, call.message.id)
        bot.send_message(
            chat_id,
            messages.TRANSACTION_SAVED,
        )


def get_category(message, trans_data):
    trans_data["category"] = message.text
    write_transaction(message, trans_data)


def get_currency_codes():
    payload = {"apikey": os.getenv("CURRENCYAPI_KEY")}
    try:
        response = requests.get(CURR_URL, params=payload)
    except Exception:
        raise NoApiResponseError("No response from API")

    if response.status_code != HTTPStatus.OK:
        raise ServerResponseError(
            f"Response code is different from 200: {response.status_code}"
        )

    res = response.json()["data"]
    list_of_currencies = list(res.keys())
    return list_of_currencies


def get_rate(currency):
    payload = {
        "apikey": os.getenv("CURRENCYAPI_KEY"),
        "base_currency": currency,
        "currencies": TARGET_CUR,
    }
    try:
        response = requests.get(RATES_URL, params=payload)
    except Exception:
        raise NoApiResponseError("No response from API")

    if response.status_code != HTTPStatus.OK:
        raise ServerResponseError(
            f"Response code is different from 200: {response.status_code}"
        )

    conversion_rate = response.json()["data"]["EUR"]["value"]
    return conversion_rate


def keyboard():
    keys = ["Grocery", "Bills", "Commute", "Subs", "Misc", "Reserve"]
    markup = types.ReplyKeyboardMarkup(row_width=3)
    row = [types.KeyboardButton(x) for x in keys[:3]]
    markup.add(*row)
    row = [types.KeyboardButton(x) for x in keys[3:6]]
    markup.add(*row)
    return markup


def check_tokens():
    """Check for all required tokens"""
    if (
        not os.getenv("BOT_TOKEN")
        or not os.getenv("SHEET_ID")
        or not os.getenv("CURRENCYAPI_KEY")
    ):
        logging.critical("Not all required tokens are present.")
        return False
    return True


if __name__ == "__main__":
    if not check_tokens():
        raise NoCredentialsError

    bot.polling(skip_pending=True)
