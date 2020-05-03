"""Default permissions for core models

discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

from .perms import Groups


default_bot_permissions = {
    'core': {
        'help': {
            Groups.EVERYONE: {
                'allowed': True,
                'times': 1,
                'interval': 0.5
            }
        }
    }
}
