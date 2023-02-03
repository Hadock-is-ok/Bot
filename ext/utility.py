import discord, asyncio, typing, random
from datetime import datetime
from discord.ext import commands
from typing import Optional
import time
import inspect, json
from utils import views, bot


class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def uptime(self, ctx: commands.Context):
        uptime = datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        timestamp = int(self.bot.launch_time.timestamp())
        await ctx.reply(
            embed=discord.Embed(
                title="Current Uptime",
                description=f"Uptime: {days}d, {hours}h, {minutes}m, {seconds}s\n\nStartup Time: <t:{timestamp}:F>",
                color=0x88FF44,
            )
        )

    @commands.group(invoke_without_command=True)
    async def prefix(self, ctx: commands.Context):
        prefixes = ""
        for prefix in await self.bot.get_prefix(ctx.message):
            if prefix == "":
                prefixes += "No prefix enabled!"
            prefixes += f"{prefix}\n"
        await ctx.reply(
            embed=discord.Embed(title="My available prefixes", description=prefixes)
        )

    @prefix.command()
    @commands.has_guild_permissions(manage_guild=True)
    async def guild(self, ctx: commands.Context, *, prefix: Optional[str] = None) -> discord.Message:
        if not prefix or "remove" in prefix.lower():
            self.bot.guild_prefix.pop(ctx.guild.id)
            await self.bot.db.execute("DELETE FROM guilds WHERE guild_id = $1")
            await ctx.message.add_reaction(ctx.Emojis.check)
            return await ctx.reply("Custom prefix for this guild has been cleared.")

        self.bot.guild_config[ctx.guild.id]["prefix"] = prefix
        await self.bot.db.execute("INSERT INTO guilds VALUES ($1, $2)", ctx.guild.id, prefix)
        await ctx.message.add_reaction(ctx.Emojis.check)
        await ctx.reply(f"Custom prefix for this guild has been changed to `{prefix}`")

    @prefix.command(name="add")
    async def prefix_add(self, ctx: commands.Context, *, prefix: Optional[str] = ""):
        if len(prefix) > 5:
            return await ctx.reply(
                "Your prefix can't be longer than 5 characters, sorry!"
            )
        prefixes = self.bot.user_prefixes.get(ctx.author.id, [])
        prefixes.append(prefix)
        self.bot.user_prefixes[ctx.author.id] = prefixes
        await self.bot.db.execute("INSERT INTO prefix VALUES ($1, $2)", ctx.author.id, prefix)
        await ctx.message.add_reaction(ctx.Emojis.check)

    @prefix.command(name="remove", aliases=["erase", "delete"])
    async def prefix_remove(self, ctx: commands.Context, prefix: str = None):
        if not self.bot.user_prefixes.get(ctx.author.id):
            return await ctx.reply("You don't have any custom prefixes!")
        if not prefix:
            self.bot.user_prefixes.pop(ctx.author.id)
            await self.bot.db.execute("DELETE FROM prefix WHERE user_id = $1", ctx.author.id)
            return await ctx.message.add_reaction(ctx.Emojis.check)
        try:
            self.bot.user_prefixes[ctx.author.id].remove(prefix)
            await self.bot.db.execute("DELETE FROM prefix WHERE user_id = $1 AND prefix = $2", ctx.author.id, prefix)
            await ctx.message.add_reaction(ctx.Emojis.check)
        except ValueError:
            await ctx.message.add_reaction(ctx.Emojis.x)
            await ctx.reply("That prefix isn't in the list!")

    @commands.group(invoke_without_command=True)
    async def todo(self, ctx: commands.Context):
        _todo = self.bot.todos.get(ctx.author.id)
        if not _todo:
            return await ctx.reply("You don't have a todo list!")
        todo_list = ""
        for number, todo in enumerate(_todo, start=1):
            todo_list += f"**__[{number}]({todo.jump_url})__**: **{todo.task}**\n"
        await ctx.reply(embed=discord.Embed(title="Todo", description=todo_list))

    @todo.command(name="add")
    async def todo_add(self, ctx: commands.Context, *, todo_text: str):
        _todo = self.bot.todos.get(ctx.author.id)
        if not _todo:
            self.bot.todos[ctx.author.id] = []
        task = bot.Todo(todo_text, ctx.message.jump_url)
        self.bot.todos[ctx.author.id].append(task)
        await self.bot.db.execute("INSERT INTO todo VALUES ($1, $2, $3)", ctx.author.id, todo_text, ctx.message.jump_url)
        await ctx.message.add_reaction(ctx.Emojis.check)
    
    @todo.command(name="remove", aliases=["delete", "erase"])
    async def todo_remove(self, ctx: commands.Context, _number: int = None):
        _todo = self.bot.todos.get(ctx.author.id)
        if not _todo:
            return await ctx.reply("You don't have any tasks!")
        
        if not _number:
            self.bot.todos.pop(ctx.author.id)
            await self.bot.db.execute("DELETE FROM todo WHERE user_id = $1", ctx.author.id)
            return await ctx.message.add_reaction(ctx.Emojis.check)
        
        for number, todo in enumerate(_todo, start=1):
            if _number == number:
                try:
                    _todo.remove(todo)
                    await self.bot.db.execute("DELETE FROM todo WHERE user_id = $1 AND task = $2", ctx.author.id, todo.task)
                    await ctx.message.add_reaction(ctx.Emojis.check)
                except KeyError:
                    await ctx.reply("That isn't a valid task!")

    @commands.command()
    async def source(self, ctx, *, command_name: str = None):
        if not command_name:
            return await ctx.reply("https://github.com/Alone-Bot/Alone-Bot")
        command = self.bot.get_command(command_name)
        if not command:
            return await ctx.reply("That's not a valid command!")
        source = inspect.getsource(command.callback).replace("`","​`")
        await ctx.reply(embed=discord.Embed(title=f"Source for {command_name}", description=f"```py\n{source}```"))
    
    @commands.command()
    async def invite(self, ctx: commands.Context):
        link = discord.utils.oauth_url(
            self.bot.user.id,
        )
        await ctx.reply(
            embed=discord.Embed(
                title="Invite me!",
                description=f"[Invite Me!]({link})",
                color=0x28E8ED,
            )
        )

    @commands.command()
    async def quote(self, ctx: commands.Context, message: discord.Message = None):
        if not message:
            if not ctx.message.reference:
                return await ctx.reply("You need to give me a message to quote.")
            message = ctx.message.reference.resolved
        await ctx.reply(
            embed=discord.Embed(
                title=f"{message.author} sent:",
                description=f"> {message.content}\n- {message.author.mention}",
            )
        )

    @commands.command()
    async def ping(self, ctx: commands.Context):
        websocket = self.bot.latency * 1000
        startwrite = time.perf_counter()
        msg = await ctx.reply("Pong!")
        endwrite = time.perf_counter()
        startdb = time.perf_counter()
        await self.bot.db.execute("SELECT 1")
        enddb = time.perf_counter()
        database = (enddb - startdb) * 1000
        duration = (endwrite - startwrite) * 100
        embed = discord.Embed(title="Pong!", color=discord.Colour.blue())
        embed.add_field(
            name="<a:typing:990387851940229120> | Typing",
            value=f"```py\n{duration:.2f}ms```",
        )
        embed.add_field(
            name="<a:loading2:990387928213631046> | Websocket",
            value=f"```py\n{websocket:.2f}ms```",
        )
        embed.add_field(
            name="<:PostgreSQL:1019435339124850708> | Database",
            value=f"```py\n{database:.2f}ms```",
        )
        embed.timestamp = discord.utils.utcnow()
        await msg.edit(embed=embed)

    @commands.command()
    async def counter(self, ctx: commands.Context):
        await ctx.reply(
            embed=discord.Embed(
                title="Command Counter",
                description=f"Commands used since last restart: {self.bot.command_counter}",
                color=0x1F84C5,
            )
        )

    @commands.command(aliases=["av"])
    async def avatar(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            member = ctx.author
        embed = discord.Embed(title=f"{member}'s avatar")
        embed.set_image(url=member.avatar.url)
        await ctx.reply(embed=embed)

    @commands.command(aliases=["ui", "user_info", "user info"])
    @commands.guild_only()
    async def userinfo(self, ctx: commands.Context, *, member: discord.Member = None):
        if not member:
            member = ctx.author
        jointime = int(member.joined_at.timestamp())
        createdtime = int(member.created_at.timestamp())
        status = member.status
        embed = discord.Embed(
            title="Userinfo",
            description=f"""
Name: {member.name}
Nicname: {member.nick}
Joined at: <t:{jointime}:F>
Created at: <t:{createdtime}:F>
Avatar: [Click Here]({member.avatar.url})
Status: {status}
{"Banner:" if member.banner else ""}""",
            color=0x53BDCE,
        )
        if member.banner:
            embed.set_image(url=member.banner)
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.reply(embed=embed)

    @commands.command(aliases=["server_info", "server info", "si", "guildinfo"])
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context, guild: discord.Guild = None):
        if not guild:
            guild = ctx.guild
        members = len([members for members in guild.members])
        bots = sum(m.bot for m in guild.members)
        embed = discord.Embed(
            title="Server Info",
            description=f"""
Owner: {guild.owner}
ID: {guild.id}
Name: {guild.name}
Members: {guild.member_count}
Bots: {bots}
Nitro Tier: Level {guild.premium_tier}""",
            color=0x184EF3,
        )
        embed.set_thumbnail(url=guild.icon.url)
        await ctx.reply(embed=embed)

    @commands.command()
    async def support(self, ctx: commands.Context):
        await ctx.reply(
            embed=discord.Embed(
                title="Support",
                description=f"Join my [support server]({self.bot.support_server})!",
            ), view=views.JoinSupportView(ctx)
        )

    @commands.command(aliases=["cf", "flip_coin"])
    async def coinflip(self, ctx):
        message = await ctx.reply("Choosing a side..")
        coin = ["heads", "tails"]
        choice = random.choice(coin)
        await message.edit(
            content=f"It's {choice}!"
        )

    @commands.command()
    async def choose(
        self, ctx: commands.Context, choices: commands.Greedy[typing.Union[str, int]]
    ):
        choice = random.choice(choices)
        await ctx.reply(choice)

    @commands.command()
    async def cleanup(self, ctx: commands.Context, limit: int = 50):
        bulk = ctx.guild.me.guild_permissions.ban_members
        
        def is_bot(message: discord.Message):
            return message.author == ctx.me
        
        await ctx.channel.purge(limit=limit, bulk=bulk, check=is_bot)
        await ctx.message.add_reaction(ctx.Emojis.check)

    @commands.command()
    async def afk(self, ctx: commands.Context, *, reason: str = "no reason"):
        await ctx.message.add_reaction(ctx.Emojis.check)
        await ctx.reply(f"**AFK**\nYou are now afk for {reason}.")
        await self.bot.db.execute("INSERT INTO afk VALUES ($1, $2)", ctx.author.id, reason)
        await asyncio.sleep(0.1)
        self.bot.afks[ctx.author.id] = reason


async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
