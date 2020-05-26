"""
discord-hero
~~~~~~~~~~~~

Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import builtins
from collections import namedtuple
from importlib.util import spec_from_file_location
import os
import re
import sys

_GLOBAL_VAR_NAME = '_do_not_include_all'


def _start_all(globs):
    globs[_GLOBAL_VAR_NAME] = list(globs.keys()) + [_GLOBAL_VAR_NAME]


def _end_all(globs):
    globs['__all__'] = list(
        set(list(globs.keys())) - set(globs[_GLOBAL_VAR_NAME])
    )

from django.apps import AppConfig


class DiscordHeroConfig(AppConfig):
    name = 'hero'
    verbose_name = "Discord Hero"


_start_all(globals())

start_all = _start_all

end_all = _end_all

ROOT_DIR = os.getcwd()
"""str: The root directory of the running application.
Use in conjunction with ``os.path.join``.
"""

LIB_ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
"""str: The root directory of the discord-hero library.
Use in conjunction with ``os.path.join``.
"""

sys.path.append(ROOT_DIR)

from .i18n import translate

builtins._ = translate

from discord.ext.commands import command, check, cooldown, Context

from .utils import async_using_db
from .conf import Config, Extension, ExtensionConfig
from .db import Database
from .cog import Cog, listener
from .controller import Controller
# from .perms import (BotPermission, BotPermissions, BotPermissionsEnum)
from .cache import cached, get_cache
from .core import Core
from .errors import ObjectDoesNotExist, ConfigurationError, InvalidArgument


default_app_config = f"{DiscordHeroConfig.__module__}.{DiscordHeroConfig.__name__}"


__title__ = 'discord-hero'
__author__ = 'monospacedmagic et al.'
__license__ = 'Apache-2.0 OR MIT'
__copyright__ = 'Copyright 2019 monospacedmagic et al.'
__version__ = '0.1.0-beta.1'
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

end_all(globals())
