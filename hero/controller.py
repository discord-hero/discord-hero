"""Main entry point for running discord-hero

discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

from aiologger.levels import LogLevel

import hero
from hero import logging


class Controller:
    def __init__(self, core, extension, db, cache):
        self.core = core
        self.extension = extension
        self.db = db
        self.cache = cache
        self.log = logging.Logger.with_default_handlers(name=f"{self.extension.name}.controller",
                                                        level=LogLevel.DEBUG if hero.TEST else LogLevel.INFO,
                                                        loop=self.core.loop)
