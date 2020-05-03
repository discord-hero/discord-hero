"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

from enum import Enum


class Languages(Enum):
    # TODO
    en_us = 'en_US'
    default = 'en_US'
    custom = 'custom'

    def __len__(self):
        return len(self.value)


def translate(s: str, translation_context=None):
    if translation_context is None:
        return s
    return translation_context.translate(s)
