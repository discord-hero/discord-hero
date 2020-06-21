"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import asyncio

from django.core.exceptions import ObjectDoesNotExist


class ConfigurationError(ValueError):
    pass


class NotUpdated(RuntimeError):
    pass


class InvalidArgument(ValueError):
    pass


class InactiveUser(ObjectDoesNotExist):
    def __init__(self, *args, user_id=None):
        self.user_id = user_id
        super().__init__(*args)


class UserDoesNotExist(ObjectDoesNotExist):
    def __init__(self, *args, user_id=None):
        self.user_id = user_id
        super().__init__(*args)


class ResponseTookTooLong(asyncio.TimeoutError):
    pass


class ExtensionNotFound(Exception):
    def __init__(self, *args, name=None):
        self.name = name
        super().__init__(*args)


class ExtensionAlreadyExists(Exception):
    def __init__(self, *args, name=None):
        self.name = name
        super().__init__(*args)
