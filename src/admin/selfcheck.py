import discord
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta

class SelfCheckCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fckr_server_id = int(os.getenv('FCKR_SERVER', 0))
        
        # Anti-flood control
        self.command_timestamps = {}
        self.spam_threshold = 5  # e.g., 5 commands
        self.spam_time_window = timedelta(seconds=10)  # e.g., within 10 seconds
        
        # Start the self-check loop
        self.self_check.start()

    def cog_unload(self):
        self.self_check.cancel()

    @tasks.loop(minutes=5.0)  # Run every 5 minutes
    async def self_check(self):
        """Periodically checks the bot's critical systems."""
        guild = self.bot.get_guild(self.fckr_server_id)
        if not guild:
            print(f"❌ Self-Check Error at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: FCKR server not found.")
            return

        # 1. Check Voice Stats Cog
        voice_cog = self.bot.get_cog('VoiceStatsCog')
        if voice_cog:
            if not voice_cog.initialized:
                print(f"⚠️ Self-Check Warning at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: VoiceStatsCog not initialized. Attempting to re-initialize.")
                try:
                    await voice_cog.initialize_voice_stats()
                except Exception as e:
                    print(f"❌ Self-Check Error at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Failed to re-initialize VoiceStatsCog: {e}")
        else:
            print(f"❌ Self-Check Error at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: VoiceStatsCog not found.")

        # 2. Check Counting Cog
        counting_cog = self.bot.get_cog('CountingCog')
        if counting_cog:
            if not counting_cog.initialized:
                print(f"⚠️ Self-Check Warning at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: CountingCog is not initialized. Attempting to re-initialize.")
                try:
                    await counting_cog.initialize_counting()
                except Exception as e:
                    print(f"❌ Self-Check Error at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Failed to re-initialize CountingCog: {e}")
        else:
            print(f"❌ Self-Check Error at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: CountingCog not found.")

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Listener for command usage to implement anti-spam."""
        author_id = ctx.author.id
        current_time = datetime.now()

        # Clean up old timestamps
        if author_id in self.command_timestamps:
            self.command_timestamps[author_id] = [
                t for t in self.command_timestamps[author_id] 
                if current_time - t < self.spam_time_window
            ]
        else:
            self.command_timestamps[author_id] = []

        # Add current command timestamp
        self.command_timestamps[author_id].append(current_time)

        # Check for spam
        if len(self.command_timestamps[author_id]) > self.spam_threshold:
            # Optional: Lock the user out for a short period
            # This part can be expanded to be more sophisticated
            print(f"🚨 Possible command spam detected from {ctx.author.display_name} (ID: {author_id})")
            # We won't block the command here, just log it. 
            # For a real block, you would raise an exception or return.

    @self_check.before_loop
    async def before_self_check(self):
        """Wait until the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()
        print("⚙️ SelfCheckCog is ready and starting the loop.")

def setup(bot):
    bot.add_cog(SelfCheckCog(bot))