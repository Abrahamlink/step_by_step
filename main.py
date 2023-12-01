import asyncio
import logging
import json
import os
import time
import random

from aiogram.enums import ParseMode
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InputMediaPhoto, BufferedInputFile, InputMediaVideo

from config import Token

from aiohttp import ClientSession

from core import get_stats, initialize_play, Play, get_cat, get_fact
from filters import GameFilter, IsAdmin
from telegram_bots.buttons import make_keyboard

FILENAME = 'addition/stats.json'
admin_ids: list[int] = [1241547832]
fact_modes = ['trivial', 'math', 'date', 'year']
commands = ['play', 'cat', 'my_stats', 'help', *fact_modes]

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=Token)
# Диспетчер
dp = Dispatcher()


# Этот хэндлер будет срабатывать на команду "/start"
@dp.message(Command(commands=["start"]))
async def process_start_command(message: Message):
    await initialize_play(message=message)
    keyboard = await make_keyboard(commands)
    await message.answer(f'Привет, {message.from_user.first_name}!\n'
                         f'Я игровой бот, раздающий котиков и интересные факты)\n'
                         f'Напиши мне что-нибудь!\n'
                         f'Для того, чтобы получить помощь, напиши команду /help', reply_markup=keyboard)


# Этот хэндлер будет срабатывать на команду "/help"
@dp.message(Command(commands=['help']))
async def process_help_command(message: Message):
    await initialize_play(message=message)
    try:
        path = os.path.join(os.path.dirname(__file__), 'addition/docs.txt')
        text = open(path, 'r').read()

        await message.answer(text, parse_mode=ParseMode.HTML)
    except Exception as ex:
        print(ex)
        await message.answer(
            'Напиши мне что-нибудь, и в ответ '
            'я пришлю тебе твое сообщение\n'
            'Также мы можем сыграть в игру "Угадай число" Для этого напиши команду /play\n'
            'За каждую победу ты будешь получать котокоины, которые можно обменять на котиков))))\n'
            'Котиков можно купить если написать /cat'
        )


@dp.message(Command("cats"))
async def cmd_cats(message: Message):
    player = await initialize_play(message=message)
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


@dp.message(Command("cats_gifs"))
async def cmd_cats_gifs(message: Message):
    player = await initialize_play(message=message)
    cats_urls = [pic for pic in player.cats_pics if pic.split('.')[-1] == 'gif'][::-1][:10]
    if len(cats_urls) != 0:
        for url in cats_urls:
            await message.answer_animation(animation=url)
    else:
        await message.answer(text=f'У тебя пока нет гифок с котиками :(\n'
                                  f'Нужны Котокоины и удача))')
    del player


@dp.message(Command("all_cats"))
async def cmd_all_cats(message: Message):
    player = await initialize_play(message=message)
    cats_urls = [pic for pic in player.cats_pics if pic.split('.')[-1] != 'gif']
    if len(cats_urls) != 0:
        for i in range(0, int(len(cats_urls) / 10) + 1):
            media = []
            for url in cats_urls[i * 10:(i * 10) + 10]:
                group_member = InputMediaPhoto(type='photo', media=url)
                media.append(group_member)
            await message.answer_media_group(media)
            time.sleep(1)
    else:
        await message.answer(text=f'У тебя пока нет Котиков :(\n'
                                  f'Нужны Котокоины))')
    del player


@dp.message(Command("cat"))
async def cmd_cat(message: Message):
    player = await initialize_play(message=message)
    if player.cats_coins != 0:
        cat = await get_cat(player)
        text = await get_fact(len(player.cats_pics), player.rules['fact_mode'])
        if cat:
            if not text:
                text = f'Баланс котокоинов: {player.cats_coins}'
            else:
                text = f'Интересный факт о числе {len(player.cats_pics)}: {text}\n\n' \
                       f'Баланс котокоинов: {player.cats_coins}'
            if cat.split('.')[-1] == 'gif':
                await message.answer_animation(animation=cat, caption=text)
            else:
                await message.answer_photo(photo=cat, caption=text)
        else:
            await message.answer(text=f'Ой, какие-то неполадки...\n'
                                      f'Попробуй снова, если не получится, '
                                      f'я всё исправлю позже)\n'
                                      f'Твой котокоин я не заберу, не бойся, сладкий)\n')
    else:
        await message.answer(text=f'У тебя пока нет котокоинов((\n'
                                  f'Сыграй со мной в игру, и если выиграешь, получишь котокоин))\n'
                                  f'P.S. пиши /play')
    del player


