#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os
import re
from setuptools import find_namespace_packages, setup, Command
from shutil import rmtree
import stat
import sys


here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, 'README.rst'), encoding='utf-8') as readme_file:
    readme = readme_file.read()

python_requirement = '>= 3.7.0'

requirements = [
    "django",
    "discord.py",
    "aiocache",
    "click",
    "aiologger",
    "aiofiles",
    "python-dotenv",
    "colorama; sys_platform == 'win32'",
    "uvloop; sys_platform != 'win32' and implementation_name == 'cpython'",
]

test_requirements = [
    'pytest',
    'pytest-asyncio'
]

setup_requirements = []

extra_requirements = {
    'redis': ['aioredis>=1.0.0'],
    'postgresql': ['psycopg2']
}

with codecs.open(os.path.join(here, 'hero', '__init__.py'), encoding='utf-8') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        f.read(), re.MULTILINE).group(1)


class PublishCommand(Command):
    """Support setup.py publish [--test]"""

    description = 'Build and publish the package.'
    user_options = [
        ('test', None, 'publish to TestPyPI')
    ]

    def initialize_options(self):
        self.test = False

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
            print('Removing previous buildsâ€¦')
            rmtree(os.path.join(here, 'dist'), onerror=onerror)
        except (OSError, FileNotFoundError):
            pass

        print('Building Source and Wheel distribution...')
        os.system('{0} setup.py sdist bdist_wheel'.format(sys.executable))

        if self.test:
            print('Uploading the package to TestPyPI via Twine...')
            os.system('twine upload --repository testpypi dist/*')
        else:
            print('Uploading the package to PyPI via Twine...')
            os.system('twine upload dist/*')

        sys.exit()


setup(
    author="monospacedmagic",
    author_email='luci@monospacedmagic.dev',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Other Environment',
        'Environment :: Web Environment',
        'Framework :: AsyncIO',
        'Framework :: Django',
        'Framework :: Django :: 3.0',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Communications :: Chat',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    cmdclass={
        'publish': PublishCommand,
    },
    dependency_links=[],
    description="discord-hero is an asynchronous, fully modular Discord bot framework that comes with "
                "batteries included, allowing you to write powerful Discord applications easily and quickly.",
    entry_points={
        'console_scripts': [
            'hero=hero.cli:main_cli',
        ],
    },
    extras_require=extra_requirements,
    install_requires=requirements,
    license="Apache-2.0 OR MIT",
    long_description=readme,
    long_description_content_type='text/x-rst',
    include_package_data=True,
    keywords='discord bot framework django',
    name='discord-hero',
    packages=find_namespace_packages(include=['hero', 'hero.*', 'hero.extensions.essentials'], exclude=['*.migrations']),
    python_requires=python_requirement,
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/discord-hero/discord-hero',
    version=version,
    zip_safe=False,
)
