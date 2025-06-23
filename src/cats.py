import discord
from discord.ext import commands
import os
import random

class Cats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Collection of random cat ASCII art
        self.cat_ascii = [
            "=^.^=",
            "(=^･ω･^=)",
            "(=^‥^=)",
            "ฅ(^・ω・^ฅ)",
            "(=｀ω´=)",
            "(=^･ｪ･^=)",
            "ヾ(=｀ω´=)ノ",
            "(^･o･^)ﾉ",
            "(=ＴェＴ=)",
            "(=^-ω-^=)",
            "ฅ(⌯͒• ɪ •⌯͒)ฅ",
            "(^◡^)っ",
            "(=ↀωↀ=)",
            "(=ΦωΦ=)",
            "(=ＴωＴ=)"
        ]

    @commands.Cog.listener()
    async def on_member_join(self, member):
        fckr_server_id = os.getenv('FCKR_SERVER')
        join_log_channel_id = os.getenv('JOIN_LOG_CHANNEL')

        if not fckr_server_id or not join_log_channel_id:
            return

        try:
            fckr_server_id = int(fckr_server_id)
            join_log_channel_id = int(join_log_channel_id)
        except ValueError:
            return

        if member.guild.id != fckr_server_id:
            return

        channel = self.bot.get_channel(join_log_channel_id)
        if not channel:
            return

        try:
            # Select random cat ASCII
            random_cat = random.choice(self.cat_ascii)
            
            # Create welcome embed with links
            embed = discord.Embed(
                title="🎉 Welcome to FCKR Tag & Community!",
                description=f"Hey {member.mention}! Welcome to our awesome community! 🚀\n\nFeel free to explore and have fun!\n\n🐱 Here's a virtual cat for you: {random_cat}",
                color=0x00ff00
            )
            
            # Add useful links
            embed.add_field(
                name="📋 Server Rules",
                value="[Read our rules here](https://discord.com/channels/{}/{})".format(fckr_server_id, os.getenv('RULES_CHANNEL_ID', 'rules')),
                inline=True
            )
            
            embed.add_field(
                name="🏷️ Server Tag Setup",
                value="[Learn how to set your server tag](https://discord.com/channels/{}/{})".format(fckr_server_id, os.getenv('SERVERTAG_CHANNEL_ID', 'servertag')),
                inline=True
            )
            
            embed.add_field(
                name="🎨 Choose Your Color",
                value="[Pick your favorite color role](https://discord.com/channels/{}/{})".format(fckr_server_id, os.getenv('COLORS_CHANNEL_ID', 'colors')),
                inline=True
            )
            
            embed.add_field(
                name="🏆 Rankings",
                value="[Check rankings here](https://discord.com/channels/{}/{})".format(fckr_server_id, os.getenv('RANKING_CHANNEL_ID', 'ranking')),
                inline=True
            )
            
            embed.set_footer(text="Enjoy your stay! 🎮")
            
            # Send welcome message
            await channel.send(embed=embed)
            
        except Exception as e:
            await channel.send(f"Welcome {member.mention}! The cat delivery service is currently sleeping, but we're happy to have you!")

async def setup(bot):
    await bot.add_cog(Cats(bot))