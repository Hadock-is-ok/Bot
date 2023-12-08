from revolt.ext import commands


class BlacklistedError(commands.CheckError):
    pass


class MaintenanceError(commands.CheckError):
    pass


class NoSubredditFound(commands.CheckError):
    pass


class NoValidDefinition(commands.CheckError):
    pass
