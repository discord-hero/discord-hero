import enum


class RateLimit:
    def __init__(self, times: int, per_seconds: int):
        self.times = times
        self.per_seconds = per_seconds


class Methods(enum.Enum):
    GET = 'get'
    LIST = 'list'
    SET = 'set'
    CREATE = 'create'
    EDIT = 'edit'
    DELETE = 'delete'


class Groups(enum.Enum):
    EVERYONE = 'everyone'
    AUTHENTICATED = 'authenticated'
    STAFF = 'hero_staff'
    OWNER = 'hero_owner'


class GuildGroups(enum.Enum):
    MEMBER = 'guild_member'
    MODERATOR = 'guild_moderator'
    ADMINISTRATOR = 'guild_administrator'
    OWNER = 'guild_owner'


default_bot_permissions = {
    'core': {
        'help': {
            Groups.EVERYONE.value: {
                'allowed': True,
                'times': 1,
                'interval': 0.5
            }
        }
    }
}


default_api_permissions = {
    'member': {
        'nickname': {
            Methods.GET.value: {
                Groups.EVERYONE.value: {
                    'allowed': True,
                    'times': 1,
                    'interval': 300.0
                },
                Groups.AUTHENTICATED.value: {
                    'allowed': True,
                    'times': 1,
                    'interval': 300.0
                },
                Groups.STAFF.value: {
                    'allowed': True,
                    'times': 1,
                    'interval': 300.0
                },
                Groups.OWNER.value: {
                    'allowed': True,
                    'times': 1,
                    'interval': 300.0
                },
                GuildGroups.MEMBER.value: {
                    'allowed': True,
                    'times': 1,
                    'interval': 300.0
                },
                GuildGroups.MODERATOR.value: {
                    'allowed': True,
                    'times': 1,
                    'interval': 300.0
                },
                GuildGroups.ADMINISTRATOR.value: {
                    'allowed': True,
                    'times': 1,
                    'interval': 300.0
                },
                GuildGroups.OWNER.value: {
                    'allowed': True,
                    'times': 1,
                    'interval': 300.0
                }
            }
        }
    }
}
