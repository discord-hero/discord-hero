# Ultima

Ultima is an asynchronous, fully modular [Discord](https://discordapp.com/) bot framework with a
REST API and an exchangeable web frontend.

This project follows a new development approach for libraries that I wanted to try out for some time
which is called FDTI, short for **F**eature-driven **D**ocumentation, **D**ocumentation-driven **T**ests,
**T**est-driven **I**mplementation. This results in following development process:

1. Line out **features** (use case diagrams, activity diagrams etc. can be used for this)
2. **Document** how those features (will) look like (and write accompanying guides if it makes sense)
3. Add examples to the documentation where you didn't already add ones and set up a way to automatically
   test them if possible (easier to maintain), or write tests outside of the documentation
4. Make those examples and tests work by implementing all the features according to the documentation

After each of these steps, check with users, stakeholders, coworkers and whoever else is interested
in your project. If there are design flaws, they are likely to surface much earlier this way, which can
save you and those who use your software a tremendous amount of headache and wasted time and effort.

At the time of this writing, I have already completed step 1 for the entire project, so expect to see
some documentation soon.

## Extensions

Extensions are Ultima's plug-ins. They can be disabled, enabled, installed and uninstalled during runtime.

## Bot



## Cogs

Cogs are the main building blocks of an extension. They are essentially simply classes that inherit from
`ultima.Cog`. By inheriting from `ultima.Cog`, the class is automatically added to the `Bot` instance's cogs
unless the extension it belongs to is disabled. A Cog that is added to the bot instance can be accessed via
the bot instance's attributes. The name of the cog attribute of the bot instance is the `snake_case`'d version
of the cog's class name.

    import ultima
    
    class RoleManagement(ultima.Cog):
        @property
        def is_enabled(self):
            return getattr(self.bot, "role_management", None) is self

(This property already exists for every cog, by the way, so you don't need to write it yourself.)

## Commands

Decorate a `Cog`'s coroutine method with `ultima.command()` to create a `Command`.

    @ultima.command()
    @ultima.guild_only()  # A check ensuring that the command can only be invoked on a Discord server (Guild)
    async def set_channel_name(self, ctx: ultima.Context, name: str, channel: ultima.Channel=None):
        # !set channel name <new name> [channel]
        # TODO actually set the channel name
        pass

### Event listeners

Start a coroutine method's name with `on_` to turn it into an event listener.
Valid listener names and parameters can be looked up [here](https://www.example.com/).

    async def on_message(self, message: ultima.Message):
        # essentially be a stereotypical parrot
        if message.author != self.bot.user:
            await message.channel.send(message.content)

## Background tasks

Decorate a coroutine method with `@ultima.background_task()` to turn it into a background task. It will be ran in the
background as soon as Ultima launches. If you want to keep it running, just use e.g. `while True:`.
Don't use too many of these though, as they can slow down Ultima.

    @ultima.background_task()
    async def say_hello_every_minute(self):
        while True:
            print("Hello World!")
            await asyncio.sleep(60)

## Models



## API Routes
