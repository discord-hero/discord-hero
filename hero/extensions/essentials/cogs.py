"""Main entry point for running discord-hero

discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import time

import discord

import hero
from hero import checks


class Essentials(hero.Cog):
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
    async def ping(self, ctx):
        """Calculates the ping time."""
        t_1 = time.perf_counter()
        await ctx.trigger_typing()
        t_2 = time.perf_counter()
        time_delta = round((t_2-t_1)*1000)
        await ctx.send("Pong.\nTime: {}ms".format(time_delta))
