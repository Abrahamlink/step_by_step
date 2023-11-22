import random
import json
import asyncio


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


class Play(object):
    def __init__(self, user_id, user_stats: dict = dict):
        self.user_id = user_id
        if user_stats != {}:
            self.in_game = user_stats.get('in_game')
            self.number = user_stats.get('number')
            self.attempts = user_stats.get('attempts')
            self.total_games = user_stats.get('total_games')
            self.wins = user_stats.get('wins')
            self.cats_coins = user_stats.get('cats_coins')
            self.cats_pics = user_stats.get('cats_pics')
        else:
            self.in_game = False
            self.number = random.randint(1, 100)
            self.attempts = 5
            self.total_games = 0
            self.wins = 0
            self.cats_coins = 0
            self.cats_pics = []

    async def stats(self):
        return {f'{self.user_id}': {
            'in_game': self.in_game,
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
            print(data, 'if data == {}')
            user_data = await set_stats(user_id=self.user_id, data=data, filename=filename)
        else:
            local_stats = await self.stats()
            data[f'{self.user_id}'] = local_stats[f'{self.user_id}']
            print(data, 'else')
            user_data = await set_stats(user_id=self.user_id, data=data, filename=filename)
        return user_data

    async def _win(self):
        self.in_game = False
        self.total_games += 1
        self.wins += 1
        self.cats_coins += 1
        self.attempts = 5

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
        self.number = random.randint(1, 100)
        self.attempts = 5
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
        self.attempts = 5

        await self.save_stats()
        return 'cancel'

    async def buy_cat(self, cat_url: str):
        self.cats_coins -= 1
        self.cats_pics.append(cat_url)
        await self.save_stats()


# d = {'313123':
#          {'in_game': True,
#           'number': 313123,
#           'attempts': 5}
#      }
#
# print(list(d.keys())[0])