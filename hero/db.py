"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import discord


class Database:
    def __init__(self, core):
        self.core = core

        from hero.models import (User, Guild, TextChannel, VoiceChannel,
                                 Role, Emoji, Member, Message)
        self._model_map = {
            discord.User: User,
            discord.Guild: Guild,
            discord.TextChannel: TextChannel,
            discord.VoiceChannel: VoiceChannel,
            discord.Role: Role,
            discord.Emoji: Emoji,
            discord.PartialEmoji: Emoji,
            discord.Member: Member,
            discord.Message: Message
        }

    async def load(self, discord_obj):
        if isinstance(discord_obj, tuple(self._model_map.keys())):
            cls = self._model_map[type(discord_obj)]
            obj, existed_already = await cls.from_discord_obj(discord_obj)
            return obj, existed_already
        else:
            raise TypeError("obj has to be an object from Discord")
