import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from config import Token

from aiohttp import ClientSession


# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=Token)
# Диспетчер
dp = Dispatcher()


# Этот хэндлер будет срабатывать на команду "/start"
@dp.message(Command(commands=["start"]))
async def process_start_command(message: Message):
    await message.answer(f'Привет, {message.from_user.first_name}!\nМеня зовут Эхо-бот!\nНапиши мне что-нибудь')


# Этот хэндлер будет срабатывать на команду "/help"
@dp.message(Command(commands=['help']))
async def process_help_command(message: Message):
    await message.answer(
        'Напиши мне что-нибудь и в ответ\n'
        'я пришлю тебе твое сообщение\n'
        'Для того, чтобы получить помощь, напиши команду "/help"'
    )


@dp.message(Command("cat"))
async def cmd_cat(message: Message):
    async with ClientSession() as session:
        url = f'https://api.thecatapi.com/v1/images/search'

        async with session.get(url=url) as response:
            cat_json = await response.json()
            cat = cat_json[0]['url']
            await message.answer_photo(cat)


# Этот хэндлер будет срабатывать на любые ваши текстовые сообщения,
# кроме команд "/start" и "/help"
@dp.message()
async def send_echo(message: Message):
    await message.reply(text=message.text)


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
