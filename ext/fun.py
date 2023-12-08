from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

import revolt
from revolt.ext import commands
from typing_extensions import LiteralString

from utils import NoSubredditFound

if TYPE_CHECKING:
    from client import AloneBot
    from utils import AloneContext


class Fun(commands.Cog[AloneBot]):
    def __init__(self, client: AloneBot) -> None:
        self.client: AloneBot = client

    async def fetch_subreddit(self, subreddit: str, sort: str = "hot") -> Dict[str, Any]:
        async with self.client.session.get(
            f"https://www.reddit.com/r/{subreddit}/{sort}.json",
            headers={"User-Agent": "Alone Bot"},
        ) as response:
            data: Any = await response.json()
            try:
                data["data"]
            except KeyError:
                raise NoSubredditFound("No subreddit by that name.")

        return random.choice(data["data"]["children"])["data"]
    
    async def upload_image(self, client: revolt.Client, url: str) -> str:
        async with client.session.get(url) as response:
            data: Any = await response.read()

        upload = await self.client.upload_file(data, tag="attachments")
        return str(upload)

    @commands.command(aliases=["define"])
    async def urban(self, ctx: AloneContext, *, word: Optional[str]) -> revolt.Message | None:
        if not word:
            return await ctx.send("You need to give me a word to look up!")

        async with self.client.session.get("https://api.urbandictionary.com/v0/define", params={"term": word}) as response:
            data: Any = await response.json()
            try:
                word_info: Any = data["list"][0]
            except IndexError:
                return await ctx.send("I couldn't find a definition for that word.")
            else:
                definition, name = word_info["definition"], word_info["word"]

        await ctx.send(embed=revolt.SendableEmbed(title=name, description=definition))

    @commands.command()
    async def pp(self, ctx: AloneContext, member: Union[revolt.Member, revolt.User]) -> None:
        member = member or ctx.author
        pp: LiteralString = "=" * random.randint(1, 50)

        await ctx.send(embed=revolt.SendableEmbed(title=f"{member.name}'s pp", description=f"8{pp}D\n({len(pp)}cm)"))

    @commands.command()
    async def meme(self, ctx: AloneContext) -> None:
        data: Dict[str, Any] = await self.fetch_subreddit("dankmemes")
        upload_id = await self.upload_image(self.client, data["url"])
        embed: revolt.SendableEmbed = revolt.SendableEmbed(title=data["title"], url=data["url"], media=upload_id)

        await ctx.send(embed=embed)

    @commands.command()
    async def waifu(self, ctx: AloneContext) -> None:
        async with self.client.session.get("https://api.waifu.im/search/", params={"included_tags": "waifu"}) as response:
            hori: Any = await response.json()
            image: Any = hori["images"][0]
            waifu_url: Any = image["url"]

        upload_id = await self.upload_image(self.client, waifu_url)
        embed: revolt.SendableEmbed = revolt.SendableEmbed(
            title=f"Here's your waifu, {ctx.author.name}",
            description=f"[Here's the link]({waifu_url})",
            media=upload_id,
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def reddit(self, ctx: AloneContext, subreddit: Optional[str]) -> revolt.Message | None:
        if not subreddit:
            return await ctx.send("You should give me a subreddit to search!")

        data: Dict[str, Any] = await self.fetch_subreddit(subreddit)
        if not ctx.channel:
            pass
        elif data["over_18"] and not ctx.channel.is_nsfw():  # type: ignore
            return await ctx.send("This post is nsfw! I cannot send this in a normal channel!")

        upload_url = await self.upload_image(self.client, data["url"])
        embed: revolt.SendableEmbed = revolt.SendableEmbed(title=data["title"], url=data["url"], media=upload_url)
        await ctx.send(embed=embed)


async def setup(client: AloneBot) -> None:
    client.add_cog(Fun(client))
