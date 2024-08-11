from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from bot import AloneBot
    from utils import AloneContext

message_param: discord.Message = commands.parameter(default=lambda ctx: ctx.message)  # type: ignore


class Owner(commands.Cog):
    def __init__(self, bot: AloneBot) -> None:
        self.bot: AloneBot = bot

    def cog_check(self, ctx: AloneContext) -> bool:
        return ctx.author.id in self.bot.owner_ids

    @commands.command()
    async def maintenance(self, ctx: AloneContext, *, reason: str = "no reason provided") -> None:
        if not self.bot.maintenance:
            self.bot.maintenance = reason
        else:
            self.bot.maintenance = None

        await ctx.message.add_reaction(ctx.emojis["tick"])

    @commands.group(invoke_without_command=True)
    async def blacklist(self, ctx: AloneContext) -> None:
        fmt: list[str] = []
        for user_id, reason in self.bot.blacklisted_users.items():
            user: discord.User | None = self.bot.get_user(user_id)
            if not user:
                continue

            fmt.append(f"{user} - {reason}")

        await ctx.reply(embed=discord.Embed(title="Blacklisted users", description="\n".join(fmt)))

    @blacklist.command()
    async def add(
        self,
        ctx: AloneContext,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ) -> None:
        self.bot.blacklisted_users[member.id] = reason
        await self.bot.db.execute("INSERT INTO blacklist (user_id, reason) VALUES ($1, $2)", member.id, reason)
        await ctx.message.add_reaction(ctx.emojis["tick"])

    @blacklist.command()
    async def remove(self, ctx: AloneContext, *, member: discord.Member) -> discord.Message | None:
        try:
            self.bot.blacklisted_users.pop(member.id)
            await self.bot.db.execute("DELETE FROM blacklist WHERE user_id = $1", member.id)
        except KeyError:
            await ctx.message.add_reaction(ctx.emojis["cross"])
            return await ctx.reply("That user isn't blacklisted!")

        await ctx.message.add_reaction(ctx.emojis["tick"])

    @commands.command()
    async def disable(self, ctx: AloneContext, name: str) -> discord.Message | None:
        command = self.bot.get_command(name)
        if not command:
            await ctx.message.add_reaction(ctx.emojis["cross"])
            return await ctx.reply("That command doesn't exist!")

        if not command.enabled:
            await ctx.message.add_reaction(ctx.emojis["cross"])
            return await ctx.reply("This command is already disabled!")

        command.enabled = False
        await ctx.reply(f"Disabled {name}.")

    @commands.command()
    async def enable(self, ctx: AloneContext, name: str) -> discord.Message | None:
        command = self.bot.get_command(name)
        if not command:
            await ctx.message.add_reaction(ctx.emojis["cross"])
            return await ctx.reply("That command doesn't exist!")

        if command.enabled:
            await ctx.message.add_reaction(ctx.emojis["cross"])
            return await ctx.reply("This command is already enabled!")

        command.enabled = True
        await ctx.reply(f"Enabled {name}.")

    @commands.command()
    async def say(
        self,
        ctx: AloneContext,
        *,
        text: str = "hi im stupid and i put nothing here",
    ) -> None:
        await ctx.reply(text)

    @commands.command(aliases=["d", "delete"])
    async def delmsg(self, ctx: AloneContext, _message: Optional[discord.Message] = message_param) -> None:
        message: discord.Message | None = _message or ctx.message.reference.resolved  # type: ignore
        if not message:
            return await ctx.message.add_reaction(ctx.emojis["slash"])

        await message.delete()

    @commands.command()
    async def nick(self, ctx: AloneContext, *, name: Optional[str]) -> None:
        if not ctx.guild:
            return

        await ctx.guild.me.edit(nick=name)
        await ctx.message.add_reaction(ctx.emojis["tick"])

    @commands.command(aliases=["shutdown", "fuckoff", "quit"])
    async def logout(self, ctx: AloneContext) -> None:
        await ctx.message.add_reaction(ctx.emojis["tick"])
        await self.bot.close()

    @commands.command()
    async def load(self, ctx: AloneContext, cog: str) -> None:
        try:
            await self.bot.load_extension(cog)
            message: str = "Loaded!"
        except Exception as error:
            message = f"Error! {error}"
        await ctx.reply(message)

    @commands.command()
    async def unload(self, ctx: AloneContext, cog: str) -> None:
        try:
            await self.bot.unload_extension(cog)
            message: str = "Unloaded!"
        except Exception as error:
            message = f"Error! {error}"
        await ctx.reply(message)

    @commands.command()
    async def reload(self, ctx: AloneContext, *exts: str) -> None:
        cogs: list[str] = []
        if exts:
            cogs = list(exts)
        else:
            cogs = self.bot.INITIAL_EXTENSIONS.copy()

        cog_status: str = ""
        for cog in cogs:
            cog_name = cog.split(".")[-1].capitalize()
            try:
                await self.bot.reload_extension(cog)
            except commands.ExtensionNotLoaded:
                cog_status += f"{ctx.emojis['cross']} {cog_name} not loaded!\n\n"
                continue
            cog_status += f"\U0001f504 {cog_name} Reloaded!\n\n"

        await ctx.reply(embed=discord.Embed(title="Reload", description=cog_status))
        await ctx.message.add_reaction(ctx.emojis["tick"])


async def setup(bot: AloneBot) -> None:
    await bot.add_cog(Owner(bot))
