"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import inspect

import discord
from discord.ext.commands import converter

from django.conf import settings as django_settings
from django.db import models as _models
from django.db.models import prefetch_related_objects
from django.db.models.fields.reverse_related import ForeignObjectRel

import hero
from hero import fields
from .errors import InactiveUser, UserDoesNotExist
# temporary fix until Django's ORM is async
from .utils import async_using_db


class QuerySet(_models.QuerySet):
    @async_using_db
    def async_get(self, *args, **kwargs):
        return super(QuerySet, self).get(*args, **kwargs)
    async_get.__doc__ = _models.QuerySet.get.__doc__

    @async_using_db
    def async_create(self, **kwargs):
        return super(QuerySet, self).create(**kwargs)
    async_create.__doc__ = _models.QuerySet.create.__doc__

    @async_using_db
    def async_get_or_create(self, *args, **kwargs):
        return super(QuerySet, self).get_or_create(*args, **kwargs)
    async_get_or_create.__doc__ = _models.QuerySet.get_or_create.__doc__

    @async_using_db
    def async_update_or_create(self, *args, **kwargs):
        return super(QuerySet, self).update_or_create(*args, **kwargs)
    async_update_or_create.__doc__ = _models.QuerySet.update_or_create.__doc__

    @async_using_db
    def async_bulk_create(self, *args, **kwargs):
        return super(QuerySet, self).bulk_create(*args, **kwargs)
    async_bulk_create.__doc__ = _models.QuerySet.bulk_create.__doc__

    @async_using_db
    def async_bulk_update(self, *args, **kwargs):
        return super(QuerySet, self).bulk_update(*args, **kwargs)
    async_bulk_update.__doc__ = _models.QuerySet.bulk_update.__doc__

    @async_using_db
    def async_count(self):
        return super(QuerySet, self).count()
    async_count.__doc__ = _models.QuerySet.count.__doc__

    @async_using_db
    def async_in_bulk(self, *args, **kwargs):
        return super(QuerySet, self).in_bulk(*args, **kwargs)
    async_in_bulk.__doc__ = _models.QuerySet.in_bulk.__doc__

    @async_using_db
    def async_iterator(self, *args, **kwargs):
        return super(QuerySet, self).iterator(*args, **kwargs)
    async_iterator.__doc__ = _models.QuerySet.iterator.__doc__

    @async_using_db
    def async_latest(self, *args):
        return super(QuerySet, self).latest(*args)
    async_latest.__doc__ = _models.QuerySet.latest.__doc__

    @async_using_db
    def async_earliest(self, *args):
        return super(QuerySet, self).earliest(*args)
    async_earliest.__doc__ = _models.QuerySet.earliest.__doc__

    @async_using_db
    def async_first(self):
        return super(QuerySet, self).first()
    async_first.__doc__ = _models.QuerySet.first.__doc__

    @async_using_db
    def async_last(self):
        return super(QuerySet, self).last()
    async_last.__doc__ = _models.QuerySet.last.__doc__

    @async_using_db
    def async_aggregate(self, *args, **kwargs):
        return super(QuerySet, self).aggregate(*args, **kwargs)
    async_aggregate.__doc__ = _models.QuerySet.aggregate.__doc__

    @async_using_db
    def async_exists(self):
        return super(QuerySet, self).exists()
    async_exists.__doc__ = _models.QuerySet.exists.__doc__

    @async_using_db
    def async_update(self, **kwargs):
        return super(QuerySet, self).update(**kwargs)
    async_update.__doc__ = _models.QuerySet.update.__doc__

    @async_using_db
    def async_delete(self):
        return super(QuerySet, self).delete()
    async_delete.__doc__ = _models.QuerySet.delete.__doc__


