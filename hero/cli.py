"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import os

import click
from click import (argument, option, prompt, confirm, echo, echo_via_pager, style, secho as styled_echo,
                   progressbar, clear, edit, launch)
from dotenv import load_dotenv

import hero
from .main import main


def load_correct_dotenv(ctx, param, is_test):
    file_name = '.testenv' if is_test else '.env'
    file_path = os.path.join(hero.ROOT_DIR, file_name)
    try:
        load_dotenv(file_path)
    except FileNotFoundError:
        pass


@click.group(name='main', invoke_without_command=True)
@click.option('-t/-p', '--test/--prod', callback=load_correct_dotenv, default=True)
@click.option('--namespace', show_default=False,
              default=lambda: os.getenv('NAMESPACE', 'default'))
@click.option('--db-type', type=click.Choice(['sqlite', 'postgres', 'mysql'], case_sensitive=False),
              default=lambda: os.getenv('DB_TYPE', 'sqlite'))
@click.option('--db-name', default=lambda: os.getenv('DB_NAME'))
@click.option('--db-user', default=lambda: os.getenv('DB_USER'))
@click.option('--db-password', default=lambda: os.getenv('DB_PASSWORD'))
@click.option('--db-host', default=lambda: os.getenv('DB_HOST'))
@click.option('--db-port', default=lambda: os.getenv('DB_PORT'))
@click.option('--cache-type', type=click.Choice(['simple', 'redis'], case_sensitive=False),
              default=lambda: os.getenv('CACHE_TYPE', 'simple'))
@click.option('--cache-host', default=lambda: os.getenv('CACHE_HOST'))
@click.option('--cache-port', default=lambda: os.getenv('CACHE_PORT'))
@click.option('--cache-password', default=lambda: os.getenv('CACHE_PASSWORD'))
def main_cli(test, namespace, db_type, db_name, db_user, db_password, db_host, db_port,
             cache_type, cache_host, cache_port, cache_password):
    main(test=not test, namespace=namespace, db_type=db_type, db_name=db_name, db_user=db_user,
         db_password=db_password, db_host=db_host, db_port=db_port, cache_type=cache_type,
         cache_host=cache_host, cache_port=cache_port, cache_password=cache_password)


command = main_cli.command
group = main_cli.group
