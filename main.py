import discord
import logging
import os, asyncio, aiohttp
from discord.ext import commands
from utils.bot import AloneBot, BlacklistedError, MaintenanceError
from dotenv import load_dotenv

load_dotenv()

bot = AloneBot(intents=discord.Intents.all())


@bot.after_invoke
async def aftercount(ctx: commands.Context):
    bot.command_counter += 1


@bot.check_once
async def blacklist(ctx: commands.Context):
    if not bot.is_blacklisted(ctx.author.id):
        return True
    if ctx.author.id in bot.owner_ids:
        return True
    raise BlacklistedError


@bot.check_once
async def maintenance(ctx: commands.Context):
    if not bot.maintenance or ctx.author.id in bot.owner_ids:
        return True
    raise MaintenanceError


async def main():
    async with aiohttp.ClientSession() as session, bot:
        discord.utils.setup_logging(handler=logging.FileHandler("bot.log"))
        bot.logger = logging.getLogger("discord")
        bot.session = session
        await bot.start(os.environ["token"])

if __name__ == "__main__":
    asyncio.run(main())
