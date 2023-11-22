import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from config import Token

from aiohttp import ClientSession

from core import Play, get_stats

FILENAME = 'addition/stats.json'


async def initialize_play(message):
    player_stats = await get_stats(user_id=message.from_user.id, filename=FILENAME)
    player = Play(user_id=message.from_user.id, user_stats=player_stats)
    return player


# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=Token)
# Диспетчер
dp = Dispatcher()


# Этот хэндлер будет срабатывать на команду "/start"
@dp.message(Command(commands=["start"]))
async def process_start_command(message: Message):
    await message.answer(f'Привет, {message.from_user.first_name}!\n'
                         f'Меня зовут Эхо-бот!\n'
                         f'Напиши мне что-нибудь\n'
                         f'Для того, чтобы получить помощь, напиши команду /help')


# Этот хэндлер будет срабатывать на команду "/help"
@dp.message(Command(commands=['help']))
async def process_help_command(message: Message):
    await message.answer(
        'Напиши мне что-нибудь, и в ответ '
        'я пришлю тебе твое сообщение\n'
        'Также мы можем сыграть в игру "Угадай число" Для этого напиши команду /play'
    )


@dp.message(Command("cat"))
async def cmd_cat(message: Message):
    async with ClientSession() as session:
        url = f'https://api.thecatapi.com/v1/images/search'

        async with session.get(url=url) as response:
            cat_json = await response.json()
            cat = cat_json[0]['url']
            await message.answer_photo(cat)


@dp.message(Command("play"))
async def cmd_play(message: Message):
    player = await initialize_play(message=message)
    if not player.in_game:
        await player.play()
        await message.answer(text=f'Мы начали играть! Для отмены напиши /cancel\n'
                                  f'Я загадал число от 1 до 100! Попробуй его угадать))\n'
                                  f'У тебя есть {player.attempts} попыток\n\n'
                                  f'Введи число:\n')
    else:
        await message.answer(text=f'Мы уже в игре) Осталось попыток: {player.attempts}\n'
                                  f'Для отмены напиши /cancel')


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    player_stats = await get_stats(user_id=message.from_user.id, filename=FILENAME)
    if player_stats == {}:
        await message.answer(text=f'У тебя пока нет статистики!')
    else:
        win_percentage = 100 * player_stats["wins"] / player_stats["total_games"]
        await message.answer(text=f'Статистика:\n'
                                  f'Сыграно игр: {player_stats["total_games"]}\n'
                                  f'Победы: {player_stats["wins"]}\n'
                                  f'Процент побед: {win_percentage:.2f}%')
    del player_stats


@dp.message(Command("cancel"))
async def cmd_cancel(message: Message):
    player = await initialize_play(message=message)
    await player.cancel()
    await message.answer(text=f'Жаль, что ты уходишь :(\n'
                              f'Если надумаешь сыграть снова, пиши /play\n'
                              f'Для статистики, напиши /stats\n')
    del player


@dp.message(lambda x: x.text and x.text.isdigit() and 1 <= int(x.text) <= 100)
async def process_numbers_answer(message: Message):
    player = await initialize_play(message=message)
    if player.in_game:
        if player.attempts != 0:
            try_it = await player.try_number(number=int(message.text))
            if try_it == 'more':
                await message.answer(text=f'Загаданное число больше, чем {message.text}, попробуй ввести другое\n'
                                          f'Осталось попыток: {player.attempts}\n\n'
                                          f'Введи число:\n')
            elif try_it == 'less':
                await message.answer(text=f'Загаданное число меньше, чем {message.text}, попробуй ввести другое\n'
                                          f'Осталось попыток: {player.attempts}\n\n'
                                          f'Введи число:\n')
            elif try_it == 'lose':
                await message.answer(text=f'Ты проиграл... Загаданное число: {player.number}\n'
                                          f'Хочешь попробовать снова - введи /play')
            elif try_it == 'won':
                await message.answer(text=f'Ты выиграл!!! Мои поздравления, это действительно {player.number}!\n'
                                          f'Хочешь попробовать снова - введи /play')
        else:
            await player.lose()
            await message.answer(text=f'Ты проиграл... Загаданное число: {player.number}\n'
                                      f'Хочешь попробовать снова - введи /play')
    else:
        await message.answer(text=f'Ты не в игре!\n'
                                  f'Хочешь сыграть - введи /play')


# Этот хэндлер будет срабатывать на любые ваши текстовые сообщения,
# кроме команд "/start" и "/help"
@dp.message()
async def send_echo(message: Message):
    try:
        await message.reply(text=message.text)
    except:
        await message.answer(text="Чё за прикол?!")


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot, polling_timeout=60)


if __name__ == "__main__":
    asyncio.run(main())
