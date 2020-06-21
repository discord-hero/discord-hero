discord-hero
============

discord-hero is an asynchronous, fully modular Discord bot framework that comes with
batteries included, allowing you to write powerful `Discord <https://discordapp.com/>`_
applications easily and quickly. It is intended for:

-  developers interested in an **easy way to develop a powerful public
   or private Discord bot** with a clean, readable, pythonic,
   persistent storage solution and easy-to-use caching
-  managers of Discord communities who want to **automate tasks on
   Discord** in a highly customizable way and/or without relying on
   external bots
-  beginner and intermediate level developers who are interested in
   asynchronous concurrency with Python using asyncio
-  any developer who's interested in trying something new and
   wants to give this project a chance!

Although discord-hero is **easy to get started with**, it comes with all
the tools experienced developers enjoy using to build production-ready
applications for communities, games or companies on Discord:

-  a **Discord bot** built on top of
   `discord.py <https://github.com/Rapptz/discord.py>`_
-  [TODO] a **Web API** powered by
   `FastAPI <https://fastapi.tiangolo.com/>`_
-  a **familiar asynchronous ORM** based on
   `Django <https://www.djangoproject.com/>`_
-  an **easy-to-use cache system**, optionally powered by Redis, via
   `aiocache <https://github.com/argaen/aiocache>`_ and
   `aioredis <https://github.com/aio-libs/aioredis>`_
-  full modularity thanks to a clever Extension system

You might think that with all these dependencies Discord Hero will perform badly,
but so far that has actually not been the case at all! Continue reading
if you want to give it a test run.

Getting started
---------------

**Note:** In this section, the content of every code block is intended
to be entered in a terminal / command prompt.

Requirements
~~~~~~~~~~~~

You need `Python 3.7 or above <https://www.python.org/downloads/>`_,
`Git <https://git-scm.com/downloads>`_, ``cookiecutter`` and ``pipenv``.
On Windows you may also need the
`Visual C++ Build Tools <https://visualstudio.microsoft.com/visual-cpp-build-tools/>`_
if you run into errors when trying to install discord-hero.
Install ``cookiecutter`` and ``pipenv`` if you haven’t yet:

Linux / Mac: ::

   python3 install --user -U cookiecutter
   python3 install --user -U --pre pipenv

Windows: ::

   py -3 -m pip install -U cookiecutter
   py -3 -m pip install -U --pre pipenv

If you’re just testing things out, it’s probably fine to just use the
default database and cache solutions (SQLite3 and simple memory cache).
However, if you want to use discord-hero for a production application,
it is recommended to run it on a Linux VPS, dedicated
server or something equally powerful, and use PostgreSQL for storing
data and Redis for caching. To do the latter two changes, check your
`.env` file and make the following changes: ::

    export DB_TYPE=postgres
    export CACHE_TYPE=redis

You will be promped for further configuration details the next time
you run your bot in production mode (``--prod``).

**Note:** ``mysql`` is also an option for ``DB_TYPE``, however it is not
officially supported.

Installation
~~~~~~~~~~~~

Replace ``<your_directory_name>`` with the project name you will have
entered by then. ::

   cookiecutter https://github.com/monospacedmagic/discord-hero-cookiecutter.git
   cd <your_directory_name>
   pipenv install --three

For production applications: ::

   pipenv install discord-hero[postgresql,redis]

Run discord-hero in test mode: ::

   cd <your_project_path>
   pipenv run hero --test

Run discord-hero in production mode: ::

   cd <your_project_path>
   pipenv run hero --prod

**Note:** You have the option to enter completely different configuration
details for test mode and production mode, including your bot token,
meaning you can test with a different bot account, out of the box.

Features
--------

Core
~~~~

The central control unit that exposes all extensions and connects all
the moving parts of the application. Inherits from
```discord.ext.commands.Bot <https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Bot>`_``.

Extensions
~~~~~~~~~~

Extensions are discord-hero’s plug-ins. They can be disabled, enabled,
installed and uninstalled at runtime (TODO).

Cogs
~~~~

Cogs are the main building blocks of an extension. They are essentially
simple classes that inherit from ``hero.Cog``. By inheriting from
``hero.Cog``, the class is automatically added to the ``Core``\ ’s cogs
unless the extension it belongs to is disabled.
discord-hero Cogs are based on discord.py Cogs, thus they inherit
all of their functionalities. For a documentation on discord.py Cogs,
`check here <https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Cog>`_.

Commands
~~~~~~~~

Decorate a ``Cog``\ ’s coroutine method with ``hero.command(**options)``
to create a ``Command``. ::

   @hero.command()
   @hero.guild_only()  # A check ensuring that the command can only be invoked on a Discord server (Guild)
   async def set_channel_name(self, ctx: hero.Context, name: str, channel: hero.Channel=None):
       # !set channel name <new name> [channel]
       # TODO actually set the channel name
       pass

Event listeners
~~~~~~~~~~~~~~~

Decorate a Cog's async method with ``hero.listener()`` to turn it into an event
listener. Valid listener names and parameters can be looked up
`here <https://discordpy.readthedocs.io/en/stable/api.html#event-reference>`__. ::

   @hero.listener()
   async def on_message(self, message: discord.Message):
       # essentially be a stereotypical parrot
       if message.author != self.bot.user:
           await message.channel.send(message.content)

Controllers
~~~~~~~~~~~

