from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Mapping, Optional, Tuple

import revolt
from revolt.ext import commands

from utils import AloneContext, views

if TYPE_CHECKING:
    from client import AloneBot
    from utils import AloneContext


class _Help(commands.HelpCommand):
    if TYPE_CHECKING:
        context: AloneContext

    def get_command_signature(self, command: commands.Command[Any, ..., Any], /) -> str:
        return f"{command.qualified_name}"

    async def send_bot_help(
        self, mapping: Mapping[Optional[commands.Cog], List[commands.Command[Any, ..., Any]]], /
    ) -> None:
        embed: revolt.SendableEmbed = revolt.SendableEmbed(
            title="Help",
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
        for name, cog in self.context.client.cogs.items():
            if not await self.filter_commands(cog.get_commands(), sort=True):
                continue

            if not cog.get_commands():
                continue

            view.cog_select.append_option(revolt.SelectOption(label=name))
        view.cog_select.add_option(label="Close", description="Closes the help menu.")
        await self.context.send(embed=embed, add_button_view=False, view=view)  # type: ignore

    async def send_command_help(self, command: commands.Command[Any, ..., Any], /) -> None:
        command_name: str = self.get_command_signature(command)
        embed: revolt.SendableEmbed = revolt.SendableEmbed(title=command_name)
        embed.add_field(name="Description of the command", value=command.help)
        alias: List[str] | Tuple[str] = command.aliases
        if alias:
            embed.add_field(name="Aliases", value=", ".join(alias), inline=False)

        await self.context.send(embed=embed)

    async def send_error_message(self, error: str, /) -> None:
        embed: revolt.SendableEmbed = revolt.SendableEmbed(title="Error", description=error, colour="0xF02E2E")
        assert isinstance(self.context, AloneContext)
        await self.context.message.add_reaction(self.context.emojis["cross"])
        await self.context.send(embed=embed)

    async def send_group_help(self, group: commands.Group[Any, ..., Any], /) -> None:
        embed: revolt.SendableEmbed = revolt.SendableEmbed(title=group)
        embed.add_field(
            name="Subcommands",
            value=", ".join([command.name for command in group.commands]),
        )
        await self.context.send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog, /) -> None:
        embed: revolt.SendableEmbed = revolt.SendableEmbed(
            title=cog.qualified_name,
            description=cog.description,
            colour="0x5865f2",
        )
        embed.add_field(
            name="Commands",
            value="\n".join([command.name for command in cog.commands]),
        )
        await self.context.send(embed=embed)


class Help(commands.Cog[AloneBot]):
    def __init__(self, client: AloneBot) -> None:
        self.client: AloneBot = client
        self._original_help_command: commands.HelpCommand | None = client.help_command
        help_command: _Help = _Help()
        help_command.cog = self
        client.help_command = help_command


async def setup(client: AloneBot) -> None:
    client.add_cog(Help(client))
