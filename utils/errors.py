from discord.ext import commands


class BlacklistedError(commands.CheckFailure):
    pass


class MaintenanceError(commands.CheckFailure):
    pass
