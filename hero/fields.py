"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import asyncio
from functools import partial

import discord

from django.core.exceptions import SynchronousOnlyOperation
from django.db.models import (AutoField, BigIntegerField, BooleanField, CharField as _CharField,
                              CASCADE, DateField, DateTimeField, DecimalField, FloatField,
                              ForeignKey as _ForeignKey, ForeignObject,
                              IntegerField, ManyToManyField as _ManyToManyField,
                              SET_DEFAULT, SET_NULL, SmallIntegerField, TextField)
from django.db.models.fields.related_descriptors import (ManyToManyDescriptor as _ManyToManyDescriptor,
                                                         ReverseManyToOneDescriptor as _ReverseManyToOneDescriptor,
                                                         ForwardManyToOneDescriptor as _ForwardManyToOneDescriptor,
                                                         ForeignKeyDeferredAttribute as _ForeignKeyDeferredAttribute,
                                                         create_forward_many_to_many_manager,
                                                         create_reverse_many_to_one_manager)
from django.db.models.fields.related import lazy_related_operation, create_many_to_many_intermediary_model
from django.db.models.signals import pre_delete
from django.utils.functional import cached_property

from .i18n import Languages
from .errors import InactiveUser
from .utils import async_using_db, maybe_coroutine


class ForeignKeyDeferredAttribute(_ForeignKeyDeferredAttribute):
    def __get__(self, instance, cls=None):
        # make ForeignKeys compatible with asyncio
        try:
            event_loop = asyncio.get_event_loop()
        except RuntimeError:
            return super(ForeignKeyDeferredAttribute, self).__get__(instance, cls=cls)
        else:
            if event_loop.is_running():
                if self.field.is_cached(instance):
                    # wrap cached value in coroutine so it will always have to be awaited
                    # if accessed from an async context to make behavior more consistent
                    return maybe_coroutine(super(ForeignKeyDeferredAttribute, self).__get__, instance, cls=cls)
                else:
                    return async_using_db(super(ForeignKeyDeferredAttribute, self).__get__)(instance, cls=cls)
            return super(ForeignKeyDeferredAttribute, self).__get__(instance, cls=cls)


class ForwardManyToOneDescriptor(_ForwardManyToOneDescriptor):
    def __get__(self, instance, cls=None):
        if instance is None:
            return self

        try:
            event_loop = asyncio.get_event_loop()
        except RuntimeError:
            return super(ForwardManyToOneDescriptor, self).__get__(instance, cls=cls)
        else:
            if event_loop.is_running():
                if self.field.is_cached(instance):
                    # wrap cached value in coroutine so it will always have to be awaited
                    # if accessed from an async context to make behavior more consistent
                    return maybe_coroutine(super(ForwardManyToOneDescriptor, self).__get__, instance, cls=cls)
                else:
                    return async_using_db(super(ForwardManyToOneDescriptor, self).__get__)(instance, cls=cls)
            return super(ForwardManyToOneDescriptor, self).__get__(instance, cls=cls)


# Make calls to related fields' methods async
# (kinda hacky since Django does not provide an
# easy way to override the (Many)RelatedManager used)
class ReverseManyToOneDescriptor(_ReverseManyToOneDescriptor):
    @cached_property
    def related_manager_cls(self):
        related_model = self.rel.related_model

        class RelatedManager(create_reverse_many_to_one_manager(
            related_model._default_manager.__class__,
            self.rel,
        )):
            @async_using_db
            def async_create(self, **kwargs):
                self.create(**kwargs)

            @async_using_db
            def async_get_or_create(self, **kwargs):
                self.get_or_create(**kwargs)

            @async_using_db
            def async_update_or_create(self, **kwargs):
                return self.update_or_create(**kwargs)

            @async_using_db
            def async_clear(self, *, bulk=True):
                self.clear(bulk=bulk)

            @async_using_db
            def async_set(self, objs, *, bulk=True, clear=False):
                return self.set(objs, bulk=bulk, clear=clear)

            @async_using_db
            def async_remove(self, *args, **kwargs):
                return self.remove(*args, **kwargs)

            @async_using_db
            def async_add(self, *args, **kwargs):
                return self.add(*args, **kwargs)

        return RelatedManager


