"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import importlib
from importlib.util import spec_from_file_location, module_from_spec
import inspect
import os

from django.apps import AppConfig
from django.core.management.utils import get_random_secret_key

from dotenv import load_dotenv

import hero
from .errors import ConfigurationError, ExtensionNotFound, InvalidArgument


class ExtensionConfig(AppConfig):
    def __init_subclass__(cls, **kwargs):
        cls.name = cls.__module__


class Extension:
    def __init__(self, name: str, module):
        self.name = name
        self._module = module

    @classmethod
    async def convert(cls, ctx, argument):
        core: hero.Core = ctx.bot
        try:
            argument = str(argument)
            extension = core.get_extension(argument)
        except TypeError:
            raise InvalidArgument("extension must be an extension name")
        if extension is None:
            raise ExtensionNotFound(name=argument)
        return extension

    @property
    def module_name(self):
        if self._module is None:
            return None
        return self._module.__name__

    @property
    def config_cls(self) -> ExtensionConfig:
        config_class = inspect.getmembers(self._module, lambda member: isinstance(member, type)
                                                                       and issubclass(member, ExtensionConfig)
                                                                       and member is not ExtensionConfig)
        return config_class[0][1]

    def get_controller(self, core):
        db = hero.Database(core)
        cache = hero.get_cache(self.name)
        settings = core.get_settings(self.name)
        _ControllerClass = self._controller_cls
        if _ControllerClass is None:
            return None
        return _ControllerClass(core, self, db, cache, settings)

    @property
    def _controller_cls(self):
        try:
            controller_module = importlib.import_module(f'extensions.{self.name}.controller')
        except ImportError:
            try:
                controller_module = importlib.import_module(f'hero.extensions.{self.name}.controller')
            except ImportError:
                return None

        controller_class = inspect.getmembers(controller_module, lambda member: isinstance(member, type)
                                                                                and issubclass(member, hero.Controller)
                                                                                and member is not hero.Controller)
        return controller_class[0][1]

    def get_settings(self, core):
        _SettingsModel = self._settings_model
        if _SettingsModel is None:
            return None
        settings, _ = _SettingsModel.get_or_create(namespace=core.settings)
        return settings

    @property
    def _settings_model(self):
        try:
            models_module = importlib.import_module(f'extensions.{self.name}.models')
        except ImportError:
            try:
                models_module = importlib.import_module(f'hero.extensions.{self.name}.models')
            except ImportError:
                return None

        from hero.models import CoreSettings, Settings

        settings_model = inspect.getmembers(models_module, lambda member: isinstance(member, type)
                                                                          and issubclass(member, Settings)
                                                                          and member is not Settings
                                                                          and member is not CoreSettings)
        if not len(settings_model):
            return None
        return settings_model[0][1]

    def load_models(self):
        from hero.models import Model
        try:
            models_module = self._module.models
            module_dict = models_module.__dict__
            try:
                to_import = models_module.__all__
            except AttributeError:
                to_import = [name for name in module_dict if not name.startswith('_')]

            return [module_dict[name] for name in to_import
                    if issubclass(module_dict[name], Model)]
        except AttributeError:
            return []

    def __str__(self):
        return self.name


class Extensions(dict):
    def __init__(self, name: str = None):
        self.name = name or 'default'
        self._extensions = ['essentials']
        self._local_extensions = []
        self.loaded_by_core = []
        super(Extensions, self).__init__()

    @property
    def data(self):
        return self._extensions + self._local_extensions

    def load(self):
        with open(os.path.join(hero.ROOT_DIR, 'extensions.txt')) as extensions_file:
            _extensions = extensions_file.read().splitlines()
        os.environ['EXTENSIONS'] = ';'.join(_extensions)
        with open(os.path.join(hero.ROOT_DIR, 'local_extensions.txt')) as local_extensions_file:
            _local_extensions = local_extensions_file.read().splitlines()
        os.environ['LOCAL_EXTENSIONS'] = ';'.join(_local_extensions)
        if _extensions:
            self._extensions = ['essentials'] + _extensions
        else:
            self._extensions = ['essentials']
        if _local_extensions:
            self._local_extensions = _local_extensions
        else:
            self._local_extensions = []
        _gen = ((_name, Extension(_name, self.get_extension_module(_name, local=False)))
                for _name in self._extensions)
        _local_gen = ((_name, Extension(_name, self.get_extension_module(_name, local=True)))
                      for _name in self._local_extensions)
        self.clear()
        self.update(_gen)
        self.update(_local_gen)

    @classmethod
    def get_extension_module(cls, name: str, local: bool):
        if name == "essentials":
            return None
        if local:
            spec = spec_from_file_location(f'extensions.{name}',
                                           os.path.join(hero.ROOT_DIR, 'extensions',
                                                        name, '__init__.py'))
        else:
            spec = spec_from_file_location(f'hero.extensions.{name}',
                                           os.path.join(hero.LIB_ROOT_DIR, 'extensions',
                                                        name, '__init__.py'))
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


class Config:
    def __init__(self, test):
        self.test = test
        self._load()

    def _load(self):
        """expects environment variables to exist already"""
        self.bot_token = os.getenv('BOT_TOKEN')
        self.disabled_extensions = os.getenv('DISABLED_EXTENSIONS', '').split(';')

    @property
    def file_name(self):
        return '.testenv' if self.test else '.env'

    @property
    def file_path(self):
        return os.path.join(hero.ROOT_DIR, self.file_name)

    def reload(self):
        load_dotenv(self.file_path)

    def generate_config_dict(self):
        _config = {
            'PROD': os.getenv('PROD', self.test),
            'NAMESPACE': os.getenv('NAMESPACE', 'default'),
            'SECRET_KEY': os.getenv('SECRET_KEY', get_random_secret_key()),
            'BOT_TOKEN': os.getenv('BOT_TOKEN'),
            'DB_TYPE': os.getenv('DB_TYPE', 'sqlite'),
            'DB_NAME': os.getenv('DB_NAME', None),
            'DB_USER': os.getenv('DB_USER', None),
            'DB_PASSWORD': os.getenv('DB_PASSWORD', None),
            'DB_HOST': os.getenv('DB_HOST', None),
            'DB_PORT': os.getenv('DB_PORT', None),
            'CACHE_TYPE': os.getenv('CACHE_TYPE', 'simple'),
            'CACHE_HOST': os.getenv('CACHE_HOST', None),
            'CACHE_PORT': os.getenv('CACHE_PORT', None),
            'CACHE_PASSWORD': os.getenv('CACHE_PASSWORD', None),
            'CACHE_DB': os.getenv('CACHE_DB', 0)
        }
        _config = {key: value for key, value in _config.items() if value is not None}
        return _config

    def _generate_dotenv_file(self, config: dict):
        dotenv_lines = [f"export {key}={value}" for key, value in config.items()]
        dotenv_lines.append("")
        dotenv_lines = '\n'.join(dotenv_lines)
        with open(self.file_path, 'w+') as dotenv_file:
            dotenv_file.write(dotenv_lines)

    def save(self, config_dict=None):
        if config_dict is None:
            config_dict = self.generate_config_dict()
        self._generate_dotenv_file(config_dict)
        self.reload()


def get_extension_config(extension_name, local=False):
    module = Extensions.get_extension_module(extension_name, local=local)
    extension = Extension(extension_name, module)
    try:
        return extension.config_cls
    except IndexError:
        raise ConfigurationError(f"extension {extension_name} doesn't have a hero.ExtensionConfig subclass")
