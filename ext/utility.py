from datetime import datetime
from inspect import getsource
from random import choice
from time import perf_counter
from typing import Optional, Union

import discord
from discord.ext import commands

from utils import AloneBot, AloneContext, InviteView, SupportView, Todo as Todo_class


class Utility(commands.Cog):
    def __init__(self, bot: AloneBot):
        self.bot = bot

    @commands.command()
    async def afk(self, ctx: AloneContext, *, reason: Optional[str] = "no reason") -> None:
        assert reason
        await self.bot.db.execute("INSERT INTO afk VALUES ($1, $2)", ctx.author.id, reason)
        self.bot.afk_users[ctx.author.id] = reason

        if reason != "no reason":
            fmt = f" for {reason}."
        else:
            fmt = "!"

        await ctx.message.add_reaction(ctx.Emojis.check)
        await ctx.reply(f"**AFK**\nYou are now afk{fmt}")

    @commands.command(aliases=["av", "pfp"])
    async def avatar(self, ctx: AloneContext, member: Optional[discord.Member]) -> None:
        member = member or ctx.author  # type: ignore
        assert member
        embed = discord.Embed(title=f"{member.display_name}'s avatar")
        embed.set_image(url=member.avatar.url)  # type: ignore

        await ctx.reply(embed=embed)

    @commands.command()
    async def choose(self, ctx: AloneContext, choices: commands.Greedy[Union[str, int]]) -> None:
        await ctx.reply(str(choice(choices)))

    @commands.command()
    async def cleanup(self, ctx: AloneContext, limit: Optional[int] = 50) -> None:
        bulk = ctx.channel.permissions_for(ctx.me).manage_messages  # type: ignore

        def is_bot(message: discord.Message) -> bool:
            return message.author == ctx.me

        await ctx.channel.purge(bulk=bulk, check=is_bot, limit=limit)  # type: ignore
        await ctx.message.add_reaction(ctx.Emojis.check)

    @commands.command()
    async def invite(self, ctx: AloneContext) -> None:
        assert self.bot.user
        link = discord.utils.oauth_url(self.bot.user.id)
        embed = discord.Embed(title="Thank you for supporting me!", description=f"[Invite Me!]({link})")
        await ctx.reply(embed=embed, view=InviteView(ctx))

    @commands.command()
    async def ping(self, ctx: AloneContext) -> None:
        websocket_ping = self.bot.latency * 1000

        start = perf_counter()
        message = await ctx.reply("Pong!")
        end = perf_counter()
        typing_ping = end - start

        start = perf_counter()
        await self.bot.db.execute("SELECT 1")
        end = perf_counter()
        database_ping = end - start

        embed = discord.Embed(title="Ping", color=discord.Color.random())
        embed.add_field(
            name="<a:typing:1041021440352337991> | Typing",
            value=await ctx.create_codeblock(f"{typing_ping:.2f}ms"),
        )
        embed.add_field(
            name="<a:loading:1041021510590152834> | Websocket",
            value=await ctx.create_codeblock(f"{websocket_ping:.2f}ms"),
        )
        embed.add_field(
            name="<:PostgreSQL:1019435339124850708> | Database",
            value=await ctx.create_codeblock(f"{database_ping:.2f}ms"),
        )

        await message.edit(content=None, embed=embed)

    @commands.group(invoke_without_command=True)
    async def prefix(self, ctx: AloneContext) -> None:
        prefix_list = "\n".join(await self.bot.get_prefix(ctx.message))
        embed = discord.Embed(title="Prefixes you can use", description=prefix_list)
        await ctx.reply(embed=embed)

    @prefix.command(name="add")
    async def prefix_add(self, ctx: AloneContext, *, prefix: Optional[str] = ""):
        assert prefix
        if len(prefix) > 5:
            return await ctx.reply("You can't have a prefix that's longer than 5 characters, sorry!")

        prefix_list = self.bot.user_prefixes.get(ctx.author.id, [])
        prefix_list.append(prefix)

        await self.bot.db.execute("INSERT INTO prefix VALUES ($1, $2)", ctx.author.id, prefix)
        await ctx.message.add_reaction(ctx.Emojis.check)

    @prefix.command(name="guild")
    async def prefix_guild(self, ctx: AloneContext, *, prefix: Optional[str]):
        assert ctx.guild
        if not prefix or "remove" in prefix.lower():
            guild_config = self.bot.guild_configs.get(ctx.guild.id, None)
            if not guild_config or not guild_config.get("prefix", None):
                return await ctx.reply("There is no guild prefix to remove!")

            await self.bot.db.execute("UPDATE guilds SET prefix = NULL WHERE guild_id = $1", ctx.guild.id)
            await ctx.message.add_reaction(ctx.Emojis.check)
            return await ctx.reply("The prefix for this guild has been removed.")

        if len(prefix) > 5:
            return await ctx.reply("You can't have a prefix that's longer than 5 characters, sorry!")

        self.bot.guild_configs[ctx.guild.id]["prefix"] = prefix
        await self.bot.db.execute(
            "INSERT INTO guilds VALUES ($1, $2) ON CONFLICT DO UPDATE guilds SET prefix = $2 WHERE guild_id = $1",
            ctx.guild.id,
            prefix,
        )
        await ctx.message.add_reaction(ctx.Emojis.check)
        await ctx.reply(f"The prefix for this guild is now `{prefix}`")

    @prefix.command(name="remove")
    async def prefix_remove(self, ctx: AloneContext, *, prefix: Optional[str]):
        user_prefixes = self.bot.user_prefixes.get(ctx.author.id, [])
        if not user_prefixes:
            return await ctx.reply("You don't have custom prefixes setup!")

        if not prefix:
            self.bot.user_prefixes.pop(ctx.author.id)
            await self.bot.db.execute("DELETE FROM prefix WHERE user_id = $1", ctx.author.id)
            return await ctx.message.add_reaction(ctx.Emojis.check)

        try:
            user_prefixes.remove(prefix)
            await self.bot.db.execute(
                "DELETE FROM prefix WHERE user_id = $1 AND prefix = $2",
                ctx.author.id,
                prefix,
            )
            await ctx.message.add_reaction(ctx.Emojis.check)
        except KeyError:
            await ctx.message.add_reaction(ctx.Emojis.x)
            await ctx.reply("That's not one of your prefixes!")

    @commands.command()
    async def quote(self, ctx: AloneContext, message: Optional[discord.Message]):
        message = message or ctx.message.reference.resolved  # type: ignore
        if not message:
            return await ctx.reply("You need to give me a message to quote!")

        embed = discord.Embed(
            title=f"{message.author} sent:",
            description=f"> {message.content}\n - {message.author.mention}",
        )
        await ctx.reply(embed=embed)

    @commands.command(aliases=["server_info", "server info", "si", "guildinfo"])
    @commands.guild_only()
    async def serverinfo(self, ctx: AloneContext, guild: Optional[discord.Guild]) -> None:
        guild = guild or ctx.guild
        assert guild
        assert guild.icon
        bots = sum(member.bot for member in guild.members)
        embed = discord.Embed(
            title=f"Server Info for {guild.name}",
            description=f"Owner: {guild.owner}\nID: {guild.id}"
            f"Members: {guild.member_count}\nBots: {bots}\nNitro Level: {guild.premium_tier}",
        )
        embed.set_thumbnail(url=guild.icon.url)
        await ctx.reply(embed=embed)

    @commands.command()
    async def source(self, ctx: AloneContext, *, command_name: Optional[str]):
        if not command_name:
            return await ctx.reply("https://github.com/Alone-Discord-Bot/Bot")

        command = self.bot.get_command(command_name)
        if not command:
            return await ctx.reply("That command doesn't exist!")

        source = getsource(command.callback)
        embed = discord.Embed(
            title=f"Source for {command.name}",
            description=await ctx.create_codeblock(source),
        )
        await ctx.reply(embed=embed)

    @commands.command()
    async def support(self, ctx: AloneContext) -> None:
        embed = discord.Embed(
            title="Support",
            description="Join my [support server]({self.bot.support_server})!",
        )
        await ctx.reply(embed=embed, view=SupportView(ctx))

    @commands.group(invoke_without_command=True)
    async def todo(self, ctx: AloneContext):
        user_todo = self.bot.todos.get(ctx.author.id)
        if not user_todo:
            return await ctx.reply("You don't have a to-do list!")

        todo_list = ""
        for number, todo in enumerate(user_todo, start=1):
            todo_list = "".join(f"**__[{number}]({todo.jump_url})__**: **{todo.content}**\n")

        embed = discord.Embed(title="Todo", description=todo_list)
        await ctx.reply(embed=embed)

    @todo.command(name="add")
    async def todo_add(self, ctx: AloneContext, *, text: Optional[str]) -> None:
        assert text
        task: Todo_class = Todo_class(text, ctx.message.jump_url)
        self.bot.todos.setdefault(ctx.author.id, []).append(task)

        await self.bot.db.execute(
            "INSERT INTO todos VALUES ($1, $2, $3)",
            ctx.author.id,
            text,
            ctx.message.jump_url,
        )
        await ctx.message.add_reaction(ctx.Emojis.check)

    @todo.command(name="remove")
    async def todo_remove(self, ctx: AloneContext, todo_number: Optional[int]):
        user_todo = self.bot.todos.get(ctx.author.id)
        if not user_todo:
            return await ctx.reply("You don't have a to-do list!")

        if not todo_number:
            self.bot.todos.pop(ctx.author.id)
            await self.bot.db.execute("DELETE FROM todo WHERE user_id = $1", ctx.author.id)
            return await ctx.message.add_reaction(ctx.Emojis.check)

        for number, todo in enumerate(user_todo, start=1):
            if todo_number == number:
                try:
                    user_todo.remove(todo)
                    await self.bot.db.execute("DELETE FROM todo WHERE user_id = $1")
                    await ctx.message.add_reaction(ctx.Emojis.check)
                except KeyError:
                    await ctx.reply("That's not a task in your todo list!")

    @commands.command()
    async def uptime(self, ctx: AloneContext) -> None:
        uptime = datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        timestamp = int(self.bot.launch_time.timestamp())
        embed = discord.Embed(
            title="Current Uptime",
            description=f"Uptime: {days}d, {hours}h, {minutes}m, {seconds}s\n\nStartup Time: <t:{timestamp}:F>",
            color=0x88FF44,
        )
        await ctx.reply(embed=embed)

    @commands.command()
    async def userinfo(self, ctx: AloneContext, member: Union[discord.Member, discord.User]) -> None:
        member = member or ctx.author

        if ctx.guild:
            joined_at = f"Joined At: <t:{int(member.joined_at.timestamp())}:F>\n"  # type: ignore
        else:
            joined_at = ""
        created_at = f"Created At: <t:{int(member.created_at.timestamp())}:F>\n"

        embed = discord.Embed(
            title="Userinfo",
            description=f"Name: {member.name}\n{joined_at}{created_at}"
            f"Avatar: [Click Here]({(member.avatar or member.default_avatar).url})"
            f"Status: {member.status}\n{'Banner' if member.banner else ''}",  # type: ignore
        )
        if member.banner:
            embed.set_image(url=member.banner)
        embed.set_thumbnail(url=member.display_avatar)

        await ctx.reply(embed=embed)


async def setup(bot: AloneBot):
    await bot.add_cog(Utility(bot))
