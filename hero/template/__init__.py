from hero import ExtensionConfig, version

__version__ = "0.1.0-alpha"

VERSION = version(__version__)


class nameConfig(ExtensionConfig):
    verbose_name = "{name} Tools"