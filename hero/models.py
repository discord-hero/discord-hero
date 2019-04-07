"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import time
from typing import Union

import tortoise

import hero
from hero import db, fields, logging


class Model(tortoise.models.Model):
    class Meta:
        abstract = True

    @property
    def _core(self):
        """The :class:`Core`. Should only be accessed from within the
        model class itself.
        """
        return self._meta.db.core

    @property
    def _extension(self):
        if self._meta.app == 'hero':
            return None
        return self._core.extensions[self._meta.app]


class AbstractSettings(Model):
    class Meta:
        abstract = True

    async def setdefault(self):
        # TODO implement dict-like API
        pass


class CoreSettings(AbstractSettings):
    name = fields.CharField(pk=True, max_length=64)
    token = fields.CharField(max_length=64)
    lang = fields.LanguageField()

    @property
    def logging_level(self):
        if hero.TEST:
            return logging.DEBUG
        else:
            return logging.WARNING


class DiscordModel(Model):
    class Meta:
        abstract = True

    id = fields.BigIntField(pk=True)
    _discord_obj = None

    @classmethod
    def from_discord_obj(cls, discord_obj):
        discord_cls = db.discord_model_map[cls]
        if (not isinstance(discord_obj, discord_cls)
            or isinstance(getattr(discord_obj, 'user', None), discord_cls)):
            raise TypeError(f"discord_obj has to be a discord.{discord_cls.__name__} "
                            f"but a discord.{type(discord_obj).__name__} was passed")
        obj = cls(id=discord_obj.id)
        obj._discord_obj = discord_obj
        return obj

    @classmethod
    async def get(cls, *args, **kwargs):
        if isinstance(args[0], db.discord_model_map.get(cls)):
            if len(args) != 1:
                raise TypeError(f"Unexpected arguments {' '.join(args[1:])}")
            obj = await super().get(id=args[0].id, **kwargs)
            obj._discord_obj = args[0]
            return obj
        return super().get(*args, **kwargs)

    @classmethod
    async def get_or_create(cls, *args, **kwargs):
        if isinstance(args[0], db.discord_model_map.get(cls)):
            if len(args) != 1:
                raise TypeError(f"Unexpected arguments {' '.join(args[1:])}")
            obj = await super().get_or_create(id=args[0].id, **kwargs)
            obj._discord_obj = args[0]
            return obj
        return super().get_or_create(*args, **kwargs)

    @classmethod
    async def create(cls, *args, **kwargs):
        if isinstance(args[0], db.discord_model_map.get(cls)):
            if len(args) != 1:
                raise TypeError(f"Unexpected arguments {' '.join(args[1:])}")
            obj = await super().create(id=args[0].id, **kwargs)
            obj._discord_obj = args[0]
            return obj
        return super().get(*args, **kwargs)

    async def load(self):
        await self.fetch_fields()

    async def connect(self, discord_obj: Union[db.discord_models]=None):
        # TODO
        pass

    @property
    def is_loaded(self):
        # TODO
        return False

    @property
    def is_connected(self):
        return self._discord_obj is not None

    def __getattr__(self, name):
        if hasattr(self._discord_obj, name):
            return getattr(self._discord_obj, name)

    def __dir__(self):
        tmp = super(DiscordModel, self).__dir__()

    def __str__(self):
        if self.is_connected:
            return self.name
        else:
            return str(self.id)

    def __int__(self):
        return self.id

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return self.id


USER_ACCESS_CACHE_KEY = "{user.id}_{queried_field}_{method}"


class User(DiscordModel):
    is_staff = fields.BooleanField(default=False, index=True)
    is_active = fields.BooleanField(default=True, index=True)
    lang = fields.LanguageField()
    prefers_dm = fields.BooleanField(default=False)
    # TODO when user wants to delete their data, delete user,
    # let the DB cascade, and create a new user with is_active=False

    async def get_all_groups(self):
        # TODO
        pass

    async def get_last_access(self, queried_field: str, method: hero.perms.Methods):
        """Returns when the queried_field was last accessed with the specified method"""
        cache = hero.get_cache()
        key = USER_ACCESS_CACHE_KEY.format(user=self,
                                           queried_field=queried_field,
                                           method=method)
        return await cache.get(key, default=0)

    async def register_access(self, queried_field: str, method: hero.perms.Methods):
        """Returns when the queried_field was last accessed with the specified method to now"""
        cache = hero.get_cache()
        key = USER_ACCESS_CACHE_KEY.format(user=self,
                                           queried_field=queried_field,
                                           method=method)
        return await cache.set(key, time.time())


class Guild(DiscordModel):
    # TODO normalize Guild
    register_time = fields.DatetimeField(auto_now_add=True)
    invite_code = fields.CharField(max_length=64, index=True)
    url = fields.CharField(max_length=256, unique=True)
    is_deleted = fields.BooleanField(default=False)
    prefix = fields.CharField(max_length=64)
    lang = fields.LanguageField()
    members = fields.ManyUsersField('hero.User', through='hero.Member',
                                    forward_key='user', backward_key='guild',
                                    related_name='guilds')

    @property
    def invite_url(self):
        return f'https://discord.gg/{self.invite_code}'

    @invite_url.setter
    def invite_url(self, value: str):
        if not isinstance(value, str):
            raise TypeError("invite_url must be a str")
        try:
            self.invite_code = value.split('://discord.gg/')[1]
        except IndexError:
            try:
                self.invite_code = value.split('://discordapp.com/invite/')[1]
            except IndexError:
                raise ValueError("Not a valid invite URL.")


class TextChannel(DiscordModel):
    guild = fields.GuildField(on_delete=fields.CASCADE)
    lang = fields.LanguageField()


class VoiceChannel(DiscordModel):
    guild = fields.GuildField(on_delete=fields.CASCADE)


class Role(DiscordModel):
    guild = fields.GuildField(on_delete=fields.CASCADE)


class Emoji(DiscordModel):
    guild = fields.GuildField(on_delete=fields.CASCADE)
    name = fields.CharField(max_length=64)


# TODO use ManyToManyField for this
class Member(DiscordModel):
    user = fields.UserField(pk=True, on_delete=fields.CASCADE)
    guild = fields.GuildField(pk=True, on_delete=fields.CASCADE)

    def __getattribute__(self, name):
        if name == 'id':
            _discord_obj = getattr(self, '_discord_obj', None)
            if _discord_obj is not None:
                return self._discord_obj.id
        return super().__getattribute__(name)


class Message(DiscordModel):
    channel = fields.TextChannelField(index=True, on_delete=fields.CASCADE)
    author = fields.UserField(index=True, on_delete=fields.CASCADE)
    guild = fields.GuildField(index=True, on_delete=fields.CASCADE)


class UserGroup(Model):
    name = fields.CharField(max_length=64, unique=True)


class UserGroupMember(Model):
    group = fields.ForeignKeyField(UserGroup, index=True)
    user = fields.UserField(index=True, on_delete=fields.CASCADE)
