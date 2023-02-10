import os
from asyncio import run
from typing import Literal

from discord import Intents
from dotenv import load_dotenv

from utils import AloneBot, AloneContext, BlacklistedError, MaintenanceError

load_dotenv()

bot = AloneBot(intents=Intents.all())


@bot.after_invoke
async def command_counter() -> None:
    bot.command_counter += 1


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
