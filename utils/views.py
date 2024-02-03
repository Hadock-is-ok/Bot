from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from bot import AloneBot
    from utils.context import AloneContext


class DeleteView(discord.ui.View):
    def __init__(self, author_id: int) -> None:
        super().__init__(timeout=None)
        self.author_id: int = author_id

    @discord.ui.button(
        emoji="\U0001f5d1",
        style=discord.ButtonStyle.danger,
        label="Delete",
        custom_id="delete",
    )
    async def delete(self, interaction: discord.Interaction, _) -> None:
        if interaction.user.id == self.author_id:
            if not interaction.message:
                return

            return await interaction.message.delete()

        await interaction.response.send_message(
            f"This command was ran by <@{self.author_id}>, so you can't delete it!",
            ephemeral=True,
        )


class SupportView(discord.ui.View):
    def __init__(self, support_url: str) -> None:
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Support", url=f"discord://-/invite/{support_url}"))


class GithubButton(discord.ui.View):
    def __init__(self, ctx: AloneContext) -> None:
        super().__init__(timeout=None)
        self.ctx: AloneContext = ctx
        self.add_item(
            discord.ui.Button(
                emoji="<:github:1019435755979935794>",
                label="GitHub",
                url=self.ctx.bot.github_link,
            )
        )


class SourceButton(discord.ui.View):
    def __init__(
        self,
        ctx: AloneContext,
        source_lines: tuple[list[str], int],
        file_name: str | None,
    ) -> None:
        super().__init__(timeout=None)
        self.ctx: AloneContext = ctx
        self.add_item(
            discord.ui.Button(
                emoji="<:github:1019435755979935794>",
                label="Source",
                url=f"{self.ctx.bot.github_link}/tree/master/{file_name}#L{source_lines[1]}-L{len(source_lines[0])+source_lines[1]}",
            )
        )


class CogSelect(discord.ui.View):
    def __init__(self, ctx: AloneContext) -> None:
        self.ctx: AloneContext = ctx
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(f"This is {self.ctx.author.display_name}'s command!", ephemeral=True)
            return False

        return True

    @discord.ui.select(
        custom_id="select_cog",
        placeholder="Choose a category",
        min_values=1,
        max_values=1,
        row=1,
    )
    async def cog_select(self, interaction: discord.Interaction[AloneBot], select: discord.ui.Select[Any]) -> None:
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

        embed: discord.Embed = discord.Embed(
            title=cog.qualified_name,
            description=command_list,
            color=interaction.user.color,
        )
        await interaction.response.edit_message(embed=embed)


class InviteView(discord.ui.View):
    def __init__(self, bot_id: int) -> None:
        super().__init__(timeout=None)

        self.add_item(discord.ui.Button(label="Invite", url=discord.utils.oauth_url(bot_id)))
