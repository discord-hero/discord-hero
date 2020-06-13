"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import warnings

from aiologger.levels import LogLevel

import hero
from hero import logging, utils

from discord.ext.commands import cog as _discord_cog, GroupMixin


class Cog(_discord_cog.Cog):
    def __init__(self, core, extension: hero.Extension):
        self.core = core
        self.extension = extension
        self.ctl = core.get_controller(self.extension.name)
        self.db = hero.Database(self.core)
        self.cache = hero.get_cache(self.extension.name)
        self.settings = core.get_settings(self.extension.name)

        self.log = logging.Logger.with_default_handlers(name=f"hero.extensions.{self.qualified_name}",
                                                        level=LogLevel.DEBUG if hero.TEST else LogLevel.INFO,
                                                        loop=self.core.loop)

    @property
    def bot(self):
        warnings.warn("self.bot is deprecated; use self.core instead", DeprecationWarning)
        return self.core

    @property
    def name(self):
        return utils.snakecaseify(self.__class__.__name__)

    @property
    def qualified_name(self):
        return f'{self.extension.name}.cogs.{self.name}'

    @property
    def config(self):
        return self.extension.config

    def _inject(self, core):
        cls = self.__class__

        # realistically, the only thing that can cause loading errors
        # is essentially just the command loading, which raises if there are
        # duplicates. When this condition is met, we want to undo all what
        # we've added so far for some form of atomic loading.
        for index, command in enumerate(self.__cog_commands__):
            command.cog = self
            if not isinstance(command, GroupMixin) or command.name not in core.all_commands:
                try:
                    core.add_command(command)
                except Exception as e:
                    # undo our additions
                    for to_undo in self.__cog_commands__[:index]:
                        core.remove_command(to_undo)
                    raise e

        # check if we're overriding the default
        if cls.bot_check is not Cog.bot_check:
            core.add_check(self.bot_check)

        if cls.bot_check_once is not Cog.bot_check_once:
            core.add_check(self.bot_check_once, call_once=True)

        # while Bot.add_listener can raise if it's not a coroutine,
        # this precondition is already met by the listener decorator,
        # thus this should never raise.
        # Outside of, memory errors and the like...
        for name, method_name in self.__cog_listeners__:
            core.add_listener(getattr(self, method_name), name)

        return self

    def _eject(self, core):
        cls = self.__class__

        try:
            for command in self.__cog_commands__:
                core.remove_command(command.name)
                if command.parent is not None:
                    command.parent.remove_command(command.name)

            for _, method_name in self.__cog_listeners__:
                core.remove_listener(getattr(self, method_name))

            if cls.bot_check is not Cog.bot_check:
                core.remove_check(self.bot_check)

            if cls.bot_check_once is not Cog.bot_check_once:
                core.remove_check(self.bot_check_once, call_once=True)
        finally:
            self.cog_unload()


listener = Cog.listener
