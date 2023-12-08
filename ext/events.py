from __future__ import annotations

from typing import TYPE_CHECKING, Any, List

import revolt
from revolt.ext import commands

if TYPE_CHECKING:
    from client import AloneBot


class Events(commands.Cog[AloneBot]):
    def __init__(self, client: AloneBot) -> None:
        self.client: AloneBot = client

    @commands.Cog.listener()
    async def on_server_join(self, server: revolt.Server) -> None:
        channel: Any = self.client.get_log_channel()
        bots: int = sum(member.client for member in server.members)

        server_metadata: list[str] = [
            f'Owner: {server.owner}',
            f'Name: {server.name}',
            f'Members: {len(server.members)}',
            f'Bots: {bots}',
        ]

        embed: revolt.SendableEmbed = revolt.SendableEmbed(
            title="I joined a new server!",
            description='\n'.join(server_metadata),
            colour="0x5FAD68",
        )

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_server_remove(self, server: revolt.Server) -> None:
        channel: Any = self.client.get_log_channel()
        bots: int = sum(member.client for member in server.members)

        server_metadata: List[str] = [
            f'Owner: {server.owner}',
            f'Name: {server.name}',
            f'Members: {len(server.members)}',
            f'Bots: {bots}',
        ]

        embed: revolt.SendableEmbed = revolt.SendableEmbed(
            title="I have left a server",
            description='\n'.join(server_metadata),
            colour="0xFF0000",
        )

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: revolt.Message) -> None:
        if not self.client.user:
            # Asserting here will break as the client can receieve events before it has hit
            # on_ready and cached the user.
            return

        if message.content == f"<@{self.client.user.id}>" and not message.author.client:
            await message.send("Hello, I am Alone Bot, my prefix is alone.")

    @commands.Cog.listener("on_message")
    async def afk_check(self, message: revolt.Message) -> None:
        for mention in message.mentions:
            if mention.id in self.client.afk_users and not message.author.client:
                await message.send(
                    f"I'm sorry, but <@{mention.id}> went afk for {self.client.afk_users[mention.id]}.",
                    mention_author=False,
                )

        if message.author.id in self.client.afk_users:
            self.client.afk_users.pop(message.author.id)
            await self.client.db.execute("DELETE FROM afk WHERE user_id = $1", message.author.id)

            await message.send(f"Welcome back {message.author.display_name}!", mention_author=False)

    @commands.Cog.listener()
    async def on_message_edit(self, before: revolt.Message, after: revolt.Message) -> None:
        if not self.client.bot_messages_cache.get(before):
            return await self.client.process_commands(after)

        message: revolt.Message | None = self.client.bot_messages_cache.get(before)

        if not after.content.startswith(tuple(await self.client.get_prefix(before))):
            self.client.bot_messages_cache.pop(before)
            if not message:
                return

            await message.delete()
        else:
            await self.client.process_commands(after)

    @commands.Cog.listener()
    async def on_message_delete(self, message: revolt.Message) -> None:
        if self.client.bot_messages_cache.get(message):
            bot_message: revolt.Message = self.client.bot_messages_cache.pop(message)
            await bot_message.delete()

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: revolt.Member, before: revolt.VoiceState, after: revolt.VoiceState
    ) -> None:
        if not before.channel:
            return self.client.dispatch("voice_join", member, after)

        elif not after.channel:
            return self.client.dispatch("voice_leave", member, before)


async def setup(client: AloneBot) -> None:
    client.add_cog(Events(client))
