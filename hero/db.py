"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

from typing import Union
import warnings

import discord


class Database:
    def __init__(self, core):
        self.core = core

        from hero.models import (User, Guild, TextChannel, VoiceChannel,
                                 CategoryChannel, Role, Emoji, Member, Message)
        self._model_map = {
            discord.User: User,
            discord.Guild: Guild,
            discord.TextChannel: TextChannel,
            discord.VoiceChannel: VoiceChannel,
            discord.CategoryChannel: CategoryChannel,
            discord.Role: Role,
            discord.Emoji: Emoji,
            discord.PartialEmoji: Emoji,
            discord.Member: Member,
            discord.Message: Message
        }
        self._models = tuple(self._model_map.values())
        self._discord_classes = tuple(self._model_map.keys())

    async def load(self, discord_obj):
        warnings.warn("Database.load is deprecated; use Database.wrap_{} methods instead", DeprecationWarning)
        obj, existed_already = await self._load(discord_obj)
        return obj, existed_already

    async def _load(self, discord_obj):
        if isinstance(discord_obj, self._discord_classes):
            cls = self._model_map[type(discord_obj)]
            obj, existed_already = await cls.from_discord_obj(discord_obj)
            return obj, existed_already
        elif isinstance(discord_obj, self._models):
            try:
                await discord_obj.async_load()
                existed_already = True
            except discord_obj.__class__.DoesNotExist:
                existed_already = False
            return discord_obj, existed_already
        else:
            raise TypeError("obj has to be an object from Discord")

    async def wrap_user(self, user: Union[discord.User, discord.Member]):
        """Wrap a User (or Member) object obtained from Discord
        in a hero.User to provide it with
        database-related functionalities (see hero.Model,
        hero.DiscordModel and hero.User for more details).
        The returned hero.User will still have all the
        attributes and methods of the discord.User
        that it is holding inside.
        """
        if not isinstance(user, (discord.User, discord.Member)):
            raise TypeError("user must be a discord.User or discord.Member")
        if isinstance(user, discord.Member):
            user = user._user
        user, _ = await self._load(user)
        return user

    async def wrap_guild(self, guild: discord.Guild):
        """Wrap a Guild object obtained from Discord
        in a hero.Guild to provide it with
        database-related functionalities (see hero.Model,
        hero.DiscordModel and hero.Guild for more details).
        The returned hero.Guild will still have all the
        attributes and methods of the discord.Guild
        that it is holding inside.
        """
        if not isinstance(guild, discord.Guild):
            raise TypeError("guild must be a discord.Guild")
        guild, _ = await self._load(guild)
        return guild

    async def wrap_text_channel(self, text_channel: discord.TextChannel):
        """Wrap a TextChannel object obtained from Discord
        in a hero.TextChannel to provide it with
        database-related functionalities (see hero.Model,
        hero.DiscordModel and hero.TextChannel for more details).
        The returned hero.TextChannel will still have all the
        attributes and methods of the discord.TextChannel
        that it is holding inside.
        """
        if not isinstance(text_channel, discord.TextChannel):
            raise TypeError("text_channel must be a discord.TextChannel")
        text_channel, _ = await self._load(text_channel)
        return text_channel

    async def wrap_voice_channel(self, voice_channel: discord.VoiceChannel):
        """Wrap a VoiceChannel object obtained from Discord
        in a hero.VoiceChannel to provide it with
        database-related functionalities (see hero.Model,
        hero.DiscordModel and hero.VoiceChannel for more details).
        The returned hero.VoiceChannel will still have all the
        attributes and methods of the discord.VoiceChannel
        that it is holding inside.
        """
        if not isinstance(voice_channel, discord.VoiceChannel):
            raise TypeError("voice_channel must be a discord.VoiceChannel")
        voice_channel, _ = await self._load(voice_channel)
        return voice_channel

    async def wrap_category_channel(self, category_channel: discord.CategoryChannel):
        """Wrap a CategoryChannel object obtained from Discord
        in a hero.CategoryChannel to provide it with
        database-related functionalities (see hero.Model,
        hero.DiscordModel and hero.CategoryChannel for more details).
        The returned hero.CategoryChannel will still have all the
        attributes and methods of the discord.CategoryChannel
        that it is holding inside.
        """
        if not isinstance(category_channel, discord.CategoryChannel):
            raise TypeError("category_channel must be a discord.CategoryChannel")
        return await self._load(category_channel)

    async def wrap_role(self, role: discord.Role):
        """Wrap a Role object obtained from Discord
        in a hero.Role to provide it with
        database-related functionalities (see hero.Model,
        hero.DiscordModel and hero.Role for more details).
        The returned hero.Role will still have all the
        attributes and methods of the discord.Role
        that it is holding inside.
        """
        if not isinstance(role, discord.Role):
            raise TypeError("role must be a discord.Role")
        role, _ = await self._load(role)
        return role

    async def wrap_emoji(self, emoji: Union[discord.Emoji, discord.PartialEmoji]):
        """Wrap a Emoji (or discord.PartialEmoji) object obtained
        from Discord in a hero.Emoji to provide it with
        database-related functionalities (see hero.Model,
        hero.DiscordModel and hero.Emoji for more details).
        The returned hero.Emoji will still have all the
        attributes and methods of the discord.Emoji
        (or discord.PartialEmoji) that it is holding inside.
        """
        if not isinstance(emoji, (discord.Emoji, discord.PartialEmoji)):
            raise TypeError("emoji must be a discord.Emoji or discord.PartialEmoji")
        emoji, _ = await self._load(emoji)
        return emoji

    async def wrap_member(self, member: discord.Member):
        """Wrap a Member object obtained from Discord
        in a hero.Member to provide it with
        database-related functionalities (see hero.Model,
        hero.DiscordModel and hero.Member for more details).
        The returned hero.Member will still have all the
        attributes and methods of the discord.Member
        that it is holding inside.
        """
        if not isinstance(member, discord.Member):
            raise TypeError("member must be a discord.Member")
        member, _ = await self._load(member)
        return member

    async def wrap_message(self, message: discord.Message):
        """Wrap a Message object obtained from Discord
        in a hero.Message to provide it with
        database-related functionalities (see hero.Model,
        hero.DiscordModel and hero.Message for more details).
        The returned hero.Message will still have all the
        attributes and methods of the discord.Message
        that it is holding inside.
        """
        if not isinstance(message, discord.Message):
            raise TypeError("message must be a discord.Message")
        message, _ = await self._load(message)
        return message
