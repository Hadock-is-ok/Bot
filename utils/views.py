import discord


class DeleteView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx

    @discord.ui.button(
        emoji="\U0001f5d1",
        style=discord.ButtonStyle.danger,
        label="Delete",
        custom_id="delete",
    )
    async def delete(self, interaction, _):
        if interaction.user.id == self.ctx.author.id:
            return await interaction.message.delete()
        await interaction.response.send_message(
            f"This command was ran by {self.ctx.author.name}, so you can't delete it!",
            ephemeral=True,
        )


class SupportView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.add_item(
            discord.ui.Button(label="Support", url=self.ctx.bot.support_server)
        )


class CogSelect(discord.ui.View):
    def __init__(self, ctx):
        self.ctx = ctx
        super().__init__(timeout=None)

    async def interaction_check(self, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                f"This is {self.ctx.author.display_name}'s command!", ephemeral=True
            )
            return False
        return True

    @discord.ui.select(
        custom_id="select_cog",
        placeholder="Choose a category",
        min_values=1,
        max_values=1,
        row=1,
    )
    async def cog_select(self, interaction, select):
        if select.values[0] == "Close":
            return await interaction.message.delete()
        cog = interaction.client.get_cog(select.values[0])
        command_list = ""
        for command in cog.get_commands():
            command_list += f"{command.name}\n"
        embed = discord.Embed(title=cog.qualified_name, description=command_list)
        await interaction.response.edit_message(embed=embed)


class InviteView(discord.ui.View):
    def __init__(self, ctx):
        self.ctx = ctx
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="Invite", url=discord.utils.oauth_url(self.ctx.bot.user.id)
            )
        )
