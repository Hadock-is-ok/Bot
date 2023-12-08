from __future__ import annotations

from typing import TYPE_CHECKING, Any

import revolt
from revolt.ext import commands

if TYPE_CHECKING:
    from client import AloneBot
    from utils.context import AloneContext


class DeleteView(revolt.ui.View):
    def __init__(self, ctx: AloneContext) -> None:
        super().__init__(timeout=None)
        self.ctx: AloneContext = ctx

    @revolt.ui.button(
        emoji="\U0001f5d1",
        style=revolt.ButtonStyle.danger,
        label="Delete",
        custom_id="delete",
    )
    async def delete(self, interaction: revolt.Interaction, _) -> None:
        if interaction.user.id == self.ctx.author.id:
            if not interaction.message:
                return

            return await interaction.message.delete()

        await interaction.response.send_message(
            f"This command was ran by {self.ctx.author.name}, so you can't delete it!",
            ephemeral=True,
        )


class SupportView(revolt.ui.View):
    def __init__(self, support_url: str) -> None:
        super().__init__(timeout=None)
        self.add_item(revolt.ui.Button(label="Support", url=support_url))


class GithubButton(revolt.ui.View):
    def __init__(self, ctx: AloneContext) -> None:
        super().__init__(timeout=None)
        self.ctx: AloneContext = ctx
        self.add_item(revolt.ui.Button(emoji="<:github:1019435755979935794>", label="GitHub", url=self.ctx.client.github_link))


class SourceButton(revolt.ui.View):
    def __init__(self, ctx: AloneContext, source_lines: tuple[list[str], int], file_name: str | None) -> None:
        super().__init__(timeout=None)
        self.ctx: AloneContext = ctx
        self.add_item(
            revolt.ui.Button(
                emoji="<:github:1019435755979935794>",
                label="Source",
                url=f"{self.ctx.client.github_link}/tree/master/{file_name}#L{source_lines[1]}-L{len(source_lines[0])+source_lines[1]}",
            )
        )


class CogSelect(revolt.ui.View):
    def __init__(self, ctx: AloneContext) -> None:
        self.ctx: AloneContext = ctx
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: revolt.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(f"This is {self.ctx.author.display_name}'s command!", ephemeral=True)
            return False

        return True

    @revolt.ui.select(
        custom_id="select_cog",
        placeholder="Choose a category",
        min_values=1,
        max_values=1,
        row=1,
    )
    async def cog_select(self, interaction: revolt.Interaction[AloneBot], select: revolt.ui.Select[Any]) -> None:
        if select.values[0] == "Close":
            if not interaction.message:
                return

            return await interaction.message.delete()

        cog: commands.Cog | None = interaction.client.get_cog(select.values[0])
        if not cog:
            return await interaction.followup.send(
                "Somehow, this cog doesn't exist. Please report this in my support server."
            )

        command_list: str = ""
        for command in cog.get_commands():
            command_list += f"{command.name}\n"

        embed: revolt.SendableEmbed = revolt.SendableEmbed(
            title=cog.qualified_name, description=command_list, colour="interaction.user.colour
        )
        await interaction.response.edit_message(embed=embed)


class InviteView(revolt.ui.View):
    def __init__(self, bot_id: int) -> None:
        super().__init__(timeout=None)

        self.add_item(revolt.ui.Button(label="Invite", url=revolt.utils.oauth_url(bot_id)))
