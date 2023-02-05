import os
from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv
from asyncio import run, environ

import utils.bot as _bot

load_dotenv()

bot = _bot.AloneBot(intents=Intents.all())

@bot.after_invoke
async def command_counter(ctx: commands.Context):
    bot.command_counter += 1

@bot.check_once
async def blacklist(ctx: commands.Context):
    if not bot.is_blacklisted(ctx.author.id):
        return True
    if ctx.author.id in bot.owner_ids:
        return True
    raise _bot.BlacklistedError

@bot.check_once
async def maintenance(ctx: commands.Context):
    if not bot.maintenance or ctx.author.id in bot.owner_ids:
        return True
    raise _bot.MaintenanceError

async def main():
    async with bot:
        await bot.start(environ["token"])

if __name__ == "__main__":
    run(main())