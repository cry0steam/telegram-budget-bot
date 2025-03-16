from telebot import types


def category_keyboard():
    """Keyboard with categories markup."""
    keys = ['Grocery', 'Bills', 'Commute', 'Subs', 'Misc', 'Reserve']
    markup = types.ReplyKeyboardMarkup(row_width=3)
    row = [types.KeyboardButton(x) for x in keys[:3]]
    markup.add(*row)
    row = [types.KeyboardButton(x) for x in keys[3:6]]
    markup.add(*row)
    return markup
