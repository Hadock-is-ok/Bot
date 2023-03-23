from typing import Any, Optional

import discord
from discord.ext import commands
from typing_extensions import Self

from utils import AloneBot, AloneContext


class Moderation(commands.Cog):
    def __init__(self: Self, bot: AloneBot) -> None:
        self.bot: AloneBot = bot

    def cog_check(self: Self, ctx: commands.Context[Any]) -> bool:
        if not ctx.guild:
            return False
        return True

    @commands.command()
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.has_guild_permissions(ban_members=True)
    async def ban(
        self: Self,
        ctx: AloneContext,
        member: discord.Member,
        *,
        reason: str = "No reason provided.",
    ) -> discord.Message | None:
        if not member:
            return await ctx.reply(
                embed=discord.Embed(
                    title="An error occured",
                    description="You need to provide a member to ban.",
                )
            )

        if ctx.author.top_role <= member.top_role:  # type: ignore
            return await ctx.reply(
                embed=discord.Embed(
                    title="An error occured",
                    description="You do not have permissions to ban this person.",
                )
            )

        await member.ban(reason=reason)
        await ctx.reply(f"Banned {member}{f' for {reason}.' if reason else '.'}")

    @commands.command()
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self: Self, ctx: AloneContext, member_id: Optional[int]) -> discord.Message | None:
        "This command only works with IDs!"
        if not member_id:
            return await ctx.reply("You need to supply a User ID to unban!")

        user: discord.User = await self.bot.fetch_user(member_id)
        await ctx.guild.unban(user)  # type: ignore
        await ctx.message.add_reaction(ctx.Emojis.check)

    @commands.command()
    @commands.bot_has_guild_permissions(kick_members=True)
    @commands.has_guild_permissions(kick_members=True)
    async def kick(
        self: Self,
        ctx: AloneContext,
        member: discord.Member,
        *,
        reason: str = "No reason provided.",
    ) -> discord.Message | None:
        if not member:
            return await ctx.reply(
                embed=discord.Embed(
                    title="An error occured",
                    description="You need to provide a member to kick.",
                )
            )

        if ctx.author.top_role <= member.top_role:  # type: ignore
            return await ctx.reply(
                embed=discord.Embed(
                    title="An error occured",
                    description="You do not have permissions to kick this person.",
                )
            )

        await member.kick(reason=reason)
        await ctx.reply(f"Kicked {member}{f' for {reason}.' if reason else '.'}")

    @commands.command()
    @commands.bot_has_guild_permissions(manage_messages=True)
    @commands.has_guild_permissions(manage_messages=True)
    async def purge(self: Self, ctx: AloneContext, limit: int = 20) -> None:
        await ctx.message.delete()
        messages: Any = await ctx.channel.purge(limit=limit)  # type: ignore
        await ctx.send(f"{len(messages)} messages deleted.")


async def setup(bot: AloneBot) -> None:
    await bot.add_cog(Moderation(bot))
