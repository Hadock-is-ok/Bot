from typing import Any, Dict, Optional

import discord, random, os, aiohttp
from discord.ext import commands
from utils import AloneBot

class Fun(commands.Cog):
    def __init__(self, bot: AloneBot):
        self.bot = bot

    async def fetch_subreddit(self, subreddit: str, sort: str = "hot") -> Dict[str, Any]:
        async with self.bot.session.get(
            f"https://www.reddit.com/r/{subreddit}/{sort}.json", headers={"User-Agent": "Alone Bot"}
        ) as response:
            data = await response.json()

        return random.choice(data["data"]["children"])["data"]

    @commands.command(aliases=["define"])
    async def urban(self, ctx: commands.Context, *, word: str):
        async with self.bot.session.get(
            f"https://api.urbandictionary.com/v0/define", params={"term": word}
        ) as response:
            data = await response.json()
            word = data["list"][0]
        definition, name = word["definition"], word["word"]

        await ctx.reply(embed=discord.Embed(title=name, description=definition))

    @commands.command()
    async def pp(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        member = member or ctx.author # type: ignore
        pp = "=" * random.randint(1, 50)

        await ctx.reply(
            embed=discord.Embed(
                title=f"{member}'s pp", description=f"8{pp}D\n({len(pp)}cm)"
            )
        )

    @commands.command()
    async def meme(self, ctx: commands.Context):
        data = await self.fetch_subreddit("dankmemes")
        embed = discord.Embed(title=data["title"], url=data["url"]).set_image(url=data["url"])

        await ctx.reply(embed=embed)

    @commands.command()
    async def waifu(self, ctx: commands.Context):
        async with self.bot.session.get(
            f"https://api.waifu.im/search/", params={"included_tags": "waifu"}
        ) as response:
            hori = await response.json()
            image = hori["images"][0]
            waifu_url = image["url"]
        embed = discord.Embed(
            title=f"Here's your waifu, {ctx.author.name}",
            description=f"[Here's the link]({waifu_url})",
        )
        embed.set_image(url=waifu_url)
        await ctx.reply(embed=embed)
    
    @commands.command()
    async def reddit(self, ctx: commands.Context, subreddit: Optional[str]):
        data = await self.fetch_subreddit(subreddit)
        if data["over_18"]:
            return await ctx.reply("This post is nsfw! I cannot send this in a normal channel!")
        embed = discord.Embed(title=data["title"], url=data["url"]).set_image(url=data["url"])
        await ctx.reply(embed=embed)

async def setup(bot: AloneBot):
    await bot.add_cog(Fun(bot))
