from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from . import AloneContext


class DeleteView(discord.ui.View):
    def __init__(self, ctx: AloneContext):
        super().__init__(timeout=None)
        self.ctx = ctx

    @discord.ui.button(
        emoji="\U0001f5d1",
        style=discord.ButtonStyle.danger,
        label="Delete",
        custom_id="delete",
    )
    async def delete(self, interaction: discord.Interaction, _):
        if interaction.user.id == self.ctx.author.id:
            if not interaction.message:
                return

            return await interaction.message.delete()

        await interaction.response.send_message(
            f"This command was ran by {self.ctx.author.name}, so you can't delete it!",
            ephemeral=True,
        )


class SupportView(discord.ui.View):
    def __init__(self, ctx: AloneContext):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.add_item(discord.ui.Button(label="Support", url=self.ctx.bot.support_server))


class CogSelect(discord.ui.View):
    def __init__(self, ctx: commands.Context[Any]) -> None:
        self.ctx = ctx
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(f"This is {self.ctx.author.display_name}'s command!", ephemeral=True)
            return False

        return True

    @discord.ui.select(  # type: ignore
        custom_id="select_cog",
        placeholder="Choose a category",
        min_values=1,
        max_values=1,
        row=1,
    )
    async def cog_select(self, interaction: discord.Interaction, select: discord.ui.Select[Any]):
        if select.values[0] == "Close":
            if not interaction.message:
                return

            return await interaction.message.delete()

        cog: commands.Cog = interaction.client.get_cog(select.values[0])  # type: ignore
        command_list = ""
        for command in cog.get_commands():
            command_list += f"{command.name}\n"

        embed = discord.Embed(title=cog.qualified_name, description=command_list)
        await interaction.response.edit_message(embed=embed)


class InviteView(discord.ui.View):
    def __init__(self, ctx: AloneContext):
        self.ctx = ctx
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Invite", url=discord.utils.oauth_url(self.ctx.bot.user.id)))
