from telebot import types
from categories import EXPENSE_CATEGORIES


def category_keyboard():
    """Keyboard with categories markup."""
    keys = EXPENSE_CATEGORIES
    markup = types.ReplyKeyboardMarkup(row_width=3)
    row = [types.KeyboardButton(x) for x in keys[:3]]
    markup.add(*row)
    row = [types.KeyboardButton(x) for x in keys[3:6]]
    markup.add(*row)
    return markup


def get_stop_markup():
    """Create an inline keyboard with a stop button."""
    markup = types.InlineKeyboardMarkup()
    stop_btn = types.InlineKeyboardButton('Stop', callback_data='stop_budget')
    markup.add(stop_btn)
    return markup
