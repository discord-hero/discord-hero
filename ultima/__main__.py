import asyncio
import sys
import traceback

import discord

import aiocache

import ultima
from ultima import cli
from .cache import Cache
from .db import Database


def run(loop=None, bot=None):
    if loop is None:
        loop = asyncio.get_event_loop()

    if bot is None:
        bot = ultima.Core(loop=loop)

    if not bot.is_configured:
        bot.initial_config()

    error = False
    error_message = ""
    try:
        loop.run_until_complete(bot.run())
    except discord.LoginFailure:
        error = True
        error_message = _('Invalid credentials')
        choice = input(strings.invalid_credentials)
        if choice.strip() == 'reset':
            bot.base.delete_token()
        else:
            bot.base.disable_restarting()
    except KeyboardInterrupt:
        bot.base.disable_restarting()
        loop.run_until_complete(bot.logout())
    except Exception as ex:
        error = True
        print(ex)
        error_message = traceback.format_exc()
        bot.base.disable_restarting()
        loop.run_until_complete(bot.logout())
    finally:
        if error:
            print(error_message)

    return bot


@cli.group()
@cli.option('-t', '--test', is_flag=True, default=False)
def main(test):
    if test:
        ultima.TEST = True
    if sys.implementation.name == 'cpython':
        try:
            # noinspection PyUnresolvedReferences
            import uvloop
        except ImportError:
            pass
        else:
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    if sys.platform == "win32":
        asyncio.set_event_loop(asyncio.ProactorEventLoop())

    with Cache() as cache:
        with


@main.command()
def update():
    # sync with cookiecutter template (see https://github.com/audreyr/cookiecutter/issues/784 )
    print("update")


@main.command()
def install():
    # use cookiecutter
    # connect to DB
    # set up tables
    # connect to Redis
    # set keys
    pass


main()
