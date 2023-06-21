from discord.ext import commands


class BlacklistedError(commands.CheckFailure):
    pass


class MaintenanceError(commands.CheckFailure):
    pass


class NoSubredditFound(commands.CheckFailure):
    pass


class NoValidDefinition(commands.CheckFailure):
    pass