class BaseManager(_models.manager.BaseManager):
    # Django's version doesn't support callables other than functions so we have to override this
    @classmethod
    def _get_queryset_methods(cls, queryset_class):
        def create_method(name, method):
            def manager_method(self, *args, **kwargs):
                return getattr(self.get_queryset(), name)(*args, **kwargs)
            # support SyncToAsync
            try:
                manager_method.__name__ = method.__name__
                manager_method.__doc__ = method.__doc__
            except AttributeError:
                manager_method.__name__ = method.func.__name__
                manager_method.__doc__ = method.func.__doc__
            return manager_method

        new_methods = {}
        for name, method in inspect.getmembers(queryset_class, predicate=callable):
            # Only copy missing methods.
            if hasattr(cls, name):
                continue
            # Only copy public methods or methods with the attribute `queryset_only=False`.
            queryset_only = getattr(method, 'queryset_only', None)
            if queryset_only or (queryset_only is None and name.startswith('_')):
                continue
            # Copy the method onto the manager.
            new_methods[name] = create_method(name, method)
        return new_methods


class Manager(BaseManager.from_queryset(QuerySet)):
    pass


class Model(_models.Model):
    class Meta:
        abstract = True
        base_manager_name = 'objects'
        default_manager_name = 'custom_default_manager'

    def __init_subclass__(cls):
        if not cls._meta.abstract:
            # make error handling much more simple
            cls.DoesNotExist.model = cls
            cls.MultipleObjectsReturned.model = cls

    objects: QuerySet = Manager()
    custom_default_manager = Manager()
    _cached_core = None
    _is_loaded = False

    @property
    def _core(self):
        """The :class:`Core`. Should only be accessed from within the
        model class itself.
        """
        if self._cached_core is None:
            self._cached_core = hero.get_cache(django_settings.NAMESPACE).core
        return self._cached_core

    @property
    def _extension(self):
        if self._meta.app_label == 'hero':
            return None
        return self._core.__extensions[self._meta.app_label]

    @property
    def is_loaded(self):
        return self._is_loaded

    @async_using_db
    def async_load(self, prefetch_related=True):
        self.load(prefetch_related=prefetch_related)

    def load(self, prefetch_related=True):
        self.refresh_from_db()
        if prefetch_related is not False:
            if prefetch_related is True:
                prefetch_related_objects((self,), *tuple((f.get_attname() + '_set' for f in self._meta.fields
                                                          if isinstance(f, ForeignObjectRel))))
            elif prefetch_related is None:
                self.objects.prefetch_related((None,))
            else:
                self.objects.prefetch_related(prefetch_related)
        self._is_loaded = True

    @async_using_db
    def async_save(self, **kwargs):
        super().save(**kwargs)

    @async_using_db
    def async_validate(self):
        self.full_clean()

    def validate(self):
        self.full_clean()

    @async_using_db
    def async_delete(self, keep_parents=False, **kwargs):
        super().delete(keep_parents=keep_parents, **kwargs)

    @classmethod
    @async_using_db
    def async_get(cls, **kwargs):
        return cls.objects.get(**kwargs)

    @classmethod
    def get(cls, **kwargs):
        return cls.objects.get(**kwargs)

    @classmethod
    @async_using_db
    def async_create(cls, **kwargs):
        return cls.objects.create(**kwargs)

    @classmethod
    def create(cls, **kwargs):
        return cls.objects.create(**kwargs)

    @classmethod
    @async_using_db
    def async_get_or_create(cls, defaults=None, **kwargs):
        return cls.objects.get_or_create(defaults=defaults, **kwargs)

    @classmethod
    def get_or_create(cls, defaults=None, **kwargs):
        return cls.objects.get_or_create(defaults=defaults, **kwargs)

    @classmethod
    @async_using_db
    def async_update_or_create(cls, defaults=None, **kwargs):
        return cls.objects.update_or_create(defaults=defaults, **kwargs)

    @classmethod
    def update_or_create(cls, defaults=None, **kwargs):
        return cls.objects.update_or_create(defaults=defaults, **kwargs)


class CoreSettings(Model):
    name = fields.CharField(primary_key=True, max_length=64)
    prefixes = fields.SeparatedValuesField(max_length=256, default=['!'])
    description = fields.TextField(max_length=512, blank=True, null=True)
    status = fields.CharField(max_length=128, blank=True, null=True)
    lang = fields.LanguageField()
    home = fields.GuildField(blank=True, null=True, on_delete=fields.SET_NULL)


