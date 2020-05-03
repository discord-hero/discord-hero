"""Main entry point for running discord-hero

discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import asyncio
import os
import sys

import django
from django.core import management

import hero
from hero.cli import prompt, confirm, launch
from hero.conf import Config


def main(test, **kwargs):
    # check configuration and request missing information from user

    # dotenv config values
    os.environ['PROD'] = str(not test)
    os.environ.update({key: str(value) for key, value in kwargs.items() if value is not None})

    # TODO custom prompt function based on click's that asks for config details that aren't given

    database_type = os.getenv('DB_TYPE')
    if database_type != 'sqlite':
        os.environ['DB_HOST'] = prompt("DB host", value_proc=str, default='localhost')
        os.environ['DB_PORT'] = prompt("DB port", value_proc=str,
                                       default='5432' if database_type == 'postgres'
                                       else '3306' if database_type == 'mysql' else None)
        os.environ['DB_NAME'] = prompt("DB name", value_proc=str)
        os.environ['DB_USER'] = prompt("DB user", value_proc=str)
        os.environ['DB_PASSWORD'] = prompt("DB password", value_proc=str, hide_input=True)

    cache_type = os.getenv('CACHE_TYPE')
    if os.getenv('CACHE_TYPE') != 'simple':
        os.environ['CACHE_HOST'] = prompt("Cache host", value_proc=str, default='localhost')
        os.environ['CACHE_PORT'] = prompt("Cache port", value_proc=str,
                                          default='6379' if cache_type == 'redis' else None)
        os.environ['CACHE_PASSWORD'] = input("Cache password: ")
        os.environ['CACHE_DB'] = prompt("Cache number", value_proc=str, default='0')

    if not os.getenv('BOT_TOKEN'):
        if sys.platform in ('win32', 'cygwin', 'darwin'):
            if confirm("You need a bot token for your bot. Do you want to create a "
                       "bot now? (This will open a browser window/tab.)"):
                launch("https://discordapp.com/developers/applications/")
        os.environ['BOT_TOKEN'] = input("Bot token: ")

    config = Config(test)
    config.save()

    # load extensions
    with open(os.path.join(hero.ROOT_DIR, 'extensions.txt')) as extensions_file:
        os.environ['EXTENSIONS'] = ';'.join(extensions_file.readlines())
    with open(os.path.join(hero.ROOT_DIR, 'local_extensions.txt')) as local_extensions_file:
        os.environ['LOCAL_EXTENSIONS'] = ';'.join(local_extensions_file.readlines())

    hero.TEST = test
    os.environ['PROD'] = str(not test)

    # setup cache
    hero.cache.init()

    # setup django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hero.django_settings")
    django.setup(set_prefix=False)

    # handle database model changes of the library itself
    management.call_command('makemigrations', 'hero', interactive=False)
    management.call_command('makemigrations', 'hero', interactive=False, merge=True)

    try:
        management.call_command('migrate', 'hero', interactive=False)
    except management.CommandError as command_error:
        print(command_error)

    from hero.models import CoreSettings

    # setup asyncio loop
    try:
        # noinspection PyUnresolvedReferences
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        pass

    if sys.platform == "win32":
        asyncio.set_event_loop(asyncio.ProactorEventLoop())

    loop = asyncio.get_event_loop()

    # db config values
    settings = CoreSettings(os.getenv('NAMESPACE'))
    try:
        settings.load()
    except CoreSettings.DoesNotExist:
        settings.prefixes = [prompt("Bot command prefix", value_proc=str, default='!')]
        settings.description = [prompt("Short description of your bot", value_proc=str, default='')]
        settings.save()

    with hero.Core(config=config, settings=settings, name=os.getenv('NAMESPACE', 'default'), loop=loop) as core:
        # handle database model changes
        management.call_command('makemigrations', interactive=False)
        management.call_command('makemigrations', interactive=False, merge=True)
        try:
            management.call_command('migrate', interactive=False)
        except management.CommandError as command_error:
            print(command_error)

        core.run()
