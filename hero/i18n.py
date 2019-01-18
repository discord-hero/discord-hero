"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""


from enum import Enum


class Language(Enum):
    # TODO
    en_us = 'en_US'
    default = 'en_US'
    custom = 'custom'


def translate(s: str, translation_context):
    return translation_context.translate(s)
