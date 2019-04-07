"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import enum
from typing import Union

import discord

import tortoise
from tortoise import Tortoise

import hero
from hero.utils import ismodelobject
from .fields import DiscordField


class Object(discord.Object):
    def __init__(self, id, field: DiscordField):
        super(Object, self).__init__(id)
        self._field = field

    @property
    def _discord_obj(self):
        return self._field._discord_obj

    @_discord_obj.setter
    def _discord_obj(self, value):
        self._field._discord_obj = value

    async def connect(self, core: hero.Core):
        # TODO
        pass


class DatabaseBackends(enum.Enum):
    SQLITE3 = 'sqlite3'
    MYSQL = 'mysql'
    POSTGRESQL = 'postgresql'


# TODO turn these into enums
discord_models = (discord.Message, discord.TextChannel,
                  discord.VoiceChannel, discord.User,
                  discord.Member, discord.Guild,
                  discord.Role, discord.Emoji)


hero_models = (hero.Message, hero.TextChannel,
               hero.VoiceChannel, hero.User,
               hero.Member, hero.Guild,
               hero.Role, hero.Emoji)


discord_model_map = dict(zip(discord_models, hero_models))

# reverse version
hero_model_map = dict(zip(hero_models, discord_models))


def get_database_client(name='default'):
    return Tortoise.get_connection(name)


class Database:
    def __init__(self, core: hero.Core, extension: hero.Extension=None):
        self.core = core
        self.extension = extension
        if self.extension is not None:
            _models = self.extension.get_models()

    async def connect(self, obj: Union[discord_models]):
        if isinstance(obj, discord_models):
            cls = discord_model_map[obj.__class__]
            return await cls.from_discord_obj(obj)
        elif ismodelobject(obj):
            for field in obj.fields:
                if isinstance(field, DiscordField):
                    field._discord_obj = self.core.get()
            raise TypeError("obj has to be an object from Discord")

    @staticmethod
    async def merge(discord_obj: Union[discord_models], ultima_obj: Union[hero_models]):
        # merge discord object and ultima object into one
        ultima_obj._discord_obj = discord_obj
        return ultima_obj

    async def get(self, model: str, *args, **kwargs):
        """Get an object from the database.

        :param model:
            The snake_case version of the :class:`Model`'s name
        :type model: str
        """
        # TODO
        pass

    async def get_user(self, *args, **kwargs):
        await self.get(*args, **kwargs)


def init(core: hero.Core):
    # TODO
    if hero.CONFIG.get('db', None) is None:
        file_name = 'test_db.sqlite3' if hero.TEST else 'db.sqlite3'
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
                    'models': [str(extension) for extension in core.extensions],
                }
            }
        }
    elif hero.CONFIG['db']['backend'] == 'postgres':
        pass  # TODO
    Tortoise.get_connection('default')
    Tortoise.init(config=_db_config)


# TODO figure out a way to migrate DB models automatically
