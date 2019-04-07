"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import click
from click import argument, option

import hero
from .main import main


@click.group(name='main')
@click.option('-t/-p', '--test/--prod', default=not hero.__is_release__)
def main_cli(test):
    main(test=test)


command = main_cli.command
group = main_cli.group
