from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import revolt
from revolt.ext import commands

if TYPE_CHECKING:
    from client import AloneBot
    from utils import AloneContext


class Moderation(commands.Cog[AloneBot]):
    def __init__(self, client: AloneBot) -> None:
        self.client: AloneBot = client

    def cog_check(self, ctx: AloneContext) -> bool:
        if not ctx.server:
            return False
        return True

    @commands.command()
    @commands.bot_has_server_permissions(ban_members=True)
    @commands.has_server_permissions(ban_members=True)
    async def ban(
        self,
        ctx: AloneContext,
        member: revolt.Member,
        *,
        reason: str = "No reason provided.",
    ) -> revolt.Message | None:
        if isinstance(ctx.author, revolt.User):
            return

        if not member:
            return await ctx.send(
                embed=revolt.SendableEmbed(
                    title="An error occured",
                    description="You need to provide a member to ban.",
                )
            )

        if ctx.author.top_role <= member.top_role:
            return await ctx.send(
                embed=revolt.SendableEmbed(
                    title="An error occured",
                    description="You do not have permissions to ban this person.",
                )
            )

        await member.ban(reason=reason)
        await ctx.send(f"Banned {member}{f' for {reason}.' if reason else '.'}")

    @commands.command()
    @commands.bot_has_server_permissions(ban_members=True)
    @commands.has_server_permissions(ban_members=True)
    async def unban(self, ctx: AloneContext, member_id: Optional[int]) -> revolt.Message | None:
        "This command only works with IDs!"
        if not member_id:
            return await ctx.send("You need to supply a User ID to unban!")

        assert ctx.server
        user: revolt.User = await self.client.fetch_user(member_id)
        await ctx.server.unban(user)
        await ctx.message.add_reaction(ctx.emojis["tick"])

    @commands.command()
    @commands.bot_has_server_permissions(kick_members=True)
    @commands.has_server_permissions(kick_members=True)
    async def kick(
        self,
        ctx: AloneContext,
        member: revolt.Member,
        *,
        reason: str = "No reason provided.",
    ) -> revolt.Message | None:
        if isinstance(ctx.author, revolt.User):
            return

        if not member:
            return await ctx.send(
                embed=revolt.SendableEmbed(
                    title="An error occured",
                    description="You need to provide a member to kick.",
                )
            )

        if ctx.author.top_role <= member.top_role:
            return await ctx.send(
                embed=revolt.SendableEmbed(
                    title="An error occured",
                    description="You do not have permissions to kick this person.",
                )
            )

        await member.kick(reason=reason)
        await ctx.send(f"Kicked {member}{f' for {reason}.' if reason else '.'}")

    @commands.command()
    @commands.bot_has_server_permissions(manage_messages=True)
    @commands.has_server_permissions(manage_messages=True)
    async def purge(self, ctx: AloneContext, limit: int = 20) -> None:
        await ctx.message.delete()
        messages: Any = await ctx.channel.purge(limit=limit)  # type: ignore
        await ctx.send(f"{len(messages)} messages deleted.")


async def setup(client: AloneBot) -> None:
    client.add_cog(Moderation(client))
