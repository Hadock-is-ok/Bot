import discord
from discord.ext import commands
from utils.bot import AloneBot

class Voice(commands.Cog):
    def __init__(self, bot: AloneBot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_voice_join(self, member, state):
        vc = self.bot.guild_config.get(state.channel.guild.id, None).get("voice_channel", None)
        if not vc or state.channel.id != vc:
            return
        
        new_vc = await member.guild.create_voice_channel(name=member.display_name, category=member.guild.get_channel(self.bot.guild_config.get(state.channel.guild.id, None).get("voice_category", None)), reason="Made by the personal voice chat module")
        await member.move(channel=new_vc)

async def setup(bot: AloneBot):
    await bot.add_cog(Voice(bot))