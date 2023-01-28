from typing import List, Optional
import discord
from discord.ext import commands

from utils.bot import AloneBot

class Owner(commands.Cog):
    def __init__(self, bot: AloneBot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context):
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    async def maintenance(self, ctx: commands.Context, *, reason="No reason provided."):
        if not self.bot.maintenance:
            await ctx.message.add_reaction(ctx.Emojis.check)
            self.bot.maintenance = reason

            channel = self.bot.get_log_channel()
            return await channel.send(
                "I am going on maintenance break, all commands will not work during the downtime."
            )
        await ctx.reply("Maintenance mode is now off.")
        self.bot.maintenance = None

        channel = self.bot.get_log_channel()
        await channel.send(
            "The maintenance break is over. All commands should be up now."
        )

    @commands.group(invoke_without_command=True)
    async def blacklist(self, ctx: commands.Context):
        fmt: List[str] = []
        for user_id, reason in self.bot.blacklists.items():
            user = self.bot.get_user(user_id)
            if not user:
                continue

            fmt.append(f"{user} - {reason}")

        await ctx.reply(
            embed=discord.Embed(title="Blacklisted users", description="\n".join(fmt))
        )

    @blacklist.command()
    async def add(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ):
        self.bot.blacklists[member.id] = reason
        await self.bot.db.execute(
            "INSERT INTO blacklist (user_id, reason) VALUES ($1, $2)", member.id, reason
        )

        await ctx.message.add_reaction(ctx.Emojis.check)

    @blacklist.command()
    async def remove(self, ctx: commands.Context, *, member: discord.Member):
        try:
            self.bot.blacklists.pop(member.id)
            await self.bot.db.execute(
                "DELETE FROM blacklist WHERE user_id = $1", member.id
            )
        except KeyError:
            await ctx.message.add_reaction(ctx.Emojis.x)
            return await ctx.reply("That user isn't blacklisted!")

        await ctx.message.add_reaction(ctx.Emojis.check)

    @commands.command()
    async def disable(self, ctx: commands.Context, name: str):
        command = self.bot.get_command(name)
        if not command:
            await ctx.message.add_reaction(ctx.Emojis.x)
            return await ctx.reply("That command doesn't exist!")

        if not command.enabled:
            await ctx.message.add_reaction(ctx.Emojis.x)
            return await ctx.reply("This command is already disabled!")

        command.enabled = False
        await ctx.reply(f"Disabled {name}.")

    @commands.command()
    async def enable(self, ctx: commands.Context, name: str):
        command = self.bot.get_command(name)
        if not command:
            await ctx.message.add_reaction(ctx.Emojis.x)
            return await ctx.reply("That command doesn't exist!")

        if command.enabled:
            await ctx.message.add_reaction(ctx.Emojis.x)
            return await ctx.reply("This command is already enabled!")

        command.enabled = True
        await ctx.reply(f"Enabled {name}.")

    @commands.command()
    async def say(self, ctx: commands.Context, *, arg=None):
        await ctx.reply(arg)

    @commands.command(aliases=["d", "delete"])
    async def delmsg(self, ctx: commands.Context, message: Optional[discord.Message] = None):
        if not message:
            message = ctx.message.reference
            if not message:
                return await ctx.message.add_reaction(ctx.Emojis.slash)
    
        await message.delete()

    @commands.command()
    @commands.guild_only()
    async def nick(self, ctx: commands.Context, *, name: Optional[str] = None):
        await ctx.me.edit(nick=name)
        await ctx.message.add_reaction(ctx.Emojis.check)

    @commands.command(aliases=["shutdown", "fuckoff", "quit"])
    async def logout(self, ctx: commands.Context):
        await ctx.message.add_reaction(ctx.Emojis.check)

        await self.bot.session.close()
        await self.bot.db.close()

        await self.bot.close()

    @commands.command()
    async def load(self, ctx: commands.Context, cog: str):
        try:
            await self.bot.load_extension(cog)
            message = "Loaded!"
        except Exception as error:
            message = f"Error! {error}"
        await ctx.reply(message)

    @commands.command()
    async def unload(self, ctx: commands.Context, cog: str):
        try:
            await self.bot.unload_extension(cog)
            message = "Unloaded!"
        except Exception as error:
            message = f"Error! {error}"
        await ctx.reply(message)

    @commands.command()
    async def reload(self, ctx: commands.Context):
        cog_status = ""
        for extension in self.bot.INITIAL_EXTENSIONS:
            if extension == "jishaku":
                continue

            try:
                await self.bot.reload_extension(extension)
                cog_status += f"\U0001f504 {extension} Reloaded!\n\n"
            except commands.ExtensionNotLoaded:
                try:
                    await self.bot.load_extension(extension)
                    cog_status += f"\U00002705 {extension} Loaded!\n\n"
                except Exception as error:
                    cog_status += (
                        f"\U0000274c {extension} Errored!\n```py\n{error}```\n\n"
                    )
        await ctx.reply(embed=discord.Embed(title="Cogs", description=cog_status))
        await ctx.message.add_reaction(ctx.Emojis.check)


async def setup(bot: AloneBot):
    await bot.add_cog(Owner(bot))
