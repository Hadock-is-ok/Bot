import discord
from discord.ext import commands
from utils.bot import AloneBot

class Voice(commands.Cog):
    def __init__(self, bot: AloneBot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_voice_join(self, member, state):
        print("helplo")
        vc = self.bot.guild_config.get(state.channel.guild.id, None).get("voice_channel", None)
        print("hehe")
        if not vc or state.channel.id != vc:
            print("if not")
            return
        
        guild = vc.guild
        print("hi")
        new_vc = await guild.create_voice_channel(name=member.display_name, category=await guild.get_channel(self.bot.guild_config.get(state.channel.guild.id, None).get("voice_category", None)), reason="Made by the personal voice chat module")
        print("hm")
        await member.move(channel=new_vc)

async def setup(bot: AloneBot):
    await bot.add_cog(Voice(bot))