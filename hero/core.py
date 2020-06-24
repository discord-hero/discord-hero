"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import asyncio
import importlib
import inspect
import io
import math
import os
import sys
import traceback
import types
import warnings

import aiohttp

import discord
from discord.ext import commands
from discord.ext.commands import when_mentioned_or

from django.core import management

import hero
from . import strings
from .command import group
from .conf import Extension, Extensions
from .cache import get_cache
from .errors import ObjectDoesNotExist, InactiveUser, UserDoesNotExist, ResponseTookTooLong
from .cli import style
from .db import Database
from .utils import issubmodule, titlecaseify


class CommandConflict(discord.ClientException):
    pass


class Core(commands.Bot):
    """Represents Hero's Core."""

    YES_EMOJI = '\u2705'
    NO_EMOJI = '\u274E'

    def __init__(self, config, settings, name='default', loop=None):
        self.name = name
        self.__extensions = Extensions(name=name)
        self.__controllers = {}
        self.__settings = {}
        self.cache = get_cache(namespace=name)
        # hack that allows Discord models to fetch the Discord object they belong to using the core
        self.cache.core = self
        self.db = Database(self)
        self.config = config

        self.sync_db('hero')

        extension_names = set(os.getenv('EXTENSIONS', '').split(';'))
        extension_names.update(os.getenv('LOCAL_EXTENSIONS', '').split(';'))
        if '' in extension_names:
            extension_names.remove('')
        self.sync_db(*extension_names)

        self.settings = settings
        if self.settings is None:
            from hero.models import CoreSettings
            self.settings = CoreSettings.get_or_create(name=os.getenv('NAMESPACE'))

        super(Core, self).__init__(command_prefix=when_mentioned_or(*self.get_prefixes()),
                                   loop=loop, description=self.get_description(),
                                   pm_help=None, cache_auth=False,
                                   command_not_found=strings.command_not_found,
                                   command_has_no_subcommands=strings.command_has_no_subcommands)

        user_agent = 'discord-hero (https://github.com/discord-hero/discord-hero {0}) ' \
                     'Python/{1} aiohttp/{2} discord.py/{3}'
        self.http.user_agent = user_agent.format(hero.__version__, sys.version.split(maxsplit=1)[0],
                                                 aiohttp.__version__, discord.__version__)

    def __getattr__(self, item):
        try:
            return self.__controllers[item]
        except KeyError:
            raise AttributeError("'Core' object has no attribute '%s'" % item)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        try:
            self.clear()
        except AttributeError:
            pass

    @property
    def is_configured(self):
        return self.config.bot_token is not None

    @property
    @hero.cached(include_self=False)
    def translations(self):
        # TODO
        return {}

    async def on_ready(self):
        from hero.models import User
        # save the bot user in the database if it isn't saved yet
        qs = User.objects.filter(id=self.user.id)
        existed_already = await qs.async_exists()
        if not existed_already:
            await User.async_create(id=self.user.id)

        status = self.settings.status or f"Use {self.default_prefix}help"
        activity = discord.Game(status)
        await self.change_presence(status=discord.Status.online, activity=activity)
        # clear terminal screen
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

        print(strings.bot_is_online.format(self.user.name))
        print("\n{} active extensions".format(len(self.__extensions) - 1))  # we don't count essentials
        prefix_label = strings.prefix_singular
        if len(self.get_prefixes()) > 1:
            prefix_label = strings.prefix_plural
        print("{}: {}\n".format(prefix_label, " ".join(list(self.get_prefixes()))))
        print(strings.use_this_url)
        print(self.get_oauth_url(), "\n")
        print(strings.official_server.format(strings.invite_link), "\n")

    def clear(self):
        self.recursively_remove_all_commands()
        self.extra_events.clear()
        self.cogs.clear()
        self.__extensions.clear()
        self._stopped.clear()
        self._checks.clear()
        self._check_once.clear()
        self._before_invoke = None
        self._after_invoke = None

        super().clear()

    def add_cog(self, cog):
        super().add_cog(cog)

        self._resolve_groups(cog)

    def _resolve_groups(self, cog_or_command):
        if isinstance(cog_or_command, hero.Cog):
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
                            await ctx.send_help()

                    group_help = strings.group_help.format(group_name)
                    group_command = self.group(name=entire_group, invoke_without_command=True,
                                               help=group_help)(groupcmd)
                    self._resolve_groups(group_command)

                cog_or_command = self.all_commands.get(cog_or_command.name)
                # cog_or_command.name = command_name
                if cog_or_command is not None:
                    group_command.add_command(cog_or_command)

        else:
            raise TypeError("cog_or_command must be either a cog or a command")

    def group(self, *args, **kwargs):
        """A shortcut decorator that invokes :func:`.group` and adds it to
        the internal command list via :meth:`~.GroupMixin.add_command`.
        """
        def decorator(func):
            kwargs.setdefault('parent', self)
            result = group(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator

    def load_extension(self, name):
        """Loads an extension

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
        if name in self.__extensions.loaded_by_core:
            raise commands.ExtensionAlreadyLoaded(name)
        try:
            cog_module = importlib.import_module(f'extensions.{name}.cogs')
            _local = True
        except ImportError:
            cog_module = importlib.import_module(f'hero.extensions.{name}.cogs')
            _local = False

        if name not in self.config.disabled_extensions:
            if name not in self.__extensions:
                self.__extensions[name] = Extension(name, Extensions.get_extension_module(name, local=_local))

            self.__settings[name] = self.__extensions[name].get_settings(self)
            self.__controllers[name] = self.__extensions[name].get_controller(self)

            if hasattr(cog_module, 'setup'):
                cog_module.setup(self, name)
            else:
                cog_classes = inspect.getmembers(cog_module, lambda member: isinstance(member, type) and
                                                 issubclass(member, hero.Cog) and member is not hero.Cog)
                for _, _Cog in cog_classes:
                    if _Cog is None:
                        raise ImportError(f"The {name} extension's cog module didn't have "
                                          f"any Cog subclass and no setup function")
                    self.add_cog(_Cog(self, self.__extensions[name]))

            self.__extensions.loaded_by_core.append(name)
            return cog_module
        else:
            del self.__extensions[name]
            return None

    def unload_extension(self, name):
        extension = self.__extensions.get(name)
        if extension is None:
            raise commands.ExtensionNotLoaded(name)

        lib = extension._module

        print(lib.__name__)
        self._remove_module_references(lib.__name__)
        self._call_module_finalizers(lib, name)
        self.__extensions.loaded_by_core.remove(name)

    def reload_extension(self, name):
        extension = self.__extensions.get(name)
        if extension is None:
            raise commands.ExtensionNotLoaded(name)

        lib = extension._module

        # get the previous module states from sys modules
        modules = {
            name: module
            for name, module in sys.modules.items()
            if issubmodule(lib.__name__, name)
        }

        try:
            # Unload and then load the module...
            self._remove_module_references(lib.__name__)
            self._call_module_finalizers(lib, name)
            self.__extensions.loaded_by_core.remove(name)
            self.load_extension(name)
        except Exception as e:
            # if the load failed, the remnants should have been
            # cleaned from the load_extension function call
            # so let's load it from our old compiled library.
            try:
                lib.setup(self)
            except AttributeError:
                pass
            self.__extensions[name] = lib

            # revert sys.modules back to normal and raise back to caller
            sys.modules.update(modules)
            raise

    def _remove_module_references(self, name):
        # find all references to the module
        # remove the cogs registered from the module
        print("Name:", name)
        for cogname, cog in self.cogs.copy().items():
            if issubmodule(name, cog.__module__):
                print(cogname)
                self.remove_cog(cogname)

        # remove all the commands from the module
        for cmd in self.all_commands.copy().values():
            if cmd.module is not None and issubmodule(name, cmd.module):
                if isinstance(cmd, commands.GroupMixin):
                    print("Removing group:", cmd.name)
                    cmd.recursively_remove_all_commands()
                else:
                    print("Removing command:", cmd.name)
                    self.remove_command(cmd.name)

        # remove all the listeners from the module
        for event_list in self.extra_events.copy().values():
            remove = []
            for index, event in enumerate(event_list):
                if event.__module__ is not None and issubmodule(name, event.__module__):
                    remove.append(index)

            for index in reversed(remove):
                del event_list[index]

    def _call_module_finalizers(self, lib, key):
        try:
            func = getattr(lib, 'teardown')
        except AttributeError:
            pass
        else:
            try:
                func(self)
            except Exception as ex:
                warnings.warn(f"Couldn't teardown {lib.__name__} properly: {ex}")
        finally:
            self.__extensions.pop(key, None)

    def get_extension(self, name):
        return self.__extensions.get(name)

    def get_extensions(self):
        return self.__extensions.data

    def get_controller(self, extension_name):
        return self.__controllers[extension_name]

    def get_settings(self, extension_name):
        return self.__settings[extension_name]

    def get_prefixes(self):
        return self.settings.prefixes

    async def set_prefixes(self, prefixes):
        old_prefixes = self.settings.prefixes
        self.settings.prefixes = prefixes
        try:
            await self.settings.async_save()
        except Exception:
            self.settings.prefixes = old_prefixes
            raise
        # test
        from hero.models import CoreSettings
        _settings = await CoreSettings.async_get(name=self.settings.name)
        self.command_prefix = when_mentioned_or(*prefixes)

    @property
    def default_prefix(self):
        return self.get_prefixes()[0]

    def get_description(self):
        return self.settings.description

    async def set_description(self, description: str):
        self.settings.description = description
        await self.settings.async_save()
        self.description = description

    def get_status(self):
        return self.settings.status

    async def set_status(self, status: str):
        self.settings.status = status
        await self.settings.async_save()
        activity = discord.Game(status)
        await self.change_presence(activity=activity)

    def _load_cogs(self):
        # discord and hero each have their own definition of an extension
        self.__extensions.load()
        self.load_extension('essentials')

        essentials_cog = self.get_cog('Essentials')
        if essentials_cog is None:
            raise ImportError("Could not find the Essentials cog.")

        failed = []
        extensions = self.get_extensions()[1:]
        for extension in extensions:
            try:
                self.load_extension(extension)
            except Exception as error:
                if not hero.TEST:
                    print("{}: {}".format(error.__class__.__name__, str(error)))
                else:
                    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
                del self.__extensions[extension]
                failed.append(extension)

        if failed:
            print("\nFailed to load: " + ", ".join(failed))

        return essentials_cog

    def sync_db(self, *extension_names):
        if not extension_names:
            extension_names = list(self.__extensions.keys())

        print(f"Synchronizing database with models from {', '.join(extension_names)}...", end=' ')
        # temporarily silence stdout while we sync the database
        backup_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            management.call_command('makemigrations', *extension_names, interactive=False)
            management.call_command('makemigrations', *extension_names, interactive=False, merge=True)
            for extension_name in extension_names:
                try:
                    management.call_command('migrate', extension_name, interactive=False)
                except management.CommandError:
                    management.call_command('migrate', extension_name, interactive=False, run_syncdb=True)
        except management.CommandError as command_error:
            print(command_error, file=sys.stderr)
            return False
        else:
            print(style("OK", fg='green'), file=backup_stdout)
            return True
        finally:
            sys.stdout = backup_stdout

    async def on_message(self, message):
        if not self.is_ready():
            return

        await super().on_message(message)

    async def wait_for_response(self, ctx, message_check=None, timeout=60, force_response=True) -> str:
        def response_check(message):
            is_response = ctx.message.author == message.author and ctx.message.channel == message.channel
            return is_response and (message_check(message) if callable(message_check) else True)

        try:
            response = await self.wait_for('message', check=response_check, timeout=timeout)
        except asyncio.TimeoutError:
            if force_response:
                raise ResponseTookTooLong()
            else:
                return None
        return response.content

    async def wait_for_confirmation(self, ctx, timeout=60, force_response=True) -> bool:
        def is_confirmation(message):
            return message.content.lower().startswith('y') or message.content.lower().startswith('n')

        answer = await self.wait_for_response(ctx, message_check=is_confirmation, timeout=timeout,
                                              force_response=force_response)
        if not force_response and answer is None:
            return None
        if answer.lower().startswith('y'):
            return True
        if answer.lower().startswith('n'):
            return False

    async def wait_for_choice(self, ctx, choices, timeout=60, force_response=True) -> int:
        if isinstance(choices, types.GeneratorType):
            choices = list(choices)

        choice_format = "**{}**: {}"

        def choice_check(message):
            try:
                return 1 <= int(message.content.split(maxsplit=1)[0]) <= len(choices)
            except ValueError:
                return False

        paginator = commands.Paginator(prefix='', suffix='')
        for i, _choice in enumerate(choices, 1):
            paginator.add_line(choice_format.format(i, _choice))

        for page in paginator.pages:
            await ctx.send(page)

        choice = await self.wait_for_response(ctx, message_check=choice_check, timeout=timeout)
        if not force_response and choice is None:
            return None
        return int(choice.split(maxsplit=1)[0])

    async def on_error(self, event_method, *args, **kwargs):
        from hero.models import User
        type, value, traceback = sys.exc_info()

        if isinstance(value, (User.DoesNotExist, InactiveUser)):
            return

        if isinstance(value, UserDoesNotExist):
            prefix = self.default_prefix
            delete_after = None
            if event_method in ('raw_reaction_add', 'raw_reaction_remove'):
                send_message = True
                delete_after = 60
                payload: discord.RawReactionActionEvent = args[0]
                user = self.get_user(payload.user_id)
                if user is None:
                    user = self.fetch_user(payload.user_id)
                channel = self.get_channel(payload.channel_id)
                if channel is None:
                    channel = await self.fetch_channel(payload.channel_id)
            elif event_method in ('reaction_add', 'reaction_remove'):
                send_message = True
                delete_after = 60
                user = args[1]
                reaction = args[0]
                channel = reaction.message.channel
            elif event_method in ('raw_message_delete', 'raw_message_edit'):
                send_message = False
                payload = args[0]
                channel = self.get_channel(payload.channel_id)
                if channel is None:
                    channel = await self.fetch_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                user = message.author
            elif event_method in ('message', 'message_delete', 'message_edit'):
                send_message = False
                message = args[0]
                user = message.author
                channel = message.channel
            elif event_method in ('member_join' or 'member_remove'):
                send_message = True
                user = member = args[0]
                channel = member.guild.system_channel
            elif event_method in ('member_update' or 'user_update'):
                send_message = False
                user = args[1]
                channel = None
            elif event_method == 'private_channel_pins_update':
                send_message = True
                channel = args[0]
                user = channel.recipient
                channel = None
            else:
                await super().on_error(event_method, *args, **kwargs)
                return

            error_user = self.get_user(value.user_id)
            if error_user is None:
                error_user = await self.fetch_user(value.user_id)

            if send_message:
                inactive = isinstance(value, InactiveUser)
                prefix = self.default_prefix
                register_message = await self.send_gdpr(error_user, author=user, fallback_channel=channel,
                                                        inactive=inactive,
                                                        prefix=prefix, delete_after=delete_after)

                if not inactive and register_message is not None:
                    saved_user = User(user.id)
                    saved_user.is_active = False
                    register_message = await self.db.wrap_message(register_message)
                    saved_user.register_message = register_message
                    await saved_user.async_save()
                    try:
                        await register_message.add_reaction(self.YES_EMOJI)
                    except discord.Forbidden:
                        pass
            else:
                if hero.TEST:
                    if channel.guild:
                        where = f"#{channel.name} on {channel.guild}"
                    else:
                        where = "DMs"
                    print(style(f"DEBUG: User {error_user} is not registered in the database; origin: "
                                f"on_{event_method} triggered by user {user} in {where}", fg='bright_blue'))
            return

        await super().on_error(event_method, *args, **kwargs)

    async def on_command_error(self, ctx: commands.Context, error):
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
            await ctx.send_help()
            return

        if isinstance(error, ResponseTookTooLong):
            await ctx.send("Response took too long, aborting...")
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

        # GDPR
        from hero.models import User
        if isinstance(error, User.DoesNotExist):
            await ctx.send(strings.one_user_is_not_registered.format(ctx.prefix))
            return

        if isinstance(error, (UserDoesNotExist, InactiveUser)):
            user = self.get_user(error.user_id)
            if user is None:
                user = await self.fetch_user(error.user_id)
            inactive = isinstance(error, InactiveUser)
            register_message = await self.send_gdpr(user, author=ctx.author, fallback_channel=ctx.channel,
                                                    inactive=inactive, prefix=ctx.prefix)

            if not inactive and register_message is not None:
                saved_user = User(user.id)
                saved_user.is_active = False
                register_message: discord.Message = await self.db.wrap_message(register_message)
                saved_user.register_message = register_message
                await saved_user.async_save()
                try:
                    await register_message.add_reaction(self.YES_EMOJI)
                except discord.Forbidden:
                    pass
            return

        if isinstance(error, ObjectDoesNotExist) and not hero.TEST:
            model = error.model
            if hasattr(model, 'NOT_FOUND_MESSAGE'):
                msg = model.NOT_FOUND_MESSAGE
            else:
                model_name = titlecaseify(model.name)
                msg = f"Could not find {model_name}"
            await ctx.send(msg)

        # ignore all other exception types, but print them to stderr
        # and send it to ctx if in test mode
        await ctx.send(f"An error occured while running the command **{ctx.command}**.")

        if hero.TEST:
            await self.report_error(ctx, error)

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    async def report_error(self, ctx, error: BaseException, messageable=None):
        if messageable is not None:
            await messageable.send(f"An error occured while running the command **{ctx.command}**:")
        error_details = traceback.format_exception(type(error), error, error.__traceback__)
        paginator = commands.Paginator(prefix='```py')
        for line in error_details:
            paginator.add_line(line)
        for page in paginator.pages:
            if messageable is not None:
                await messageable.send(page)
            else:
                await ctx.send(page)

    @staticmethod
    async def send_gdpr(user, author=None, fallback_channel=None,
                        inactive=False, prefix=None, delete_after=None):
        register_message = None
        if author is None or author.id == user.id:
            if inactive:
                message_text = strings.user_inactive
                try:
                    await user.send(message_text.format(user.name, prefix))
                except discord.Forbidden:
                    try:
                        await fallback_channel.send(message_text.format(user.mention, prefix),
                                                    delete_after=delete_after or 60)
                    except discord.Forbidden:
                        pass
            else:
                message_text = strings.user_not_registered
                try:
                    register_message = await user.send(message_text.format(user.name, prefix))
                except discord.Forbidden:
                    register_message = await fallback_channel.send(message_text.format(user.mention, prefix),
                                                                   delete_after=delete_after or 180)
        else:
            if inactive:
                # author is not None
                message_text = strings.one_user_is_inactive
                if fallback_channel is not None:
                    try:
                        await fallback_channel.send(message_text.format(author.mention, str(user), prefix),
                                                    delete_after=delete_after or 60)
                    except discord.Forbidden:
                        try:
                            await author.send(message_text.format(author.name, str(user), prefix))
                        except discord.Forbidden:
                            pass
                else:
                    try:
                        await author.send(message_text.format(author.name, str(user), prefix))
                    except discord.Forbidden:
                        pass
            else:
                message_text = strings.other_user_not_registered
                if fallback_channel is not None:
                    try:
                        register_message = await fallback_channel.send(message_text.format(author.mention, user.mention, prefix),
                                                                       delete_after=delete_after or 180)
                    except discord.Forbidden:
                        try:
                            register_message = await author.send(message_text.format(author.name, str(user), prefix))
                        except discord.Forbidden:
                            pass
                else:
                    try:
                        register_message = await author.send(message_text.format(author.name, str(user), prefix))
                    except discord.Forbidden:
                        pass
        return register_message

    def get_oauth_url(self):
        return discord.utils.oauth_url(self.user.id)

    def run(self, reconnect=True):
        self._load_cogs()

        if self.get_prefixes():
            self.command_prefix = list(self.get_prefixes())
        else:
            print(strings.no_prefix_set)
            self.command_prefix = ["!"]

        print(strings.logging_into_discord)

        try:
            self.loop.run_until_complete(self.start(self.config.bot_token, bot=True, reconnect=reconnect))
        except asyncio.CancelledError:
            pass