@dp.message(Command("set_attempts", "sa"))
async def cmd_rules_attempts(message: Message):
    player = await initialize_play(message=message)
    if message.text.split(' ')[-1].isdigit() and int(message.text.split(' ')[-1]) >= 1:
        attempts = message.text.split(' ')[-1]
        rules = player.rules
        rules['attempts'] = int(attempts)
        await player.update_rules(rules)
        await message.answer(text=f'У тебя установлено количество попыток: {attempts}')
    else:
        await message.answer(text=f'Ты допустил ошибку..)\nНичего страшного, '
                                  f'возможно ты передал не число или оно оказалось меньше 1, попробуй еще раз\n'
                                  f'Вот тебе пример:\n\n')
        await message.answer(text=f'<code>/sa 10</code>', parse_mode=ParseMode.HTML)
    del player


@dp.message(Command("set_range", "sr"))
async def cmd_rules_attempts(message: Message):
    player = await initialize_play(message=message)
    if message.text.split(' ')[-1].isdigit() and int(message.text.split(' ')[-1]) >= 1:
        c_range = [1, int(message.text.split(' ')[-1].split('-')[-1])]
        rules = player.rules
        rules['choice_range'] = c_range
        await player.update_rules(rules)
        await message.answer(text=f'У тебя установлен диапазон ответов: от {c_range[0]} до {c_range[1]}\n')
    else:
        await message.answer(text=f'Ты допустил ошибку..)\nНичего страшного, '
                                  f'возможно ты передал не число или оно оказалось меньше 1, попробуй еще раз\n'
                                  f'Вот тебе пример:\n\n')
        await message.answer(text=f'<strong><code>/sr 150</code></strong>', parse_mode=ParseMode.HTML)
    del player


@dp.message(Command("default"))
async def cmd_rules_attempts(message: Message):
    player = await initialize_play(message=message)
    rules = {
        'attempts': 6,
        'choice_range': [1, 100],
    }
    await player.update_rules(rules)
    await message.answer(text=f'Установлены правила по умолчанию!\n')
    del player


@dp.message(Command("play"))
async def cmd_play(message: Message):
    player = await initialize_play(message=message)
    user_data = message.model_dump_json(exclude_none=True)
    user_data = json.loads(user_data)["from_user"]
    await player.update_user_info(user_data)
    if not player.in_game:
        await player.play()
        await message.answer(text=f'Мы начали играть! Для отмены напиши /cancel\n'
                                  f'Я загадал число от {player.rules.get("choice_range")[0]} до {player.rules.get("choice_range")[1]}! Попробуй его угадать))\n'
                                  f'У тебя есть {player.attempts} попыток\n\n'
                                  f'Введи число:\n')
    else:
        await message.answer(text=f'Мы уже в игре) Осталось попыток: {player.attempts}\n'
                                  f'Для отмены напиши /cancel')
    del player


@dp.message(Command("my_stats"))
async def cmd_my_stats(message: Message):
    await initialize_play(message=message)
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


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    text = f'Статистика:\n\n'
    users_stats = await get_stats(filename=FILENAME)
    for user_id, stats in sorted(users_stats.items(), key=lambda x: x[1]['total_games'], reverse=True)[:3]:
        win_percentage = 100 * stats["wins"] / stats["total_games"]
        text += f'\nID Пользователя: {user_id}\n' \
                f'Сыграно игр: {stats["total_games"]}\n' \
                f'Победы: {stats["wins"]}\n' \
                f'Процент побед: {win_percentage:.0f}%\n'
    # pprint(users_stats)
    await message.answer(text=text)


