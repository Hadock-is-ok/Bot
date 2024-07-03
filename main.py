import os
from asyncio import run
from typing import Literal

import discord
from discord.ext import commands
from dotenv import load_dotenv

from bot import AloneBot
from utils import AloneContext, BlacklistedError, MaintenanceError

load_dotenv()


bot = AloneBot(intents=discord.Intents.all())


@bot.after_invoke
async def command_counter(ctx: AloneContext) -> None:
    ctx.bot.command_counter += 1


@bot.check_once
async def blacklist(ctx: AloneContext) -> Literal[True]:
    "A check that gets applied before commands to make sure a blacklisted user can't use commands."
    if not bot.is_blacklisted(ctx.author.id) or ctx.author.id in bot.owner_ids:
        return True
    raise BlacklistedError


@bot.check_once
async def maintenance(ctx: AloneContext) -> Literal[True]:
    "A check that gets applied before commands to make sure that the bot isn't in maintenance."
    if not bot.maintenance or ctx.author.id in bot.owner_ids:
        return True
    raise MaintenanceError


async def main() -> None:
    async with bot:
        await bot.start(os.environ["token"])


if __name__ == "__main__":
    run(main())
