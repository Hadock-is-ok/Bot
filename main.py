import os
from asyncio import run
from typing import Literal

import revolt
from revolt.ext import commands
from dotenv import load_dotenv

from client import AloneBot
from utils import AloneContext, BlacklistedError, MaintenanceError

load_dotenv()


client: AloneBot = AloneBot()


@client.
async def command_counter(ctx: AloneContext) -> None:
    ctx.client.command_counter += 1


@client.check_once
async def blacklist(ctx: AloneContext) -> Literal[True]:
    "A check that gets applied before commands to make sure a blacklisted user can't use commands."
    if not client.is_blacklisted(ctx.author.id) or ctx.author.id in client.owner_ids:
        return True
    raise BlacklistedError


@client.check_once
async def maintenance(ctx: AloneContext) -> Literal[True]:
    "A check that gets applied before commands to make sure that the client isn't in maintenance."
    if not client.maintenance or ctx.author.id in client.owner_ids:
        return True
    raise MaintenanceError


@client.
async def cooldown(ctx: AloneContext) -> Literal[True]:
    "A check that gets applied before commands to make sure a user hasn't ran too many commands in X amount of time."
    if (
        ctx.author.id in client.owner_ids
    ):
        return True

    bucket: Cooldown | None = client.cooldown.get_bucket(ctx.message)

    if not bucket:
        raise RuntimeError("Cooldown Bucket does not exist!")

    retry_after: float | None = bucket.update_rate_limit()
    if retry_after:
        raise CommandOnCooldown(retry_after)

    return True


async def main() -> None:
    async with client:
        await client.start(os.environ["token"])


if __name__ == "__main__":
    run(main())
