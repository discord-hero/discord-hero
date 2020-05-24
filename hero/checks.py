"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import hero

from discord.ext.commands import (bot_has_permissions, check, guild_only,
                                  has_permissions, is_nsfw, is_owner)
from discord import TeamMembershipState


def test_only():
    def predicate(ctx):
        return hero.TEST
    return check(predicate)


def bot_staff_only():
    async def predicate(ctx):
        user = ctx.bot.db.load(ctx.author.user if ctx.guild is not None else ctx.author)
        application_info = await ctx.bot.application_info()
        if application_info.team is not None:
            staff_ids = [member.id for member in application_info.team.members
                         if member.membership_state == TeamMembershipState.accepted]
        else:
            staff_ids = [application_info.owner.id]
        return user.is_staff or user.id in staff_ids
    return check(predicate)
