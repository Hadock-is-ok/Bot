from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional

import revolt
from revolt.ext import commands

if TYPE_CHECKING:
    from client import AloneBot
    from utils import AloneContext


class Owner(commands.Cog[AloneBot]):
    def __init__(self, client: AloneBot) -> None:
        self.client: AloneBot = client

    def cog_check(self, ctx: commands.Context[Any]) -> bool:
        return ctx.author.id in self.client.owner_ids

    @commands.command()
    async def maintenance(self, ctx: AloneContext, *, reason: Optional[str] = "no reason provided") -> None:
        if not self.client.maintenance:
            self.client.maintenance = reason
        else:
            del self.client.maintenance

        await ctx.message.add_reaction(ctx.emojis["tick"])

    @commands.group(invoke_without_command=True)
    async def blacklist(self, ctx: AloneContext) -> None:
        fmt: List[str] = []
        for user_id, reason in self.client.blacklisted_users.items():
            user: revolt.User | None = self.client.get_user(user_id)
            if not user:
                continue

            fmt.append(f"{user} - {reason}")

        await ctx.send(embed=revolt.SendableEmbed(title="Blacklisted users", description="\n".join(fmt)))

    @blacklist.command()
    async def add(
        self,
        ctx: AloneContext,
        member: revolt.Member,
        *,
        reason: str = "No reason provided",
    ) -> None:
        self.client.blacklisted_users[member.id] = reason
        await self.client.db.execute("INSERT INTO blacklist (user_id, reason) VALUES ($1, $2)", member.id, reason)
        await ctx.message.add_reaction(ctx.emojis["tick"])

    @blacklist.command()
    async def remove(self, ctx: AloneContext, *, member: revolt.Member) -> revolt.Message | None:
        try:
            self.client.blacklisted_users.pop(member.id)
            await self.client.db.execute("DELETE FROM blacklist WHERE user_id = $1", member.id)
        except KeyError:
            await ctx.message.add_reaction(ctx.emojis["cross"])
            return await ctx.send("That user isn't blacklisted!")

        await ctx.message.add_reaction(ctx.emojis["tick"])

    @commands.command()
    async def disable(self, ctx: AloneContext, name: str) -> revolt.Message | None:
        command = self.client.get_command(name)
        if not command:
            await ctx.message.add_reaction(ctx.emojis["cross"])
            return await ctx.send("That command doesn't exist!")

        if not command.enabled:
            await ctx.message.add_reaction(ctx.emojis["cross"])
            return await ctx.send("This command is already disabled!")

        command.enabled = False
        await ctx.send(f"Disabled {name}.")

    @commands.command()
    async def enable(self, ctx: AloneContext, name: str) -> revolt.Message | None:
        command = self.client.get_command(name)
        if not command:
            await ctx.message.add_reaction(ctx.emojis["cross"])
            return await ctx.send("That command doesn't exist!")

        if command.enabled:
            await ctx.message.add_reaction(ctx.emojis["cross"])
            return await ctx.send("This command is already enabled!")

        command.enabled = True
        await ctx.send(f"Enabled {name}.")

    @commands.command()
    async def say(self, ctx: AloneContext, *, text: Optional[str] = "hi im stupid and i put nothing here") -> None:
        await ctx.send(text)

    @commands.command(aliases=["d", "delete"])
    async def delmsg(self, ctx: AloneContext, _message: Optional[revolt.Message]) -> None:
        message: revolt.Message | None = _message or ctx.message.reference.resolved  # type: ignore
        if not message:
            return await ctx.message.add_reaction(ctx.emojis["slash"])

        await message.delete()

    @commands.command()
    async def nick(self, ctx: AloneContext, *, name: Optional[str]) -> None:
        if not ctx.server:
            return

        await ctx.server.me.edit(nick=name)
        await ctx.message.add_reaction(ctx.emojis["tick"])

    @commands.command(aliases=["shutdown", "fuckoff", "quit"])
    async def logout(self, ctx: AloneContext) -> None:
        await ctx.message.add_reaction(ctx.emojis["tick"])
        await self.client.close()

    @commands.command()
    async def load(self, ctx: AloneContext, cog: str) -> None:
        try:
            await self.client.load_extension(cog)
            message: str = "Loaded!"
        except Exception as error:
            message = f"Error! {error}"
        await ctx.send(message)

    @commands.command()
    async def unload(self, ctx: AloneContext, cog: str) -> None:
        try:
            await self.client.unload_extension(cog)
            message: str = "Unloaded!"
        except Exception as error:
            message = f"Error! {error}"
        await ctx.send(message)

    @commands.command()
    async def reload(self, ctx: AloneContext) -> None:
        cog_status: str = ""
        for extension in self.client.INITAL_EXTENSIONS:
            try:
                await self.client.reload_extension(extension)
            except commands.ExtensionNotLoaded:
                cog_status += f"{ctx.emojis['x']} {extension} not loaded!\n\n"
                continue
            cog_status += f"\U0001f504 {extension} Reloaded!\n\n"

        await ctx.send(embed=revolt.SendableEmbed(title="Reload", description=cog_status))
        await ctx.message.add_reaction(ctx.emojis["tick"])


async def setup(client: AloneBot) -> None:
    client.add_cog(Owner(client))
