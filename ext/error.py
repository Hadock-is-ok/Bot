from __future__ import annotations

from typing import TYPE_CHECKING

import revolt
from revolt.ext import commands

from utils import BlacklistedError, MaintenanceError, NoSubredditFound

if TYPE_CHECKING:
    from client import AloneBot
    from utils import AloneContext

errors: dict[type[Exception], str] = {
    BlacklistedError: "You have been blacklisted for {self.client.blacklisted_users.get(ctx.author.id)}. you may not appeal this blacklist. There still exists a chance I'll unban you, but it's not likely.",
    MaintenanceError: "The client is currently in maintenance mode for {self.client.maintenance}, please wait. If you have any issues, you can join my support server for help.",
    NoSubredditFound: "I couldn't find a subreddit by that name, maybe you should double check the name?",
    commands.CheckError: "You do not have permission to run this command!",
    #commands.CommandOnCooldown: "You are on cooldown. Try again in {error.retry_after:.2f}s",
}


class Error(commands.Cog[AloneBot]):
    def __init__(self, client: AloneBot) -> None:
        self.client: AloneBot = client

    #@client
    async def on_command_error(self, ctx: AloneContext, error: Exception) -> None:
        "The error handler for the client."
        if isinstance(error, commands.CommandNotFound):
            return

        #await ctx.message.add_reaction(self.client._emojis["cross"])

        if reason := errors.get(type(error)):
            await ctx.send(
                embed=revolt.SendableEmbed(
                    title="Error",
                    description=reason.format(self=self, ctx=ctx, error=error),
                    colour="0xF02E2E",
                )
            )

        else:
            self.client.logger.error("An error occurred", exc_info=error)
            server: str = f"server ID: {ctx.server.id}\n" if ctx.server else ""
            embed: revolt.SendableEmbed = revolt.SendableEmbed(
                title=f"Ignoring exception in {ctx.command}:",
                description=f"```py\n{error}```\nThe developers have receieved this error and will fix it.\nError Name: {error.__name__}\nMessage: {ctx.message.content}\n{server}Channel ID: {ctx.channel.id}", # type: ignore
                colour="0xF02E2E",
            )
            #embed.set_author(name=f"{ctx.author.name}", icon_url=ctx.author.display_avatar)

            channel: revolt.Channel = await self.client.get_log_channel()
            await channel.( # type: ignore
                f"This error came from {ctx.author} using {ctx.command} in {ctx.server}.",
                embed=embed,
            )
            await ctx.send(embed=embed)


async def setup(client: AloneBot) -> None:
    client.add_cog(Error(client))
