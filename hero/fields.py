"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""


from typing import Union

import discord

from tortoise.fields import (BigIntField, BooleanField, CharField, CASCADE,
                             DateField, DatetimeField, DecimalField, FloatField,
                             ForeignKeyField, IntField, JSONField,
                             RESTRICT, SET_DEFAULT, SET_NULL,
                             SmallIntField, TextField, TimeDeltaField)

import hero
from . import db
from .i18n import Languages


class DiscordField(BigIntField):
    _discord_cls = None
    _discord_obj = None

    def __init__(self, *args, **kwargs):
        super(DiscordField, self).__init__(*args, **kwargs)

    def to_db_value(self, value: Union[hero.Object, db.discord_models, db.hero_models],
                    instance):
        if not isinstance(value, (hero.Object,) + db.discord_models + db.hero_models):
            raise TypeError("value needs to be a hero.Object, "
                            "a discord object or a hero object")
        return value.id

    def to_python_value(self, value: int):
        if self._discord_obj is not None:
            cls = db.discord_model_map[self._discord_cls]
            return cls.from_discord_obj(self._discord_obj)
        else:
            return hero.Object(value, self)


class UserField(DiscordField):
    _discord_cls = discord.User


class GuildField(DiscordField):
    _discord_cls = discord.Guild


class TextChannelField(DiscordField):
    _discord_cls = discord.TextChannel


class VoiceChannelField(DiscordField):
    _discord_cls = discord.VoiceChannel


class RoleField(DiscordField):
    _discord_cls = discord.Role


class EmojiField(DiscordField):
    _discord_cls = discord.Emoji


class MemberField(DiscordField):
    _discord_cls = discord.Member


class MessageField(DiscordField):
    _discord_cls = discord.Message


class LanguageField(CharField):
    def __init__(self, **kwargs):
        kwargs['max_length'] = 16
        super().__init__(**kwargs)

    def to_db_value(self, value: Languages, instance) -> str:
        return value.value

    def to_python_value(self, value: str) -> Languages:
        try:
            return Languages(value)
        except ValueError:
            raise ValueError(
                "{language_value} is not a valid language".format(language_value=value)
            )
