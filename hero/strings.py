"""discord-hero: Discord Application Framework for humans

:copyright: (c) 2019-2020 monospacedmagic et al.
:license: Apache-2.0 OR MIT
"""

import importlib


class Strings:
    # TODO
    def __init__(self, extension):
        self.extension = extension
        self.module = importlib.import_module('strings', f'hero.extensions.{extension}')

    def __getattr__(self, item):
        return getattr(self.module, item).format


setup_greeting = """discord-hero - First run configuration

Insert your bot's token, or enter 'cancel' to cancel the setup:"""

not_a_token = "Invalid input. Restart discord-hero and repeat the configuration process."

choose_prefix = """Choose a prefix. A prefix is what you type before a command.
A typical prefix would be the exclamation mark.
Can be multiple characters. You will be able to change it later and add more of them.
Choose your prefix:"""

confirm_prefix = """Are you sure you want {0} as your prefix?
You will be able to issue commands like this: {0}help
Type yes to confirm or no to change it"""

no_prefix_set = "No prefix set. Defaulting to !"

setup_finished = """
The configuration is done. Do not exit this session to keep your bot online.
All commands will have to be issued via Discord,
this session will now be read only.
Press enter to continue"""

logging_into_discord = "Logging into Discord..."

invalid_credentials = """Invalid login credentials.
If they worked before Discord might be having temporary technical issues.
In this case, press enter and try again later.
Otherwise you can type 'reset' to delete the current configuration and
redo the setup process again the next start.
> """

official_server = "Official support server: {}"

invite_link = "https://discord.gg/T7zcpnK"

bot_is_online = "{} is now online."

connected_to = "Connected to:"

connected_to_servers = "{} servers"

connected_to_channels = "{} channels"

connected_to_users = "{} users"

prefix_singular = "Prefix"

prefix_plural = "Prefixes"

use_this_url = "Use this URL to bring your bot to a server:"

update_the_api = """\nYou are using an outdated discord.py.\n
Update using pip3 install -U discord.py"""

command_not_found = "No command called {} found."

command_disabled = "That command is disabled."

exception_in_command = "Exception in command '{}'"

error_in_command = "Error in command '{}' - {}: {}"

not_available_in_dm = "That command is not available in DMs."

command_has_no_subcommands = "Command {0.name} has no subcommands."

group_help = "{} command group"

owner_recognized = "{} has been recognized and set as owner."

one_user_is_not_registered = "At least one user is not registered; ask them to use `{}register`."

one_user_is_inactive = "{0}, at least one user, {1}, has opted out of using commands and features that " \
                       "store data related to their Discord user ID, so this feature/command cannot be used " \
                       "if it involves them. You can ask them to use `{2}register` again to reregister " \
                       "them in my system so you can use the feature/command you wanted to use involving them."

user_not_registered = """{0}, thanks for your interest in using my features!
I noticed that you wanted to use a feature that requires me to store data \
related to your user ID on Discord. For that I need your explicit permission \
before you can use my commands. To allow me to store data related to your \
user ID, please type `{1}register` or react with \u2705. If you don't want me to store any data \
related to your user ID, type `{1}unregister` instead. Don't worry, you can \
always change your mind.

Whatever your decision looks like, I wish you lots of fun on Discord!"""

user_inactive = """{0}, you have opted out of using commands and features that \
store data related to your Discord ID, so this feature/command cannot be used.
You can opt back in using `{1}register`."""

other_user_not_registered = """Hello {0}!
I noticed that someone wanted to use a feature that requires me to store data \
related to your user ID on Discord. For that I need your explicit permission. \
To allow me to store data related to your \
user ID, please type `{1}register` or react with \u2705. If you don't want me to store any data \
related to your user ID, type `{1}unregister` instead. Don't worry, you can \
always change your mind.

Whatever your decision looks like, I wish you lots of fun on Discord!"""

failed_to_install = "Failed to install '**{}**'."

failed_to_update = "Failed to update '**{}**'."

specify_extension_name = "Please specify a name for this extension (must be a valid Python package name)."

skipping_this_extension = "Not installing this extension."

unsatisfied_requirements = "Missing required packages:"

unsatisfied_dependencies = "Missing required extensions:"

prompt_install_requirements = "Do you want to install the missing required packages?"

would_be_uninstalled_too = str("Extensions that would be uninstalled as well "
                               "as they depend on '**{}**':")

proceed_with_uninstallation = str("Do you want to proceed? This will uninstall "
                                  "the above listed extensions. (yes/no)")
