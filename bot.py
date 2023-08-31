from __future__ import annotations

import datetime
import logging
import os
import pathlib
from typing import Any, ClassVar, Dict, List, NamedTuple, Optional, TypedDict

import aiohttp
import asyncpg
import discord
from cachetools import TTLCache
from discord.ext import commands

from utils.context import AloneContext


class TODO_DATA(NamedTuple):
    content: str
    jump_url: str


class DEFAULT_GUILD_CONFIG(TypedDict):
    prefix: str
    enabled: bool
    voice_channel: int
    voice_category: int
    community_voice_channels: dict[int, int]


BOILERPLATE_GUILD_CONFIG: DEFAULT_GUILD_CONFIG = {
    "prefix": "Alone",
    "enabled": False,
    "voice_channel": 0,
    "voice_category": 0,
    "community_voice_channels": {},
}


class AloneBot(commands.AutoShardedBot):
    INITAL_EXTENSIONS: List[str] = []
    DEFAULT_PREFIXES: ClassVar[List[str]] = ["Alone", "alone"]
    owner_ids: List[int]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(
            command_prefix=self.get_prefix,  # type: ignore
            strip_after_prefix=True,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=False, replied_user=False),
            case_insensitive=True,
            owner_ids=[412734157819609090],
            *args,
            **kwargs,
        )

        self.blacklisted_users: Dict[int, str] = {}
        self.bypass_cooldown_users: List[int] = []
        self.afk_users: Dict[int, str] = {}
        self.todos: Dict[int, List[TODO_DATA]] = {}
        self.user_prefixes: Dict[int, List[str]] = {}
        self.guild_configs: Dict[int, DEFAULT_GUILD_CONFIG] = {}
        self.bot_messages_cache: TTLCache[discord.Message, discord.Message] = TTLCache(maxsize=2000, ttl=300.0)

        self.cooldown: commands.CooldownMapping[discord.Message] = commands.CooldownMapping.from_cooldown(
            1, 1.5, commands.BucketType.member
        )
        self.support_server: str = os.environ["bot_guild"]
        self.github_link: str = os.environ["github"]
        self.maintenance: Optional[str] = None

        self.command_counter: int = 0
        self.launch_time: datetime.datetime = datetime.datetime.utcnow()

    async def get_prefix(self, message: discord.Message, /) -> List[str] | str:
        prefixes: List[str] = self.DEFAULT_PREFIXES.copy()
        user_prefixes: List[str] | None = self.user_prefixes.get(message.author.id)
        if user_prefixes:
            prefixes.extend(user_prefixes)

        if message.guild and not (guild_prefix := self.guild_configs.get(message.guild.id, {}).get("prefix")) is None:
            prefixes.append(guild_prefix)

        if not message.guild or message.author.id in self.owner_ids:
            prefixes.append("")

        return commands.when_mentioned_or(*prefixes)(self, message)

    async def get_context(self, message: discord.Message, *, cls: Any = AloneContext) -> Any:
        return await super().get_context(message, cls=cls)

    async def setup_hook(self) -> None:
        self.db: asyncpg.Pool[Any] | Any = await asyncpg.create_pool(
            host=os.environ["db_ip"],
            port=int(os.environ["db_port"]),
            user=os.environ["db_user"],
            password=os.environ["db_pwd"],
            database=os.environ["database"],
        )
        if not self.db:
            raise RuntimeError("Couldn't connect to database!")
        
        # Loading schemal.sql
        with open("schema.sql") as file:
            await self.pool.execute(file.read())

        await self.load_extension("jishaku")
        for file in pathlib.Path('ext').glob('**/*.py'):
            *tree, _ = file.parts
            if file.stem == "__init__":
                continue

            try:
                await self.load_extension(f"{'.'.join(tree)}.{file.stem}")
            except Exception as error:
                self.logger.error(error, exc_info=error)
            else:
                self.INITAL_EXTENSIONS.append(f"{'.'.join(tree)}.{file.stem}")

        log_webhook: str | None = os.getenv("webhook_url")
        if not log_webhook:
            raise RuntimeError("Webhook isn't set in .env!")
        self.log_webhook: str = log_webhook

        records: list[Any]
        records = await self.db.fetch("SELECT user_id, array_agg(prefix) AS prefixes FROM prefix GROUP BY user_id")
        self.user_prefixes = {user_id: prefix for user_id, prefix in records}

        records = await self.db.fetch("SELECT * FROM guilds")
        for guild_id, prefix, voice_channel, voice_category, enabled in records:
            guild = self.guild_configs.setdefault(guild_id, BOILERPLATE_GUILD_CONFIG)
            guild["prefix"] = prefix
            guild["voice_channel"] = voice_channel
            guild["voice_category"] = voice_category
            guild["enabled"] = enabled

        records = await self.db.fetch("SELECT * FROM voice")
        for guild_id, user_id, channel_id in records:
            guild: DEFAULT_GUILD_CONFIG = self.guild_configs.setdefault(guild_id, BOILERPLATE_GUILD_CONFIG)
            guild.setdefault("community_voice_channels", {})[channel_id] = user_id

        records = await self.db.fetch("SELECT * FROM todo")
        for user_id, content, jump_url in records:
            self.todos.setdefault(user_id, []).append(TODO_DATA(content, jump_url))

        records = await self.db.fetch("SELECT * FROM afk")
        self.afk_users = {user_id: reason for user_id, reason in records}

        records = await self.db.fetch("SELECT * FROM mentions")
        for user_id in records:
            self.bypass_cooldown_users.append(user_id)

    async def close(self) -> None:
        await self.session.close()

        if self.db:
            await self.db.close()

        await super().close()

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        discord.utils.setup_logging(handler=logging.FileHandler("bot.log"))
        self.logger: logging.Logger = logging.getLogger("discord")
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        await super().start(token)

    def get_log_webhook(self) -> discord.Webhook:
        return discord.Webhook.from_url(self.log_webhook, session=self.session, bot_token=os.getenv("token"))

    def is_blacklisted(self, user_id: int) -> bool:
        return user_id in self.blacklisted_users

    def add_owner(self, user_id: int) -> None:
        self.owner_ids.append(user_id)

    def remove_owner(self, user_id: int) -> str | None:
        try:
            self.owner_ids.remove(user_id)
        except ValueError:
            return "There's no owner with that ID!"

    def format_print(self, text: str) -> str:
        fmt: str = datetime.datetime.utcnow().strftime("%x | %X") + f" | {text}"
        return fmt
