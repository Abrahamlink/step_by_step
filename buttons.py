from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def deviate_by_pairs(lst: list, n: int) -> list:
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


async def make_keyboard(commands: list[str]) -> ReplyKeyboardMarkup:
    buttons = [KeyboardButton(text=f'/{command}') for command in commands]
    buttons = list(deviate_by_pairs(buttons, 2))
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)
    return keyboard
