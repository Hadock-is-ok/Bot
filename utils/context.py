from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands

from .views import DeleteView

if TYPE_CHECKING:
    from bot import AloneBot


class AloneContext(commands.Context['AloneBot']):
    async def send(
        self,
        content: str | None = None,
        add_button_view: bool = True,
        **kwargs: Any,
    ) -> discord.Message:
        for embed in kwargs.get("embeds", []):
            embed.colour = embed.colour or self.author.color
            embed.timestamp = embed.timestamp or discord.utils.utcnow()
            if not embed.footer.text:
                embed.set_footer(
                    text=f"Command ran by {self.author.display_name}",
                    icon_url=self.author.display_avatar.url,
                )

        if add_button_view:
            delete_view = DeleteView(self)
            if original_view := kwargs.get("view"):
                delete_view._children += original_view._children

            kwargs["view"] = delete_view

        return await super().send(content, **kwargs)

    @property
    def emojis(self) -> dict[str, discord.Emoji]:
        return self.bot._emojis

    def get_emoji(self, name: str) -> discord.Emoji:
        return self.bot._emojis[name]
