import importlib
from typing import Optional

import discord

import ultima
from ultima import fields, logging


class Settings(ultima.Model):
    name = fields.CharField(pk=True, max_length=64)
    token = fields.CharField(max_length=64)

    @property
    def logging_level(self):
        if ultima.TEST:
            return logging.DEBUG
        else:
            return logging.WARNING


class User(ultima.Model):
    id = fields.BigIntField(pk=True)
    is_staff = fields.BooleanField(default=False, db_index=True)
    command_count = fields.IntField(default=0)
    is_active = fields.BooleanField(default=True, db_index=True)
    _d: Optional[discord.User] = None
    # TODO when user wants to delete their data, delete user,
    # let the DB cascade, and create a new user with is_active=False

    @classmethod
    @ultima.cached
    async def from_discord_obj(cls, user: discord.User):
        return await cls.get_or_create(id=user.id)

    def __int__(self):
        return self.id

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return isinstance(other, User) and other.id == self.id


class Guild(ultima.Model):
    # I can't normalize this any further :/
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=64, unique=True, db_index=True)
    register_time = fields.DatetimeField(auto_now_add=True)
    invite_link = fields.CharField(max_length=64, unique=True, db_index=True)
    url = fields.CharField(max_length=256, unique=True)
    is_deleted = fields.BooleanField(default=False)
    _d: Optional[discord.Guild] = None

    def __int__(self):
        return self.id

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return isinstance(other, Guild) and other.id == self.id


class TextChannel(ultima.Model):
    id = fields.IntField(pk=True)
    guild = fields.ForeignKeyField('ultima.guild', on_delete=fields.CASCADE)
    _d: Optional[discord.TextChannel] = None

    def __int__(self):
        return self.id

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return isinstance(other, TextChannel) and other.id == self.id


class VoiceChannel(ultima.Model):
    id = fields.IntField(pk=True)
    guild = fields.ForeignKeyField('ultima.guild', on_delete=fields.CASCADE)
    _d: Optional[discord.VoiceChannel] = None

    def __int__(self):
        return self.id


class Role(ultima.Model):
    id = fields.IntField(pk=True)
    guild = fields.ForeignKeyField('ultima.guild', on_delete=fields.CASCADE)
    _d: Optional[discord.Role] = None

    def __int__(self):
        return self.id

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return isinstance(other, Role) and other.id == self.id


class Member(ultima.Model):
    user = fields.ForeignKeyField('ultima.user', on_delete=fields.CASCADE)
    guild = fields.ForeignKeyField('ultima.guild', on_delete=fields.CASCADE)
    _d: Optional[discord.Member] = None

    def __int__(self):
        return self.id

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return (isinstance(other, Member)
                and other.user == self.user
                and other.guild == self.guild)


class Message(ultima.Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('ultima.user', db_index=True, on_delete=fields.CASCADE)
    channel = fields.ForeignKeyField('ultima.channel', on_delete=fields.CASCADE)
    content = fields.TextField(max_length=2000)
    clean_content = fields.TextField(max_length=2000)
    _d: Optional[discord.Message] = None

    def __int__(self):
        return self.id

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return isinstance(other, Message) and other.id == self.id


# Importing models introduced by extensions.
# Kinda hacky but there seems to be no clean way to do this.
extensions = []  # TODO get extensions
for extension in extensions:
    try:
        # mimic `from dwarf.extension.models import *`
        models_module = importlib.import_module('ultima.' + extension + '.models')
        module_dict = models_module.__dict__
        try:
            to_import = models_module.__all__
        except AttributeError:
            to_import = [name for name in module_dict if not name.startswith('_')]

        globals().update({name: module_dict[name] for name in to_import})
    except ImportError:
        pass


# TODO figure out a way to use Django's migration system
