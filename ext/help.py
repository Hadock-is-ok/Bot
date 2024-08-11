from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Mapping, Optional, Tuple

import discord
from discord.ext import commands

from utils import AloneContext, views

if TYPE_CHECKING:
    from bot import AloneBot
    from utils import AloneContext


class _Help(commands.HelpCommand):
    if TYPE_CHECKING:
        context: AloneContext  # type: ignore

    async def send_bot_help(
        self,
        mapping: Mapping[Optional[commands.Cog], List[commands.Command[Any, ..., Any]]],
        /,
    ) -> None:
        embed: discord.Embed = discord.Embed(
            title="Help",
            color=self.context.author.color,
        )
        embed.add_field(
            name="How to use commands",
            value=f"My normal prefix is `alone` or {self.context.me.mention}\n\nYou can also use your custom prefixes (that is, if you have any)\n`Alone prefix add [prefix]`\n\nAn example of how to use a command is `Alone ping`",
        )
        embed.add_field(
            name="Extra information",
            value="You can also use `alone help [command|category]` to see more information about a specific command or category.",
        )

        view: views.CogSelect = views.CogSelect(self.context)
        for name, cog in self.context.bot.cogs.items():
            if not await self.filter_commands(cog.get_commands(), sort=True):
                continue

            if not cog.get_commands():
                continue

            view.cog_select.append_option(discord.SelectOption(label=name))
        view.cog_select.add_option(label="Close", description="Closes the help menu.")
        await self.context.reply(embed=embed, add_button_view=False, view=view)  # type: ignore

    async def send_command_help(self, command: commands.Command[Any, ..., Any], /) -> None:
        embed: discord.Embed = discord.Embed(title=command.qualified_name.capitalize(), description=self.get_command_signature(command), color=self.context.author.color)
        embed.set_footer(text="< > = Required | [ ] = Optional")
        if command.help:
            embed.add_field(name="Notes", value=command.help)
        alias: List[str] | Tuple[str] = command.aliases
        if alias:
            embed.add_field(name="Aliases", value=", ".join(alias), inline=False)

        await self.context.reply(embed=embed)

    async def send_error_message(self, error: str, /) -> None:
        embed: discord.Embed = discord.Embed(title="Error", description=error, color=0xF02E2E)
        assert isinstance(self.context, AloneContext)
        await self.context.message.add_reaction(self.context.emojis["cross"])
        await self.context.reply(embed=embed)

    async def send_group_help(self, group: commands.Group[Any, ..., Any], /) -> None:
        embed: discord.Embed = discord.Embed(title=group, color=self.context.author.color)
        embed.add_field(
            name="Subcommands",
            value=", ".join([command.name for command in group.walk_commands()]),
        )
        for command in group.walk_commands():
            if command.help:
                embed.add_field(name=command.name, value=command.help, inline=False)
        await self.context.reply(embed=embed)

    async def send_cog_help(self, cog: commands.Cog, /) -> None:
        embed: discord.Embed = discord.Embed(
            title=cog.qualified_name,
            description=cog.description,
            color=self.context.author.color,
        )
        embed.add_field(
            name="Commands",
            value="\n".join([command.name for command in cog.get_commands()]),
        )
        await self.context.reply(embed=embed)


class Help(commands.Cog):
    def __init__(self, bot: AloneBot) -> None:
        self.bot: AloneBot = bot
        self._original_help_command: commands.HelpCommand | None = bot.help_command
        help_command: _Help = _Help()
        help_command.cog = self
        bot.help_command = help_command


async def setup(bot: AloneBot) -> None:
    await bot.add_cog(Help(bot))
