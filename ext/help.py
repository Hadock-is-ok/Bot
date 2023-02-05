import discord
from discord.ext import commands
from utils import views

class _Help(commands.HelpCommand):
    async def get_command_signature(self, command):
        return f"{command.qualified_name}"

    async def send_bot_help(self, mapping):
        embed = discord.Embed(
            title="Help",
        )
        embed.add_field(name="How to use commands", value=f"My normal prefix is `alone` or {self.context.me.mention}\n\nYou can also use your custom prefixes (that is, if you have any)\n`Alone prefix add [prefix]`\n\nAn example of how to use a command is `Alone ping`")
        embed.add_field(name="Extra information", value="You can also use `alone help [command|category]` to see more information about a specific command or category.")

        view = views.CogSelect(self.context)
        for name, cog in self.context.bot.cogs.items():
            if not self.filter_commands(cog.get_commands(), sorted=True):
                continue
            if not cog.get_commands():
                continue
            view.cog_select.append_option(discord.SelectOption(label=name))
        await self.context.reply(embed=embed, add_button_view=False, view=view)

    async def send_command_help(self, command):
        command_name = await self.get_command_signature(command)
        embed = discord.Embed(title=command_name, color=discord.Color.blurple())
        embed.add_field(name="Description of the command", value=command.help)
        alias = command.aliases
        if alias:
            embed.add_field(name="Aliases", value=", ".join(alias), inline=False)
        await self.context.reply(embed=embed)

    async def send_error_message(self, error: Exception):
        embed = discord.Embed(title="Error", description=error, color=0xF02E2E)
        await self.context.message.add_reaction(self.context.Emojis.x)
        await self.context.reply(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title=group, color=discord.Color.blurple())
        embed.add_field(
            name="Subcommands",
            value=", ".join([command.name for command in group.walk_commands()]),
        )
        await self.context.reply(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(
            title=cog.qualified_name,
            description=cog.description,
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Commands",
            value="\n".join([command.name for command in cog.get_commands()]),
        )
        await self.context.reply(embed=embed)

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._original_help_command = bot.help_command
        bot.help_command = _Help()
        bot.help_command_cog = self

async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
