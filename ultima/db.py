from typing import Union

import discord

from tortoise import Tortoise
import tortoise

import ultima


discord_models = (discord.Message, discord.TextChannel,
                  discord.VoiceChannel, discord.User,
                  discord.Member, discord.Guild,
                  discord.Role)


ultima_models = (ultima.Message, ultima.TextChannel,
                 ultima.VoiceChannel, ultima.User,
                 ultima.Member, ultima.Guild,
                 ultima.Role)


discord_model_map = dict(zip(discord_models, ultima_models))

# reverse version
ultima_model_map = dict(zip(ultima_models, discord_models))


class Database:
    def __init__(self, cog: ultima.Cog):
        self.cog = cog

    async def save(self, obj: Union[ultima_models, discord_models]):
        if isinstance(obj, ultima_models):
            await self.update(obj)
            await obj.save()

        elif isinstance(obj, discord_models):
            cls = discord_model_map[obj.__class__]
            return await cls.from_discord_obj(obj)

        else:
            raise TypeError("obj has to be an object from Discord or "
                            "an instance of an Ultima model")

    async def load(self, obj: Union[discord_models]):
        if isinstance(obj, discord_models):
            cls = discord_model_map[obj.__class__]
            return await cls.from_discord_obj(obj)
        else:
            raise TypeError("obj has to be an object from Discord")

    async def update(self, obj: Union[ultima_models]):
        # load Discord object via self.core
        pass

    async def merge(self, discord_obj: Union[discord_models], ultima_obj: Union[ultima_models]):
        # merge discord object and ultima object into one
        pass


def init():
    if ultima.CONFIG.get('db', None) is None:
        file_name = 'test_db.sqlite3' if ultima.TEST else 'db.sqlite3'
        _db_config = {
            'connections': {
                # Dict format for connection
                'default': {
                    'engine': 'tortoise.backends.sqlite',
                    'credentials': {
                        'file_path': file_name
                    }
                }
            },
            'apps': {
                'models': {
                    'models': [str(extension) for extension in ultima.extensions],
                }
            }
        }
    elif ultima.CONFIG['db']
    Tortoise.init(config=_db_config)
