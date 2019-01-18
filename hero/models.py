"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""


from typing import Union

import tortoise

import hero
from hero import db, fields, logging
from .i18n import Language


class Model(tortoise.models.Model):
    class Meta:
        abstract = True


class DiscordModel(Model):
    class Meta:
        abstract = True

    id = fields.BigIntField(pk=True)
    _discord_obj = None

    @property
    def is_stored(self):
        return self.id is not None

    @property
    def _core(self):
        if self._discord_obj is None:
            return None
        # TODO find a cleaner way to do this
        return self._discord_obj._state.core

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
            obj = await super().get(**kwargs)
            obj._discord_obj = args[0]
            return obj
        return super().get(*args, **kwargs)

    @classmethod
    async def get_or_create(cls, *args, **kwargs):
        if isinstance(args[0], db.discord_model_map.get(cls)):
            if len(args) != 1:
                raise TypeError(f"Unexpected arguments {' '.join(args[1:])}")
            obj = await super().get_or_create(**kwargs)
            obj._discord_obj = args[0]
            return obj
        return super().get_or_create(*args, **kwargs)

    async def connect(self, discord_obj: Union[db.discord_models]):
        # TODO
        pass

    @property
    def is_connected(self):
        return self._discord_obj is not None

    async def translate(self, s: str):
        return self._core.translate(s, self.lang)

    @property
    def t(self):
        return self.translate

    def __getattr__(self, attr_name):
        if hasattr(self._discord_obj, attr_name):
            return getattr(self._discord_obj, attr_name)

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


class Settings(hero.Model):
    name = fields.CharField(pk=True, max_length=64)
    token = fields.CharField(max_length=64)
    log_channel = fields.TextChannelField(null=True)
    lang = fields.LanguageField(default=Language.default.value)

    @property
    def logging_level(self):
        if hero.TEST:
            return logging.DEBUG
        else:
            return logging.WARNING


class User(DiscordModel):
    is_staff = fields.BooleanField(default=False, db_index=True)
    command_count = fields.IntField(default=0)
    is_active = fields.BooleanField(default=True, db_index=True)
    lang = fields.LanguageField(default=Language.default.value)
    # TODO when user wants to delete their data, delete user,
    # let the DB cascade, and create a new user with is_active=False


class Guild(DiscordModel):
    # TODO normalize Guild
    register_time = fields.DatetimeField(auto_now_add=True)
    invite_code = fields.CharField(max_length=64, db_index=True)
    url = fields.CharField(max_length=256, unique=True)
    is_deleted = fields.BooleanField(default=False)
    prefix = fields.CharField(max_length=64)
    lang = fields.LanguageField(default=Language.default.value)
    # members = fields.ManyToManyField('ultima.User', through='ultima.Member')

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
    lang = fields.LanguageField(default=Language.default.value)


class VoiceChannel(DiscordModel):
    guild = fields.GuildField(on_delete=fields.CASCADE)


class Role(DiscordModel):
    guild = fields.GuildField(on_delete=fields.CASCADE)


class Emoji(DiscordModel):
    guild = fields.GuildField(on_delete=fields.CASCADE)
    name = fields.CharField(max_length=64)


class Member(DiscordModel):
    user = fields.UserField(on_delete=fields.CASCADE)
    guild = fields.GuildField(on_delete=fields.CASCADE)

    def __getattribute__(self, item):
        if item == 'id':
            _discord_obj = getattr(self, '_discord_obj', None)
            if _discord_obj is not None:
                return self._discord_obj.id
        return super().__getattribute__(item)


class Message(DiscordModel):
    channel = fields.TextChannelField(db_index=True, on_delete=fields.CASCADE)
    author = fields.UserField(db_index=True, on_delete=fields.CASCADE)
    guild = fields.GuildField(db_index=True, on_delete=fields.CASCADE)


class UserGroup(Model):
    name = fields.CharField(max_length=64, unique=True)


class UserGroupMember(Model):
    group = fields.ForeignKeyField('hero.group', db_index=True)
    user = fields.UserField(db_index=True, on_delete=fields.CASCADE)


# TODO figure out a way to migrate DB models automatically
