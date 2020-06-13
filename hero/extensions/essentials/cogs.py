"""Main entry point for running discord-hero

discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import time

import discord
from discord import RawReactionActionEvent

import hero
from hero import checks, models, strings
from hero.errors import InactiveUser, UserDoesNotExist


class Essentials(hero.Cog):
    core: hero.Core

    @hero.command()
    @checks.is_owner()
    async def set_prefixes(self, ctx, *prefixes: str):
        await self.core.set_prefixes(prefixes)
        await ctx.send("Done.")

    @hero.command()
    @checks.is_owner()
    async def set_description(self, ctx, *, description: str):
        await self.core.set_description(description)
        await ctx.send("Done.")

    @hero.command()
    @checks.is_owner()
    async def set_status(self, ctx, *, status: str):
        await self.core.set_status(status)
        await ctx.send("Done.")

    @hero.command()
    async def ping(self, ctx):
        """Calculates the ping time."""
        t_1 = time.perf_counter()
        await ctx.trigger_typing()
        t_2 = time.perf_counter()
        time_delta = round((t_2-t_1)*1000)
        await ctx.send("Pong.\nTime: {}ms".format(time_delta))

    # GDPR
    @hero.command()
    async def register(self, ctx: hero.Context):
        """Registers you in my system."""
        if ctx.guild:
            user = ctx.author._user
        else:
            user = ctx.author

        try:
            user = await self.db.wrap_user(user)
            await ctx.send("You are already registered in my system!")
            return
        except UserDoesNotExist:
            user = models.User(user.id)
            await user.async_save()
        except InactiveUser:
            user = models.User(user.id)
            user.is_active = True
            await user.async_save()

        await ctx.send(f"You are now registered. Thank you for using my commands and functions!\n\n"
                       f"If you ever change your mind, just use `{ctx.prefix}unregister` to "
                       f"remove yourself from my system, which will irreversibly and immediately "
                       f"delete all data related to your Discord ID from my system.")

    # GDPR
    @hero.command()
    async def unregister(self, ctx):
        """Removes you from my system."""
        if ctx.guild:
            user = ctx.author._user
        else:
            user = ctx.author

        try:
            user = await self.db.wrap_user(user)
            await user.async_delete()
        except UserDoesNotExist:
            user = models.User(user.id)
            user.is_active = False
            await user.async_save()
        except InactiveUser:
            await ctx.send("You are already unregistered!")
            return
        await ctx.send(f"You have been successfully removed from my system! You will have to use "
                       f"`{ctx.prefix}register` if you change your mind to enable storing data "
                       f"related to your Discord user ID again.")

    @hero.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        user_id = payload.user_id
        emoji: discord.PartialEmoji = payload.emoji
        message_id = payload.message_id
        guild_id = payload.guild_id
        channel_id = payload.channel_id

        # obligatory checks for efficiency
        if user_id == self.core.user.id or emoji.is_custom_emoji() or emoji.name != self.core.YES_EMOJI:
            return

        # check if message is user's register_message
        user = models.User(id=user_id)
        register_message = await user._get_register_message()
        if register_message is None or register_message.id != message_id:
            return

        # register the user
        user.is_active = True
        await user.async_save()
        await user.register_message.async_delete()
        await user.fetch()

        channel = None
        if guild_id is not None:
            guild = await self.core.get_guild(guild_id)
            if guild is None:
                await self.core.fetch_guild(guild_id)
            if guild is not None:
                channel = guild.get_channel(channel_id)

        message_text = "{user}, you have now been registered! Remember, you can use " \
                       "`{prefix}unregister` to immediately delete all data related to " \
                       "your Discord ID from my system."
        try:
            await user.send(message_text.format(user=user.name, prefix=self.core.default_prefix))
        except discord.Forbidden:
            if channel is not None:
                await channel.send(message_text.format(user=user.mention, prefix=self.core.default_prefix))
