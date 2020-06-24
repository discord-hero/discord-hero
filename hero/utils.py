"""A collection of various helper functions and utility functions.

discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import asyncio
import copy
import functools
import re

import aiohttp

from asgiref.sync import SyncToAsync, AsyncToSync

import websockets

from discord.utils import maybe_coroutine
from discord.errors import HTTPException, GatewayNotFound, ConnectionClosed


def issubmodule(parent, child):
    return parent == child or child.startswith(parent + ".")


def ismodelobject(obj, model_cls=None):
    # TODO check if model obj is instance of model_cls
    if model_cls is not None:
        return isinstance(obj, model_cls)
    return hasattr(obj, '_meta')


def snakecaseify(s: str):
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r'\1_\2', s)
    s = re.sub(r"([a-z\d])([A-Z])", r'\1_\2', s)
    s = s.replace("-", "_")
    s = s.replace(" ", "_")
    return s.lower()


def titlecaseify(s: str):
    # only supports snake_case, camelCase, PascalCase and SCREAMING_SNAKE_CASE
    if '_' in s:
        s = s.replace('_', ' ')
    else:
        s = s[0] + re.sub(r"([A-Z])", r' \1', s[1:])
    # capitalize first letter (first letters in snake_case)
    s = s.title()
    return s


def estimate_reading_time(text):
    """Estimates the time needed for a user to read a piece of text

    This is assuming 0.9 seconds to react to start reading
    plus 15 chars per second to actually read the text.
    Minimum is 2.4 seconds.

    Parameters
    ----------
    text : str
        The text the reading time should be estimated for.
    """
    read_time = 0.9 + len(text) / 15
    read_time = round(read_time, 1)
    return read_time if read_time > 2.4 else 2.4


def autorestart(delay_start=None, pause=None, restart_check=None):
    """Decorator that automatically restarts the decorated
    coroutine function when a connection issue occurs.

    :param Optional[Callable] delay_start:
        Will be awaited before starting the
        execution of the decorated coroutine function.
    :param Optional[Callable] pause:
        Will be awaited before restarting the
        execution of the decorated coroutine function.
    :param Optional[Callable] restart_check:
        A callable that checks whether the decorated
        coroutine function should be restarted if it
        has been cancelled. Should return a truth value.
        May be a coroutine function.
    """
    if not (delay_start is None or callable(delay_start)):
        raise TypeError("delay_start must be a callable")
    if not (pause is None or callable(pause)):
        raise TypeError("pause must be a callable")
    if not (restart_check is None or callable(restart_check)):
        raise TypeError("restart_check must be a callable")

    def wrapper(coro):
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError("decorated function must be a coroutine function")

        @functools.wraps(coro)
        async def wrapped(*args, **kwargs):
            if delay_start is not None:
                await maybe_coroutine(delay_start)
            try:
                if pause is not None:
                    await maybe_coroutine(pause)
                return await coro(*args, **kwargs)
            except asyncio.CancelledError:
                if restart_check is not None and (await maybe_coroutine(restart_check)):
                    await wrapped(*args, **kwargs)
                else:
                    raise
                # catch connection issues
            except (OSError,
                    HTTPException,
                    GatewayNotFound,
                    ConnectionClosed,
                    aiohttp.ClientError,
                    asyncio.TimeoutError,
                    websockets.InvalidHandshake,
                    websockets.WebSocketProtocolError) as e:
                if any((isinstance(e, ConnectionClosed) and e.code == 1000,  # clean disconnect
                        not isinstance(e, ConnectionClosed))):
                    await wrapped(*args, **kwargs)
                else:
                    raise

        return wrapped

    return wrapper


# somehow asgiref messed up their class decorators??? so this is necessary
class SyncToAsyncThreadSafe(SyncToAsync):
    def __init__(self, func):
        super().__init__(func, thread_sensitive=True)


sync_to_async = SyncToAsync
sync_to_async_threadsafe = SyncToAsyncThreadSafe
async_to_sync = AsyncToSync


class AsyncUsingDB(SyncToAsyncThreadSafe):
    @property
    def sync(self):
        return self.func


async_using_db = AsyncUsingDB
"""Decorate (synchronous) functions with this to turn them into async functions
and enable database operations inside them; otherwise a SynchronousOnlyOperation
exception would be raised by Django. Do NOT decorate an async function with this
as that would be not only redundant but would also stop this decorator from
working as intended.

To use functions decorated with this synchronously, call ``decorated_function.sync``.
"""


def merge_configs(default, overwrite):
    """From `cookiecutter <https://github.com/audreyr/cookiecutter>`__"""
    new_config = copy.deepcopy(default)

    for key, value in overwrite.items():
        if isinstance(value, dict):
            new_config[key] = merge_configs(default[key], value)
        else:
            new_config[key] = value

    return new_config
