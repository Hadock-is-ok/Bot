from __future__ import annotations

from typing import TYPE_CHECKING, Any

import revolt
from revolt.ext import commands

from .views import DeleteView

if TYPE_CHECKING:
    from client import AloneBot
    embed: revolt.SendableEmbed


class AloneContext(commands.Context['AloneBot']):
    async def send(
        self,
        content: str | None = None,
        add_button_view: bool = True,
        **kwargs: Any,
    ) -> revolt.Message:
        for embed in kwargs.get("embeds", []):
            embed.colour = embed.colour or None
            embed.timestamp = embed.timestamp or 
            if not embed.footer.text:
                embed.set_footer(
                    text=f"Command ran by {self.author.display_name}",
                    icon_url=self.author.avatar.url,
                )

        if self.command and (self.command.root_parent or self.command).name == "jishaku":
            return await super().send(content, **kwargs)

        if add_button_view:
            delete_button = DeleteView(self).children[0]
            original_view = kwargs.get("view") or revolt.ui.View()
            if original_view:
                original_view.add_item(delete_button)

            kwargs["view"] = original_view

        return await super().send(content, **kwargs)

    @property
    def emojis(self) -> dict[str, revolt.Emoji]:
        return self.client._emojis

    def get_emoji(self, name: str) -> revolt.Emoji:
        return self.client._emojis[name]
