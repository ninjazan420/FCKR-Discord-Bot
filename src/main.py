import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from datetime import datetime
import psutil
import platform

# Load environment variables
load_dotenv()

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix='!fckr ', intents=intents, help_command=None)

async def setup_cogs():
    """Load all cogs asynchronously"""
    from admin.help import HelpCog
    from admin.voice_stats import VoiceStatsCog
    from admin.system_stats import SystemStatsCog
    from color_roles import ColorRolesCog
    from changelog import ChangelogCog
    from counting import CountingCog
    
    # Add cogs to bot
    await bot.add_cog(HelpCog(bot))
    await bot.add_cog(VoiceStatsCog(bot))
    await bot.add_cog(SystemStatsCog(bot))
    await bot.add_cog(ColorRolesCog(bot))
    await bot.add_cog(ChangelogCog(bot))
    await bot.add_cog(CountingCog(bot))
    print("✅ All cogs loaded successfully")

@bot.event
async def on_ready():
    # Startup logging with timestamp and version
    timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    version = "1.0.4"
    
    # ASCII Art for console
    ascii_art = """
▄████  ▄█▄    █  █▀ █▄▄▄▄ 
█▀   ▀ █▀ ▀▄  █▄█   █  ▄▀ 
█▀▀    █   ▀  █▀▄   █▀▀▌  
█      █▄  ▄▀ █  █  █  █  
 █     ▀███▀    █     █   
  ▀            ▀     ▀    
    """
    
    print(ascii_art)
    print(f'{timestamp} # 🟢 Bot gestartet - Version {version}')
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is ready and serving {len(bot.guilds)} guilds')
    
    # Get system info for startup
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_used = round(memory.used / 1024 / 1024 / 1024, 2)
    memory_total = round(memory.total / 1024 / 1024 / 1024, 2)
    
    print(f'💻 System: {platform.system()} {platform.release()}')
    print(f'🧠 CPU: {cpu_percent}% | RAM: {memory_used}GB/{memory_total}GB')
    print(f'🐍 Python: {platform.python_version()}')
    
    # Set bot status
    await bot.change_presence(activity=discord.Game(name="Official FCKR Bot"))
    print("✅ Bot status set to 'Spielt Official FCKR Bot'")
    
    # Initialize voice stats manually
    voice_stats_cog = bot.get_cog('VoiceStatsCog')
    if voice_stats_cog:
        await voice_stats_cog.setup_voice_channels()
        # Initial stats update
        await voice_stats_cog.update_all_voice_stats()
        print("✅ Voice stats initialized with live updates")
    
    # Log to bot logging channel if configured
    bot_logging_channel_id = int(os.getenv('BOT_LOGGING', 0))
    if bot_logging_channel_id:
        channel = bot.get_channel(bot_logging_channel_id)
        if channel:
            # Get admin users (you can customize this list)
            admin_mentions = "<@ninjazan420>"  # Add more admin IDs as needed
            
            embed = discord.Embed(
                title="🟢 FCKR Bot Started",
                description=f"```\n▄████  ▄█▄    █  █▀ █▄▄▄▄ \n█▀   ▀ █▀ ▀▄  █▄█   █  ▄▀ \n█▀▀    █   ▀  █▀▄   █▀▀▌  \n█      █▄  ▄▀ █  █  █  █  \n █     ▀███▀    █     █   \n  ▀            ▀     ▀    \n```\n**FCKR Bot v{version} is now online!** 🚀",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="📊 Server Info", value=f"**Guilds:** {len(bot.guilds)}\n**Version:** {version}", inline=True)
            embed.add_field(name="💻 System Stats", value=f"**OS:** {platform.system()} {platform.release()}\n**CPU:** {cpu_percent}%\n**RAM:** {memory_used}GB/{memory_total}GB", inline=True)
            embed.add_field(name="🔧 Status", value="**Voice Stats:** ✅ Active\n**Color Roles:** ✅ Ready\n**Commands:** ✅ Loaded", inline=True)
            
            embed.set_footer(text="FCKR Community Bot | Made with ❤️ by ninjazan420")
            
            try:
                await channel.send(f"hey {admin_mentions} 👋", embed=embed)
                print("✅ Startup logged to bot logging channel")
            except Exception as e:
                print(f"Error logging startup: {e}")

# Load modules
if __name__ == '__main__':
    import asyncio
    
    async def main():
        # Setup cogs first
        await setup_cogs()
        
        # Run the bot
        token = os.getenv('DISCORD_API_TOKEN')
        if not token:
            print('Error: DISCORD_API_TOKEN not found in environment variables')
            exit(1)
        
        await bot.start(token)
    
    # Run the bot
    asyncio.run(main())