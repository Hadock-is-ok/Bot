import os
from asyncio import run
from typing import Literal

import discord
from discord.ext import commands
from dotenv import load_dotenv

from utils import AloneBot, AloneContext, BlacklistedError, MaintenanceError

load_dotenv()


bot = AloneBot(intents=discord.Intents.all())


@bot.after_invoke
async def command_counter() -> None:
    bot.command_counter += 1


@bot.check
async def cooldown_check(ctx: AloneContext) -> Literal[True]:
    bucket = bot.cooldown.get_bucket(ctx.message)
    time = ctx.message.created_at.timestamp()
    assert bucket
    retry_after = bucket.update_rate_limit(time)
    if ctx.guild:
        if ctx.channel.permissions_for(ctx.author): # type: ignore
            return True
    if await bot.is_owner(ctx.author) or not retry_after:
        return True
    raise commands.CommandOnCooldown(discord.app_commands.Cooldown(1, 2.5), retry_after, commands.BucketType.member)

@bot.check_once
async def blacklist(ctx: AloneContext) -> Literal[True]:
    if not bot.is_blacklisted(ctx.author.id) or ctx.author.id in bot.owner_ids:
        return True
    raise BlacklistedError


@bot.check_once
async def maintenance(ctx: AloneContext) -> Literal[True]:
    if not bot.maintenance or ctx.author.id in bot.owner_ids:
        return True
    raise MaintenanceError


async def main():
    async with bot:
        await bot.start(os.environ["token"])


if __name__ == "__main__":
    run(main())