class DiscordModel(Model):
    class Meta:
        abstract = True

    _discord_obj = None
    _discord_cls = None
    _discord_converter_cls = None

    @classmethod
    @async_using_db
    def from_discord_obj(cls, discord_obj):
        obj, existed_already = cls.sync_from_discord_obj(discord_obj)
        return obj, existed_already

    @classmethod
    def sync_from_discord_obj(cls, discord_obj):
        """Create a Hero object from a Discord object"""
        if not isinstance(discord_obj, cls._discord_cls):
            raise TypeError(f"discord_obj has to be a discord.{cls._discord_cls.__name__} "
                            f"but a {type(discord_obj).__name__} was passed")
        obj, created = cls.objects.get_or_create(id=discord_obj.id)
        obj._discord_obj = discord_obj
        return obj, not created

    @classmethod
    async def convert(cls, ctx, argument):
        discord_obj = await cls._discord_converter_cls.convert(ctx, argument)
        obj, existed_already = await cls.from_discord_obj(discord_obj)
        if not existed_already:
            await obj.async_save()
        return obj

    async def fetch(self):
        raise NotImplemented

    @property
    def is_fetched(self):
        return self._discord_obj is not None

    @property
    def discord(self):
        return self._discord_obj

    @async_using_db
    def async_delete(self, using=None, keep_parents=True):
        self.delete(using=using, keep_parents=keep_parents)

    def delete(self, using=None, keep_parents=True):
        super().delete(using=using, keep_parents=keep_parents)

    def __getattr__(self, name):
        if hasattr(self._discord_obj, name):
            return getattr(self._discord_obj, name)
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __str__(self):
        if self.is_fetched:
            return self.name
        else:
            return str(self.id)

    def __int__(self):
        return self.id

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.id)


class User(DiscordModel):
    id = fields.BigIntegerField(primary_key=True)
    is_staff = fields.BooleanField(default=False, db_index=True)
    is_active = fields.BooleanField(default=True, db_index=True)
    register_message = fields.MessageField(blank=True, null=True, on_delete=fields.SET_NULL)
    language = fields.LanguageField()

    _discord_cls = discord.User
    _discord_converter_cls = converter.UserConverter

    @classmethod
    def sync_from_discord_obj(cls, discord_obj):
        """Create a Hero object from a Discord object"""
        if not isinstance(discord_obj, (cls._discord_cls, discord.ClientUser)):
            raise TypeError(f"discord_obj has to be a discord.{cls._discord_cls.__name__} "
                            f"but a {type(discord_obj).__name__} was passed")
        if discord_obj.bot and discord_obj.id != discord_obj._state.user.id:
            raise ValueError("Bot users cannot be stored in the database")
        qs = cls.objects.filter(id=discord_obj.id)
        existed_already = qs.exists()
        if not existed_already:
            raise UserDoesNotExist(user_id=discord_obj.id)
        obj = qs.first()
        if not obj.is_active:
            raise InactiveUser(user_id=discord_obj.id)
        obj._discord_obj = discord_obj
        return obj, existed_already

    @async_using_db
    def async_delete(self, using=None, keep_parents=False):
        self.delete(using=using, keep_parents=keep_parents)

    def delete(self, using=None, keep_parents=False):
        _id = self.id
        name = self.name
        super().delete(using=using, keep_parents=keep_parents)
        new_user = User(id=_id, is_active=False)
        new_user.save()

    @async_using_db
    def async_load(self, prefetch_related=True):
        self.load(prefetch_related=prefetch_related)

    def load(self, prefetch_related=True):
        super().load(prefetch_related=True)
        if not self.is_active:
            raise InactiveUser(f"The user {self.id} is inactive")

    @async_using_db
    def _get_register_message(self):
        # allows internals to bypass GDPR checks to make the GDPR functionality
        # itself work, e.g. to handle register reactions
        super().load(prefetch_related=False)
        return self.register_message

    async def fetch(self) -> discord.User:
        if not self._is_loaded:
            self.load()
        discord_user = self._core.get_user(self.id)
        if discord_user is None:
            discord_user = await self._core.fetch_user(self.id)
        self._discord_obj = discord_user
        return discord_user


