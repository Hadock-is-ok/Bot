from __future__ import annotations

import inspect
from io import BytesIO
from random import choice
from time import perf_counter
from typing import TYPE_CHECKING, Any, List, LiteralString, Optional, Union

import discord
from discord.ext import commands

from bot import TodoData
from utils import GithubButton, InviteView, SourceButton, SupportView

if TYPE_CHECKING:
    from bot import AloneBot
    from utils import AloneContext


async def create_codeblock(content: str) -> str:
    fmt: LiteralString = "`" * 3
    return f"{fmt}py\n{content}{fmt}"


class Utility(commands.Cog):
    def __init__(self, bot: AloneBot) -> None:
        self.bot: AloneBot = bot

    @commands.command()
    async def afk(self, ctx: AloneContext, *, reason: str = ".") -> None:
        await self.bot.db.execute("INSERT INTO afk VALUES ($1, $2)", ctx.author.id, reason)
        self.bot.afk_users[ctx.author.id] = reason
        await ctx.message.add_reaction(ctx.emojis["tick"])
        await ctx.reply(f"**AFK**\nYou are now afk{f'for {reason}' if reason else ''}")

    @commands.command(aliases=["av", "pfp"])
    async def avatar(
        self,
        ctx: AloneContext,
        *,
        member: Union[discord.Member, discord.User] = commands.Author,
    ) -> None:
        embed: discord.Embed = discord.Embed(title=f"{member.display_name}'s avatar")
        embed.set_image(url=member.display_avatar.url)

        await ctx.reply(embed=embed)

    @commands.command()
    async def choose(self, ctx: AloneContext, choices: commands.Greedy[Union[str, int]]) -> None:
        if not choices:
            return await ctx.message.add_reaction(ctx.emojis["slash"])
        await ctx.reply(str(choice(choices)))

    @commands.command()
    async def cleanup(self, ctx: AloneContext, limit: int = 50) -> None:
        if not ctx.guild or isinstance(ctx.author, discord.User):
            async for message in ctx.channel.history(limit=limit):
                if message.author == ctx.me:
                    await message.delete()
            return await ctx.message.add_reaction(ctx.emojis["tick"])

        bulk: bool = ctx.channel.permissions_for(ctx.guild.me).manage_messages
        if ctx.channel.permissions_for(ctx.author).manage_messages:
            limit = 100

        await ctx.channel.purge(bulk=bulk, check=lambda m: m.author == ctx.me, limit=limit)  # type: ignore
        await ctx.message.add_reaction(ctx.emojis["tick"])

    @commands.command()
    async def invite(self, ctx: AloneContext, bot_id: Optional[int]) -> discord.Message | None:
        if not self.bot.user:
            raise RuntimeError("Bot is not ready yet.")
        if bot_id:
            user: discord.User | None = await self.bot.fetch_user(bot_id)
            if not user.bot:
                return await ctx.reply("You can't invite someone who isn't a bot!")

            link: str = discord.utils.oauth_url(user.id)
            embed: discord.Embed = discord.Embed(title=f"Invite {user.name}", description=f"[Invite]({link})")
            return await ctx.reply(embed=embed, view=InviteView(user.id))

        link = discord.utils.oauth_url(self.bot.user.id)
        embed = discord.Embed(title="Thank you for supporting me!", description=f"[Invite Me!]({link})")
        await ctx.reply(embed=embed, view=InviteView(self.bot.user.id))

    @commands.command()
    async def ping(self, ctx: AloneContext) -> None:
        websocket_ping: float = self.bot.latency * 1000

        start: float = perf_counter()
        message: discord.Message = await ctx.reply("Pong!")
        end: float = perf_counter()
        typing_ping: float = (end - start) * 1000

        start = perf_counter()
        await self.bot.db.execute("SELECT 1")
        end = perf_counter()
        database_ping: float = (end - start) * 1000

        embed: discord.Embed = discord.Embed(title="Ping")
        embed.add_field(
            name="<a:typing:1041021440352337991> | Typing",
            value=await create_codeblock(f"{typing_ping:.2f}ms"),
        )
        embed.add_field(
            name="<a:loading:1041021510590152834> | Websocket",
            value=await create_codeblock(f"{websocket_ping:.2f}ms"),
        )
        embed.add_field(
            name="<:postgresql:1180172627663396864> | Database",
            value=await create_codeblock(f"{database_ping:.2f}ms"),
        )

        await message.edit(content=None, embed=embed)

    @commands.group(invoke_without_command=True)
    async def prefix(self, ctx: AloneContext) -> None:
        prefix_list: str = "\n".join(await self.bot.get_prefix(ctx.message))
        embed: discord.Embed = discord.Embed(title="Prefixes you can use", description=prefix_list)
        await ctx.reply(embed=embed)

    @prefix.command(name="add")
    async def prefix_add(self, ctx: AloneContext, *, prefix: str = "") -> discord.Message | None:
        if len(prefix) > 25:
            return await ctx.reply("You can't have a prefix that's longer than 25 characters, sorry!")

        prefix_list: List[str] = self.bot.user_prefixes.setdefault(ctx.author.id, [])
        prefix_list.append(prefix)

        await self.bot.db.execute("INSERT INTO prefix VALUES ($1, $2)", ctx.author.id, prefix)
        await ctx.message.add_reaction(ctx.emojis["tick"])

    @prefix.command(name="guild")
    async def prefix_guild(self, ctx: AloneContext, *, prefix: Optional[str]) -> discord.Message | None:
        if not ctx.guild:
            raise commands.NoPrivateMessage("This is a guild only command!")

        if not prefix or "remove" in prefix.lower():
            guild_config: Any = self.bot.guild_prefixes.get(ctx.guild.id, None)
            if not guild_config:
                return await ctx.reply("There is no guild prefix to remove!")

            await self.bot.db.execute("UPDATE guilds SET prefix = NULL WHERE guild_id = $1", ctx.guild.id)
            await ctx.message.add_reaction(ctx.emojis["tick"])
            return await ctx.reply("The prefix for this guild has been removed.")

        if len(prefix) > 5:
            return await ctx.reply("You can't have a prefix that's longer than 5 characters, sorry!")

        self.bot.guild_prefixes[ctx.guild.id] = prefix
        await self.bot.db.execute(
            "INSERT INTO guilds VALUES ($1, $2) ON CONFLICT DO UPDATE guilds SET prefix = $2 WHERE guild_id = $1",
            ctx.guild.id,
            prefix,
        )
        await ctx.message.add_reaction(ctx.emojis["tick"])
        await ctx.reply(f"The prefix for this guild is now `{prefix}`")

    @prefix.command(name="remove")
    async def prefix_remove(self, ctx: AloneContext, *, prefix: Optional[str]) -> discord.Message | None:
        user_prefixes: List[str] = self.bot.user_prefixes.get(ctx.author.id, [])
        if not user_prefixes:
            return await ctx.reply("You don't have custom prefixes setup!")

        if not prefix:
            self.bot.user_prefixes.pop(ctx.author.id)
            await self.bot.db.execute("DELETE FROM prefix WHERE user_id = $1", ctx.author.id)
            return await ctx.message.add_reaction(ctx.emojis["tick"])

        try:
            user_prefixes.remove(prefix)
            await self.bot.db.execute(
                "DELETE FROM prefix WHERE user_id = $1 AND prefix = $2",
                ctx.author.id,
                prefix,
            )
            await ctx.message.add_reaction(ctx.emojis["tick"])
        except ValueError:
            await ctx.message.add_reaction(ctx.emojis["cross"])
            await ctx.reply("That's not one of your prefixes!")

    @commands.command(aliases=["server_info", "server info", "si", "guildinfo"])
    @commands.guild_only()
    async def serverinfo(self, ctx: AloneContext, guild: discord.Guild = commands.CurrentGuild) -> None:
        assert guild.icon
        bots: int = sum(member.bot for member in guild.members)
        embed: discord.Embed = discord.Embed(
            title=f"Server Info for {guild.name}",
            description=f"Owner: {guild.owner}\nID: {guild.id}\n"
            f"Members: {guild.member_count}\nBots: {bots}\nNitro Level: {guild.premium_tier}",
        )
        embed.set_thumbnail(url=guild.icon.url)
        await ctx.reply(embed=embed)

    @commands.command()
    async def source(self, ctx: AloneContext, *, command_name: Optional[str]) -> discord.Message | None:
        if not command_name:
            return await ctx.reply(self.bot.github_link, view=GithubButton(ctx))

        command = self.bot.get_command(command_name)
        if not command:
            return await ctx.reply("That command doesn't exist!")

        source: str = inspect.getsource(command.callback)
        source_lines: tuple[list[str], int] = inspect.getsourcelines(command.callback)
        file_name: str | None = command.callback.__module__.replace(".", "/") + ".py"
        embed: discord.Embed = discord.Embed(
            title=f"Source for {command.name}",
            description=await create_codeblock(source),
        )
        await ctx.reply(embed=embed, view=SourceButton(ctx, source_lines, file_name))

    @commands.command()
    async def spotify(self, ctx: AloneContext, *, member: discord.Member = commands.Author):
        await ctx.typing()
        spotify: discord.Spotify | None = discord.utils.find(  # type: ignore
            lambda activity: isinstance(activity, discord.Spotify), member.activities
        )
        if not spotify:
            return await ctx.reply(f"{member.display_name} isn't listening to Spotify!")

        headers: dict[str, str] = {"Authorization": f"Bearer {self.bot.jeyy_key}"}
        params: dict[str, Any] = {
            "title": spotify.title,
            "cover_url": spotify.album_cover_url,
            "duration_seconds": spotify.duration.seconds,
            "start_timestamp": spotify.start.timestamp(),
            "artists": spotify.artists,
        }
        async with self.bot.session.get(
            "https://api.jeyy.xyz/v2/discord/spotify", params=params, headers=headers
        ) as response:
            bytes = BytesIO(await response.read())

        file: discord.File = discord.File(bytes, "spotify.png")
        artists: str = ", ".join(spotify.artists)

        embed: discord.Embed = discord.Embed(
            description=f"<:spotify:1169623519630471198> **{discord.utils.escape_markdown(spotify.title)}** by **{discord.utils.escape_markdown(artists)}**"
        )
        embed.set_author(
            name=f"{discord.utils.escape_markdown(member.display_name)}'s Spotify",
            icon_url=member.display_avatar.url,
        )
        embed.set_image(url="attachment://spotify.png")

        await ctx.reply(embed=embed, file=file)

    @commands.command()
    async def support(self, ctx: AloneContext) -> None:
        embed: discord.Embed = discord.Embed(
            title="Support",
            description=f"Join my [support server](https://discord.gg/{self.bot.support_server})!",
        )
        await ctx.reply(embed=embed, view=SupportView(self.bot.support_server))

    @commands.group(invoke_without_command=True)
    async def todo(self, ctx: AloneContext) -> discord.Message | None:
        user_todo: List[TodoData] | None = self.bot.todos.get(ctx.author.id)
        if not user_todo:
            return await ctx.reply("You don't have a to-do list!")

        todo_list: str = ""
        for number, todo in enumerate(user_todo, start=1):
            todo_list += f"**__[{number}]({todo.jump_url})__**: **{todo.content}**\n"

        embed: discord.Embed = discord.Embed(title="Todo", description=todo_list)
        await ctx.reply(embed=embed)

    @todo.command(name="add")
    async def todo_add(self, ctx: AloneContext, *, text: Optional[str]) -> None:
        assert text
        task: TodoData = TodoData(text, ctx.message.jump_url)
        user_todo: List[TodoData] = self.bot.todos.setdefault(ctx.author.id, [])
        user_todo.append(task)

        await self.bot.db.execute(
            "INSERT INTO todo VALUES ($1, $2, $3)",
            ctx.author.id,
            text,
            ctx.message.jump_url,
        )
        await ctx.message.add_reaction(ctx.emojis["tick"])

    @todo.command(name="remove")
    async def todo_remove(self, ctx: AloneContext, todo_number: Optional[int]) -> discord.Message | None:
        user_todo: List[TodoData] | None = self.bot.todos.get(ctx.author.id)
        if not user_todo:
            return await ctx.reply("You don't have a to-do list!")

        if not todo_number:
            self.bot.todos.pop(ctx.author.id)
            await self.bot.db.execute("DELETE FROM todo WHERE user_id = $1", ctx.author.id)
            return await ctx.message.add_reaction(ctx.emojis["tick"])

        for number, todo in enumerate(user_todo, start=1):
            if todo_number == number:
                try:
                    user_todo.remove(todo)
                    await self.bot.db.execute(
                        "DELETE FROM todo WHERE user_id = $1 AND task = $2",
                        ctx.author.id,
                        todo.content,
                    )
                    await ctx.message.add_reaction(ctx.emojis["tick"])
                except KeyError:
                    await ctx.reply("That's not a task in your todo list!")

    @commands.command()
    async def uptime(self, ctx: AloneContext) -> None:
        uptime = discord.utils.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        timestamp: int = int(self.bot.launch_time.timestamp())
        embed: discord.Embed = discord.Embed(
            title="Current Uptime",
            description=f"Uptime: {days}d, {hours}h, {minutes}m, {seconds}s\n\nStartup Time: <t:{timestamp}:F>",
        )
        await ctx.reply(embed=embed)

    @commands.command()
    async def userinfo(self, ctx: AloneContext, member: discord.Member = commands.Author) -> None:
        if member.joined_at:
            joined_at: str = f"Joined At: <t:{int(member.joined_at.timestamp())}:F>\n"
            status: str = f"Status: {member.status}\n"
        else:
            joined_at = ""
            status: str = ""
        created_at: str = f"Created At: <t:{int(member.created_at.timestamp())}:F>\n"

        embed: discord.Embed = discord.Embed(
            title="Userinfo",
            description=f"Name: {member.name}\n{joined_at}{created_at}"
            f"Avatar: [Click Here]({(member.avatar or member.default_avatar).url})\n"
            f"{status}{'Banner' if member.banner else ''}",
        )
        if member.banner:
            embed.set_image(url=member.banner)
        embed.set_thumbnail(url=member.display_avatar)

        await ctx.reply(embed=embed)


async def setup(bot: AloneBot) -> None:
    await bot.add_cog(Utility(bot))
