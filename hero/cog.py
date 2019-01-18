"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""


import hero
from hero import logging, get_cache, utils


class Cog:
    def __init__(self, core, extension: hero.Extension):
        self.core = core
        self.extension = extension
        self.cache = get_cache(self.extension)
        self.db = hero.Database(self.core, self.extension)

        self.log = logging.Logger.with_default_handlers(name=self.qualified_name,
                                                        level=self.core.settings.logging_level,
                                                        loop=self.core.loop)

    @property
    def name(self):
        return utils.snakecaseify(self.__class__.__name__)

    @property
    def qualified_name(self):
        return f'{self.extension}.{self.name}'


