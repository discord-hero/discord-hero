"""
discord-hero
~~~~~~~~~~~~

Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import builtins
from collections import namedtuple
import os
import re

ROOT_DIR = os.getcwd()
"""str: The root directory of the running application.
Use in conjunction with ``os.path.join``.
"""

LIB_ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
"""str: The root directory of the discord-hero library.
Use in conjunction with ``os.path.join``.
"""

from .i18n import translate

builtins._ = translate

from discord.ext.commands import command, check, cooldown, Context

from .utils import async_using_db
from .conf import Config, Extension
from .db import Database
from .cog import Cog
from .controller import Controller
# from .perms import (BotPermission, BotPermissions, BotPermissionsEnum)
from .cache import cached, get_cache
from .core import Core


__all__ = ['ROOT_DIR', 'Core', 'Cog', 'Extension', 'VERSION', 'VersionInfo', 'TEST']

__title__ = 'discord-hero'
__author__ = 'monospacedmagic et al.'
__license__ = 'Apache-2.0 OR MIT'
__copyright__ = 'Copyright 2019 monospacedmagic et al.'
__version__ = '0.1.0-alpha.5'
__is_release__ = True


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
)

VERSION = VersionInfo(*re.match(version_pattern, __version__).groups())

LANGUAGE = i18n.Languages.default

TEST = None
