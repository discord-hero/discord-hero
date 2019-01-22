#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
from setuptools import find_packages, setup, Command
from shutil import rmtree
import stat
import sys


here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.rst')) as readme_file:
    readme = readme_file.read()

python_requirement = '>=3.6.0'

discordpy_version = '7f4c57dd5ad20b7fa10aea485f674a4bc24b9547'

requirements = [
    "responder",
    "tortoise-orm",
    "aiocache",
    "graphene",
    "click",
    "aiologger",
    "libsass",
    "aiofiles",
    "toml",
    "uvloop; sys_platform != 'win32'",
]

test_requirements = [
    'pytest',
    'pytest-asyncio'
]

setup_requirements = []

extra_requirements = {
    'redis:python_version<"3.7"': ['aioredis>=0.3.3'],
    'redis:python_version>="3.7"': ['aioredis>=1.0.0'],
    'memcached': ['aiomcache>=0.5.2'],
    'msgpack': ['msgpack>=0.5.5'],
    'postgresql': ['asyncpg'],
    'mysql': ['aiomysql']
}

with open(os.path.join(here, 'hero', '__init__.py')) as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        f.read(), re.MULTILINE).group(1)


class PublishCommand(Command):
    """Support setup.py publish."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        def onerror(func, path, exc_info):
            """``shutil.rmtree`` error handler that helps deleting read-only files on Windows."""
            if not os.access(path, os.W_OK):
                os.chmod(path, stat.S_IWUSR)
                func(path)
            else:
                raise exc_info[0](exc_info[1])

        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'), onerror=onerror)
        except (OSError, FileNotFoundError):
            pass

        self.status('Building Source and Wheel (universal) distribution...')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPI via Twine...')
        os.system('twine upload dist/*')

        sys.exit()


setup(
    author="Monospaced Magic",
    author_email='lucina@monospacedmagic.io',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: Other Environment',
        'Environment :: Plugins',
        'Environment :: Web Environment',
        'Framework :: AsyncIO',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: JavaScript',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Communications :: Chat',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    cmdclass={
        'publish': PublishCommand,
    },
    dependency_links=[
        'http://github.com/Rapptz/discord.py/tarball/{}#egg=discord.py'.format(discordpy_version)
    ],
    description="discord-hero is an asynchronous, fully modular application framework for humans "
                "allowing you to write applications that connect to Discord.",
    entry_points={
        'console_scripts': [
            'hero=hero.cli:main_cli',
        ],
    },
    extras_require=extra_requirements,
    install_requires=requirements,
    license="Apache-2.0 OR MIT",
    long_description=readme,
    long_description_content_type='text/rst',
    include_package_data=True,
    keywords='hero',
    name='hero',
    packages=find_packages(include=['hero']),
    python_requires=python_requirement,
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/monospacedmagic/discord-hero',
    version=version,
    zip_safe=False,
)
