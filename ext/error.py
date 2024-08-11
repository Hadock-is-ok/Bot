from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from utils import BlacklistedError, MaintenanceError, NoSubredditFound

if TYPE_CHECKING:
    from bot import AloneBot
    from utils import AloneContext


class Error(commands.Cog):
    def __init__(self, bot: AloneBot) -> None:
        self.bot: AloneBot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: AloneContext, error: Exception) -> None:
        "The error handler for the bot."
        assert ctx.command # How would this ever be None? It's a COMMAND error handler for a reason.
        error = getattr(error, "original", error)
        embed: discord.Embed = discord.Embed()
        embed.color = discord.Color.red()
        embed.set_author(name=f"{ctx.author.name}", icon_url=ctx.author.display_avatar)
        if isinstance(error, commands.CommandNotFound):
            return

        await ctx.message.add_reaction(ctx.emojis["cross"])
        if isinstance(error, commands.CommandOnCooldown):
            embed.title = "Cooldown"
            embed.description = f"Please wait {error.retry_after:.2f} seconds before using this command again."

        elif isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
            embed.title = "Wrong Arguments"
            embed.description = f"Please use the correct syntax: `{ctx.command.qualified_name} {' '.join(ctx.command.params.keys())}`."

        elif isinstance(error, commands.MissingPermissions):
            embed.title = "Missing Permissions"
            embed.description = f"You do not have the required permissions ({''.join([perm.replace('_', ' ').title() for perm in error.missing_permissions])}) to run this command."

        elif isinstance(error, commands.BotMissingPermissions):
            embed.title = "Bot Missing Permissions"
            embed.description = f"I do not have the required permissions ({''.join([perm.replace('_', ' ').title() for perm in error.missing_permissions])}) to run the actions for this command."

        elif isinstance(error, BlacklistedError):
            embed.title = "Blacklisted"
            embed.description = f"You have been blacklisted from using the bot for {self.bot.blacklisted_users[ctx.author.id]}."

        elif isinstance(error, MaintenanceError):
            embed.title = "Maintenance"
            embed.description = f"The bot is currently in maintenance mode. Please hold."

        elif isinstance(error, NoSubredditFound):
            embed.title = "No Subreddit Found"
            embed.description = "I couldn't find any subreddit with that name."

        else:
            channel = self.bot.get_log_webhook()
            self.bot.logger.error("An error occurred", exc_info=error)
            embed.title = f"Ignoring exception in {ctx.command}"
            embed.description = f"```py\n{error}```\n"
            embed.add_field(
                name="Information",
                value=f"Error Name: `{error.__class__.__name__}`\nMessage: `{ctx.message.content}`\nUser: {ctx.author.mention}",
            )

            await channel.send(
                f"This error came from {ctx.command} in {ctx.guild if ctx.guild else 'DMs'}.",
                embed=embed,
            )

            embed.title = "Error"
            embed.description = "Sorry! An error ocurred and has been reported to the developers. Don't worry, this isn't your fault."
        await ctx.reply(embed=embed)


async def setup(bot: AloneBot) -> None:
    await bot.add_cog(Error(bot))
