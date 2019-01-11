import json
import os

import ultima


class _Config:
    def __init__(self, config):
        # TODO set attributes and write read-only properties
        self._config = config


with open(os.path.join(ultima.ROOT_DIR, 'config.json')) as config_file:
    production_config = _Config(json.load(config_file))

with open(os.path.join(ultima.ROOT_DIR, 'test_config.json')) as test_config_file:
    test_config = _Config(json.load(test_config_file))
