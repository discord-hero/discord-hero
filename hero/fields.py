"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

from typing import Type

import discord

from tortoise.fields import (BigIntField, BooleanField, CharField, CASCADE,
                             DateField, DatetimeField, DecimalField, FloatField,
                             ForeignKeyField as _ForeignKeyField, IntField,
                             JSONField, ManyToManyField as _ManyToManyField,
                             RESTRICT, SET_DEFAULT, SET_NULL,
                             SmallIntField, TextField, TimeDeltaField)

import hero
from . import db
from .i18n import Languages


class ForeignKeyField(_ForeignKeyField):
    def __init__(self, model: Type[hero.Model], *args, **kwargs):
        if issubclass(model, hero.Model):
            model_name = '.'.join((model._meta.app, model.__name__))
        else:
            raise TypeError("model must be a subclass of hero.Model")
        super(ForeignKeyField, self).__init__(model_name, *args, **kwargs)


class ManyToManyField(_ManyToManyField):
    def __init__(self, model: Type[hero.Model], *args, **kwargs):
        if issubclass(model, hero.Model):
            model_name = '.'.join((model._meta.app, model.__name__))
        else:
            raise TypeError("model must be a subclass of hero.Model")
        super(ManyToManyField, self).__init__(model_name, *args, **kwargs)


class DiscordField(ForeignKeyField):
    _discord_cls = None
    _discord_obj = None

    def __init__(self, *args, **kwargs):
        super(DiscordField, self).__init__(db.hero_model_map[self._discord_cls],
                                           *args, **kwargs)


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


class ManyDiscordField(ManyToManyField):
    _discord_cls = None
    _discord_obj = None

    def __init__(self, *args, **kwargs):
        super(ManyDiscordField, self).__init__(db.hero_model_map[self._discord_cls],
                                               *args, **kwargs)


class ManyUsersField(ManyDiscordField):
    _discord_cls = discord.User


class ManyGuildsField(ManyDiscordField):
    _discord_cls = discord.Guild


class ManyTextChannelsField(ManyDiscordField):
    _discord_cls = discord.TextChannel


class ManyVoiceChannelsField(ManyDiscordField):
    _discord_cls = discord.VoiceChannel


class ManyRolesField(ManyDiscordField):
    _discord_cls = discord.Role


class ManyEmojisField(ManyDiscordField):
    _discord_cls = discord.Emoji


class ManyMembersField(ManyDiscordField):
    _discord_cls = discord.Member


class ManyMessagesField(ManyDiscordField):
    _discord_cls = discord.Message


class LanguageField(CharField):
    def __init__(self, **kwargs):
        kwargs['max_length'] = 16
        kwargs['default'] = Languages.default
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
