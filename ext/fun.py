import random
from typing import Any, Dict, Optional

import discord
from discord.ext import commands
from typing_extensions import LiteralString, Self

from utils import AloneBot, AloneContext


class Fun(commands.Cog):
    def __init__(self: Self, bot: AloneBot) -> None:
        self.bot: AloneBot = bot

    async def fetch_subreddit(self: Self, subreddit: str, sort: str = "hot") -> Dict[str, Any]:
        async with self.bot.session.get(
            f"https://www.reddit.com/r/{subreddit}/{sort}.json",
            headers={"User-Agent": "Alone Bot"},
        ) as response:
            data: Any = await response.json()

        return random.choice(data["data"]["children"])["data"]

    @commands.command(aliases=["define"])
    async def urban(self: Self, ctx: AloneContext, *, word: str) -> None:
        async with self.bot.session.get("https://api.urbandictionary.com/v0/define", params={"term": word}) as response:
            data: Any = await response.json()
            word_info: Any = data["list"][0]
        definition, name = word_info["definition"], word_info["word"]

        await ctx.reply(embed=discord.Embed(title=name, description=definition))

    @commands.command()
    async def pp(self: Self, ctx: AloneContext, member: Optional[discord.Member] = commands.Author) -> None:
        pp: LiteralString = "=" * random.randint(1, 50)

        await ctx.reply(embed=discord.Embed(title=f"{member}'s pp", description=f"8{pp}D\n({len(pp)}cm)"))

    @commands.command()
    async def meme(self: Self, ctx: AloneContext) -> None:
        data: Dict[str, Any] = await self.fetch_subreddit("dankmemes")
        embed: discord.Embed = discord.Embed(title=data["title"], url=data["url"]).set_image(url=data["url"])

        await ctx.reply(embed=embed)

    @commands.command()
    async def waifu(self: Self, ctx: AloneContext) -> None:
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
    async def reddit(self: Self, ctx: AloneContext, subreddit: Optional[str]) -> discord.Message | None:
        if not subreddit:
            return await ctx.reply("You should give me a subreddit to search!")

        data: Dict[str, Any] = await self.fetch_subreddit(subreddit)
        if data["over_18"] and not ctx.channel.is_nsfw(): # type: ignore
            return await ctx.reply("This post is nsfw! I cannot send this in a normal channel!")

        embed: discord.Embed = discord.Embed(title=data["title"], url=data["url"]).set_image(url=data["url"])
        await ctx.reply(embed=embed)


async def setup(bot: AloneBot) -> None:
    await bot.add_cog(Fun(bot))
