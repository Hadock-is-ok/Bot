import logging
import os
import pathlib
from typing import Any, ClassVar, Dict, List, NamedTuple, Optional

import aiohttp
import asyncpg
import revolt
import datetime
from cachetools import TTLCache
from revolt.ext import commands

from utils.context import AloneContext


class TodoData(NamedTuple):
    content: str
    jump_url: str


class AloneBot(commands.CommandsClient):
    INITAL_EXTENSIONS: List[str] = []
    DEFAULT_PREFIXES: ClassVar[List[str]] = ["Alone", "alone"]
    owner_ids: List[str]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(
            command_prefix=self.get_prefix,
            strip_after_prefix=True,
            case_insensitive=True,
            *args,
            **kwargs,
        )

        self.owner_ids = []
        self.blacklisted_users: Dict[str, str] = {}
        self.afk_users: Dict[str, str] = {}
        self.todos: Dict[str, List[TodoData]] = {}
        self.user_prefixes: Dict[str, List[str]] = {}
        self.server_prefixes: Dict[str, str] = {}
        self.client_messages_cache: TTLCache[revolt.Message, revolt.Message] = TTLCache(maxsize=2000, ttl=300.0)

        self.cooldown: commands.CooldownMapping[revolt.Message] = commands.CooldownMapping.from_cooldown(
            1, 1.5, commands.BucketType.member
        )
        self.support_server: str = os.environ["bot_server"]
        self.emoji_server: str = os.environ["emoji_server"]
        self._emojis: dict[str, revolt.Emoji] = {}
        self.log_webhook: str = os.environ["webhook_url"]
        self.github_link: str = os.environ["github"]
        self.maintenance: Optional[str] = None

        self.command_counter: int = 0
        self.launch_time = datetime.datetime.now(tz=datetime.UTC)
        self.jeyy_key = os.environ["jeyy_key"]

    async def get_prefix(self, message: revolt.Message, /) -> List[str] | str:
        prefixes: List[str] = self.DEFAULT_PREFIXES.copy()
        user_prefixes: List[str] | None = self.user_prefixes.get(message.author.id)
        if user_prefixes:
            prefixes.extend(user_prefixes)

        if message.server and (server_prefix := self.server_prefixes.get(message.server.id, None)):
            prefixes.append(server_prefix)

        return commands.(*prefixes)(self, message)

    async def get_context(self, message: revolt.Message, *, cls: Any = AloneContext) -> Any:
        return super().get_context(message)

    async def setup_hook(self) -> None:
        self.db: asyncpg.Pool[Any] | Any = await asyncpg.create_pool(
            host=os.environ["database_ip"],
            port=int(os.environ["database_port"]),
            user=os.environ["database_user"],
            password=os.environ["database_password"],
            database=os.environ["database_name"],
        )
        if not self.db:
            raise RuntimeError("Couldn't connect to database!")

        with open("schema.sql") as file:
            await self.db.execute(file.read())

        for emoji in (await self.fetch_server(self.emoji_server)).emojis:
            self._emojis[emoji.name] = emoji

        self.load_extension("jishaku")
        for file in pathlib.Path('ext').glob('**/*.py'):
            *tree, _ = file.parts
            if file.stem == "__init__":
                continue

            try:
                self.load_extension(f"{'.'.join(tree)}.{file.stem}")
            except Exception as error:
                self.logger.error(error, exc_info=error)
            else:
                self.INITAL_EXTENSIONS.append(f"{'.'.join(tree)}.{file.stem}")

        records: list[Any]
        records = await self.db.fetch("SELECT user_id, array_agg(prefix) AS prefixes FROM prefix GROUP BY user_id")
        self.user_prefixes = {user_id: prefix for user_id, prefix in records}

        records = await self.db.fetch("SELECT * FROM servers")
        self.server_prefixes = {server_id: prefix for server_id, prefix in records}

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
        revolt.utils.setup_logging(handler=logging.FileHandler("client.log"))
        self.logger: logging.Logger = logging.getLogger("revolt")
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        await super().start()

    async def get_log_channel(self) -> revolt.Channel:
        return await self.fetch_channel(os.environ["log_channel"])

    def is_blacklisted(self, user_id: str) -> bool:
        return user_id in self.blacklisted_users