class ManyToManyDescriptor(_ManyToManyDescriptor):
    @cached_property
    def related_manager_cls(self):
        related_model = self.rel.related_model if self.reverse else self.rel.model

        class ManyRelatedManager(create_forward_many_to_many_manager(
            related_model._default_manager.__class__,
            self.rel,
            reverse=self.reverse,
        )):
            @async_using_db
            def async_create(self, **kwargs):
                self.create(**kwargs)

            @async_using_db
            def async_get_or_create(self, *, through_defaults=None, **kwargs):
                self.get_or_create(through_defaults=through_defaults, **kwargs)

            @async_using_db
            def async_update_or_create(self, *, through_defaults=None, **kwargs):
                return self.update_or_create(through_defaults=through_defaults, **kwargs)

            @async_using_db
            def async_clear(self):
                self.clear()

            @async_using_db
            def async_set(self, objs, *, clear=False, through_defaults=None):
                return self.set(objs, clear=clear, through_defaults=through_defaults)

            @async_using_db
            def async_remove(self, *args, **kwargs):
                return self.remove(*args, **kwargs)

            @async_using_db
            def async_add(self, *args, **kwargs):
                return self.add(*args, **kwargs)

        return ManyRelatedManager


class ForeignKey(_ForeignKey):
    descriptor_class = ForeignKeyDeferredAttribute
    related_accessor_class = ReverseManyToOneDescriptor
    forward_related_accessor_class = ForwardManyToOneDescriptor


class ManyToManyField(_ManyToManyField):
    def contribute_to_class(self, cls, name, **kwargs):
        # To support multiple relations to self, it's useful to have a non-None
        # related name on symmetrical relations for internal reasons. The
        # concept doesn't make a lot of sense externally ("you want me to
        # specify *what* on my non-reversible relation?!"), so we set it up
        # automatically. The funky name reduces the chance of an accidental
        # clash.
        if self.remote_field.symmetrical and (
            self.remote_field.model == "self" or self.remote_field.model == cls._meta.object_name):
            self.remote_field.related_name = "%s_rel_+" % name
        elif self.remote_field.is_hidden():
            # If the backwards relation is disabled, replace the original
            # related_name with one generated from the m2m field name. Django
            # still uses backwards relations internally and we need to avoid
            # clashes between multiple m2m fields with related_name == '+'.
            self.remote_field.related_name = "_%s_%s_+" % (cls.__name__.lower(), name)

        super(_ManyToManyField, self).contribute_to_class(cls, name, **kwargs)

        # The intermediate m2m model is not auto created if:
        #  1) There is a manually specified intermediate, or
        #  2) The class owning the m2m field is abstract.
        #  3) The class owning the m2m field has been swapped out.
        if not cls._meta.abstract:
            if self.remote_field.through:
                def resolve_through_model(_, model, field):
                    field.remote_field.through = model
                lazy_related_operation(resolve_through_model, cls, self.remote_field.through, field=self)
            elif not cls._meta.swapped:
                self.remote_field.through = create_many_to_many_intermediary_model(self, cls)

        # Add the descriptor for the m2m relation.
        setattr(cls, self.name, ManyToManyDescriptor(self.remote_field, reverse=False))

        # Set up the accessor for the m2m table name for the relation.
        self.m2m_db_table = partial(self._get_m2m_db_table, cls._meta)

    def contribute_to_related_class(self, cls, related):
        # Internal M2Ms (i.e., those with a related name ending with '+')
        # and swapped models don't get a related descriptor.
        if not self.remote_field.is_hidden() and not related.related_model._meta.swapped:
            setattr(cls, related.get_accessor_name(), ManyToManyDescriptor(self.remote_field, reverse=True))

        # Set up the accessors for the column names on the m2m table.
        self.m2m_column_name = partial(self._get_m2m_attr, related, 'column')
        self.m2m_reverse_name = partial(self._get_m2m_reverse_attr, related, 'column')

        self.m2m_field_name = partial(self._get_m2m_attr, related, 'name')
        self.m2m_reverse_field_name = partial(self._get_m2m_reverse_attr, related, 'name')

        get_m2m_rel = partial(self._get_m2m_attr, related, 'remote_field')
        self.m2m_target_field_name = lambda: get_m2m_rel().field_name
        get_m2m_reverse_rel = partial(self._get_m2m_reverse_attr, related, 'remote_field')
        self.m2m_reverse_target_field_name = lambda: get_m2m_reverse_rel().field_name


# Django doesn't handle critical errors caused by max_length=None for some reason
class CharField(_CharField):
    def __init__(self, *args, **kwargs):
        if not kwargs.get('max_length'):
            cls = self.__class__
            raise TypeError(f"missing required keyword argument 'max_length' in {cls.__name__}")
        super().__init__(*args, **kwargs)


class DiscordField(ForeignKey):
    _discord_cls = None
    _discord_obj = None

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["to"] = f"hero.{type(self)._discord_cls.__name__}"
        return name, path, args, kwargs

    def __init__(self, *args, **kwargs):
        kwargs["to"] = f"hero.{type(self)._discord_cls.__name__}"
        super(DiscordField, self).__init__(*args, **kwargs)


