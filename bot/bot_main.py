import io
import logging
import os
import re
from datetime import date, datetime
from http import HTTPStatus

import matplotlib.pyplot as plt
import pandas as pd
import requests
from dotenv import load_dotenv
from telebot import TeleBot, types
from telebot.util import quick_markup

import keyboards
import expense_viz
import database
import messages
from categories import EXPENSE_CATEGORIES
from exceptions import (
    NoApiResponseError,
    NoCredentialsError,
    ServerResponseError,
)

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s',
    filename='main.log',
    filemode='a',
)

bot = TeleBot(token=os.getenv('BOT_TOKEN'))

TRANS_REGEX = r'^(\d+(?:[.,]\d+)?)\s+(.*?)(?:\s+\(([^)]+)\))?$'
DEFAULT_CURRENCY = 'EUR'
TARGET_CUR = 'EUR'
RATES_URL = 'https://api.currencyapi.com/v3/latest'
CURR_URL = 'https://api.currencyapi.com/v3/currencies'

data_to_write = {}

# Dictionary to store budget setting state for users
budget_state = {}


@bot.message_handler(commands=['start'])
def start_message(message):
    chat_id = message.chat.id

    message = messages.WELCOME_MESSAGE
    bot.send_message(chat_id, message)


@bot.message_handler(commands=['last'])
def last_expenses(message):
    chat_id = message.chat.id
    try:
        data = database.get_last_expenses(10)
        columns = [
            'Date',
            'User',
            'Store',
            'Amount',
            'Currency',
            'Amount EUR',
            'Category',
        ]
        buf = expense_viz.create_expense_table(data, columns, 'Last 10 Expenses')
        bot.send_photo(chat_id, buf, caption='Here are your last 10 expenses:')

    except Exception as e:
        logging.exception(
            f"""Error in last_expenses handler for chat_id={message.chat.id}.
            Error = {e}"""
        )
        bot.send_message(
            message.chat.id,
            'An error occurred while getting the last expenses.',
        )


@bot.message_handler(commands=['actual'])
def actual_expenses(message):
    chat_id = message.chat.id
    try:
        data, total, travel_amount = database.get_current_month_expenses()
        columns = ['Category', 'Total Amount (EUR)']
        buf = expense_viz.create_expense_table(
            data, 
            columns, 
            'Current Month Expenses',
            include_total=True,
            total=total,
            travel_data=travel_amount
        )
        bot.send_photo(chat_id, buf, caption='Here are your current month expenses by category:')

    except Exception as e:
        logging.exception(
            f"""Error in actual_expenses handler for chat_id={message.chat.id}.
            Error = {e}"""
        )
        bot.send_message(
            message.chat.id,
            'An error occurred while getting the current month expenses.',
        )


@bot.message_handler(commands=['top'])
def top_expenses(message):
    chat_id = message.chat.id
    try:
        data = database.get_top_expenses_per_category()
        columns = ['Category', 'User', 'Store', 'Amount (EUR)']
        buf = expense_viz.create_expense_table(data, columns, 'Top 5 Expenses per Category')
        bot.send_photo(chat_id, buf, caption='Here are top 5 expenses per category:')

    except Exception as e:
        logging.exception(
            f"""Error in top_expenses handler for chat_id={message.chat.id}.
            Error = {e}"""
        )
        bot.send_message(
            message.chat.id,
            'An error occurred while getting the top expenses.',
        )


@bot.message_handler(commands=['add_budget'])
def start_budget_setup(message):
    """Start the budget setup process."""
    chat_id = message.chat.id
    
    # Initialize state for this user
    budget_state[chat_id] = {
        'month': None,
        'current_category': None,
        'budgets': {}
    }
    
    markup = keyboards.get_stop_markup()
    msg = bot.send_message(
        chat_id,
        "Please enter the month (1-12) for which you want to set the budget:",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_month)


def process_month(message):
    """Process the month input and start category budget setup."""
    chat_id = message.chat.id
    
    try:
        month = int(message.text)
        if 1 <= month <= 12:
            budget_state[chat_id]['month'] = month
            start_category_budget(chat_id)
        else:
            markup = keyboards.get_stop_markup()
            msg = bot.send_message(
                chat_id,
                "Please enter a valid month (1-12):",
                reply_markup=markup
            )
            bot.register_next_step_handler(msg, process_month)
    except ValueError:
        markup = keyboards.get_stop_markup()
        msg = bot.send_message(
            chat_id,
            "Please enter a valid month number (1-12):",
            reply_markup=markup
        )
        bot.register_next_step_handler(msg, process_month)


