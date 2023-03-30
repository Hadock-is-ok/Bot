from __future__ import annotations

from typing import TYPE_CHECKING, Any, List

import discord

if TYPE_CHECKING:
    from . import AloneContext
    from bot import AloneBot

from typing_extensions import Self


class DeleteView(discord.ui.View):
    def __init__(self: Self, ctx: AloneContext) -> None:
        super().__init__(timeout=None)
        self.ctx: AloneContext = ctx

    @discord.ui.button(
        emoji="\U0001f5d1",
        style=discord.ButtonStyle.danger,
        label="Delete",
        custom_id="delete",
    )
    async def delete(self: Self, interaction: discord.Interaction, _) -> None:
        if interaction.user.id == self.ctx.author.id:
            if not interaction.message:
                return

            return await interaction.message.delete()

        await interaction.response.send_message(
            f"This command was ran by {self.ctx.author.name}, so you can't delete it!",
            ephemeral=True,
        )


class SupportView(discord.ui.View):
    def __init__(self: Self, ctx: AloneContext) -> None:
        super().__init__(timeout=None)
        self.ctx: AloneContext = ctx
        self.add_item(discord.ui.Button(label="Support", url=self.ctx.bot.support_server))


class CogSelect(discord.ui.View):
    def __init__(self: Self, ctx: AloneContext) -> None:
        self.ctx: AloneContext = ctx
        super().__init__(timeout=None)

    async def interaction_check(self: Self, interaction: discord.Interaction) -> bool:
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
    async def cog_select(self: Self, interaction: discord.Interaction, select: discord.ui.Select[Any]) -> None:
        if select.values[0] == "Close":
            if not interaction.message:
                return

            return await interaction.message.delete()

        cog: commands.Cog = interaction.client.get_cog(select.values[0])  # type: ignore
        command_list: str = ""
        for command in cog.get_commands():
            command_list += f"{command.name}\n"

        embed: discord.Embed = discord.Embed(title=cog.qualified_name, description=command_list)
        await interaction.response.edit_message(embed=embed)

class InviteView(discord.ui.View):
    def __init__(self: Self, ctx: AloneContext) -> None:
        super().__init__(timeout=None)

        user = ctx.bot.user
        if not user:
            raise RuntimeError("Cannot create instance of invite view without a bot user.")

        self.ctx: AloneContext = ctx
        self.add_item(discord.ui.Button(label="Invite", url=discord.utils.oauth_url(user.id)))
