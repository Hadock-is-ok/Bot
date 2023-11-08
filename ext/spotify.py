import random
import typing

import discord
from discord.ext import commands

if typing.TYPE_CHECKING:
    from bot import AloneBot


class SpotifyCog(commands.Cog):
    def __init__(self, bot: AloneBot) -> None:
        self.bot: AloneBot = bot

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member) -> None:
        if not before.id == 412734157819609090:
            return
        if before.activities == after.activities or not after.activities:
            return

        music_channel: discord.TextChannel | None = self.bot.get_channel(1130970237223829625)  # type: ignore
        if not music_channel:
            return

        spotify: discord.Spotify | None = discord.utils.find(lambda activity: isinstance(activity, discord.Spotify), after.activities)  # type: ignore
        if not spotify:
            return

        if not random.randint(1, 10) == random.randint(1, 10):
            return

        embed: discord.Embed = discord.Embed(
            title="Hadock's Spotify status", description=f"[{spotify.track_url}]({spotify.title})", color=spotify.color
        )
        embed.set_thumbnail(url=spotify.album_cover_url)
        await music_channel.send(embed=embed)


async def setup(bot: AloneBot) -> None:
    await bot.add_cog(SpotifyCog(bot))
