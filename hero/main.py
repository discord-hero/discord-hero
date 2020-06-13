"""Main entry point for running discord-hero

discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import asyncio
import io
import os
import sys

import django
from django.db import OperationalError
from django.core import management

import hero
from hero.cli import prompt, confirm, launch, style
from hero.conf import Config, get_extension_config


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

    # automatically initialize database if using SQLite for convenience
    if database_type == 'sqlite':
        if ((test and not os.path.isfile(os.path.join(hero.ROOT_DIR, "test_db.sqlite3")))
            or (not test and not os.path.isfile(os.path.join(hero.ROOT_DIR, "db.sqlite3")))):
            print("Running `hero dbinit`")
            database_initialization(test, from_main=True, **kwargs)
            print("You can now use `hero` to run your Discord Hero instance.")
            return

    # load extensions
    with open(os.path.join(hero.ROOT_DIR, 'extensions.txt')) as extensions_file:
        extensions = extensions_file.read().splitlines()
        os.environ['EXTENSIONS'] = ';'.join(extensions)
    with open(os.path.join(hero.ROOT_DIR, 'local_extensions.txt')) as local_extensions_file:
        local_extensions = local_extensions_file.read().splitlines()
        os.environ['LOCAL_EXTENSIONS'] = ';'.join(local_extensions)

    configs = []
    for extension in extensions:
        configs.append(get_extension_config(extension))
    for local_extension in local_extensions:
        configs.append(get_extension_config(local_extension, local=True))

    installed_apps = []
    for _config in configs:
        installed_apps.append(f"{_config.__module__}.{_config.__name__}")
    os.environ['INSTALLED_APPS'] = ';'.join(installed_apps)

    hero.TEST = test

    # setup cache
    hero.cache.init()

    # setup django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hero.django_settings")
    django.setup(set_prefix=False)

    # setup asyncio loop
    try:
        # noinspection PyUnresolvedReferences
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        pass

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    loop = asyncio.get_event_loop()

    from hero.models import CoreSettings

    # db config values
    try:
        settings, created = CoreSettings.get_or_create(name=os.getenv('NAMESPACE'))
    except OperationalError:
        print(style("Error: Database hasn't been initialized yet; use `hero dbinit`", fg='red'), file=sys.stderr)
        return
    if created:
        settings.prefixes = [prompt("Bot command prefix", value_proc=str, default='!')]
        settings.description = prompt("Short description of your bot", value_proc=str, default='')
        settings.save()

    with hero.Core(config=config, settings=settings, name=os.getenv('NAMESPACE', 'default'), loop=loop) as core:
        core.run()


def database_initialization(test, *, from_main=False, **kwargs):
    if not from_main:
        os.environ['PROD'] = str(not test)
        os.environ.update({key: str(value) for key, value in kwargs.items() if value is not None})

        database_type = os.getenv('DB_TYPE')
        if database_type != 'sqlite':
            os.environ['DB_HOST'] = prompt("DB host", value_proc=str, default='localhost')
            os.environ['DB_PORT'] = prompt("DB port", value_proc=str,
                                           default='5432' if database_type == 'postgres'
                                           else '3306' if database_type == 'mysql' else None)
            os.environ['DB_NAME'] = prompt("DB name", value_proc=str)
            os.environ['DB_USER'] = prompt("DB user", value_proc=str)
            os.environ['DB_PASSWORD'] = prompt("DB password", value_proc=str, hide_input=True)

    # setup django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hero.django_settings")
    django.setup(set_prefix=False)

    print(f"Initializing database...", end=' ')
    # temporarily silence stdout while we sync the database
    backup_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        management.call_command('makemigrations', 'hero', interactive=False)
        management.call_command('makemigrations', 'hero', interactive=False, merge=True)
        try:
            management.call_command('migrate', 'hero', interactive=False)
        except management.CommandError:
            management.call_command('migrate', 'hero', interactive=False, run_syncdb=True)
    except management.CommandError as command_error:
        print(command_error, file=sys.stderr)
        return False
    else:
        print(style("OK", fg='green'), file=backup_stdout)
        return True
    finally:
        sys.stdout = backup_stdout
