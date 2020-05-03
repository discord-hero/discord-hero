"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import abc
import enum
from typing import Union

from hero.models import User, Member


class Group(abc.ABC):
    def __call__(self, user: Union[User, Member]):
        return self.check(user)

    @property
    def name(self):
        return

    @abc.abstractmethod
    def check(self, user: Union[User, Member]):
        raise NotImplementedError


class JoinedGroup:
    def __init__(self, *groups):
        self.groups = groups

    def any(self, user: Union[User, Member]):
        return any((group.check(user) for group in self.groups))

    def all(self, user: Union[User, Member]):
        return all((group.check(user) for group in self.groups))


class Groups(enum.Enum):
    # this only works for immediate subclasses
    # see https://stackoverflow.com/a/5883218
    def __call__(self, value, *args, **kwargs):
        if type(self) is Groups:
            for subclass in Groups.__subclasses__():
                if value in subclass:
                    return subclass(value)
        return super().__call__(value, *args, **kwargs)

    def __getattr__(self, item):
        if type(self) is Groups:
            for subclass in Groups.__subclasses__():
                if hasattr(subclass, item):
                    return getattr(subclass, item)
        return None

    @classmethod
    def any(cls, user: Union[User, Member], *groups):
        joined_group = JoinedGroup(groups)
        return joined_group.any(user), joined_group

    @classmethod
    def all(cls, user: Union[User, Member], *groups):
        joined_group = JoinedGroup(groups)
        return joined_group.all(user), joined_group


class CoreGroups(Groups):
    EVERYONE = 'everyone'
    AUTHENTICATED = 'authenticated'
    SELF = 'self'
    STAFF = 'staff'
    OWNER = 'owner'


class GuildGroups(Groups):
    GUILD_MEMBER = 'guild_member'
    GUILD_MODERATOR = 'guild_moderator'
    GUILD_ADMINISTRATOR = 'guild_administrator'
    GUILD_OWNER = 'guild_owner'


class GuildPermissionGroups(Groups):
    CAN_MANAGE_GUILD = 'can_manage_guild'
    CAN_MANAGE_CHANNELS = 'can_manage_channels'
    CAN_VIEW_AUDIT_LOG = 'can_view_audit_log'
    CAN_KICK_MEMBERS = 'can_kick_members'
    CAN_BAN_MEMBERS = 'can_ban_members'
    IS_ADMINISTRATOR = 'is_administrator'
    CAN_CHANGE_NICKNAME = 'can_change_nickname'
    CAN_MANAGE_NICKNAMES = 'can_manage_nicknames'
    CAN_MANAGE_EMOJIS = 'can_manage_emojis'


class ChannelGroups(Groups):
    CAN_CREATE_INSTANT_INVITE = 'can_create_instant_invite'
    CAN_MANAGE_CHANNEL = 'can_manage_channel'


class TextChannelGroups(Groups):
    CAN_READ_MESSAGES = 'can_read_messages'
    CAN_SEND_MESSAGES = 'can_send_messages'
    CAN_SEND_TTS_MESSAGES = 'can_send_tts_messages'
    CAN_MANAGE_MESSAGES = 'can_manage_messages'
    CAN_EMBED_LINKS = 'can_embed_links'
    CAN_ATTACH_FILES = 'can_attach_files'
    CAN_READ_MESSAGE_HISTORY = 'can_read_message_history'
    CAN_MENTION_EVERYONE = 'can_mention_everyone'
    CAN_USE_EXTERNAL_EMOJIS = 'can_use_external_emojis'
    CAN_ADD_REACTIONS = 'can_add_reactions'
    CAN_MANAGE_WEBHOOKS = 'can_manage_webhooks'


class VoiceChannelGroups(Groups):
    CAN_VIEW_CHANNEL = 'can_view_channel'
    CAN_CONNECT = 'can_connect'
    CAN_SPEAK = 'can_speak'
    CAN_MUTE_MEMBERS = 'can_mute_members'
    CAN_DEAFEN_MEMBERS = 'can_deafen_members'
    CAN_MOVE_MEMBERS = 'can_move_members'
    CAN_USE_VOICE_ACTIVITY = 'can_use_voice_activity'


class RoleGroups(Groups):
    HAS_ROLE = 'has_role'


class RolesGroups(Groups):
    HAS_NO_ROLE = 'has_no_role'
    HAS_ANY_ROLE = 'has_any_role'
    HAS_ALL_ROLES = 'has_all_roles'


class Permission(dict):
    # TODO
    pass


class BotPermission(Permission):
    # what to show to the user if the permission check fails
    check_failure = NotImplemented


class ApiPermission(Permission):
    # TODO
    pass


class BotPermissionsEnum(enum.Enum):
    @classmethod
    def __init_subclass__(cls, **kwargs):
        for permission in cls:
            if not isinstance(permission.value, BotPermission):
                raise ValueError(f"{cls.__name__} enum members must be"
                                 f"of type hero.BotPermission")


class ApiPermissionsEnum(enum.Enum):
    # TODO
    pass


class BotPermissions(enum.Enum):
    # TODO
    pass


async def get_api_permissions(auth_token: str, field: str=None):
    # TODO where to put this
    pass
