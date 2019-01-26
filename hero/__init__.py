"""
discord-hero
~~~~~~~~~~~~

Discord Application Framework for humans

:copyright: (c) 2019 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import builtins
import os
import re

ROOT_DIR = os.getcwd()

from . import i18n

builtins._ = i18n.translate

from discord.ext.commands import command, check, cooldown

from .models import Model
from .utils import namedtuple_with_defaults as namedtuple
from .core import Core
from .cog import Cog
from .conf import Extension, production_config, test_config
from .db import Database, Object
from .models import (AbstractSettings, User, Guild, TextChannel, VoiceChannel,
                     Role, Emoji, Member, Message)
from .cache import cached, get_cache


__all__ = ['ROOT_DIR', 'Model', 'Core', 'Cog', 'Extension', 'Database', 'Object',
           'User', 'Guild', 'TextChannel', 'VoiceChannel', 'Role', 'Emoji',
           'Member', 'Message', 'cached', 'get_cache', 'CONFIG', 'TEST']


__title__ = 'discord-hero'
__author__ = 'monospacedmagic et al.'
__license__ = 'Apache-2.0 OR MIT'
__copyright__ = 'Copyright 2019 monospacedmagic et al.'
__version__ = '0.1.0'
__is_release__ = False

VersionInfo = namedtuple('VersionInfo', 'major minor micro releaselevel serial',
                         defaults=(0,) * 5)

version_pattern = re.compile(
    # major
    r'(0|[1-9]\d*)\.'
    # minor
    r'(0|[1-9]\d*)\.'
    # micro
    r'(0|[1-9]\d*)'
    # releaselevel
    r'?(?:'
    r'-(0|[1-9]\d*|\d*[A-Za-z][\dA-Za-z]*)'
    r')'
    # serial
    r'?(?:'
    r'\.(0|[1-9]\d*|\d*[A-Za-z][\dA-Za-z]*))*'
    r')'
)

VERSION = VersionInfo(*re.match(version_pattern, __version__))

CONFIG = None

LANGUAGE = i18n.Languages.default

__test = None


@property
def TEST():
    return __test


@TEST.setter
def TEST(is_test: bool):
    global __test
    global CONFIG
    if not isinstance(is_test, bool):
        raise ValueError("hero.TEST must be set to a boolean value")
    if __test is not None:
        raise RuntimeError("Tried to set hero.TEST when it was already set")
    # TODO use read-only mapping view
    if is_test:
        CONFIG = test_config
    else:
        CONFIG = production_config
    __test = is_test
