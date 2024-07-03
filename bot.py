import logging
import os
import pathlib
from typing import Any, ClassVar, Dict, List, NamedTuple, Optional

import aiohttp
import asyncpg
import discord
from cachetools import TTLCache
from discord.ext import commands

from utils.context import AloneContext


class TodoData(NamedTuple):
    content: str
    jump_url: str


class AloneBot(commands.Bot):
    INITIAL_EXTENSIONS: List[str] = []
    DEFAULT_PREFIXES: ClassVar[List[str]] = ["Alone", "alone"]
    owner_ids: List[int]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(
            command_prefix=self.get_prefix,  # type: ignore
            strip_after_prefix=True,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=False, replied_user=False),
            case_insensitive=True,
            *args,
            **kwargs,
        )

        self.owner_ids = [412734157819609090]  # type: ignore
        self.blacklisted_users: Dict[int, str] = {}
        self.afk_users: Dict[int, str] = {}
        self.todos: Dict[int, List[TodoData]] = {}
        self.user_prefixes: Dict[int, List[str]] = {}
        self.guild_prefixes: Dict[int, str] = {}
        self.bot_messages_cache: TTLCache[discord.Message, discord.Message] = TTLCache(maxsize=2000, ttl=300.0)

        self.cooldown: commands.CooldownMapping[discord.Message] = commands.CooldownMapping.from_cooldown(
            1, 1.5, commands.BucketType.member
        )
        self.support_server: str = os.environ["bot_guild"]
        self.emoji_guild: int = int(os.environ["emoji_guild"])
        self.EMOJIS: dict[str, discord.Emoji] = {}
        self.log_webhook: str = os.environ["webhook_url"]
        self.github_link: str = os.environ["github"]
        self.maintenance: Optional[str] = None

        self.command_counter: int = 0
        self.launch_time = discord.utils.utcnow()
        self.jeyy_key = os.environ["jeyy_key"]

    async def get_prefix(self, message: discord.Message, /) -> List[str] | str:
        prefixes: List[str] = self.DEFAULT_PREFIXES.copy()
        if user_prefixes := self.user_prefixes.get(message.author.id):
            prefixes.extend(user_prefixes)

        if message.guild and (guild_prefix := self.guild_prefixes.get(message.guild.id)):
            prefixes.append(guild_prefix)

        return commands.when_mentioned_or(*prefixes)(self, message)

    async def get_context(self, message: discord.Message, *, cls: Any = AloneContext) -> Any:
        return await super().get_context(message, cls=cls)

    async def setup_hook(self) -> None:
        self.db: asyncpg.Pool[Any] | Any = await asyncpg.create_pool(
            host=os.environ["database_ip"],
            user=os.environ["database_user"],
            password=os.environ["database_password"],
            database=os.environ["database_name"],
        )
        if not self.db:
            raise RuntimeError("Couldn't connect to database!")

        with open("schema.sql") as file:
            await self.db.execute(file.read())

        for emoji in (await self.fetch_guild(self.emoji_guild)).emojis:
            self.EMOJIS[emoji.name] = emoji

        await self.load_extension("jishaku")
        for file in pathlib.Path("ext").glob("**/*.py"):
            *tree, _ = file.parts
            if file.stem == "__init__":
                continue

            try:
                await self.load_extension(f"{'.'.join(tree)}.{file.stem}")
            except Exception as error:
                self.logger.error(error, exc_info=error)
            else:
                self.INITIAL_EXTENSIONS.append(f"{'.'.join(tree)}.{file.stem}")

        records: list[Any]
        records = await self.db.fetch("SELECT user_id, array_agg(prefix) AS prefixes FROM prefix GROUP BY user_id")
        self.user_prefixes = {user_id: prefix for user_id, prefix in records}

        records = await self.db.fetch("SELECT * FROM guilds")
        self.guild_prefixes = {guild_id: prefix for guild_id, prefix in records}

        records = await self.db.fetch("SELECT * FROM todo")
        for user_id, content, jump_url in records:
            self.todos.setdefault(user_id, []).append(TodoData(content, jump_url))

        records = await self.db.fetch("SELECT * FROM afk")
        self.afk_users = {user_id: reason for user_id, reason in records}

    async def close(self) -> None:
        await self.session.close()
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