class Guild(DiscordModel):
    id = fields.BigIntegerField(primary_key=True)
    home = fields.BooleanField(default=False)
    # shard_id = fields.SmallIntegerField(db_index=True)
    register_time = fields.DateTimeField(auto_now_add=True)
    invite_code = fields.CharField(null=True, blank=True, max_length=64, db_index=True)
    prefix = fields.CharField(null=True, blank=True, max_length=64)
    language = fields.LanguageField()
    members = fields.ManyToManyField(to='User', through='Member')
    moderating_guild = fields.GuildField(null=True, blank=True, on_delete=fields.SET_NULL)

    _discord_cls = discord.Guild

    @property
    def invite_url(self):
        if self.invite_code is None:
            return None
        return f'https://discord.gg/{self.invite_code}'

    @invite_url.setter
    def invite_url(self, value: str):
        if not isinstance(value, str):
            raise TypeError("invite_url must be a str")
        try:
            self.invite_code = value.split('://discord.gg/')[1]
        except IndexError:
            try:
                self.invite_code = value.split('://discordapp.com/invite/')[1]
            except IndexError:
                try:
                    self.invite_code = value.split('://discord.com/invite/')[1]
                except IndexError:
                    raise ValueError("Not a valid invite URL.")

    async def fetch(self) -> discord.Guild:
        discord_guild = self._core.get_guild(self.id)
        if discord_guild is None:
            discord_guild = await self._core.fetch_guild(self.id)
        self._discord_obj = discord_guild
        return discord_guild


class TextChannel(DiscordModel):
    # can also be a DMChannel
    id = fields.BigIntegerField(primary_key=True)
    guild = fields.GuildField(db_index=True, null=True, blank=True, on_delete=fields.CASCADE)
    is_dm = fields.BooleanField(default=False)
    language = fields.LanguageField()

    _discord_cls = discord.TextChannel
    _discord_converter_cls = converter.TextChannelConverter

    @classmethod
    def sync_from_discord_obj(cls, discord_obj):
        """Create a Hero object from a Discord object"""
        if not isinstance(discord_obj, cls._discord_cls):
            if isinstance(discord_obj, discord.DMChannel):
                is_dm = True
            else:
                raise TypeError(f"discord_obj has to be a discord.{cls._discord_cls.__name__} "
                                f"or a discord.DMChannel "
                                f"but a {type(discord_obj).__name__} was passed")
        else:
            is_dm = False

        if is_dm:
            obj, created = cls.objects.get_or_create(id=discord_obj.id, is_dm=True)
        else:
            guild, _ = Guild.sync_from_discord_obj(discord_obj.guild)
            obj, created = cls.objects.get_or_create(id=discord_obj.id, guild=guild, is_dm=False)

        obj._discord_obj = discord_obj
        return obj, not created

    @classmethod
    async def convert(cls, ctx, argument):
        discord_obj = await cls._discord_converter_cls.convert(ctx, argument)
        obj, existed_already = await cls.from_discord_obj(discord_obj)
        if not existed_already:
            await obj.async_save()
        return obj

    async def fetch(self) -> discord.TextChannel:
        discord_text_channel = self._core.get_channel(self.id)
        if discord_text_channel is None:
            discord_text_channel = await self._core.fetch_channel(self.id)
        self._discord_obj = discord_text_channel
        if not self.is_dm and not self.guild.is_fetched:
            await self.guild.fetch()
        return discord_text_channel


