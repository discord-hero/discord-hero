from ultima import logging, get_cache
from .db import Database


class Cog:
    def __init__(self, core, extension):
        self.core = core
        self.extension = extension
        self.db = Database(self)
        self.cache = get_cache(self.extension)

        self.log = logging.Logger.with_default_handlers(name=self.qualified_name,
                                                        level=self.core.settings.logging_level,
                                                        loop=self.core.loop)

    @property
    def name(self):
        return self.__class__.__name__.lower()

    @property
    def qualified_name(self):
        return f'ultima.{self.extension}.{self.name}'
