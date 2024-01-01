from __future__ import annotations

from typing import TYPE_CHECKING, Any, List

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from bot import AloneBot


class Events(commands.Cog):
    def __init__(self, bot: AloneBot) -> None:
        self.bot: AloneBot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        channel: Any = self.bot.get_log_webhook()
        bots: int = sum(member.bot for member in guild.members)

        guild_metadata: list[str] = [
            f"Owner: {guild.owner}",
            f"Name: {guild.name}",
            f"Members: {guild.member_count}",
            f"Bots: {bots}",
            f"Nitro Tier: {guild.premium_tier}",
        ]

        embed: discord.Embed = discord.Embed(
            title="I joined a new guild!",
            description="\n".join(guild_metadata),
            color=0x5FAD68,
        )

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        channel: Any = self.bot.get_log_webhook()
        bots: int = sum(member.bot for member in guild.members)

        guild_metadata: List[str] = [
            f"Owner: {guild.owner}",
            f"Name: {guild.name}",
            f"Members: {guild.member_count}",
            f"Bots: {bots}",
            f"Nitro Tier: {guild.premium_tier}",
        ]

        embed: discord.Embed = discord.Embed(
            title="I have left a guild",
            description="\n".join(guild_metadata),
            color=0xFF0000,
        )

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not self.bot.user:
            # Asserting here will break as the client can receieve events before it has hit
            # on_ready and cached the user.
            return

        if message.content == f"<@{self.bot.user.id}>" and not message.author.bot:
            await message.reply("Hello, I am Alone Bot, my prefix is alone.")

    @commands.Cog.listener("on_message")
    async def afk_check(self, message: discord.Message) -> None:
        for mention in message.mentions:
            if mention.id in self.bot.afk_users and not message.author.bot:
                await message.reply(
                    f"I'm sorry, but <@{mention.id}> went afk for {self.bot.afk_users[mention.id]}.",
                    mention_author=False,
                )

        if message.author.id in self.bot.afk_users:
            self.bot.afk_users.pop(message.author.id)
            await self.bot.db.execute("DELETE FROM afk WHERE user_id = $1", message.author.id)

            await message.reply(f"Welcome back {message.author.display_name}!", mention_author=False)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if not self.bot.bot_messages_cache.get(before):
            return await self.bot.process_commands(after)

        message: discord.Message | None = self.bot.bot_messages_cache.get(before)

        if not after.content.startswith(tuple(await self.bot.get_prefix(before))):
            self.bot.bot_messages_cache.pop(before)
            if not message:
                return

            await message.delete()
        else:
            await self.bot.process_commands(after)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if self.bot.bot_messages_cache.get(message):
            bot_message: discord.Message = self.bot.bot_messages_cache.pop(message)
            await bot_message.delete()

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if not before.channel:
            return self.bot.dispatch("voice_join", member, after)

        elif not after.channel:
            return self.bot.dispatch("voice_leave", member, before)


async def setup(bot: AloneBot) -> None:
    await bot.add_cog(Events(bot))
