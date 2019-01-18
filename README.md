# Hero

Hero is an asynchronous, fully modular application framework for humans allowing you to write
applications that connect to [Discord](https://discordapp.com/). It comes with a Discord bot framework
built on top of [the rewrite version of discord.py](https://github.com/Rapptz/discord.py/tree/rewrite),
a GraphQL API powered by [Graphene](https://graphene-python.org/) and
[Responder](https://python-responder.org/) and a web frontend backed by
[WhiteNoise](http://whitenoise.evans.io/), [Starlette](https://www.starlette.io/) and
[Jinja2](http://jinja.pocoo.org/) (also via Responder),
written with [Vue](https://vuejs.org/) and [Bulma](https://bulma.io/) via
[Buefy](https://buefy.github.io/).

## Getting started

**Note:** In this section, the content of every code block is intended to be
entered in a terminal / command prompt. 

### Requirements

You need Python 3.6 or above, Git, `cookiecutter` and `pipenv`. Install
`cookiecutter` and `pipenv` if you haven't yet:

Linux / Mac:

    python3 install --user -U cookiecutter pipenv

Windows:

    py -3 -m pip install -U cookiecutter pipenv

If you're just testing things out, it's probably fine to just use the default database
and cache solutions (SQLite3 and Python memory cache). However, if you want to use Hero
for a production application, it is recommended to use PostgreSQL and Redis.

### Installation

Replace `<your_directory_name>` with the project name you will have entered by then.

    cookiecutter https://github.com/monospacedmagic/discord-hero-cookiecutter.git
    cd <your_directory_name>
    pipenv install --three --skip-lock
    pipenv lock --pre
    pipenv run hero --test

For production applications:

    pipenv install asyncpg aioredis --skip-lock
    pipenv lock --pre

Run Hero in production mode:

    cd <your_project_path>
    pipenv run hero

## Development

This project follows a new development approach for libraries that I wanted to try out for some time
which is called FDTI, short for **F**eature-driven **D**ocumentation, **D**ocumentation-driven **T**ests,
**T**est-driven **I**mplementation. This results in following development process:

1. Line out **features** (use case diagrams, activity diagrams etc. can be used for this)
2. **Document** how those features (will) look like (and write accompanying guides if it makes sense)
3. Add examples to the documentation where you didn't already add ones and set up a way to automatically
   test them if possible (easier to maintain), or write tests outside of the documentation
4. Make those examples and tests work by implementing all the features according to the documentation

After each of these steps, check with users, stakeholders, coworkers/contributors and whoever else is
interested in your project. If there are design flaws, they are likely to surface much earlier this way,
which can save you and those who use your software a tremendous amount of headache and wasted time and effort.

## Features

### Core

The central control unit that exposes all extensions and connects all the moving parts of the application.

### Extensions

Extensions are Hero's plug-ins. They can be disabled, enabled, installed and uninstalled at runtime.

### Cogs

Cogs are the main building blocks of an extension. They are essentially simply classes that inherit from
`hero.Cog`. By inheriting from `hero.Cog`, the class is automatically added to the `Core`'s cogs
unless the extension it belongs to is disabled. A cog that is added to the core can be accessed via
the core's attributes. The name of the cog attribute of the core is the `snake_case`'d version
of the cog's class name.

    import hero
    
    class RoleManagement(hero.Cog):
        @property
        def is_enabled(self):
            return getattr(self.core, "role_management", None) is self

### Commands

Decorate a `Cog`'s coroutine method with `hero.command(**options)` to create a `Command`.

    @hero.command()
    @hero.guild_only()  # A check ensuring that the command can only be invoked on a Discord server (Guild)
    async def set_channel_name(self, ctx: hero.Context, name: str, channel: hero.Channel=None):
        # !set channel name <new name> [channel]
        # TODO actually set the channel name
        pass

### Event listeners

Start a coroutine method's name with `on_` to turn it into an event listener.
Valid listener names and parameters can be looked up [here](https://www.example.com/).

    async def on_message(self, message: hero.Message):
        # essentially be a stereotypical parrot
        if message.author != self.bot.user:
            await message.channel.send(message.content)

### Background tasks

Decorate a coroutine method with `@hero.background_task(**options)` to turn it into a background task.
It will be ran in the background as soon as Hero launches. If you want to keep it running,
just use e.g. `while True:`. Don't use too many of these though, as they can slow down Hero.

    @hero.background_task()
    async def say_hello_every_minute(self):
        while True:
            print("Hello World!")
            await asyncio.sleep(60)

### Models

Structure your data by writing subclasses of `hero.Model`. This will automatically set up
your database schema when Hero launches or when the extension the cog belongs to is installed.
If you're coming from Django, you might already be familiar with the basic API.

    from hero import fields
    # ...
    # Every Guild can have their own currency
    class Currency(hero.Model):
        guild = fields.GuildField(pk=True, on_delete=fields.CASCADE)
        name = fields.CharField(max_length=64)
    
    # Every Member can have bank account with an amount of the Guild's currency
    class BankAccount(hero.Model):
        member = fields.MemberField(pk=True, on_delete=fields.CASCADE)
        balance = fields.IntField(db_index=True)

Hero comes with a few built-in models: User, 

### GraphQL schemas

TODO

## Legal stuff

Except as otherwise noted, discord-hero is licensed under the Apache License, Version 2.0
([LICENSE.Apache-2.0](blob/master/LICENSE.Apache-2.0) or <http://www.apache.org/licenses/LICENSE-2.0>)
or the MIT license [LICENSE.MIT](blob/master/LICENSE.MIT) or <http://opensource.org/licenses/MIT>,
at your option.

SPDX-License-Identifier: Apache-2.0 OR MIT
