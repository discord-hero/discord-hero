import typing

import aiocache

import ultima
from .errors import ConfigurationError


if ultima.CONFIG['cache'] is None:
    _Cache = aiocache.SimpleMemoryCache
else:
    _Cache = aiocache.RedisCache


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
    aiocache.caches.set_config({namespace: _cache_config})
    return aiocache.caches.get(namespace)


class Cache:
    """Represents Ultima's cache.
    This class is mainly used to store keys into and retrieve keys
    from the cache.

    :param extension:
        If specified, the :class:`Cache` stores data in the
        extension's own namespace.
    :type extension: typing.Optional[str]
    :param core:
        The core.
    :type core: ultima.Core
    :ivar backend:
        The cache backend the :class:`Cache` connects to.
    :ivar extension:
        If specified, the :class:`Cache` stores data in that
        extension's own storage area.
    :ivar core:
        The core.
    """
    def __init__(self, extension=None, core=None, loop=None):
        self.backend = get_cache(extension)  #: aiocache.
        self.extension = extension
        self.bot = core
        if loop is None and self.bot is not None and hasattr(self.bot, 'loop'):
            self.loop = self.bot.loop
        else:
            self.loop = loop


def cached(expire_after=None, include_self=True):
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
    :type expire_after: typing.Optional[int]
    :param include_self:
        Whether or not ``self`` should be included when checking
        whether or not the parameters passed to the decorated
        function are equal to ones that were passed to the
        function before.
    :type include_self: typing.Optional[bool]
    """
    return aiocache.cached(ttl=expire_after, alias='default', noself=not include_self)


def init():
    cache_config = ultima.CONFIG.get('cache', None)
    if cache_config is None or cache_config.get('backend', None) is None:
        _cache_config = {
            'default': {
                'cache': 'aiocache.SimpleMemoryCache',
                'namespace': 'ultima'
            }
        }
    elif ultima.CONFIG['cache']['backend'] == 'redis':
        _cache_config = {
            'default': {
                'cache': 'aiocache.RedisCache',
                'endpoint': ultima.CONFIG['cache'].get('host', '127.0.0.1'),
                'port': ultima.CONFIG['cache'].get('port', 6379),
                'password': ultima.CONFIG['cache'].get('password', None),
                'db': ultima.CONFIG['cache'].get('db', 0),
                'namespace': ultima.CONFIG['cache'].get('namespace', 'ultima'),
                'pool_min_size': ultima.CONFIG['cache'].get('pool_min_size', 1),
                'pool_max_size': ultima.CONFIG['cache'].get('pool_max_size', 10),
                'serializer': {
                    'class': 'aiocache.serializers.PickleSerializer'
                },
                'plugins': [
                    {'class': 'aiocache.plugins.HitMissRatioPlugin'},
                    {'class': 'aiocache.plugins.TimingPlugin'}
                ]
            }
        }
    else:
        raise ConfigurationError(f"The configuration uses an unsupported cache backend: "
                                 f"{ultima.CONFIG['cache']['backend']}")

    aiocache.caches.set_config(_cache_config)
