"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import os

import aiocache

import hero
from .errors import ConfigurationError


def get_cache(namespace=None):
    if namespace is None:
        return aiocache.caches.get('default')

    try:
        return aiocache.caches.get(namespace)
    except KeyError:
        pass

    _cache_config = aiocache.caches.get_alias_config('default')
    base_namespace = _cache_config['namespace']
    if not base_namespace:
        actual_namespace = namespace
    else:
        actual_namespace = '_'.join((base_namespace, namespace))
    _cache_config['namespace'] = actual_namespace
    aiocache.caches.add(namespace, _cache_config)
    return aiocache.caches.get(namespace)


class Cache:
    """Represents Hero's cache.
    This class is mainly used to store keys into and retrieve keys
    from the cache.

    :param extension:
        If specified, the :class:`Cache` stores data in the
        extension's own namespace.
    :type extension: typing.Optional[str]
    :param core:
        The core.
    :type core: hero.Core
    :ivar backend:
        The cache backend the :class:`Cache` connects to.
    :ivar extension:
        If specified, the :class:`Cache` stores data in that
        extension's own storage area.
    :ivar core:
        The core.
    """
    def __init__(self, extension=None, core=None, loop=None):
        self.backend = get_cache(extension)
        self.extension = extension
        self.bot = core
        if loop is None and self.bot is not None and hasattr(self.bot, 'loop'):
            self.loop = self.bot.loop
        else:
            self.loop = loop


def cached(expire_after=None, key=None, include_self=True):
    """Creates a decorator that caches the return value of the
    decorated function or method.

    The decorated function can be a regular function, a method,
    a coroutine function or a coroutine method. The decorated
    function returns the cached return value only if the
    arguments passed to the function are equal to a set of
    parameters that have been passed to the function before.

    :param expire_after:
        When to discard the cached return value after it has
        been cached. The default is ``None``, which means the
        cached return value does never expire and will not be
        discarded.
    :type expire_after: Optional[int]
    :param key:
        The custom key to save the cached return value in.
        If not provided, a key will be assigned automatically.
        :type key: Optional[str]
    :param include_self:
        Whether or not ``self`` should be included when checking
        whether or not the parameters passed to the decorated
        function are equal to ones that were passed to the
        function before.
    :type include_self: Optional[bool]

    Example: ::

        @cached(expire_after=1800)
        async def expensive_coroutine():
            # highly complicated and expensive calculation
            await asyncio.sleep(10)
            return 1 + 1
    """
    # TODO check parameter for custom validity/integrity checks
    return aiocache.cached(key=key, ttl=expire_after, alias='default', noself=not include_self)


def init():
    cache_type = os.getenv('CACHE_TYPE')
    if cache_type == 'simple':
        _cache_config = {
            'default': {
                'cache': 'aiocache.SimpleMemoryCache',
                'namespace': 'hero',
                'serializer': {
                    'class': 'aiocache.serializers.PickleSerializer'
                }
            }
        }
    elif cache_type == 'redis':
        _cache_config = {
            'default': {
                'cache': 'aiocache.RedisCache',
                'endpoint': os.getenv('CACHE_HOST'),
                'port': os.getenv('CACHE_PORT'),
                'password': os.getenv('CACHE_PASSWORD'),
                'db': os.getenv('CACHE_DB'),
                'namespace': 'hero_' + os.getenv('NAMESPACE'),
                'pool_min_size': 1,
                'pool_max_size': 10,
                'serializer': {
                    'class': 'aiocache.serializers.PickleSerializer'
                }
            }
        }
    else:
        raise ConfigurationError("The configuration uses an unsupported cache backend: "
                                 "{}".format(os.getenv('CACHE_TYPE')))

    aiocache.caches.set_config(_cache_config)