class VoiceChannel(DiscordModel):
    id = fields.BigIntegerField(primary_key=True)
    guild = fields.GuildField(db_index=True, on_delete=fields.CASCADE)

    _discord_cls = discord.VoiceChannel
    _discord_converter_cls = converter.VoiceChannelConverter

    @classmethod
    def sync_from_discord_obj(cls, discord_obj):
        """Create a Hero object from a Discord object"""
        if not isinstance(discord_obj, cls._discord_cls):
            raise TypeError(f"discord_obj has to be a discord.{cls._discord_cls.__name__} "
                            f"but a {type(discord_obj).__name__} was passed")
        guild, _ = Guild.sync_from_discord_obj(discord_obj.guild)
        obj, created = cls.objects.get_or_create(id=discord_obj.id, guild=guild)
        obj._discord_obj = discord_obj
        return obj, not created

    async def fetch(self) -> discord.VoiceChannel:
        discord_voice_channel = self._core.get_channel(self.id)
        if discord_voice_channel is None:
            discord_voice_channel = await self._core.fetch_channel(self.id)
        self._discord_obj = discord_voice_channel
        if not self.guild.is_fetched:
            await self.guild.fetch()
        return discord_voice_channel


class CategoryChannel(DiscordModel):
    id = fields.BigIntegerField(primary_key=True)
    guild = fields.GuildField(db_index=True, on_delete=fields.CASCADE)

    _discord_cls = discord.CategoryChannel
    _discord_converter_cls = converter.CategoryChannelConverter

    @classmethod
    def sync_from_discord_obj(cls, discord_obj):
        """Create a Hero object from a Discord object"""
        if not isinstance(discord_obj, cls._discord_cls):
            raise TypeError(f"discord_obj has to be a discord.{cls._discord_cls.__name__} "
                            f"but a {type(discord_obj).__name__} was passed")
        guild, _ = Guild.sync_from_discord_obj(discord_obj.guild)
        obj, created = cls.objects.get_or_create(id=discord_obj.id, guild=guild)
        obj._discord_obj = discord_obj
        return obj, not created

    async def fetch(self) -> discord.CategoryChannel:
        discord_category_channel = self._core.get_channel(self.id)
        if discord_category_channel is None:
            discord_category_channel = await self._core.fetch_channel(self.id)
        self._discord_obj = discord_category_channel
        if not self.guild.is_fetched:
            await self.guild.fetch()
        return discord_category_channel


class Role(DiscordModel):
    id = fields.BigIntegerField(primary_key=True)
    guild = fields.GuildField(db_index=True, on_delete=fields.CASCADE)

    _discord_cls = discord.Role
    _discord_converter_cls = converter.RoleConverter

    @classmethod
    def sync_from_discord_obj(cls, discord_obj):
        """Create a Hero object from a Discord object"""
        if not isinstance(discord_obj, cls._discord_cls):
            raise TypeError(f"discord_obj has to be a discord.{cls._discord_cls.__name__} "
                            f"but a {type(discord_obj).__name__} was passed")
        guild, _ = Guild.sync_from_discord_obj(discord_obj.guild)
        obj, created = cls.objects.get_or_create(id=discord_obj.id, guild=guild)
        obj._discord_obj = discord_obj
        return obj, not created

    async def fetch(self) -> discord.Role:
        if not self.guild.is_fetched:
            await self.guild.fetch()
        discord_role = self.guild.get_role(self.id)
        if discord_role is None:
            discord_role = await self.guild.fetch_role(self.id)
        self._discord_obj = discord_role
        return discord_role


class Emoji(DiscordModel):
    id = fields.BigIntegerField(primary_key=True, auto_created=True)
    name = fields.CharField(max_length=64)
    animated = fields.BooleanField(default=False)
    is_custom = fields.BooleanField()

    _discord_cls = discord.PartialEmoji
    _discord_converter_cls = converter.PartialEmojiConverter

    @classmethod
    def sync_from_discord_obj(cls, discord_obj):
        """Create a Hero object from a Discord object"""
        if not isinstance(discord_obj, (cls._discord_cls, discord.Emoji)):
            raise TypeError(f"discord_obj has to be a discord.{cls._discord_cls.__name__} "
                            f"or discord.Emoji"
                            f"but a {type(discord_obj).__name__} was passed")
        if isinstance(discord_obj, discord.Emoji):
            discord_obj = discord.PartialEmoji(name=discord_obj.name, animated=discord_obj.animated, id=discord_obj.id)
        obj, created = cls.objects.get_or_create(id=discord_obj.id, name=discord_obj.name, animated=discord_obj.animated)
        obj._discord_obj = discord_obj
        return obj, not created

    async def fetch(self) -> discord.PartialEmoji:
        if self.is_custom:
            if not self.guild.is_fetched:
                await self.guild.fetch()
            self.guild: discord.Guild
            emoji = await self.guild.fetch_emoji(self.id)
            discord_emoji = discord.PartialEmoji(name=emoji.name, animated=emoji.animated, id=emoji.id)
            if self.name != emoji.name:
                self.name = emoji.name
                await self.async_save()
        else:
            discord_emoji = discord.PartialEmoji(name=self.name)
        self._discord_obj = discord_emoji

        return discord_emoji