@dp.message(Command("cancel"))
async def cmd_cancel(message: Message):
    player = await initialize_play(message=message)
    await player.cancel()
    await message.answer(text=f'Жаль, что ты уходишь :(\n'
                              f'Если надумаешь сыграть снова, пиши /play\n'
                              f'Для просмотра статистики, напиши /my_stats\n')
    del player


@dp.message(Command("trivial", "math", "date", "year"))
async def cmd_math(message: Message):
    mode = message.text.split()[0].split('/')[-1]
    await initialize_play(message=message)
    try:
        digit = message.text.split()[1]
    except IndexError:
        if mode != 'date':
            digit = random.randint(0, 3000)
        else:
            month = random.randint(1, 12)
            month = f'0{month}' if month < 10 else f'{month}'
            if month in [1, 3, 5, 7, 8, 10, 12]:
                day = random.randint(1, 31)
            elif month in [4, 6, 9, 11]:
                day = random.randint(1, 30)
            else:
                day = random.randint(1, 28)
            digit = f'{month}/{day}'
    fact = await get_fact(digit, mode)
    if 'это число, для которого нам не хватает факта' in fact:
        fact = f'{digit} — скучное число.'
    if fact:
        await message.answer(text=f'Необъяснимо, но факт:\n\n'
                                  f'{fact}')
    else:
        await message.answer(text=f'Сервис не отвечает...(\nПопробуй позже.')


# @dp.message(lambda x: x.text and x.text.isdigit() and 1 <= int(x.text) <= 100)
# @dp.message(lambda x: x.text and x.text.isdigit())
@dp.message(GameFilter())
async def process_numbers_answer(message: Message, player: Play):
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
                if message.from_user.id == '5195589950':
                    await message.answer(text=f'Ты проиграл, если ты читаешь это письмо, то ты, вероятно, проиграл, '
                                              f'так что не обижайся и возьми с полки пирожок) Что, нету (лох)? '
                                              f'А ты что такой наивный..? Чтобы он там был, надо сначала '
                                              f'заработать на него и самим положить его туда '
                                              f'(ахахахахха)\nЗагаданное число: {player.number}\n'
                                              f'Хочешь попробовать снова - введи /play')
                else:
                    await message.answer(text=f'Ты проиграл... Загаданное число: {player.number}\n'
                                              f'Хочешь попробовать снова - введи /play')
            elif try_it == 'won':
                await message.answer(text=f'Ты выиграл!!! Мои поздравления '
                                          f'(Хотя мне как-то пофиг, иди тренируйся, дрищ)\n'
                                          f'это действительно {player.number}!\n'
                                          f'Хочешь попробовать снова - введи /play')
        else:
            await player.lose()
            await message.answer(text=f'Ты проиграл... Загаданное число: {player.number}\n'
                                      f'Хочешь попробовать снова - введи /play')
    else:
        await message.answer(text=f'Ты не в игре!\n'
                                  f'Хочешь сыграть - введи /play')


@dp.message(Command("send_news"), IsAdmin(admin_ids))
async def cmd_send_news(message: Message):
    ids = await get_stats(filename=FILENAME)
    users_ids = list(ids.keys())[1:-2]
    text = open('addition/news.txt', 'r').read()
    photo = "https://cdn2.thecatapi.com/images/5tl.jpg"
    for user_id in users_ids:
        await bot.send_photo(chat_id=user_id, photo=photo, caption=text)


# Этот хэндлер будет срабатывать на любые ваши текстовые сообщения,
# кроме команд "/start" и "/help"
@dp.message()
async def send_echo(message: Message):
    try:
        await message.reply(text=message.text)
    except Exception as e:
        print(e)
        await message.answer(text="Чё за прикол?!")


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot, polling_timeout=60)


if __name__ == "__main__":
    asyncio.run(main())
