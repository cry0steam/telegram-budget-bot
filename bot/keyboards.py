from telebot import types
from categories import EXPENSE_CATEGORIES


def category_keyboard():
    """Keyboard with categories markup."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [types.KeyboardButton(cat) for cat in EXPENSE_CATEGORIES]
    # Add buttons in rows of 3
    markup.add(*buttons)
    return markup


def get_stop_markup():
    """Create an inline keyboard with a stop button."""
    markup = types.InlineKeyboardMarkup()
    stop_btn = types.InlineKeyboardButton('Stop', callback_data='stop_budget')
    markup.add(stop_btn)
    return markup