class Member(DiscordModel):
    class Meta:
        unique_together = (('user', 'guild'),)

    auto_id = _models.BigAutoField(primary_key=True)
    user = fields.UserField(db_index=True, on_delete=fields.CASCADE)
    guild = fields.GuildField(db_index=True, on_delete=fields.CASCADE)

    _discord_cls = discord.Member
    _discord_converter_cls = converter.MemberConverter

    def __getattr__(self, name):
        if name == 'id':
            _discord_obj = getattr(self, '_discord_obj', None)
            if _discord_obj is not None:
                return self._discord_obj.id
        return super().__getattr__(name)

    @classmethod
    def sync_from_discord_obj(cls, discord_obj):
        """Create a Hero object from a Discord object"""
        if not isinstance(discord_obj, discord.Member):
            raise TypeError(f"discord_obj has to be a discord.Member "
                            f"but a {type(discord_obj).__name__} was passed")
        _user, _ = User.sync_from_discord_obj(discord_obj._user)
        _guild, _ = Guild.sync_from_discord_obj(discord_obj.guild)
        # workaround for the nonexistence of composite primary keys in Django
        qs = cls.objects.filter(user=_user, guild=_guild)
        if qs.exists():
            obj = qs.first()
            obj.load()
            existed_already = True
        else:
            obj = cls.objects.create(user=_user, guild=_guild)
            existed_already = False
        obj._discord_obj = discord_obj
        return obj, existed_already

    async def fetch(self) -> discord.Member:
        if not self.guild.is_fetched:
            await self.guild.fetch()
        discord_member = self.guild.get_member(self.id)
        if discord_member is None:
            discord_member = await self.guild.fetch_member(self.id)
        self._discord_obj = discord_member
        if not self.user.is_fetched:
            self.user._discord_obj = discord_member.user
        return discord_member


class Message(DiscordModel):
    id = fields.BigIntegerField(primary_key=True)
    channel = fields.TextChannelField(db_index=True, on_delete=fields.CASCADE)
    author = fields.UserField(db_index=True, on_delete=fields.CASCADE)

    _discord_cls = discord.Message
    _discord_converter_cls = converter.MessageConverter

    @property
    def guild(self):
        return self.channel.guild

    @guild.setter
    def guild(self, value):
        if self.channel.is_dm:
            raise AttributeError("Cannot set guild of private message")
        self.channel.guild = value

    @classmethod
    def sync_from_discord_obj(cls, discord_obj):
        """Create a Hero object from a Discord object"""
        if not isinstance(discord_obj, cls._discord_cls):
            raise TypeError(f"discord_obj has to be a discord.{cls._discord_cls.__name__} "
                            f"but a {type(discord_obj).__name__} was passed")
        channel, _ = TextChannel.sync_from_discord_obj(discord_obj.channel)
        if discord_obj.guild:
            user = discord_obj.author._user
        else:
            user = discord_obj.author
        author, _ = User.sync_from_discord_obj(user)
        obj, created = cls.objects.get_or_create(id=discord_obj.id, channel=channel, author=author)
        obj._discord_obj = discord_obj
        return obj, not created

    async def fetch(self) -> discord.Message:
        if not self.channel.is_fetched:
            await self.channel.fetch()
        discord_message = self.channel.get_message(self.id)
        if discord_message is None:
            discord_message = await self.channel.fetch_message(self.id)
        self._discord_obj = discord_message
        return discord_message


class Settings(Model):
    class Meta:
        abstract = True

    namespace = fields.NamespaceField(primary_key=True)
