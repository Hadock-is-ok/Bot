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


class _CogSelect(discord.ui.Select['CogSelect']):
    def __init__(
        self,
        bot: AloneBot,
        cog_names: List[str],
        parent: CogSelect,
    ) -> None:

        options: List[discord.SelectOption] = [discord.SelectOption(label=cog_name) for cog_name in cog_names]
        options.append(discord.SelectOption(label="Close", description="Closes the help menu."))

        super().__init__(options=options, custom_id='select_cog', row=1)
        self.bot: AloneBot = bot
        self.parent: CogSelect = parent

    async def callback(self, interaction: discord.Interaction[AloneBot]) -> Any:
        await interaction.response.defer()

        selected_option = self.values[0]

        if selected_option == "Close":
            await interaction.delete_original_response()  # Note; I forget if this works

        cog = interaction.client.get_cog(selected_option)
        assert cog

        command_list = '\n'.join(command.qualified_name for command in cog.get_commands())
        embed = discord.Embed(title=cog.qualified_name, description=command_list)
        await interaction.edit_original_response(embed=embed)


class CogSelect(discord.ui.View):
    def __init__(self: Self, ctx: AloneContext, /, *, cog_names: List[str]) -> None:
        super().__init__(timeout=None)
        self.ctx: AloneContext = ctx
        self.add_item(_CogSelect(ctx.bot, cog_names, self))

    async def interaction_check(self: Self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(f"This is {self.ctx.author.display_name}'s command!", ephemeral=True)
            return False

        return True


class InviteView(discord.ui.View):
    def __init__(self: Self, ctx: AloneContext) -> None:
        super().__init__(timeout=None)

        user = ctx.bot.user
        if not user:
            raise RuntimeError("Cannot create instance of invite view without a bot user.")

        self.ctx: AloneContext = ctx
        self.add_item(discord.ui.Button(label="Invite", url=discord.utils.oauth_url(user.id)))
