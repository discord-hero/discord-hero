"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""


from importlib.util import spec_from_file_location, module_from_spec
import os

import toml

import hero


class Extension:
    def __init__(self, name: str, module):
        self.name = name
        self._module = module

    def get_models(self):
        try:
            models_module = self._module.models
            module_dict = models_module.__dict__
            try:
                to_import = models_module.__all__
            except AttributeError:
                to_import = [name for name in module_dict if not name.startswith('_')]

            return [module_dict[name] for name in to_import
                    if issubclass(module_dict[name], hero.Model)]
        except AttributeError:
            return []

    def __getattr__(self, item):
        return getattr(self._module, item, None)

    def __str__(self):
        return self.name


class Extensions(dict):
    def __init__(self, name: str = None):
        self.name = name or 'default'
        with open(os.path.join(hero.ROOT_DIR, 'Herofile')) as toml_file:
            self._data = toml.load(toml_file)[self.name]['extensions']
        gen = ((_name, Extension(_name, self.get_extension_module(_name)))
               for _name in self._data.keys())
        super(Extensions, self).__init__(gen)

    def reload(self):
        with open(os.path.join(hero.ROOT_DIR, 'Herofile')) as toml_file:
            self._data = toml.load(toml_file)[self.name]['extensions']
        gen = ((_name, Extension(_name, self.get_extension_module(_name)))
               for _name in self._data.keys())
        self.clear()
        self.update(gen)

    @classmethod
    def get_extension_module(cls, name: str):
        spec = spec_from_file_location(f'ultima.extensions.{name}',
                                       os.path.join(hero.ROOT_DIR, 'extensions',
                                                    name, '__init__.py'))
        module = module_from_spec(spec)
        spec.loader.exec_module(module)


class _Config(dict):
    def __init__(self, config, extensions: Extensions, permissions: Permissions):
        # TODO write properties for additional attributes
        super(_Config, self).__init__(config)
        self.extensions = extensions
        self.permissions = permissions


with open(os.path.join(hero.ROOT_DIR, 'config', 'config.toml')) as config_file:
    production_config = _Config(toml.load(config_file))

with open(os.path.join(hero.ROOT_DIR, 'config', 'test_config.toml')) as test_config_file:
    test_config = _Config(toml.load(test_config_file))
