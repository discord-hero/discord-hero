"""
discord-hero
~~~~~~~~~~~~

Discord Application Framework for humans

:copyright: (c) 2019 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""


import os

ROOT_DIR = os.getcwd()

import builtins
from collections import namedtuple

from . import i18n

builtins._ = i18n.translate

from tortoise import fields
from tortoise.models import Model

from discord.ext.commands import command

from .core import Core
from .cog import Cog
from .conf import Extension, production_config, test_config
from .db import Database, Object
from .models import (Settings, User, Guild, TextChannel, VoiceChannel,
                     Role, Emoji, Member, Message)
from .cache import cached, get_cache


__all__ = ['ROOT_DIR', 'Core', 'Cog', 'Extension', 'Database', 'Object', 'User',
           'Guild', 'TextChannel', 'VoiceChannel', 'Role', 'Emoji', 'Member',
           'Message', 'cached', 'get_cache', 'CONFIG', 'TEST']


__title__ = 'Hero'
__author__ = 'monospacedmagic et al.'
__license__ = 'Apache-2.0 OR MIT'
__copyright__ = 'Copyright 2019 monospacedmagic et al.'
__version__ = '0.1.0'
__is_release__ = False


VersionInfo = namedtuple('VersionInfo', 'major minor micro releaselevel serial')

VERSION_INFO = VersionInfo(major=0, minor=1, micro=0, releaselevel='alpha', serial=0)


CONFIG = None


__test = None


@property
def TEST():
    return __test


@TEST.setter
def TEST(is_test: bool):
    global __test
    global CONFIG
    if not isinstance(is_test, bool):
        raise ValueError(_("hero.TEST must be set to a boolean value"))
    if isinstance(__test, bool):
        raise RuntimeError(_("Tried to set hero.TEST when it was already set"))
    if is_test:
        CONFIG = test_config
    else:
        CONFIG = production_config
    __test = is_test
