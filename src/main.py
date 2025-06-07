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
    
    # Add cogs to bot
    await bot.add_cog(HelpCog(bot))
    await bot.add_cog(VoiceStatsCog(bot))
    await bot.add_cog(SystemStatsCog(bot))
    await bot.add_cog(ColorRolesCog(bot))
    await bot.add_cog(ChangelogCog(bot))
    print("✅ All cogs loaded successfully")

@bot.event
async def on_ready():
    # Startup logging with timestamp and version
    timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    version = "1.0.2"
    print(f'{timestamp} # 🟢 Bot gestartet - Version {version}')
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is ready and serving {len(bot.guilds)} guilds')
    
    # Set bot status
    await bot.change_presence(activity=discord.Game(name="Official FCKR Bot"))
    print("✅ Bot status set to 'Spielt Official FCKR Bot'")
    
    # Initialize voice stats manually
    voice_stats_cog = bot.get_cog('VoiceStatsCog')
    if voice_stats_cog:
        await voice_stats_cog.setup_voice_channels()
        if not voice_stats_cog.update_voice_stats.is_running():
            voice_stats_cog.update_voice_stats.start()
            print("✅ Voice stats task started")
    
    # Log to bot logging channel if configured
    bot_logging_channel_id = int(os.getenv('BOT_LOGGING', 0))
    if bot_logging_channel_id:
        channel = bot.get_channel(bot_logging_channel_id)
        if channel:
            embed = discord.Embed(
                title="🟢 Bot Started",
                description=f"FCKR Bot v{version} is now online!",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.add_field(name="Guilds", value=str(len(bot.guilds)), inline=True)
            embed.add_field(name="Version", value=version, inline=True)
            try:
                await channel.send(embed=embed)
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