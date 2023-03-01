from typing import Any

import discord
from discord.ext import commands
from typing_extensions import Self

from utils import AloneBot


class Events(commands.Cog):
    def __init__(self: Self, bot: AloneBot) -> None:
        self.bot: AloneBot = bot

    @commands.Cog.listener()
    async def on_ready(self: Self) -> None:
        fmt: str = self.bot.format_print("Alone Bot")
        assert self.bot.user

        print(
            f"{fmt} | Ready",
            "|--------------------------------------------------|",
            "Name: Alone Bot",
            f"ID: {self.bot.user.id}",
            f"Users: {len(self.bot.users)}",
            f"Guilds: {len(self.bot.guilds)}",
            f"Support Server: {self.bot.support_server}",
            "|--------------------------------------------------|",
            sep="\n",
        )

    @commands.Cog.listener()
    async def on_guild_join(self: Self, guild: discord.Guild) -> None:
        channel: Any = self.bot.get_log_channel()
        bots: int = sum(member.bot for member in guild.members)
        embed: discord.Embed = discord.Embed(
            title="I joined a new guild!",
            description=f"""
Owner: {guild.owner}
Name: {guild.name}
Members: {guild.member_count}
Bots: {bots}
Nitro Tier: {guild.premium_tier}""",
            color=0x5FAD68,
        )

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self: Self, guild: discord.Guild) -> None:
        channel: Any = self.bot.get_log_channel()
        bots: int = sum(member.bot for member in guild.members)
        embed: discord.Embed = discord.Embed(
            title="I have left a guild",
            description=f"""
Owner: {guild.owner}
Name: {guild.name}
Members: {guild.member_count}
Bots: {bots}
Nitro Tier: {guild.premium_tier}""",
            color=0xFF0000,
        )

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self: Self, message: discord.Message) -> None:
        assert self.bot.user
        if message.content == f"<@{self.bot.user.id}>" and not message.author.bot:
            await message.reply("Hello, I am Alone Bot, my prefix is alone.")

    @commands.Cog.listener("on_message")
    async def afk_check(self: Self, message: discord.Message) -> None:
        for mention in message.mentions:
            if mention.id in self.bot.afk_users and not message.author.bot:
                assert message.guild
                user: discord.Member | None = message.guild.get_member(mention.id)
                assert user

                await message.reply(
                    f"I'm sorry, but {user.display_name} went afk for {self.bot.afk_users[mention.id]}.",
                    mention_author=False,
                )

        if message.author.id in self.bot.afk_users:
            self.bot.afk_users.pop(message.author.id)
            await self.bot.db.execute("DELETE FROM afk WHERE user_id = $1", message.author.id)

            await message.reply(f"Welcome back {message.author.display_name}!", mention_author=False)

    @commands.Cog.listener()
    async def on_message_edit(self: Self, before: discord.Message, after: discord.Message) -> None:
        if not self.bot.bot_messages_cache.get(before):
            return await self.bot.process_commands(after)

        message: discord.Message | None = self.bot.bot_messages_cache.get(before)

        if not after.content.startswith(tuple(await self.bot.get_prefix(before))):
            assert message
            await message.delete()
            self.bot.bot_messages_cache.pop(before)
        else:
            await self.bot.process_commands(after)

    @commands.Cog.listener()
    async def on_message_delete(self: Self, message: discord.Message) -> None:
        if self.bot.bot_messages_cache.get(message):
            bot_message: discord.Message = self.bot.bot_messages_cache.pop(message)
            await bot_message.delete()

    @commands.Cog.listener()
    async def on_voice_state_update(
        self: Self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ) -> None:
        if not before.channel:
            return self.bot.dispatch("voice_join", member, after)

        elif not after.channel:
            return self.bot.dispatch("voice_leave", member, before)


async def setup(bot: AloneBot) -> None:
    await bot.add_cog(Events(bot))
