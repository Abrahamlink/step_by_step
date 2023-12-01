from aiogram.types import Message
from aiogram.filters import BaseFilter
from core import initialize_play


class IsAdmin(BaseFilter):
    def __init__(self, admin_ids: list[int]) -> None:
        self.admin_ids = admin_ids

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids


class GameFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool | dict:
        if message.text and message.text.isdigit():
            player = await initialize_play(message=message)
            if player.rules.get('choice_range')[0] <= int(message.text) <= player.rules.get('choice_range')[1]:
                return {'player': player}
        return False


async def game_filter(message) -> bool | dict:
    if message.text and message.text.isdigit():
        player = await initialize_play(message=message)
        if player.rules.get('choice_range')[0] <= int(message.text) <= player.rules.get('choice_range')[1]:
            return {'player': player}
        else:
            return False


# balovstvo
def custom_filter(digits: list):
    return sum([x for x in digits if type(x) == int and x % 7 == 0]) <= 83


def custom_filter_from_solutions(some_list):
    return sum(filter(lambda x: isinstance(x, int) and not x % 7, some_list)) <= 83


anonymous_filter = lambda x: len(x.lower().split("я")) >= 23
anonymous_filter_2 = lambda x: x.lower().count('я') >= 23
