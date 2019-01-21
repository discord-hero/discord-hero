"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""


import asyncio
import importlib
import inspect
import logging
import math
import os
import sys
import traceback
import types
from typing import Type, Union

import aiohttp

import discord
from discord.ext import commands

import responder

import hero
from . import utils
from .models import Settings, User, Guild, TextChannel
from .conf import Extensions
from .db import Database
from .cache import get_cache


class CommandConflict(discord.ClientException):
    pass


class Core(commands.Bot, responder.API):
    """Represents Hero's Core."""

    def __init__(self, name='default', loop=None):
        self.name = name
        self.settings = Settings(name=name)
        self.extensions = Extensions(name=name)
        self.cache = get_cache()
        self.db = Database(self)
        self.base = BaseController(self)
        super(Core, self).__init__(command_prefix=self.base.get_prefixes(),
                                   loop=loop, description=self.base.get_description(),
                                   pm_help=None, cache_auth=False,
                                   command_not_found=strings.command_not_found,
                                   command_has_no_subcommands=strings.command_has_no_subcommands)
        self._connection.core = self

        self.create_task(self.wait_for_restart)
        self.create_task(self.wait_for_shutdown)
        self.tasks = {}
        self.extra_tasks = {}
        self._stopped = asyncio.Event(loop=self.loop)

        user_agent = 'Hero (https://github.com/monospacedmagic/discord-hero {0}) Python/{1} aiohttp/{2} discord.py/{3}'
        self.http.user_agent = user_agent.format(hero.__version__, sys.version.split(maxsplit=1)[0],
                                                 aiohttp.__version__, discord.__version__)

    def __getattr__(self, item):
        return self.extensions.get(item, None)

    @property
    def is_configured(self):
        return hero.CONFIG['token'] is not None

    @property
    @hero.cached(include_self=False)
    def translations(self):
        # TODO
        return {}

    def initial_config(self):
        print(strings.setup_greeting)

        entered_token = input("> ")

        if len(entered_token) >= 50:  # assuming token
            self.base.set_token(entered_token)
        else:
            print(strings.not_a_token)
            exit(1)

        while True:
            print(strings.choose_prefix)
            while True:
                chosen_prefix = input('> ')
                if chosen_prefix:
                    break
            print(strings.confirm_prefix.format(chosen_prefix))
            if input("> ") in ['y', 'yes']:
                self.base.add_prefix(chosen_prefix)
                break

        print(strings.setup_finished)
        input("\n")

    async def on_command_completion(self, ctx):
        author = ctx.message.author
        user = self.base.get_user(author)
        user_already_registered = self.base.user_is_registered(user)
        user.command_count += 1
        user.save()
        if not user_already_registered:
            await author.send(strings.user_registered.format(author.name))

    async def on_ready(self):
        if self.base.get_owner_id() is None:
            await self.set_bot_owner()

        restarted_from = self.base.get_restarted_from()
        if restarted_from is not None:
            restarted_from_messageable = discord.utils.get(self.get_all_channels(), id=restarted_from)
            if restarted_from_messageable is None:
                restarted_from_messageable = self.get_user(restarted_from)
            await restarted_from_messageable.send("I'm back!")
            self.base.reset_restarted_from()

        # clear terminal screen
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

        print('------')
        print(strings.bot_is_online.format(self.user.name))
        print('------')
        # print(strings.connected_to)
        # print(strings.connected_to_servers.format(Guild.count()))
        # print(strings.connected_to_channels.format(TextChannel.count()))
        # print(strings.connected_to_users.format(User.count()))
        print("\n{} active extensions".format(len(self.settings.extensions)))
        prefix_label = strings.prefix_singular
        if len(self.base.get_prefixes()) > 1:
            prefix_label = strings.prefix_plural
        print("{}: {}\n".format(prefix_label, " ".join(list(self.base.get_prefixes()))))
        print("------\n")
        print(strings.use_this_url)
        print(self.get_oauth_url())
        print("\n------")
        self.base.enable_restarting()

    async def logout(self):
        await super().logout()
        self.stop()

    def stop(self):
        def silence_gathered(future):
            try:
                future.result()
            except Exception as ex:
                traceback.print_exception(type(ex), ex, ex.__traceback__, file=sys.stderr)

        # cancel lingering tasks
        if self.tasks or self.extra_tasks:
            tasks = set()
            for task in self.tasks:
                tasks.add(task)
            for _, extra_tasks in self.extra_tasks:
                for task in extra_tasks:
                    tasks.add(task)
            gathered = asyncio.gather(*tasks, loop=self.loop)
            gathered.add_done_callback(silence_gathered)
            gathered.cancel()

        self._stopped.set()

    def clear(self):
        super().clear()

        self.recursively_remove_all_commands()
        self.extra_events.clear()
        self.tasks.clear()
        self.extra_tasks.clear()
        self.cogs.clear()
        self.extensions.clear()
        self._stopped.clear()
        self._checks.clear()
        self._check_once.clear()
        self._before_invoke = None
        self._after_invoke = None

    def add_cog(self, cog):
        super().add_cog(cog)

        members = inspect.getmembers(cog)
        for name, member in members:
            # register tasks the cog has
            if name.startswith('do_'):
                self.add_task(member, resume_check=self.base.restarting_enabled)

        self._resolve_groups(cog)

    def _resolve_groups(self, cog_or_command):
        if isinstance(cog_or_command, Cog):
            for _, member in inspect.getmembers(cog_or_command, lambda _member: isinstance(_member, commands.Command)):
                self._resolve_groups(member)

        elif isinstance(cog_or_command, commands.Command):
            # if command is in a group
            if '_' in cog_or_command.name:
                # resolve groups recursively
                entire_group, command_name = cog_or_command.name.rsplit('_', 1)
                group_name = entire_group.rsplit('_', 1)[-1]
                # just ignore this command if its name is like '_eval' for some reason
                if group_name == '':
                    if entire_group == '' and '__' not in cog_or_command.name:
                        return
                    else:  # raise if command name is like 'group__command'
                        raise ValueError("command {} has two or more consecutive underscores "
                                         "in its name".format(cog_or_command.name))
                if group_name in self.all_commands:
                    if not isinstance(self.all_commands[group_name], commands.Group):
                        raise CommandConflict("cannot group command {0} under {1} because {1} is already a "
                                              "command".format(command_name, group_name))
                    group_command = self.all_commands[group_name]
                else:
                    async def groupcmd(ctx):
                        if ctx.invoked_subcommand is None:
                            await self.send_command_help(ctx)

                    group_help = strings.group_help.format(group_name)
                    group_command = self.group(name=entire_group, invoke_without_command=True,
                                               help=group_help)(groupcmd)
                    self._resolve_groups(group_command)

                self.all_commands.pop(cog_or_command.name)
                cog_or_command.name = command_name
                group_command.add_command(cog_or_command)

        else:
            raise TypeError("cog_or_command must be either a cog or a command")

    async def get(self, discord_cls, id: int):
        if discord_cls not in hero.db.discord_models:
            raise TypeError("discord_cls has to be a Discord class")

        if discord_cls == discord.User:
            # TODO
            pass

    def create_task(self, coro, *args, resume_check=None, **kwargs):
        def actual_resume_check():
            return resume_check() and not self.is_closed()

        async def pause():
            if not self.is_ready():
                await asyncio.wait((self.wait_for('resumed'), self.wait_for('ready')),
                                   loop=self.loop, return_when=asyncio.FIRST_COMPLETED)

        return self.loop.create_task(utils.autorestart(pause, self.wait_until_ready,
                                                       actual_resume_check)(coro)(*args, **kwargs))

    def add_task(self, coro, name=None, unique=True, resume_check=None):
        """The non decorator alternative to :meth:`.task`.

        Parameters
        -----------
        coro : coroutine
            The extra coro to register and execute in the background.
        name : Optional[str]
            The name of the coro to register as a task. Defaults to ``coro.__name__``.
        unique : Optional[bool]
            If this is ``True``, tasks with the same name that are already in
            :attr:`extra_tasks` will not be overwritten, and the original task will
            not be cancelled. Defaults to ``True``.
        resume_check : Optional[predicate]
            A predicate used to determine whether a task should be
            cancelled on logout or restarted instead when the bot is
            ready again. Defaults to ``None``, in which case the task
            will be cancelled on logout.

        Example
        --------

        .. code-block:: python3

            async def do_stuff: pass
            async def my_other_task(ctx): pass

            bot.add_task(do_stuff)
            bot.add_task(my_other_task, name='do_something_else', ctx=ctx)

        """
        if not asyncio.iscoroutinefunction(coro):
            raise discord.ClientException('Tasks must be coroutines')

        name = coro.__name__ if name is None else name

        if name in self.extra_tasks:
            if not unique:
                self.extra_tasks[name].append(self.create_task(coro, resume_check))
            else:
                return
        else:
            self.extra_tasks[name] = [coro]

    async def wait_for_shutdown(self):
        await self.base.cache.subscribe('shutdown')

    async def wait_for_restart(self):
        await self.base.cache.subscribe('restart')

    async def on_shutdown_message(self, _):
        self.base.disable_restarting()
        print("Shutting down...")
        await self.logout()

    async def on_restart_message(self, _):
        print("Restarting...")
        await self.logout()

    def load_extension(self, name):
        """Loads an extension's cog module.

        Parameters
        ----------
        name: str
            The name of the extension.

        Raises
        ------
        ImportError
            The cog module could not be imported
            or didn't have any ``Cog`` subclass.
        """

        if name in self.extensions:
            return None

        cog_module = importlib.import_module('dwarf.' + name + '.cogs')

        if hasattr(cog_module, 'setup'):
            cog_module.setup(self, name)
        else:
            cog_classes = inspect.getmembers(cog_module, lambda member: isinstance(member, type) and
                                             issubclass(member, Cog) and member is not Cog)
            for _, _Cog in cog_classes:
                if _Cog is None:
                    raise ImportError("The {} extension's cog module didn't have "
                                      "any Cog subclass and no setup function".format(name))
                self.add_cog(_Cog(self, name))

        self.extensions[name] = cog_module
        return cog_module

    def _load_cogs(self):
        self.load_extension('core')

        core_cog = self.get_cog('Core')
        if core_cog is None:
            raise ImportError("Could not find the Core cog.")

        failed = []
        extensions = self.base.get_extensions()
        for extension in extensions:
            try:
                self.load_extension(extension)
            except Exception as error:
                if not settings.DEBUG:
                    print("{}: {}".format(error.__class__.__name__, str(error)))
                else:
                    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
                failed.append(extension)

        if failed:
            print("\nFailed to load: " + ", ".join(failed))

        return core_cog

    def task(self, unique=True, resume_check=None):
        """A decorator that registers a task to execute in the background.

        If a task is running when the Client disconnects from Discord
        because it logged itself out, it will cancel the execution of the
        task. If the Client loses the connection to Discord because
        of network issues or similar, it will cancel the execution of the task,
        wait for itself to reconnect, then restart the task.

        Example
        -------

        ::

            @bot.task()
            async def do_say_hello_every_minute():
                while True:
                    print("Hello World!")
                    await asyncio.sleep(60)

        Parameters
        ----------
        unique : Optional[bool]
            If this is ``True``, tasks with the same name that are
            already sttributes of ``self`` will not be overwritten,
            and the original task will not be cancelled.
            Defaults to ``True``.
        resume_check : Optional[predicate]
            A predicate used to determine whether a task should be
            cancelled on logout or restarted instead when the bot is
            ready again. Defaults to ``None``, in which case the task
            will be cancelled on logout.

        Raises
        -------
        TypeError
            The decorated ``coro`` is not a coroutine function.
        """

        async def wrapped(coro):
            if not asyncio.iscoroutinefunction(coro):
                raise TypeError('task registered must be a coroutine function')

            name = coro.__name__
            if hasattr(self, name):
                if unique:
                    return coro
            setattr(self, name, self.create_task(coro, resume_check))

        return wrapped

    def run_tasks(self):
        members = inspect.getmembers(self)
        for name, member in [_member for _member in members if _member[0].startswith('do')]:
            task = self.create_task(member)
            self.tasks[name] = task

    async def wait_for_response(self, ctx, message_check=None, timeout=60):
        def response_check(message):
            is_response = ctx.message.author == message.author and ctx.message.channel == message.channel
            return is_response and message_check(message) if callable(message_check) else True

        try:
            response = await self.wait_for('message', check=response_check, timeout=timeout)
        except asyncio.TimeoutError:
            return None
        return response.content

    async def wait_for_answer(self, ctx, timeout=60):
        def is_answer(message):
            return message.content.lower().startswith('y') or message.content.lower().startswith('n')

        answer = await self.wait_for_response(ctx, message_check=is_answer, timeout=timeout)
        if answer is None:
            return None
        if answer.lower().startswith('y'):
            return True
        if answer.lower().startswith('n'):
            return False

    async def wait_for_choice(self, ctx, choices, timeout=60):
        if isinstance(choices, types.GeneratorType):
            choices = list(choices)

        choice_format = "**{}**: {}"

        def choice_check(message):
            try:
                return int(message.content.split(maxsplit=1)[0]) <= len(choices)
            except ValueError:
                return False

        paginator = commands.Paginator(prefix='', suffix='')
        for i, _choice in enumerate(choices, 1):
            paginator.add_line(choice_format.format(i, _choice))

        for page in paginator.pages:
            await ctx.send(page)

        choice = await self.wait_for_response(ctx, message_check=choice_check, timeout=timeout)
        if choice is None:
            return None
        return int(choice.split(maxsplit=1)[0])

    async def send_command_help(self, ctx):
        if ctx.invoked_subcommand:
            pages = await self.formatter.format_help_for(ctx, ctx.invoked_subcommand)
            for page in pages:
                await ctx.send(page)
        else:
            pages = await self.formatter.format_help_for(ctx, ctx.command)
            for page in pages:
                await ctx.send(page)

    async def on_command_error(self, ctx, error, ignore_local_handlers=False):
        if not ignore_local_handlers:
            if hasattr(ctx.command, 'on_error'):
                return

        # get the original exception
        error = getattr(error, 'original', error)

        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.BotMissingPermissions):
            missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
            if len(missing) > 2:
                fmt = '{}, and {}'.format("**, **".join(missing[:-1]), missing[-1])
            else:
                fmt = ' and '.join(missing)
            _message = 'I need the **{}** permission(s) to run this command.'.format(fmt)
            await ctx.send(_message)
            return

        if isinstance(error, commands.DisabledCommand):
            await ctx.send('This command has been disabled.')
            return

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("This command is on cooldown, please retry in {}s.".format(math.ceil(error.retry_after)))
            return

        if isinstance(error, commands.MissingPermissions):
            missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
            if len(missing) > 2:
                fmt = '{}, and {}'.format("**, **".join(missing[:-1]), missing[-1])
            else:
                fmt = ' and '.join(missing)
            _message = 'You need the **{}** permission(s) to use this command.'.format(fmt)
            await ctx.send(_message)
            return

        if isinstance(error, commands.UserInputError):
            await ctx.send("Invalid input.")
            await self.send_command_help(ctx)
            return

        if isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send('This command cannot be used in direct messages.')
            except discord.HTTPException:
                pass
            return

        if isinstance(error, commands.CheckFailure):
            await ctx.send("You do not have permission to use this command.")
            return

        # ignore all other exception types, but print them to stderr
        # and send it to ctx if settings.DEBUG is True
        await ctx.send("An error occured while running the command **{0}**.".format(ctx.command))

        if settings.DEBUG:
            error_details = traceback.format_exception(type(error), error, error.__traceback__)
            paginator = commands.Paginator(prefix='```py')
            for line in error_details:
                paginator.add_line(line)
            for page in paginator.pages:
                await ctx.send(page)

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    def get_oauth_url(self):
        return discord.utils.oauth_url(self.user.id)

    async def set_bot_owner(self):
        try:
            data = await self.application_info()
            self.base.set_owner_id(data.owner.id)
        except AttributeError:
            print(strings.update_the_api)
            raise
        print(strings.owner_recognized.format(data.owner.name))

    async def run(self, reconnect=True):
        # TODO create essential user groups if they don't exist
        self._load_cogs()

        if self.base.get_prefixes():
            self.command_prefix = list(self.base.get_prefixes())
        else:
            print(strings.no_prefix_set)
            self.command_prefix = ["!"]

        self.run_tasks()

        print(strings.logging_into_discord)
        print(strings.keep_updated.format(self.command_prefix[0]))
        print(strings.official_server.format(strings.invite_link))

        await self.start(self.base.get_token(), reconnect=reconnect)

        await self._stopped.wait()


class Cog:
    """The base class for cogs, classes that include
    commands, event listeners and background tasks

    Parameters
    ----------
    bot : Core
        The bot to add the cog to.
    extension : str
        The name of the extension the cog belongs to.

    Attributes
    ----------
    log : logging.Logger
        The cog's logger.
    """

    def __init__(self, bot, extension):
        self.bot = bot
        self.extension = extension

        log_name = 'dwarf.' + extension + '.cogs'
        if self.__module__ != 'cogs':
            log_name += '.' + self.__module__
        self.log = logging.getLogger('dwarf.' + extension + '.cogs')


def main(loop=None, bot=None):
    if loop is None:
        loop = asyncio.get_event_loop()

    if bot is None:
        bot = Core(loop=loop)

    if not bot.is_configured:
        bot.initial_config()

    error = False
    error_message = ""
    try:
        loop.run_until_complete(bot.run())
    except discord.LoginFailure:
        error = True
        error_message = 'Invalid credentials'
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
