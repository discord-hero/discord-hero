from typing import Union

import discord

import hero


class Settings(hero.Cog):
    @hero.command()
    async def set_permissions(self, ctx, target: Union[discord.Member, discord.Role]=None):
        # TODO
        pass
