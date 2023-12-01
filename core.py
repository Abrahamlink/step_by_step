import datetime
import random
import json
import math

from aiohttp import ClientSession
from googletrans import Translator

FILENAME = 'addition/stats.json'


async def get_stats(user_id: int = -1, filename: str = 'addition/stats.json'):
    with open(filename, 'r', encoding='utf-8') as file:
        try:
            players_stats = json.load(file)
            if user_id == -1:
                return players_stats
            return players_stats[f'{user_id}']
        except Exception as e:
            return {}


async def set_stats(user_id: int, data: dict, filename: str = 'addition/stats.json'):
    with open(filename, 'w+', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
        file.close()
        print(f'Stats was saved to {filename} successfully!')
        return data[f'{user_id}']


async def calculate_reward(attempts: int, game_range: list):
    return round(6 * (game_range[1] - game_range[0] + 1) / (99 * attempts))


async def initialize_play(message):
    player_stats = await get_stats(user_id=message.from_user.id, filename=FILENAME)
    player = Play(user_id=message.from_user.id, user_stats=player_stats)
    await player.update_date(message.date.strftime("%d.%m.%Y, %H:%M:%S"))
    return player


class Play(object):
    def __init__(self, user_id=-1, user_stats: dict = dict):
        self.user_id = user_id
        if user_stats != {}:
            self.user_info = user_stats.get('user_info')
            self.rules = user_stats.get('rules')
            self.in_game = user_stats.get('in_game')
            self.last_activity = user_stats.get('last_activity')
            self.number = user_stats.get('number')
            self.attempts = user_stats.get('attempts')
            self.total_games = user_stats.get('total_games')
            self.wins = user_stats.get('wins')
            self.cats_coins = user_stats.get('cats_coins')
            self.cats_pics = user_stats.get('cats_pics')
        else:
            self.user_info = {}
            self.rules = {
                'attempts': 6,
                'choice_range': [1, 100],
                'fact_mode': 'trivial',
            }
            self.in_game = False
            self.last_activity = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            self.number = random.randint(1, 100)
            self.attempts = self.rules.get('attempts')
            self.total_games = 0
            self.wins = 0
            self.cats_coins = 0
            self.cats_pics = []

    async def stats(self) -> dict:
        return {f'{self.user_id}': {
            'user_info': self.user_info,
            'rules': self.rules,
            'in_game': self.in_game,
            'last_activity': self.last_activity,
            'number': self.number,
            'attempts': self.attempts,
            'total_games': self.total_games,
            'wins': self.wins,
            'cats_coins': self.cats_coins,
            'cats_pics': self.cats_pics
        }}

    async def save_stats(self, filename: str = 'addition/stats.json'):
        data = await get_stats(filename=filename)
        if data == {}:
            data = await self.stats()
            user_data = await set_stats(user_id=self.user_id, data=data, filename=filename)
        else:
            local_stats = await self.stats()
            data[f'{self.user_id}'] = local_stats[f'{self.user_id}']
            user_data = await set_stats(user_id=self.user_id, data=data, filename=filename)
        return user_data

    async def update_user_info(self, data_to_update: dict = {}):
        user_stats = await self.stats()
        user_data = user_stats[f'{self.user_id}'].get('user_info')
        self.user_info = {**user_data, **data_to_update}
        await self.save_stats()
        print('User data updated successfully!\n')

    async def update_date(self, updating_data: str):
        self.last_activity = updating_data
        await self.save_stats()
        print('Date of last activity updated successfully!\n')

    async def update_rules(self, updating_data: dict = {}):
        if not self.in_game:
            self.rules['attempts'] = updating_data['attempts']
            self.rules['choice_range'] = updating_data['choice_range']
            await self.save_stats()
            print('New rules updated successfully!\n')
            return True
        else:
            print('Can\'t update rules, game is in progress yet!\n')
            return False

    async def _win(self):
        self.in_game = False
        self.total_games += 1
        self.wins += 1
        reward = await calculate_reward(attempts=self.rules.get('attempts'),
                                        game_range=self.rules.get('choice_range'))
        self.cats_coins += reward

        await self.save_stats()
        print("Game won!")
        return 'won'

    async def _mistake(self):
        print("Mistake!")
        self.attempts -= 1
        if self.attempts == 0:
            return await self.lose()
        await self.save_stats()
        return

    async def lose(self):
        self.in_game = False
        self.total_games += 1

        await self.save_stats()
        print("Game lost...")
        return 'lose'

    async def play(self):
        """Start the game"""
        self.in_game = True
        self.number = random.randint(self.rules.get('choice_range')[0], self.rules.get('choice_range')[1])
        self.attempts = self.rules.get('attempts')
        await self.save_stats()
        print("Game started")

    async def try_number(self, number: int):
        if self.attempts == 0:
            return await self.lose()
        if self.number == number:
            return await self._win()
        elif self.number > number:
            mis = await self._mistake()
            if mis == 'lose':
                return await self.lose()
            print("More")
            return 'more'
        elif self.number < number:
            mis = await self._mistake()
            if mis == 'lose':
                return await self.lose()
            print("Less")
            return 'less'

    async def cancel(self):
        self.in_game = False

        await self.save_stats()
        return 'cancel'

    async def buy_cat(self, cat_url: str):
        self.cats_coins -= 1
        self.cats_pics.append(cat_url)
        await self.save_stats()


async def get_fact(digit: int | str, mode='trivial', src: str = 'en', dest: str = 'ru') -> str | bool:
    base_url = 'http://numbersapi.com'
    async with ClientSession() as session:
        if mode == 'trivial':
            url_number = base_url + f'/{digit}'
        elif mode == 'math' or 'year' or 'date':
            url_number = base_url + f'/{digit}' + f'/{mode}'
        else:
            url_number = base_url + 'random' + f'/{mode}'
        print(url_number)
        async with session.get(url=url_number) as response:
            try:
                data = await response.text()
                translate = Translator()
                translation = translate.translate(text=data, src=src, dest=dest)
                return translation.text
            except Exception as ex:
                print(ex)
                return False
            finally:
                await session.close()


async def get_cat(player: Play) -> str | bool:
    async with ClientSession() as session:
        url_cats = f'https://api.thecatapi.com/v1/images/search'
        try:
            async with session.get(url=url_cats) as response:
                cat_json = await response.json()
                cat = cat_json[0]['url']
                await player.buy_cat(cat)
                return cat
        except Exception as ex:
            print(ex)
            return False
        finally:
            await session.close()