discord-hero encourages the Model-View-Controller pattern by
automatically adding an Extension's Controller to its Cogs.
To make that happen, you just need to subclass ``hero.Controller``
in your Extension's ``controller`` module.

Models
~~~~~~

Structure your data by writing subclasses of ``hero.models.Model``. This will
automatically set up your database schema when discord-hero launches or
when the extension the cog belongs to is installed. If you’re coming
from Django, you might already be familiar with the basic API. ::

   # Every Guild can have their own currency
   class Currency(models.Model):
       guild = fields.GuildField(pk=True, on_delete=fields.CASCADE)
       name = fields.CharField(max_length=64)

   # Every Member can have bank account with an amount of the Guild's currency
   class BankAccount(models.Model):
       member = fields.MemberField(pk=True, on_delete=fields.CASCADE)
       balance = fields.IntegerField(db_index=True)

discord-hero comes with a few built-in models: User, Guild, TextChannel,
VoiceChannel, Role, Emoji, Member and Message. Each of them have a
corresponding field, e.g. UserField, GuildField, etc., that works like
a ForeignKey and allows you to easily reference the model in your own models.

Settings
~~~~~~~~

Settings are a special type of Models, you can define one of these Model
classes by subclassing ``hero.models.Settings``.

GraphQL schemas
~~~~~~~~~~~~~~~

# TODO

The GraphQL schemas generated automatically, you just need to configure
your models accordingly. If you want to overwrite the default
permissions, you can use the web interface. You can still add custom permissions.

Usage
-----

Writing a discord-hero Extension
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Structure:**

**\_\_init\_\_**

Required for the Extension to be recognized.

**cogs**

This is where your Cogs live. Cogs are a part of a discord-hero Extension that
enhance the bot by adding commands, event listeners, and optional state and
methods that you want to make available inside the Cog. For more information
see below.

**cogs.\_\_init\_\_**

Your Cogs can be anywhere inside the `cogs` package as long as you
import them here so discord-hero's Extension loader can find them.

**models**

This is where your Models live.

**Additional features**

New in discord-hero are the following features available from inside a Cog:

*await* `self.db.load(discord_obj)`

Used to connect a given Discord object to the database and load data
related to it that is stored in the database.

- Returns: an instance of the hero Model that is associated to the class
  the `discord_obj` is an instance of. This object wraps the Discord
  object and exposes all of its attributes and methods, which means
  it can be used like one as well.

Example: ::

    @hero.command()
    @hero.guild_only()
    async def get_balance(self, ctx):
        member = await self.db.load(ctx.author)
        await ctx.send(f"You have {member.balance} currency.")

*Hero Models as parameters*

You can define a discord-hero Model as a parameter type for a command.
This will automatically parse the user input and pass a (loaded) instance
of the Model to your command. Example: ::

    @hero.command()
    @hero.guild_only()
    async def get_balance(self, ctx, member: hero.Member):
        await ctx.send(f"{member.name} has {member.balance} currency.")

*Automatic grouping of commands*

discord-hero automatically interprets a ``_`` in a command name as a
space. This means there is no need to manually group commands anymore,
and you can use groups introduced by other Extensions or discord-hero
itself to create commands that are closer to natural language and
thus more intuitive to use for the general audience.

`self.cache`

This is a `hero.Cache` instance that allows you to set or get
a given key into the database. There are more methods available
to you than just get or set; for now, check out the source code
for those.

`self.ctl`

Your Extension's Controller. ``None`` if your Extension doesn't have
a ``hero.Controller`` subclass (you can only have one per Extension).

`self.settings`

Your Extension's Settings. ``None`` if your Extension doesn't have
a ``hero.Settings`` subclass (you can only have one per Extension).

**Note:** You need at least one Cog for your extension to work.
Alternatively, you can define a (non-async) function called ``setup``
that takes one argument, a ``hero.Core`` instance.
This function will be called when discord-hero loads the Extension.
It needs to be imported to ``cogs.__init__`` if it isn't defined there,
it needs to instantiate all the Cog classes you have created, and
it needs to pass each Cog instance to the Core's ``add_cog`` method.

New in discord-hero are the following features regarding (Django) Models:

*async*

Django's ORM has been made to work well with asyncio with the help of asgiref.
discord-hero introduces a decorator ``hero.async_using_db`` that turns a
synchronous function or method into an async one (that needs to be awaited)
and also makes any database operations in it work, magically. What happens
behind the scenes is that these database operations are executed in order
in a single, separate thread.

Furthermore, discord-hero adds async versions of QuerySet and Model instance
methods that are prefixed with ``async_`` (only for those methods that
actually operate on the database to load, create, update or delete data).
This is a temporary solution until Django's ORM officially supports async,
but for the time being it works extremely well!

Legal stuff
-----------

Discord is a registered trademark of Discord Inc.

Except as otherwise noted, discord-hero is licensed under the Apache
License, Version 2.0 (`<LICENSE.Apache-2.0>`__ or
`<http://www.apache.org/licenses/LICENSE-2.0>`__) or
the MIT license (`<LICENSE.MIT>`__ or
`<http://opensource.org/licenses/MIT>`__), at your option.

Unless you explicitly state otherwise, any contribution intentionally
submitted for inclusion in the work by you, as defined in the
Apache-2.0 license, shall be dual licensed under the Apache
License, Version 2.0, and the MIT license, without any
additional terms or conditions.

SPDX-License-Identifier: Apache-2.0 OR MIT
