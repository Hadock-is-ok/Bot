from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Optional, NamedTuple

import os
import asyncpg
import datetime
import discord
import logging
import aiohttp
from cachetools import TTLCache
from discord.ext import commands

from .context import AloneContext

class Todo(NamedTuple):
    task: str
    jump_url: str

class AloneBot(commands.AutoShardedBot):
    DEFAULT_PREFIXES: ClassVar[List[str]] = ["Alone", "alone"]
    INITIAL_EXTENSIONS: ClassVar[List[str]] = [
        "ext.events",
        "ext.error",
        "ext.fun",
        "ext.help",
        "ext.moderation",
        "ext.owner",
        "ext.utility",
        "jishaku",
    ]

    owner_ids: List[int]
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(
            command_prefix=self.get_prefix,
            strip_after_prefix=True,
            case_insensitive=True,
            owner_ids=[412734157819609090],
            *args,
            **kwargs,
        )

        self.blacklists: Dict[int, str] = {}
        self.afks: Dict[int, str] = {}
        self.todos: Dict[int, List[Todo]] = {}
        self.user_prefixes: Dict[int, List[str]] = {}
        self.guild_config: Dict[int, Dict[str, Any]] = {}
        self.messages: TTLCache[str, discord.Message] = TTLCache(maxsize=2000, ttl=300.0)

        self.support_server: str = os.environ["bot_guild"]
        self.maintenance: Optional[str] = None

        self.command_counter: int = 0
        self.launch_time: datetime.datetime = datetime.datetime.utcnow()

    async def get_prefix(self, message: discord.Message):
        prefixes: List[str] = self.DEFAULT_PREFIXES.copy()
        user_prefixes = self.user_prefixes.get(message.author.id)
        if user_prefixes:
            prefixes.extend(user_prefixes)

        if message.guild and (self.guild_config.get(message.guild.id, None).get("prefixes", None)):
            prefixes.append(self.guild_config.get(message.guild.id)["prefix"])

        if not message.guild or message.author.id in self.owner_ids:
            prefixes.append("")

        assert self.user
        return *prefixes, f"<@!{self.user.id}> ", f"<@{self.user.id}> "

    async def get_context(self, message: discord.Message, *, cls=AloneContext):
        return await super().get_context(message, cls=cls)

    async def process_commands(self, message: discord.Message):
        if message.author.bot:
            return
        
        ctx = await self.get_context(message)
        if not ctx.valid:
            return

        async with ctx.typing():
            await self.invoke(ctx)
    
    async def setup_hook(self):
        self.db = await asyncpg.create_pool(
            host=os.environ["database"], 
            port=int(os.environ["db_port"]), 
            user=os.environ["db_user"],
            password=os.environ["db_pwd"], 
            database="postgres",
        )

        assert self.db
        for extension in self.INITIAL_EXTENSIONS:
            await self.load_extension(extension)

        records = await self.db.fetch("SELECT user_id, array_agg(prefix) AS prefixes FROM prefix GROUP BY user_id")
        self.user_prefixes = {user_id: prefix for user_id, prefix in records}

        records = await self.db.fetch("SELECT * FROM guilds WHERE prefix IS NOT NULL")
        for guild_id, prefix in records:
            self.guild_config[guild_id]["prefix"] = prefix

        records = await self.db.fetch("SELECT * FROM todo")
        for user_id, task, jump_url in records:
            if not self.todos.get(user_id):
                self.todos[user_id] = []
            self.todos[user_id].append(Todo(task, jump_url))

        records = await self.db.fetch("SELECT * FROM afk")
        self.afk = {user_id: reason for user_id, reason in records}
    
    async def close(self):
        await self.session.close()
        await self.db.close()
        await super().close()
    
    async def start(self, token: str):
        discord.utils.setup_logging(handler=logging.FileHandler("bot.log"))
        self.logger = logging.getLogger("discord")
        self.session = aiohttp.ClientSession()
        await super().start(token)

    def get_log_channel(self):
        return self.get_channel(906683175571435550)
    
    def is_blacklisted(self, user_id: int) -> bool:
        return user_id in self.blacklists

    def add_owner(self, user_id: int):
        self.owner_ids.append(user_id)

    def remove_owner(self, user_id: int):
        if user_id == 412734157819609090:
            return
        
        try:
            self.owner_ids.remove(user_id)
        except ValueError:
            return

    def format_print(self, text):
        format = datetime.datetime.utcnow().strftime("%x | %X") + f" | {text}"
        return format

class BlacklistedError(commands.CheckFailure):
    pass

class MaintenanceError(commands.CheckFailure):
    pass