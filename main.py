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
async def command_counter(ctx: AloneContext) -> None:
    ctx.bot.command_counter += 1


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


@bot.check_once
async def cooldown(ctx: AloneContext) -> Literal[True]:
    if (
        ctx.author.id in bot.owner_ids
        or ctx.author.id in bot.bypass_cooldown_users
        or isinstance(ctx.author, discord.User)
        or ctx.channel.permissions_for(ctx.author).manage_messages
    ):
        return True

    bucket: commands.Cooldown | None = bot.cooldown.get_bucket(ctx.message)
    assert bucket
    retry_after = bucket.update_rate_limit()
    if retry_after:
        raise commands.CommandOnCooldown(bucket, retry_after, commands.BucketType.member)

    return True


async def main():
    async with bot:
        await bot.start(os.environ["token"])


if __name__ == "__main__":
    run(main())