def start_category_budget(chat_id):
    """Start the process of setting budget for each category."""
    state = budget_state[chat_id]
    
    # Find the next category that needs a budget
    next_category = None
    for category in EXPENSE_CATEGORIES:
        if category not in state['budgets']:
            next_category = category
            break
    
    if next_category:
        state['current_category'] = next_category
        markup = keyboards.get_stop_markup()
        msg = bot.send_message(
            chat_id,
            f"Enter budget amount in EUR for {next_category}:",
            reply_markup=markup
        )
        bot.register_next_step_handler(msg, process_category_budget)
    else:
        # All categories are done
        save_budgets(chat_id)


def process_category_budget(message):
    """Process the budget amount for a category."""
    chat_id = message.chat.id
    state = budget_state[chat_id]
    
    try:
        amount = float(message.text)
        if amount >= 0:
            state['budgets'][state['current_category']] = round(amount, 2)
            start_category_budget(chat_id)  # Move to next category
        else:
            markup = keyboards.get_stop_markup()
            msg = bot.send_message(
                chat_id,
                "Please enter a non-negative amount:",
                reply_markup=markup
            )
            bot.register_next_step_handler(msg, process_category_budget)
    except ValueError:
        markup = keyboards.get_stop_markup()
        msg = bot.send_message(
            chat_id,
            "Please enter a valid number:",
            reply_markup=markup
        )
        bot.register_next_step_handler(msg, process_category_budget)


