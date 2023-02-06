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
        self.bot.guild_config[member.guild.id].setdefault("community_voice_channels", {})[new_vc.id] = member.id
        await self.bot.db.execute("INSERT INTO voice VALUES ($1, $2, $3)", member.guild.id, member.id, new_vc.id)
        await member.send("Welcome to your own voice chat! Here, you lay the rules. your house, your magic. Have fun!")
    
    @commands.Cog.listener()
    async def on_voice_leave(self, member, state):
        print("ahuidwiagdawda")
        vc = self.bot.guild_config.get(member.guild.id, {}).get("community_voice_channels", {})
        print("asgwuh")
        if not vc or not state.channel.id in vc:
            print("HUAhsd")
            return
        print("HEHRH")
        if not state.channel.members:
            print("uaihdauwdh")
            channel = state.channel
            print("bitch what")
            try:
                print("wtf?")
                owner = bot.get_member(vc.get(state.channel.id))
                print("as")
                message = await owner.send("I will delete this channel for inactivity in 5 minutes if it's not used!")
                print("asaduwah")
                await self.bot.wait_for("voice_join", timeout=300, check=channel_check)
                await message.delete()
            except asyncio.TimeoutError:
                try:
                    await channel.delete()
                except Exception:
                    pass
        print("wtf how")


async def setup(bot: AloneBot):
    await bot.add_cog(Voice(bot))