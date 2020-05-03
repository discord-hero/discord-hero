"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

from functools import partial

import discord

from django.db import router, signals, transaction
from django.db.models import (BigIntegerField, BooleanField, CharField, CASCADE,
                              DateField, DateTimeField, DecimalField, FloatField,
                              ForeignKey as _ForeignKey, ForeignObject,
                              IntegerField, ManyToManyField as _ManyToManyField,
                              SET_DEFAULT, SET_NULL, SmallIntegerField, TextField)
from django.db.models.fields.related_descriptors import (ManyToManyDescriptor as _ManyToManyDescriptor,
                                                         ReverseManyToOneDescriptor as _ReverseManyToOneDescriptor,
                                                         create_forward_many_to_many_manager,
                                                         create_reverse_many_to_one_manager)
from django.db.models.fields.related import lazy_related_operation, create_many_to_many_intermediary_model
from django.utils.functional import cached_property

from .i18n import Languages
from .errors import InactiveUser
from .utils import sync_to_async_threadsafe


# Make calls to related fields async
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
            @sync_to_async_threadsafe
            def async_async_create(self, **kwargs):
                self.create(**kwargs)

            @sync_to_async_threadsafe
            def async_get_or_create(self, **kwargs):
                self.get_or_create(**kwargs)

            @sync_to_async_threadsafe
            def async_update_or_create(self, **kwargs):
                return self.update_or_create(**kwargs)

            @sync_to_async_threadsafe
            def async_clear(self, *, bulk=True):
                self.clear(bulk=bulk)

            @sync_to_async_threadsafe
            def async_set(self, objs, *, bulk=True, clear=False):
                return self.set(objs, bulk=bulk, clear=clear)

            @sync_to_async_threadsafe
            def async_remove(self, *args, **kwargs):
                return self.remove(*args, **kwargs)

            @sync_to_async_threadsafe
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
            @sync_to_async_threadsafe
            def async_create(self, **kwargs):
                self.create(**kwargs)

            @sync_to_async_threadsafe
            def async_get_or_create(self, *, through_defaults=None, **kwargs):
                self.get_or_create(through_defaults=through_defaults, **kwargs)

            @sync_to_async_threadsafe
            def async_update_or_create(self, *, through_defaults=None, **kwargs):
                return self.update_or_create(through_defaults=through_defaults, **kwargs)

            @sync_to_async_threadsafe
            def async_clear(self):
                self.clear()

            @sync_to_async_threadsafe
            def async_set(self, objs, *, clear=False, through_defaults=None):
                return self.set(objs, clear=clear, through_defaults=through_defaults)

            @sync_to_async_threadsafe
            def async_remove(self, *args, **kwargs):
                return self.remove(*args, **kwargs)

            @sync_to_async_threadsafe
            def async_add(self, *args, **kwargs):
                return self.add(*args, **kwargs)

        return ManyRelatedManager


class ForeignKey(_ForeignKey):
    related_accessor_class = ReverseManyToOneDescriptor


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


class DiscordField(ForeignKey):
    _discord_cls = None
    _discord_obj = None

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["to"] = type(self)._discord_cls.__name__
        return name, path, args, kwargs

    def __init__(self, *args, **kwargs):
        kwargs["to"] = type(self)._discord_cls.__name__
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


class MessageField(DiscordField):
    _discord_cls = discord.Message


class ManyDiscordField(ManyToManyField):
    _discord_cls = None
    _discord_obj = None

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["to"] = type(self)._discord_cls.__name__
        return name, path, args, kwargs

    def __init__(self, *args, **kwargs):
        kwargs["to"] = type(self)._discord_cls.__name__
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


class ManyMembersField(ManyDiscordField):
    _discord_cls = discord.Member


class ManyMessagesField(ManyDiscordField):
    _discord_cls = discord.Message


class NamespaceField(ForeignKey):
    def __init__(self, **kwargs):
        super().__init__(to='CoreSettings', on_delete=CASCADE)


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
    def to_python(self, value):
        if not value:
            return []
        if isinstance(value, (tuple, list, set)):
            return value
        return value.split(';')

    def get_prep_value(self, value):
        if not value:
            return ''
        return ';'.join(value)

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)
