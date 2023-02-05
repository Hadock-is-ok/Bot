import discord
from discord.ext import commands

class DeleteView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx
    
    @discord.ui.button(emoji="\U0001f5d1", style=discord.ButtonStyle.danger, label="Delete", custom_id="delete")
    async def delete(self, interaction, button):
        if interaction.user.id == self.ctx.author.id:
            return await interaction.message.delete()
        await interaction.response.send_message(f"This command was ran by {self.ctx.author.name}, so you can't delete it!", ephemeral=True)

class JoinSupportView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.add_item(discord.ui.Button(label="Support", url=self.ctx.bot.support_server))

class CogSelect(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
    
    @discord.ui.select(custom_id="select_cog", placeholder="Choose a category", min_values=1, max_values=1, row=1)
    async def cog_select(self, interaction, select):
        cog = interaction.client.get_cog(select.values[0])
        command_list = ""
        for command in cog.get_commands():
            command_list += f"{command.name}\n"
        embed = discord.Embed(title=cog.qualified_name, description=command_list)
        await interaction.response.edit_message(embed=embed)