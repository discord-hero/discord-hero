"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""


import asyncio
import traceback

import discord

import hero
from . import cli
from .cli import _main as main


def run(core=None):
    error = False
    error_message = ""
    try:
        loop.run_until_complete(core.run())
    except discord.LoginFailure:
        error = True
        error_message = _('Login failed!')
        choice = input(strings.invalid_credentials)
        if choice.strip() == 'reset':
            core.base.delete_token()
        else:
            core.base.disable_restarting()
    except KeyboardInterrupt:
        core.base.disable_restarting()
        loop.run_until_complete(core.logout())
    except Exception as ex:
        error = True
        print(ex)
        error_message = traceback.format_exc()
        core.base.disable_restarting()
        loop.run_until_complete(core.logout())
    finally:
        if error:
            print(error_message)

    return core


@cli.command()
def install():
    # use cookiecutter
    # connect to DB
    # set up tables
    # connect to Redis
    # set keys
    # TODO
    pass


@cli.command()
def update():
    # sync with cookiecutter template (see https://github.com/audreyr/cookiecutter/issues/784 )
    # TODO
    pass


@cli.command()
def check():
    # TODO
    pass


main()