class UserField(DiscordField):
    _discord_cls = discord.User

    def validate(self, value, model_instance):
        if value.is_inactive:
            raise InactiveUser(f"The user {value.id} is inactive")


class GuildField(DiscordField):
    _discord_cls = discord.Guild


class MemberField(DiscordField):
    _discord_cls = discord.Member


class TextChannelField(DiscordField):
    _discord_cls = discord.TextChannel


class VoiceChannelField(DiscordField):
    _discord_cls = discord.VoiceChannel


class RoleField(DiscordField):
    _discord_cls = discord.Role


class EmojiField(DiscordField):
    _discord_cls = discord.Emoji

    def __init__(self, *args, **kwargs):
        self.reverse_cascade = kwargs.pop('reverse_cascade', True)
        super(EmojiField, self).__init__(*args, **kwargs)

    def _reverse_cascade(self, sender, instance, using, **kwargs):
        emoji = getattr(instance, self.name)
        if emoji:
            emoji.delete()

    def contribute_to_class(self, cls, name, private_only=False, **kwargs):
        super(EmojiField, self).contribute_to_class(cls, name, private_only=private_only, **kwargs)
        if self.reverse_cascade:
            pre_delete.connect(self._reverse_cascade, sender=cls)


class MessageField(DiscordField):
    _discord_cls = discord.Message


class ManyDiscordField(ManyToManyField):
    _discord_cls = None
    _discord_obj = None

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["to"] = f"hero.{type(self)._discord_cls.__name__}"
        return name, path, args, kwargs

    def __init__(self, *args, **kwargs):
        kwargs["to"] = f"hero.{type(self)._discord_cls.__name__}"
        super(ManyDiscordField, self).__init__(*args, **kwargs)


class ManyUsersField(ManyDiscordField):
    _discord_cls = discord.User


class ManyGuildsField(ManyDiscordField):
    _discord_cls = discord.Guild


class ManyTextChannelsField(ManyDiscordField):
    _discord_cls = discord.TextChannel


class ManyVoiceChannelsField(ManyDiscordField):
    _discord_cls = discord.VoiceChannel


class ManyRolesField(ManyDiscordField):
    _discord_cls = discord.Role


class ManyEmojisField(ManyDiscordField):
    _discord_cls = discord.Emoji

    def __init__(self, *args, **kwargs):
        self.reverse_cascade = kwargs.pop('reverse_cascade', True)
        super(ManyEmojisField, self).__init__(*args, **kwargs)

    def _reverse_cascade(self, sender, instance, using, **kwargs):
        emojis = getattr(instance, self.name)
        if emojis is not None:
            for emoji in emojis:
                emoji.delete()

    def contribute_to_class(self, cls, name, private_only=False, **kwargs):
        super(ManyEmojisField, self).contribute_to_class(cls, name, private_only=private_only, **kwargs)
        if self.reverse_cascade:
            pre_delete.connect(self._reverse_cascade, sender=cls)


class ManyMembersField(ManyDiscordField):
    _discord_cls = discord.Member


class ManyMessagesField(ManyDiscordField):
    _discord_cls = discord.Message


class NamespaceField(ForeignKey):
    def __init__(self, **kwargs):
        super().__init__(to='hero.CoreSettings', on_delete=CASCADE)


class LanguageField(CharField):
    def __init__(self, **kwargs):
        kwargs['max_length'] = 16
        kwargs['default'] = Languages.default
        super().__init__(**kwargs)

    def get_prep_value(self, value: Languages) -> str:
        return value.value

    def from_db_value(self, value, expression, connection):
        return Languages(value)

    def to_python(self, value: str) -> Languages:
        if isinstance(value, Languages):
            return value
        if value is None:
            return Languages.default
        try:
            return Languages(value)
        except ValueError:
            raise ValueError(
                "{language_value} is not a valid language".format(language_value=value)
            )


class SeparatedValuesField(CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', [])
        self.converter = kwargs.pop('converter', None)
        self.serializer = kwargs.pop('serializer', None)
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            return []
        if isinstance(value, (tuple, list, set)):
            return value
        ret = value.split(';')
        if self.converter:
            ret = [self.converter(value) for value in ret]
        return ret

    def get_prep_value(self, value):
        if not value:
            return ''
        if self.converter:
            if self.serializer:
                value = [self.serializer(_value) for _value in value]
            else:
                value = [str(_value) for _value in value]
        return ';'.join(value)

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)
