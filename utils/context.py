from typing import Any, Optional

import discord
from discord import PartialEmoji
from discord.ext import commands
from typing_extensions import Self

from .views import DeleteView

BASE_KWARGS: dict[str, Any] = {
    "content": None,
    "embeds": [],
    "attachments": [],
    "suppress": False,
    "delete_after": None,
    "view": None,
}


class _Emojis:
    x = PartialEmoji(name="cross", id=1019436205269602354)
    check = PartialEmoji(name="tick", id=1019436222260723744)
    slash = PartialEmoji(name="slash", id=1041021694682349569)


class AloneContext(commands.Context[Any]):
    async def send(
        self: Self,
        content: str | None = None,
        add_button_view: bool = True,
        **kwargs: Any,
    ):
        embed: Optional[discord.Embed] = kwargs.get("embed")
        if embed:
            if not embed.color:
                embed.color = discord.Color.random()

            if not embed.footer:
                embed.set_footer(
                    text=f"Command ran by {self.author.display_name}",
                    icon_url=self.author.display_avatar,
                )

            if not embed.timestamp:
                embed.timestamp = discord.utils.utcnow()

        if add_button_view:
            _view: discord.ui.View | None = kwargs.get("view")
            if not _view:
                kwargs["view"] = DeleteView(self)

            else:
                view = kwargs["view"] = DeleteView(self)
                view.add_item(_view.children[0])

        if not self.bot.bot_messages_cache.get(self.message):
            self.bot.bot_messages_cache[self.message] = message = await super().send(content, **kwargs)
            return message

        else:
            message = self.bot.bot_messages_cache.get(self.message)
            edit_kwargs = {key: value for key, value in kwargs.items() if key in BASE_KWARGS}
            edit_kwargs["content"] = content
            edit_kwargs["embeds"] = (kwargs.pop("embeds", [])) or (
                [kwargs.pop("embed")] if kwargs.get("embed", None) else []
            )

            try:
                self.bot.bot_messages_cache[self.message] = message = await self.bot.bot_messages_cache[self.message].edit(
                    **edit_kwargs
                )
                return message

            except discord.HTTPException:
                self.bot.bot_messages_cache[self.message] = message = await super().send(content, **kwargs)
                return message

    async def create_codeblock(self: Self, content: str):
        fmt = "`" * 3
        return f"{fmt}py\n{content}{fmt}"

    Emojis = _Emojis()