def save_budgets(chat_id):
    """Save all budget targets to the database."""
    state = budget_state[chat_id]
    success = True
    
    for category, amount in state['budgets'].items():
        if not database.add_budget(state['month'], category, amount):
            success = False
            break
    
    if success:
        bot.send_message(
            chat_id,
            f"Budget targets for month {state['month']} have been saved successfully!",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        bot.send_message(
            chat_id,
            "An error occurred while saving the budget targets.",
            reply_markup=types.ReplyKeyboardRemove()
        )
    
    # Clean up state
    budget_state.pop(chat_id, None)


@bot.callback_query_handler(func=lambda call: call.data == 'stop_budget')
def handle_budget_stop(call):
    """Handle the stop button press during budget setup."""
    chat_id = call.message.chat.id
    
    # Clean up state
    budget_state.pop(chat_id, None)
    
    bot.answer_callback_query(call.id)
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    bot.send_message(
        chat_id,
        "Budget setup has been cancelled.",
        reply_markup=types.ReplyKeyboardRemove()
    )


@bot.message_handler(regexp=TRANS_REGEX)
def check_message_for_transaction(message):
    chat_id = message.chat.id
    trans_data = parse_message(message.text)
    try:
        if trans_data['currency'] == 'EUR':
            trans_data['sum_in_eur'] = trans_data['sum']
            write_transaction(message, trans_data)
        elif trans_data['currency'] not in get_currency_codes():
            check_currency_code(message, trans_data)
        else:
            sum_in_eur = get_rate(trans_data['currency']) * trans_data['sum']
            trans_data['sum_in_eur'] = round(sum_in_eur, 2)
            write_transaction(message, trans_data)
    except Exception as err:
        bot.send_message(chat_id, err)


@bot.message_handler(func=lambda message: True)
def send_basic_message(message):
    bot.send_message(message.chat.id, messages.NOT_TRANSACTION)


@bot.message_handler(commands=['get_budget'])
def get_budget(message):
    """Send budget comparison table to the user."""
    chat_id = message.chat.id
    try:
        data = database.get_budget_comparison()
        if not data:
            bot.send_message(
                chat_id,
                'No budget or expense data found for this year.'
            )
            return

        buf = expense_viz.create_budget_table(data)
        if buf:
            bot.send_photo(
                chat_id,
                buf,
                caption='Budget vs Actual Expenses Comparison'
            )
        else:
            bot.send_message(
                chat_id,
                'No data to display.'
            )

    except Exception as e:
        logging.exception(
            f"""Error in get_budget handler for chat_id={message.chat.id}.
            Error = {e}"""
        )
        bot.send_message(
            message.chat.id,
            'An error occurred while getting the budget comparison.',
        )


def setup_bot_commands():
    """Setup bot commands in the Bot Menu"""
    commands = [
        types.BotCommand(command='start', description='Start the bot'),
        types.BotCommand(command='last', description='Show last 10 expenses'),
        types.BotCommand(command='actual', description='Get actual month expenses'),
        types.BotCommand(command='top', description='Show top 5 expenses per category'),
        types.BotCommand(command='add_budget', description='Set budget targets for a month'),
        types.BotCommand(command='get_budget', description='Show budget vs actual expenses'),
    ]
    bot.set_my_commands(commands)


def parse_message(message):
    """Parse message text to create expanse data."""
    pattern = re.compile(
        TRANS_REGEX,
        re.IGNORECASE,
    )
    match = pattern.match(message.strip())

    amount_str = match.group(1).replace(',', '.')
    pos = match.group(2).strip()
    cur_str = match.group(3)

    try:
        amount = round(float(amount_str), 2)
    except ValueError:
        return None

    if cur_str is None:
        cur = DEFAULT_CURRENCY
    else:
        cur = cur_str.upper().strip()

    return {'pos': pos, 'sum': amount, 'currency': cur}


def check_currency_code(message, trans_data):
    """Check that currency code is valid, if not - ask for a valid one"""
    chat_id = message.chat.id
    trans_data['currency'] = message.text.upper().strip()
    if message.text == 'stop':
        bot.send_message(chat_id, messages.STOP_INPUT)
    elif trans_data['currency'] not in get_currency_codes():
        msg = bot.send_message(chat_id, messages.UNKNOWN_CURRENCY)
        bot.register_next_step_handler(
            msg,
            check_currency_code,
            trans_data,
        )
    else:
        sum_in_eur = get_rate(trans_data['currency']) * trans_data['sum']
        trans_data['sum_in_eur'] = round(sum_in_eur, 2)
        write_transaction(message, trans_data)


def write_transaction(message, trans_data):
    """Write expense data DB"""
    chat_id = message.chat.id
    if 'category' not in trans_data:
        cat_msg = bot.send_message(
            chat_id,
            messages.CATEGORY,
            reply_markup=keyboards.category_keyboard(),
        )
        bot.register_next_step_handler(cat_msg, get_category, trans_data)
    else:
        data_to_write[chat_id] = trans_data
        message = f'<b>Store</b>: {trans_data["pos"]}\
                    <b>Price</b>: {trans_data["sum"]}\
                    <b>Currency</b>: {trans_data["currency"]}\
                    <b>Sum in EUR</b>: {trans_data["sum_in_eur"]}\
                    <b>Category</b>: {trans_data["category"]}'

        markup = quick_markup(
            {
                'Yes': {'callback_data': 'approve'},
                'No': {'callback_data': 'decline'},
            },
            row_width=2,
        )

        bot.send_message(
            chat_id,
            message,
            'HTML',
            reply_markup=types.ReplyKeyboardRemove(),
        )
        bot.send_message(
            chat_id,
            'Is everything correct?',
            'HTML',
            reply_markup=markup,
        )


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """Handle callback action."""
    chat_id = call.message.chat.id
    user = call.from_user
    trans_data = data_to_write.get(chat_id)
    if call.data == 'decline':
        bot.answer_callback_query(call.id, 'Declined')
        trans_data.pop(chat_id, None)
        bot.delete_message(chat_id, call.message.id)
        bot.send_message(
            chat_id,
            messages.TRANSACTION_DELETED,
        )
    if call.data == 'approve':
        trans_date = date.today()
        database.add_expense(
            trans_date.strftime('%d/%m/%Y'),
            user.username,
            trans_data['pos'],
            trans_data['sum'],
            trans_data['currency'],
            trans_data['sum_in_eur'],
            trans_data['category'],
        )
        data_to_write.pop(chat_id, None)
        bot.answer_callback_query(call.id, 'Approved')
        bot.delete_message(chat_id, call.message.id)
        bot.send_message(
            chat_id,
            messages.TRANSACTION_SAVED,
        )


def get_category(message, trans_data):
    """Add category to expanse data."""
    trans_data['category'] = message.text
    write_transaction(message, trans_data)


def get_currency_codes() -> list[str]:
    """Get list of currency codes from CurrencyAPI."""
    payload = {'apikey': os.getenv('CURRENCYAPI_KEY')}
    try:
        response = requests.get(CURR_URL, params=payload)
    except Exception:
        raise NoApiResponseError('No response from API')

    if response.status_code != HTTPStatus.OK:
        raise ServerResponseError(
            f'Response code is different from 200: {response.status_code}'
        )

    res = response.json()['data']
    list_of_currencies = list(res.keys())
    return list_of_currencies


def get_rate(currency: str) -> float:
    """Get conversion rate for provided currency code."""
    payload = {
        'apikey': os.getenv('CURRENCYAPI_KEY'),
        'base_currency': currency,
        'currencies': TARGET_CUR,
    }
    try:
        response = requests.get(RATES_URL, params=payload)
    except Exception:
        raise NoApiResponseError('No response from API')

    if response.status_code != HTTPStatus.OK:
        raise ServerResponseError(
            f'Response code is different from 200: {response.status_code}'
        )

    conversion_rate = response.json()['data']['EUR']['value']
    return conversion_rate


def check_tokens():
    """Check for all required tokens"""
    if not os.getenv('BOT_TOKEN') or not os.getenv('CURRENCYAPI_KEY'):
        logging.critical('Not all required tokens are present.')
        return False
    return True


def main():
    if not check_tokens():
        raise NoCredentialsError

    database.init_db()
    setup_bot_commands()

    bot.polling(skip_pending=True)


if __name__ == '__main__':
    main()
