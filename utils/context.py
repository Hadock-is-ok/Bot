from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import discord
from discord import PartialEmoji
from discord.ext import commands
from typing_extensions import LiteralString

from .views import DeleteView

if TYPE_CHECKING:
    from bot import AloneBot

BASE_KWARGS: dict[str, Any] = {
    "content": None,
    "embeds": [],
    "attachments": [],
    "suppress": False,
    "delete_after": None,
    "view": None,
}


class _Emojis:
    x: PartialEmoji = PartialEmoji(name="cross", id=1019436205269602354)
    check: PartialEmoji = PartialEmoji(name="tick", id=1019436222260723744)
    slash: PartialEmoji = PartialEmoji(name="slash", id=1041021694682349569)


class AloneContext(commands.Context['AloneBot']):
    Emojis: _Emojis = _Emojis()

    async def send(
        self,
        content: str | None = None,
        add_button_view: bool = True,
        **kwargs: Any,
    ) -> discord.Message:
        embed: Optional[discord.Embed] = kwargs.get("embed")
        if embed:
            if not embed.color:
                embed.color = self.author.color

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

        return await super().send(content, **kwargs)

    async def create_codeblock(self, content: str) -> str:
        fmt: LiteralString = "`" * 3
        return f"{fmt}py\n{content}{fmt}"
