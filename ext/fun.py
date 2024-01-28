from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Optional

import discord
from discord.ext import commands
from typing_extensions import LiteralString

from utils import NoSubredditFound

if TYPE_CHECKING:
    from bot import AloneBot
    from utils import AloneContext


class Fun(commands.Cog):
    def __init__(self, bot: AloneBot) -> None:
        self.bot: AloneBot = bot

    async def fetch_subreddit(self, subreddit: str, sort: str = "hot") -> dict[str, Any]:
        async with self.bot.session.get(f"https://old.reddit.com/r/{subreddit}/{sort}.json") as response:
            data: Any = await response.json()
            try:
                data["data"]
            except KeyError:
                raise NoSubredditFound("No subreddit by that name.")

        return random.choice(data["data"]["children"])["data"]

    @commands.command(aliases=["define"])
    async def urban(self, ctx: AloneContext, *, word: Optional[str]) -> discord.Message | None:
        if not word:
            return await ctx.reply("You need to give me a word to look up!")

        async with self.bot.session.get("https://api.urbandictionary.com/v0/define", params={"term": word}) as response:
            data: Any = await response.json()
            try:
                word_info: Any = data["list"][0]
            except IndexError:
                return await ctx.reply("I couldn't find a definition for that word.")
            else:
                definition, name = word_info["definition"], word_info["word"]

        await ctx.reply(embed=discord.Embed(title=name, description=definition))

    @commands.command()
    async def pp(self, ctx: AloneContext, member: Optional[discord.Member] = commands.Author) -> None:
        pp: LiteralString = "=" * random.randint(1, 50)

        await ctx.reply(embed=discord.Embed(title=f"{member}'s pp", description=f"8{pp}D\n({len(pp)}cm)"))

    @commands.command()
    async def meme(self, ctx: AloneContext) -> None:
        data: dict[str, Any] = await self.fetch_subreddit("dankmemes")
        embed: discord.Embed = discord.Embed(title=data["title"], url=data["url"]).set_image(url=data["url"])

        await ctx.reply(embed=embed)

    @commands.command()
    async def waifu(self, ctx: AloneContext) -> None:
        async with self.bot.session.get("https://api.waifu.im/search/", params={"included_tags": "waifu"}) as response:
            hori: Any = await response.json()
            image: Any = hori["images"][0]
            waifu_url: Any = image["url"]

        embed: discord.Embed = discord.Embed(
            title=f"Here's your waifu, {ctx.author.name}",
            description=f"[Here's the link]({waifu_url})",
        )

        embed.set_image(url=waifu_url)
        await ctx.reply(embed=embed)

    @commands.command()
    async def reddit(self, ctx: AloneContext, subreddit: Optional[str]) -> discord.Message | None:
        if not subreddit:
            return await ctx.reply("You should give me a subreddit to search!")

        data: dict[str, Any] = await self.fetch_subreddit(subreddit)
        if not ctx.channel:
            pass
        elif data["over_18"] and not ctx.channel.is_nsfw():  # type: ignore
            return await ctx.reply("This post is nsfw! I cannot send this in a normal channel!")

        embed: discord.Embed = discord.Embed(title=data["title"], url=data["url"]).set_image(url=data["url"])
        await ctx.reply(embed=embed)


async def setup(bot: AloneBot) -> None:
    await bot.add_cog(Fun(bot))
