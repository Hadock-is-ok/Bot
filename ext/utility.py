from __future__ import annotations

import inspect
from io import BytesIO
from random import choice
from time import perf_counter
from typing import TYPE_CHECKING, Any, List, LiteralString, Optional, Union

import revolt
from revolt.ext import commands

from client import TodoData
from utils import GithubButton, InviteView, SourceButton, SupportView

if TYPE_CHECKING:
    from client import AloneBot
    from utils import AloneContext


async def create_codeblock(content: str) -> str:
    fmt: LiteralString = "`" * 3
    return f"{fmt}py\n{content}{fmt}"


class Utility(commands.Cog[AloneBot]):
    def __init__(self, client: AloneBot) -> None:
        self.client: AloneBot = client

    @commands.command()
    async def afk(self, ctx: AloneContext, *, reason: str = "no reason") -> None:
        await self.client.db.execute("INSERT INTO afk VALUES ($1, $2)", ctx.author.id, reason)
        self.client.afk_users[ctx.author.id] = reason

        if reason != "no reason":
            fmt: str = f" for {reason}."
        else:
            fmt = "."

        await ctx.message.add_reaction(ctx.emojis["tick"])
        await ctx.send(f"**AFK**\nYou are now afk{fmt}")

    @commands.command(aliases=["av", "pfp"])
    async def avatar(self, ctx: AloneContext, *, member: Union[revolt.Member, revolt.User] = commands.Author) -> None:
        embed: revolt.SendableEmbed = revolt.SendableEmbed(title=f"{member.display_name}'s avatar")
        embed.set_image(url=member.display_avatar.url)

        await ctx.send(embed=embed)

    @commands.command()
    async def choose(self, ctx: AloneContext, choices: commands.Greedy[Union[str, int]]) -> None:
        await ctx.send(str(choice(choices)))

    @commands.command()
    async def cleanup(self, ctx: AloneContext, limit: int = 50) -> None:
        if not ctx.server or isinstance(ctx.author, revolt.User):
            async for message in ctx.channel.history(limit=limit):
                if message.author == ctx.me:
                    await message.delete()
            return await ctx.message.add_reaction(ctx.emojis["tick"])

        bulk: bool = ctx.channel.permissions_for(ctx.server.me).manage_messages
        if ctx.channel.permissions_for(ctx.author).manage_messages:
            limit = 100

        await ctx.channel.purge(bulk=bulk, check=lambda m: m.author == ctx.me, limit=limit)  # type: ignore
        await ctx.message.add_reaction(ctx.emojis["tick"])

    @commands.command()
    async def invite(self, ctx: AloneContext, bot_id: Optional[int]) -> revolt.Message | None:
        if not self.client.user:
            raise RuntimeError("Bot is not ready yet.")
        if bot_id:
            user: revolt.User | None = await self.client.fetch_user(bot_id)
            if not user.client:
                return await ctx.send("You can't invite someone who isn't a client!")

            link: str = revolt.utils.oauth_url(user.id)
            embed: revolt.SendableEmbed = revolt.SendableEmbed(title=f"Invite {user.name}", description=f"[Invite]({link})")
            return await ctx.send(embed=embed, view=InviteView(user.id))

        link = revolt.utils.oauth_url(self.client.user.id)
        embed = revolt.SendableEmbed(title="Thank you for supporting me!", description=f"[Invite Me!]({link})")
        await ctx.send(embed=embed, view=InviteView(self.client.user.id))

    @commands.command()
    async def ping(self, ctx: AloneContext) -> None:
        websocket_ping: float = self.client.latency * 1000

        start: float = perf_counter()
        message: revolt.Message = await ctx.send("Pong!")
        end: float = perf_counter()
        typing_ping: float = end - start

        start = perf_counter()
        await self.client.db.execute("SELECT 1")
        end = perf_counter()
        database_ping: float = end - start

        embed: revolt.SendableEmbed = revolt.SendableEmbed(title="Ping")
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
        prefix_list: str = "\n".join(await self.client.get_prefix(ctx.message))
        embed: revolt.SendableEmbed = revolt.SendableEmbed(title="Prefixes you can use", description=prefix_list)
        await ctx.send(embed=embed)

    @prefix.command(name="add")
    async def prefix_add(self, ctx: AloneContext, *, prefix: str = "") -> revolt.Message | None:
        if len(prefix) > 5:
            return await ctx.send("You can't have a prefix that's longer than 5 characters, sorry!")

        prefix_list: List[str] = self.client.user_prefixes.setdefault(ctx.author.id, [])
        prefix_list.append(prefix)

        await self.client.db.execute("INSERT INTO prefix VALUES ($1, $2)", ctx.author.id, prefix)
        await ctx.message.add_reaction(ctx.emojis["tick"])

    @prefix.command(name="server")
    async def prefix_server(self, ctx: AloneContext, *, prefix: Optional[str]) -> revolt.Message | None:
        if not ctx.server:
            raise commands.NoPrivateMessage("This is a server only command!")

        if not prefix or "remove" in prefix.lower():
            server_config: Any = self.client.server_prefixes.get(ctx.server.id, None)
            if not server_config:
                return await ctx.send("There is no server prefix to remove!")

            await self.client.db.execute("UPDATE servers SET prefix = NULL WHERE server_id = $1", ctx.server.id)
            await ctx.message.add_reaction(ctx.emojis["tick"])
            return await ctx.send("The prefix for this server has been removed.")

        if len(prefix) > 5:
            return await ctx.send("You can't have a prefix that's longer than 5 characters, sorry!")

        self.client.server_prefixes[ctx.server.id] = prefix
        await self.client.db.execute(
            "INSERT INTO servers VALUES ($1, $2) ON CONFLICT DO UPDATE servers SET prefix = $2 WHERE server_id = $1",
            ctx.server.id,
            prefix,
        )
        await ctx.message.add_reaction(ctx.emojis["tick"])
        await ctx.send(f"The prefix for this server is now `{prefix}`")

    @prefix.command(name="remove")
    async def prefix_remove(self, ctx: AloneContext, *, prefix: Optional[str]) -> revolt.Message | None:
        user_prefixes: List[str] = self.client.user_prefixes.get(ctx.author.id, [])
        if not user_prefixes:
            return await ctx.send("You don't have custom prefixes setup!")

        if not prefix:
            self.client.user_prefixes.pop(ctx.author.id)
            await self.client.db.execute("DELETE FROM prefix WHERE user_id = $1", ctx.author.id)
            return await ctx.message.add_reaction(ctx.emojis["tick"])

        try:
            user_prefixes.remove(prefix)
            await self.client.db.execute(
                "DELETE FROM prefix WHERE user_id = $1 AND prefix = $2",
                ctx.author.id,
                prefix,
            )
            await ctx.message.add_reaction(ctx.emojis["tick"])
        except ValueError:
            await ctx.message.add_reaction(ctx.emojis["cross"])
            await ctx.send("That's not one of your prefixes!")

    @commands.command(aliases=["server_info", "server info", "si", "serverinfo"])
    @commands.server_only()
    async def serverinfo(self, ctx: AloneContext, server: revolt.server = commands.Currentserver) -> None:
        assert server.icon
        bots: int = sum(member.client for member in server.members)
        embed: revolt.SendableEmbed = revolt.SendableEmbed(
            title=f"Server Info for {server.name}",
            description=f"Owner: {server.owner}\nID: {server.id}\n"
            f"Members: {server.member_count}\nBots: {bots}\nNitro Level: {server.premium_tier}",
        )
        embed.set_thumbnail(url=server.icon.url)
        await ctx.send(embed=embed)

    @commands.command()
    async def source(self, ctx: AloneContext, *, command_name: Optional[str]) -> revolt.Message | None:
        if not command_name:
            return await ctx.send(self.client.github_link, view=GithubButton(ctx))

        command = self.client.get_command(command_name)
        if not command:
            return await ctx.send("That command doesn't exist!")

        source: str = inspect.getsource(command.callback)
        source_lines: tuple[list[str], int] = inspect.getsourcelines(command.callback)
        file_name: str | None = command.callback.__module__.replace(".", "/") + ".py"
        embed: revolt.SendableEmbed = revolt.SendableEmbed(
            title=f"Source for {command.name}",
            description=await create_codeblock(source),
        )
        await ctx.send(embed=embed, view=SourceButton(ctx, source_lines, file_name))

    @commands.command()
    async def spotify(self, ctx: AloneContext, *, member: revolt.Member = commands.Author):
        spotify: revolt.Spotify | None = revolt.utils.find(  # type: ignore
            lambda activity: isinstance(activity, revolt.Spotify), member.activities
        )
        if not spotify:
            return await ctx.send(f"{member.display_name} isn't listening to Spotify!")

        headers: dict[str, str] = {"Authorization": f"Bearer {self.client.jeyy_key}"}
        params: dict[str, Any] = {
            "title": spotify.title,
            "cover_url": spotify.album_cover_url,
            "duration_seconds": spotify.duration.seconds,
            "start_timestamp": spotify.start.timestamp(),
            "artists": spotify.artists,
        }
        async with self.client.session.get(
            "https://api.jeyy.xyz/v2/revolt/spotify", params=params, headers=headers
        ) as response:
            bytes = BytesIO(await response.read())

        file: revolt.File = revolt.File(bytes, "spotify.png")
        artists: str = ", ".join(spotify.artists)

        embed: revolt.SendableEmbed = revolt.SendableEmbed(
            description=f"<:spotify:1169623519630471198> **{revolt.utils.escape_markdown(spotify.title)}** by **{revolt.utils.escape_markdown(artists)}**"
        )
        embed.set_author(
            name=f"{revolt.utils.escape_markdown(member.display_name)}'s Spotify", icon_url=member.display_avatar.url
        )
        embed.set_image(url="attachment://spotify.png")

        await ctx.send(embed=embed, file=file)

    @commands.command()
    async def support(self, ctx: AloneContext) -> None:
        embed: revolt.SendableEmbed = revolt.SendableEmbed(
            title="Support",
            description=f"Join my [support server]({self.client.support_server})!",
        )
        await ctx.send(embed=embed, view=SupportView(self.client.support_server))

    @commands.group(invoke_without_command=True)
    async def todo(self, ctx: AloneContext) -> revolt.Message | None:
        user_todo: List[TodoData] | None = self.client.todos.get(ctx.author.id)
        if not user_todo:
            return await ctx.send("You don't have a to-do list!")

        todo_list: str = ""
        for number, todo in enumerate(user_todo, start=1):
            todo_list += f"**__[{number}]({todo.jump_url})__**: **{todo.content}**\n"

        embed: revolt.SendableEmbed = revolt.SendableEmbed(title="Todo", description=todo_list)
        await ctx.send(embed=embed)

    @todo.command(name="add")
    async def todo_add(self, ctx: AloneContext, *, text: Optional[str]) -> None:
        assert text
        task: TodoData = TodoData(text, ctx.message.jump_url)
        user_todo: List[TodoData] = self.client.todos.setdefault(ctx.author.id, [])
        user_todo.append(task)

        await self.client.db.execute(
            "INSERT INTO todo VALUES ($1, $2, $3)",
            ctx.author.id,
            text,
            ctx.message.jump_url,
        )
        await ctx.message.add_reaction(ctx.emojis["tick"])

    @todo.command(name="remove")
    async def todo_remove(self, ctx: AloneContext, todo_number: Optional[int]) -> revolt.Message | None:
        user_todo: List[TodoData] | None = self.client.todos.get(ctx.author.id)
        if not user_todo:
            return await ctx.send("You don't have a to-do list!")

        if not todo_number:
            self.client.todos.pop(ctx.author.id)
            await self.client.db.execute("DELETE FROM todo WHERE user_id = $1", ctx.author.id)
            return await ctx.message.add_reaction(ctx.emojis["tick"])

        for number, todo in enumerate(user_todo, start=1):
            if todo_number == number:
                try:
                    user_todo.remove(todo)
                    await self.client.db.execute(
                        "DELETE FROM todo WHERE user_id = $1 AND task = $2", ctx.author.id, todo.content
                    )
                    await ctx.message.add_reaction(ctx.emojis["tick"])
                except KeyError:
                    await ctx.send("That's not a task in your todo list!")

    @commands.command()
    async def uptime(self, ctx: AloneContext) -> None:
        uptime = revolt.utils.utcnow() - self.client.launch_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        timestamp: int = int(self.client.launch_time.timestamp())
        embed: revolt.SendableEmbed = revolt.SendableEmbed(
            title="Current Uptime",
            description=f"Uptime: {days}d, {hours}h, {minutes}m, {seconds}s\n\nStartup Time: <t:{timestamp}:F>",
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def userinfo(self, ctx: AloneContext, member: revolt.Member = commands.Author) -> None:
        if member.joined_at:
            joined_at: str = f"Joined At: <t:{int(member.joined_at.timestamp())}:F>\n"
            status: str = f"Status: {member.status}\n"
        else:
            joined_at = ""
            status: str = ""
        created_at: str = f"Created At: <t:{int(member.created_at.timestamp())}:F>\n"

        embed: revolt.SendableEmbed = revolt.SendableEmbed(
            title="Userinfo",
            description=f"Name: {member.name}\n{joined_at}{created_at}"
            f"Avatar: [Click Here]({(member.avatar or member.default_avatar).url})\n"
            f"{status}{'Banner' if member.banner else ''}",
        )
        if member.banner:
            embed.set_image(url=member.banner)
        embed.set_thumbnail(url=member.display_avatar)

        await ctx.send(embed=embed)


async def setup(client: AloneBot) -> None:
    client.add_cog(Utility(client))
