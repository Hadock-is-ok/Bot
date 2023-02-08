from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Optional, NamedTuple, TypedDict

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
    content: str
    jump_url: str

class DEFAULT_GUILD_CONFIG(TypedDict):
    prefix: str
    enabled: bool
    voice_channel: int
    voice_category: int
    community_voice_channels: dict[int, int]

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
        "ext.voice",
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

        self.blacklisted_users: Dict[int, str] = {}
        self.afk_users: Dict[int, str] = {}
        self.todos: Dict[int, List[Todo]] = {}
        self.user_prefixes: Dict[int, List[str]] = {}
        self.guild_configs: Dict[int, DEFAULT_GUILD_CONFIG] = {}
        self.bot_messages_cache: TTLCache[str, discord.Message] = TTLCache(maxsize=2000, ttl=300.0)

        self.support_server: str = os.environ["bot_guild"]
        self.maintenance: Optional[str] = None

        self.command_counter: int = 0
        self.launch_time: datetime.datetime = datetime.datetime.utcnow()

    async def get_prefix(self, message: discord.Message):
        prefixes: List[str] = self.DEFAULT_PREFIXES.copy()
        user_prefixes = self.user_prefixes.get(message.author.id)
        if user_prefixes:
            prefixes.extend(user_prefixes)

        if message.guild and not (self.guild_configs.get(message.guild.id, {}).get("prefix", None)) == None:
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

        records = await self.db.fetch("SELECT * FROM guilds")
        for guild_id, prefix, voice_channel, voice_category in records:
            self.guild_config.get(guild_id, {}).setdefault("prefix", prefix)
            self.guild_config.get(guild_id, {}).setdefault("voice_channel", voice_channel)
            self.guild_config.get(guild_id, {}).setdefault("voice_category", voice_category)
        
        records = await self.db.fetch("SELECT * FROM voice")
        for guild_id, user_id, channel_id, enabled in records:
            self.guild_config.get(guild_id, {}).get("community_voice_channels", {})[channel_id] = user_id
            self.guild_config.get(guild_id, {}).setdefault("enabled", enabled)

        records = await self.db.fetch("SELECT * FROM todo")
        for user_id, content, jump_url in records:
            self.todos.setdefault(user_id, []).append(Todo(content, jump_url))

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
        return user_id in self.blacklisted_users

    def add_owner(self, user_id: int):
        self.owner_ids.append(user_id)

    def remove_owner(self, user_id: int):
        try:
            self.owner_ids.remove(user_id)
        except ValueError:
            return "There's no owner with that ID!"

    def format_print(self, text):
        format = datetime.datetime.utcnow().strftime("%x | %X") + f" | {text}"
        return format

class BlacklistedError(commands.CheckFailure):
    pass

class MaintenanceError(commands.CheckFailure):
    pass