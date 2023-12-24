from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from utils import BlacklistedError, MaintenanceError, NoSubredditFound

if TYPE_CHECKING:
    from bot import AloneBot
    from utils import AloneContext

errors: dict[type[Exception], str] = {
    BlacklistedError: "You have been blacklisted for {self.bot.blacklisted_users.get(ctx.author.id)}. you may not appeal this blacklist. There still exists a chance I'll unban you, but it's not likely.",
    MaintenanceError: "The bot is currently in maintenance mode for {self.bot.maintenance}, please wait. If you have any issues, you can join my support server for help.",
    NoSubredditFound: "I couldn't find a subreddit by that name, maybe you should double check the name?",
    commands.CheckFailure: "You do not have permission to run this command!",
    commands.CommandOnCooldown: "You are on cooldown. Try again in {error.retry_after:.2f}s",
}


class Error(commands.Cog):
    def __init__(self, bot: AloneBot) -> None:
        self.bot: AloneBot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: AloneContext, error: Exception) -> None:
        "The error handler for the bot."
        if isinstance(error, commands.CommandNotFound):
            return

        await ctx.message.add_reaction(self.bot._emojis["cross"])

        if reason := errors.get(type(error)):
            await ctx.reply(
                embed=discord.Embed(
                    title="Error",
                    description=reason.format(self=self, ctx=ctx, error=error),
                    color=0xF02E2E,
                )
            )

        else:
            self.bot.logger.error("An error occurred", exc_info=error)
            guild: str = f"Guild ID: {ctx.guild.id}\n" if ctx.guild else ""
            embed: discord.Embed = discord.Embed(
                title=f"Ignoring exception in {ctx.command}:",
                description=f"```py\n{error}```\nThe developers have receieved this error and will fix it.",
                color=0xF02E2E,
            )
            embed.set_author(name=f"{ctx.author.name}", icon_url=ctx.author.display_avatar)
            embed.add_field(
                name="Information",
                value=f"Error Name: {error.__class__.__name__}\nMessage: {ctx.message.content}\n{guild}Channel ID: {ctx.channel.id}",
            )

            channel: discord.Webhook = self.bot.get_log_webhook()
            await channel.send(
                f"This error came from {ctx.author} using {ctx.command} in {ctx.guild}.",
                embed=embed,
            )
            await ctx.reply(embed=embed)


async def setup(bot: AloneBot) -> None:
    await bot.add_cog(Error(bot))
