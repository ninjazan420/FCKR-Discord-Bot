import discord
from discord.ext import commands
import psutil
import platform
from datetime import datetime

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help')
    async def help_command(self, ctx):
        """Display help information for the FCKR Discord Bot"""
        
        # Get system stats
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_used = round(memory.used / 1024 / 1024 / 1024, 2)
        memory_total = round(memory.total / 1024 / 1024 / 1024, 2)
        memory_percent = memory.percent
        
        embed = discord.Embed(
            title="FCKR Discord Bot",
            description="The official Discord Bot for the FCKR Tag & Community server made by ninjazan420",
            color=0x00ff00
        )
        
        embed.add_field(
            name="📋 Available Commands",
            value="`!fckr help` - Show this help message\n"
                  "`!fckr stats` - Show server statistics\n"
                  "`!fckr colors` - Setup color role selection\n"
                  "`!fckr changelog` - Show recent updates\n"
                  "`!fckr refresh` - Refresh server statistics (Admin only)",
            inline=False
        )
        
        embed.add_field(
            name="Features",
            value="• Automatic voice channel statistics\n• Server member tracking\n• FCKR tag member count\n• Boost count tracking\n• Daily join statistics\n• Color role system with 30 gradient colors",
            inline=False
        )
        
        embed.add_field(
            name="🖥️ System Stats",
            value=f"**OS:** {platform.system()} {platform.release()}\n**CPU:** {cpu_percent}%\n**RAM:** {memory_used}GB / {memory_total}GB ({memory_percent}%)\n**Python:** {platform.python_version()}",
            inline=True
        )
        
        embed.add_field(
            name="🚀 Support the Server",
            value="Help us grow! Consider boosting the server to unlock more features and show your support for the FCKR community! 💜",
            inline=False
        )
        
        embed.set_footer(text="FCKR Community Bot | Made with ❤️ by ninjazan420")
        
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(HelpCog(bot))