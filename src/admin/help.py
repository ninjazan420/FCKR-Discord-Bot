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
        
        # Check if user has admin permissions
        admin_cog = self.bot.get_cog('AdminManagerCog')
        is_bot_admin = await admin_cog.is_bot_admin(ctx.author.id)
        is_admin = ctx.author.guild_permissions.administrator or is_bot_admin
        
        # Get system stats
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_used = round(memory.used / 1024 / 1024 / 1024, 2)
        memory_total = round(memory.total / 1024 / 1024 / 1024, 2)
        memory_percent = memory.percent
        
        ascii_art = "```\n▄████  ▄█▄    █  █▀ █▄▄▄▄ \n█▀   ▀ █▀ ▀▄  █▄█   █  ▄▀ \n█▀▀    █   ▀  █▀▄   █▀▀▌  \n█      █▄  ▄▀ █  █  █  █  \n █     ▀███▀    █     █   \n  ▀            ▀     ▀    \n                           \n```"
        
        embed = discord.Embed(
            title="FCKR Discord Bot",
            description=f"{ascii_art}\nThe official Discord Bot for the FCKR Tag & Community server made by ninjazan420",
            color=0x00ff00
        )
        
        # Basic commands for everyone
        basic_commands = (
            "`!fckr help` - Show this help message\n"
            "`!fckr stats` - Show server statistics\n"
            "`!fckr colors` - Setup color role selection\n"
            "`!fckr aww` - Get a random cute cat image\n"
            "`!fckr changelog` - Show recent updates\n"
            "`!fckr ai_stats` - Show AI chatbot statistics\n"
            "`!fckr ai_memory` - Show your conversation history with the AI\n"
            "`@FCKR mention` - Chat with the AI bot (mention required)"
        )
        
        # Admin commands (only shown to admins)
        admin_commands = (
            "\n`!fckr refresh` - Refresh server statistics (Admin only)\n"
            "`!fckr neofetch` - Show detailed system stats (Admin only)\n"
            "`!fckr count` - Show counting status (Admin only)\n"
            "`!fckr reset_count [number]` - Reset counting (Admin only)\n"
            "`!fckr purge [amount]` - Delete specified number of messages (Admin only)\n"
            "`!fckr admin add [user]` - Add a bot admin (Admin only)\n"
            "`!fckr admin rm [user]` - Remove a bot admin (Admin only)\n"
            "`!fckr admin list` - List bot admins (Admin only)"
        )
        
        # Show commands based on permissions
        commands_text = basic_commands
        if is_admin:
            commands_text += admin_commands
        
        embed.add_field(
            name="📋 Available Commands",
            value=commands_text,
            inline=False
        )
        
        embed.add_field(
            name="Features",
            value="• Automatic voice channel statistics\n• Server member tracking\n• Boost count tracking\n• Daily join statistics\n• Color role system with 30 gradient colors\n• Counting game with automatic validation\n• AI Chatbot with conversation memory and statistics\n• Rate-limited AI interactions (25 messages/hour)",
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
        
        embed.add_field(
            name="🔗 Links",
            value="[GitHub Repository](https://github.com/ninjazan420/FCKR-Discord-Bot)\n[Report Issues](https://github.com/ninjazan420/FCKR-Discord-Bot/issues)",
            inline=False
        )
        
        embed.set_footer(text="FCKR Community Bot | Made with ❤️ by ninjazan420")
        
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(HelpCog(bot))