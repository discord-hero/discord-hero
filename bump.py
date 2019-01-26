import os

import click


here = os.path.abspath(os.path.dirname(__file__))


@click.command()
def main():
	pass


@main.command()
def major():
	# TODO
	pass


@main.command()
def minor():
	# TODO
	pass


@main.command(aliases=['patch'])
def micro():
	# TODO
	pass


@main.command(aliases=['releaselevel', 'release_level'])
def level():
	# TODO
	pass


@main.command(aliases=['build'])
def serial():
	# TODO
	pass


@main.command(aliases=['exact', 'set'])
@click.argument('ver', str)
def version(ver: str):
	# TODO
	pass
