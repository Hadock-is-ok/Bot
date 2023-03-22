from typing import Any, List, Optional

import discord
from discord.ext import commands
from typing_extensions import Self

from utils import AloneBot, AloneContext


class Owner(commands.Cog):
    def __init__(self: Self, bot: AloneBot) -> None:
        self.bot: AloneBot = bot

    def cog_check(self: Self, ctx: commands.Context[Any]) -> bool:
        return ctx.author.id in self.bot.owner_ids

    @commands.command()
    async def maintenance(self: Self, ctx: AloneContext, *, reason: Optional[str]) -> None:
        if not self.bot.maintenance:
            await ctx.message.add_reaction(ctx.Emojis.check)
            self.bot.maintenance = reason or "no reason provided"

            channel: Any = self.bot.get_log_channel()
            return await channel.send("I am going on maintenance break, all commands will not work during the downtime.")
        await ctx.reply("Maintenance mode is now off.")
        self.bot.maintenance = None

        channel = self.bot.get_log_channel()
        await channel.send("The maintenance break is over. All commands should be up now.")

    @commands.group(invoke_without_command=True)
    async def blacklist(self: Self, ctx: AloneContext) -> None:
        fmt: List[str] = []
        for user_id, reason in self.bot.blacklisted_users.items():
            user: discord.User | None = self.bot.get_user(user_id)
            if not user:
                continue

            fmt.append(f"{user} - {reason}")

        await ctx.reply(embed=discord.Embed(title="Blacklisted users", description="\n".join(fmt)))

    @blacklist.command()
    async def add(
        self: Self,
        ctx: AloneContext,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ) -> None:
        self.bot.blacklisted_users[member.id] = reason
        await self.bot.db.execute("INSERT INTO blacklist (user_id, reason) VALUES ($1, $2)", member.id, reason)

        await ctx.message.add_reaction(ctx.Emojis.check)

    @blacklist.command()
    async def remove(self: Self, ctx: AloneContext, *, member: discord.Member) -> discord.Message | None:
        try:
            self.bot.blacklisted_users.pop(member.id)
            await self.bot.db.execute("DELETE FROM blacklist WHERE user_id = $1", member.id)
        except KeyError:
            await ctx.message.add_reaction(ctx.Emojis.x)
            return await ctx.reply("That user isn't blacklisted!")

        await ctx.message.add_reaction(ctx.Emojis.check)

    @commands.command()
    async def disable(self: Self, ctx: AloneContext, name: str) -> discord.Message | None:
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
    async def enable(self: Self, ctx: AloneContext, name: str) -> discord.Message | None:
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
    async def say(self: Self, ctx: AloneContext, *, text: Optional[str]) -> None:
        if not text:
            return await ctx.message.add_reaction(ctx.Emojis.slash)

        await ctx.reply(text)

    @commands.command(aliases=["d", "delete"])
    async def delmsg(self: Self, ctx: AloneContext, message: Optional[discord.Message]) -> None:  # type: ignore
        message: discord.Message | None = message or ctx.message.reference.resolved or None  # type: ignore
        if not message:
            return await ctx.message.add_reaction(ctx.Emojis.slash)

        await message.delete()

    @commands.command()
    @commands.guild_only()
    async def nick(self: Self, ctx: AloneContext, *, name: Optional[str] = None) -> None:
        await ctx.guild.me.edit(nick=name)  # type: ignore
        await ctx.message.add_reaction(ctx.Emojis.check)

    @commands.command(aliases=["shutdown", "fuckoff", "quit"])
    async def logout(self: Self, ctx: AloneContext) -> None:
        await ctx.message.add_reaction(ctx.Emojis.check)
        await self.bot.close()

    @commands.command()
    async def load(self: Self, ctx: AloneContext, cog: str) -> None:
        try:
            await self.bot.load_extension(cog)
            message: str = "Loaded!"
        except Exception as error:
            message = f"Error! {error}"
        await ctx.reply(message)

    @commands.command()
    async def unload(self: Self, ctx: AloneContext, cog: str) -> None:
        try:
            await self.bot.unload_extension(cog)
            message: str = "Unloaded!"
        except Exception as error:
            message = f"Error! {error}"
        await ctx.reply(message)

    @commands.command()
    async def reload(self: Self, ctx: AloneContext) -> None:
        cog_status: str = ""
        for extension in self.bot.INITAL_EXTENSIONS:
            await self.bot.reload_extension(extension)
            cog_status += f"\U0001f504 {extension} Reloaded!\n\n"

        await ctx.reply(embed=discord.Embed(title="Reload", description=cog_status))
        await ctx.message.add_reaction(ctx.Emojis.check)


async def setup(bot: AloneBot) -> None:
    await bot.add_cog(Owner(bot))
