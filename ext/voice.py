import discord, asyncio
from discord.ext import commands
from utils.bot import AloneBot

def channel_check(member, state):
    return state.channel == channel

class Voice(commands.Cog):
    def __init__(self, bot: AloneBot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_voice_join(self, member, state):
        vc = self.bot.guild_config.get(state.channel.guild.id, {}).get("voice_channel", None)
        if not vc or state.channel.id != vc:
            return
        
        new_vc = await member.guild.create_voice_channel(name=member.display_name, category=member.guild.get_channel(self.bot.guild_config.get(state.channel.guild.id, None).get("voice_category", None)), reason="Made by the personal voice chat module")
        await member.move_to(channel=new_vc)
        self.bot.guild_config[member.guild.id].setdefault("community_voice_channels", {})[member.id] = new_vc.id
        await self.bot.db.execute("INSERT INTO voice VALUES ($1, $2, $3)", member.guild.id, member.id, new_vc.id)
        await member.send("Welcome to your own voice chat! Here, you lay the rules. your house, your magic. Have fun!")
    
    @commands.Cog.listener()
    async def on_voice_leave(self, member, state):
        vc = self.bot.guild_config.get(state.guild.id, {}).get("community_voice_channels", [])
        if not vc or not state.channel.id in vc:
            return
        
        if len(state.channel.members) == 0:
            channel = state.channel
            try:
                await self.bot.wait_for("voice_join", timeout=300, check=channel_check)
            except asyncio.TimeoutError:
                try:
                    await channel.delete()
                except Exception:
                    pass


async def setup(bot: AloneBot):
    await bot.add_cog(Voice(bot))