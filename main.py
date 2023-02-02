from discord import Intents
from asyncio import run
from os import environ
from discord.ext import commands
from utils.bot import AloneBot, BlacklistedError, MaintenanceError
from dotenv import load_dotenv

load_dotenv()

bot = AloneBot(intents=Intents.all())

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
    async with bot:
        await bot.start(environ["token"])

if __name__ == "__main__":
    run(main())