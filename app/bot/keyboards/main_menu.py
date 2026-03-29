from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


MAIN_MENU_BUTTON_LOOKUP = "Поиск по коду"
MAIN_MENU_BUTTON_REPORT = "Репорт"
MAIN_MENU_BUTTON_HELP = "Помощь"


def build_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=MAIN_MENU_BUTTON_LOOKUP),
                KeyboardButton(text=MAIN_MENU_BUTTON_REPORT),
            ],
            [
                KeyboardButton(text=MAIN_MENU_BUTTON_HELP),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
