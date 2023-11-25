import asyncio
import logging
import json
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InputMediaPhoto, InputMediaAnimation, BufferedInputFile, InputMediaVideo
from aiogram.enums import InputMediaType

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
    player = await initialize_play(message=message)
    await player.update_date(message.date.strftime("%d.%m.%Y, %H:%M:%S"))
    await message.answer(f'Привет, {message.from_user.first_name}!\n'
                         f'Меня зовут Эхо-бот!\n'
                         f'Напиши мне что-нибудь\n'
                         f'Для того, чтобы получить помощь, напиши команду /help')
    del player


# Этот хэндлер будет срабатывать на команду "/help"
@dp.message(Command(commands=['help']))
async def process_help_command(message: Message):
    player = await initialize_play(message=message)
    await player.update_date(message.date.strftime("%d.%m.%Y, %H:%M:%S"))
    await message.answer(
        'Напиши мне что-нибудь, и в ответ '
        'я пришлю тебе твое сообщение\n'
        'Также мы можем сыграть в игру "Угадай число" Для этого напиши команду /play\n'
        'За каждую победу ты будешь получать котокоины, которые можно обменять на котиков))))\n'
        'Котиков можно купить если написать /cat'
    )
    del player


@dp.message(Command("cats"))
async def cmd_cats(message: Message):
    player = await initialize_play(message=message)
    await player.update_date(message.date.strftime("%d.%m.%Y, %H:%M:%S"))
    cats_urls = player.cats_pics[::-1][:10]
    if len(cats_urls) != 0:
        media = []
        for url in cats_urls:
            if url.split('.')[-1] == 'gif':
                pass
                try:
                    async with ClientSession() as session:
                        async with session.get(url=url) as r:
                            d = await r.content.read()
                            group_member = InputMediaVideo(type='video', media=BufferedInputFile(
                                file=d,
                                filename='buff.gif'
                            ))
                            media.append(group_member)
                except:
                    print('Could not')
            else:
                group_member = InputMediaPhoto(type='photo', media=url)
                media.append(group_member)

        await message.answer_media_group(media)
    else:
        await message.answer(text=f'У тебя пока нет Котиков :(\n'
                                  f'Нужны Котокоины))')
    del player


@dp.message(Command("cat"))
async def cmd_cat(message: Message):
    player = await initialize_play(message=message)
    await player.update_date(message.date.strftime("%d.%m.%Y, %H:%M:%S"))
    if player.cats_coins != 0:
        async with ClientSession() as session:
            url = f'https://api.thecatapi.com/v1/images/search'

            async with session.get(url=url) as response:
                cat_json = await response.json()
                cat = cat_json[0]['url']
                await player.buy_cat(cat)
                await message.answer_photo(cat, caption=f'Баланс котокоинов: {player.cats_coins} ')
    else:
        await message.answer(text=f'У тебя пока нет котокоинов((\n'
                                  f'Сыграй со мной в игру, и если выиграешь, получишь котокоин))\n'
                                  f'P.S. пиши /play')
    del player


@dp.message(Command("play"))
async def cmd_play(message: Message):
    player = await initialize_play(message=message)
    await player.update_date(message.date.strftime("%d.%m.%Y, %H:%M:%S"))
    user_data = message.model_dump_json(exclude_none=True)
    user_data = json.loads(user_data)["from_user"]
    await player.update_user_info(user_data)
    if not player.in_game:
        await player.play()
        await message.answer(text=f'Мы начали играть! Для отмены напиши /cancel\n'
                                  f'Я загадал число от 1 до 100! Попробуй его угадать))\n'
                                  f'У тебя есть {player.attempts} попыток\n\n'
                                  f'Введи число:\n')
    else:
        await message.answer(text=f'Мы уже в игре) Осталось попыток: {player.attempts}\n'
                                  f'Для отмены напиши /cancel')
    del player


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    player = await initialize_play(message=message)
    await player.update_date(message.date.strftime("%d.%m.%Y, %H:%M:%S"))
    player_stats = await get_stats(user_id=message.from_user.id, filename=FILENAME)
    if player_stats == {}:
        await message.answer(text=f'У тебя пока нет статистики!')
    else:
        win_percentage = 100 * player_stats["wins"] / player_stats["total_games"]
        await message.answer(text=f'Статистика:\n\n'
                                  f'Котокоины: {player_stats["cats_coins"]}\n'
                                  f'Сыграно игр: {player_stats["total_games"]}\n'
                                  f'Победы: {player_stats["wins"]}\n'
                                  f'Процент побед: {win_percentage:.0f}%')
    del player_stats
    del player


@dp.message(Command("cancel"))
async def cmd_cancel(message: Message):
    player = await initialize_play(message=message)
    await player.update_date(message.date.strftime("%d.%m.%Y, %H:%M:%S"))
    await player.cancel()
    await message.answer(text=f'Жаль, что ты уходишь :(\n'
                              f'Если надумаешь сыграть снова, пиши /play\n'
                              f'Для статистики, напиши /stats\n')
    del player


@dp.message(lambda x: x.text and x.text.isdigit() and 1 <= int(x.text) <= 100)
async def process_numbers_answer(message: Message):
    player = await initialize_play(message=message)
    await player.update_date(message.date.strftime("%d.%m.%Y, %H:%M:%S"))
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
    del player


# Этот хэндлер будет срабатывать на любые ваши текстовые сообщения,
# кроме команд "/start" и "/help"
@dp.message()
async def send_echo(message: Message):
    try:
        await message.reply(text=message.text)
    except Exception as e:
        await message.answer(text="Чё за прикол?!")


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot, polling_timeout=60)


if __name__ == "__main__":
    asyncio.run(main())
