import discord
from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            return False
        return True


    @commands.command()
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.has_guild_permissions(ban_members=True)
    async def ban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided.",
    ):
        if not member:
            return await ctx.reply(
                embed=discord.Embed(
                    title="An error occured",
                    description="You need to provide a member to ban.",
                )
            )
        if ctx.author.top_role <= member.top_role:
            return await ctx.reply(embed=discord.Embed(title="An error occured", description="You do not have permissions to ban this person."))
        await member.ban(reason=reason)
        await ctx.reply(f"Banned {member}{f' for {reason}.' if reason else '.'}")
    
    @commands.command()
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, member_id: int = None):
        "This command only works with IDs!"
        if not member_id:
            return await ctx.reply("You need to supply a User ID to unban!")
        user = await self.bot.fetch_user(member_id)
        await ctx.guild.unban(user)
        await ctx.message.add_reaction(ctx.Emojis.check)

    @commands.command()
    @commands.bot_has_guild_permissions(kick_members=True)
    @commands.has_guild_permissions(kick_members=True)
    async def kick(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided.",
    ):
        if not member:
            return await ctx.reply(
                embed=discord.Embed(
                    title="An error occured",
                    description="You need to provide a member to kick.",
                )
            )
        if ctx.author.top_role <= member.top_role:
            return await ctx.reply(embed=discord.Embed(title="An error occured", description="You do not have permissions to kick this person."))
        await member.kick(reason=reason)
        await ctx.reply(f"Kicked {member}{f' for {reason}.' if reason else '.'}")

    @commands.command()
    @commands.bot_has_guild_permissions(manage_messages=True)
    @commands.has_guild_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, limit: int = 20):
        await ctx.message.delete()
        messages = await ctx.channel.purge(limit=limit)
        await ctx.send(f"{len(messages)} messages deleted.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
