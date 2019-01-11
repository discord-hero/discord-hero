"""
Ultima
~~~~~

Discord Application Framework

:copyright: (c) 2019 monospacedmagic et al.
:license: MIT, see LICENSE for more details.
"""


import os

ROOT_DIR = os.getcwd()

import builtins
from collections import namedtuple

from . import i18n

builtins._ = i18n.dummy_translation

from tortoise import fields
from tortoise.models import Model

from discord.ext.commands import command

from .core import Core
from .cog import Cog
from .conf import production_config, test_config
from .models import Settings, User, Guild, TextChannel, VoiceChannel, Role, Member, Message
from .cache import cached, get_cache


__all__ = ['ROOT_DIR', 'Core', 'Cog', 'User', 'Guild', 'TextChannel', 'VoiceChannel',
           'Role', 'Member', 'Message', 'cached', 'get_cache', 'CONFIG', 'TEST']


__title__ = 'Ultima'
__author__ = 'monospacedmagic et al.'
__license__ = 'ISC'
__copyright__ = 'Copyright 2019 monospacedmagic et al.'
__version__ = '0.1.0'


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
        raise ValueError(_("ultima.TEST must be set to a boolean value"))
    if isinstance(__test, bool):
        raise RuntimeError(_("Tried to set ultima.TEST when it was already set"))
    if is_test:
        CONFIG = test_config
    else:
        CONFIG = production_config
    __test = is_test
