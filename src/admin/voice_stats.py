import discord
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta
import pytz

class VoiceStatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fckr_server_id = int(os.getenv('FCKR_SERVER', 0))
        self.bot_logging_channel_id = int(os.getenv('BOT_LOGGING', 0))
        self.daily_joins = 0
        self.berlin_tz = pytz.timezone('Europe/Berlin')
        self.last_reset = datetime.now(self.berlin_tz).date()
        
        # Voice channel IDs (will be created automatically)
        self.voice_channels = {
            'total_members': None,
            'boost_count': None
        }
        
        # Track if channels are already set up
        self.channels_initialized = False
        
    # on_ready is now handled in main.py to avoid conflicts
    
    async def setup_voice_channels(self):
        """Create or find the voice channels for statistics"""
        if self.channels_initialized:
            return
            
        guild = self.bot.get_guild(self.fckr_server_id)
        if not guild:
            print(f"Guild with ID {self.fckr_server_id} not found")
            return
        
        # Find existing channels or create new ones
        channel_patterns = {
            'total_members': ['total members', 'members'],
            'boost_count': ['boosts', 'boost']
        }
        
        for key, patterns in channel_patterns.items():
            # Look for existing channel with better pattern matching
            existing_channel = None
            for channel in guild.voice_channels:
                channel_name_lower = channel.name.lower()
                if any(pattern in channel_name_lower for pattern in patterns):
                    existing_channel = channel
                    break
            
            if existing_channel:
                self.voice_channels[key] = existing_channel.id
                print(f"Found existing voice channel for {key}: {existing_channel.name}")
            else:
                # Create new channel
                default_names = {
                    'total_members': '👥 Total Members: 0',
                    'boost_count': '🚀 Boosts: 0'
                }
                try:
                    new_channel = await guild.create_voice_channel(
                        name=default_names[key],
                        user_limit=0,  # No user limit
                        overwrites={
                            guild.default_role: discord.PermissionOverwrite(connect=False)
                        }
                    )
                    self.voice_channels[key] = new_channel.id
                    print(f"Created voice channel: {default_names[key]}")
                except Exception as e:
                    print(f"Error creating voice channel {default_names[key]}: {e}")
        
        # Count today's joins from audit log
        await self.count_todays_joins_from_audit_log()
        self.channels_initialized = True
    
    async def count_todays_joins_from_audit_log(self):
        """Count today's joins from audit log"""
        guild = self.bot.get_guild(self.fckr_server_id)
        if not guild:
            return
        
        berlin_now = datetime.now(self.berlin_tz)
        today_start = berlin_now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        try:
            join_count = 0
            async for entry in guild.audit_logs(action=discord.AuditLogAction.member_join, after=today_start):
                join_count += 1
            
            self.daily_joins = join_count
            print(f"Counted {join_count} joins from audit log for today")
        except Exception as e:
            print(f"Error reading audit log: {e}")
            # Fallback: keep current counter
    
    @tasks.loop(minutes=4)
    async def update_voice_stats(self):
        """Update voice channel statistics every 4 minutes"""
        guild = self.bot.get_guild(self.fckr_server_id)
        if not guild:
            return
        
        # Reset daily joins if it's a new day (Berlin time)
        berlin_now = datetime.now(self.berlin_tz)
        if berlin_now.date() > self.last_reset:
            await self.count_todays_joins_from_audit_log()
            self.last_reset = berlin_now.date()
        
        # Get statistics
        total_members = guild.member_count
        boost_count = guild.premium_subscription_count or 0
        
        # Update channels
        await self.update_channel('total_members', f'👥 Total Members: {total_members}')
        await self.update_channel('boost_count', f'🚀 Boosts: {boost_count}')
        
        # No automatic logging - only update voice channels silently
    

    
    async def update_channel(self, channel_key, new_name):
        """Update a voice channel name"""
        channel_id = self.voice_channels.get(channel_key)
        if not channel_id:
            return
        
        channel = self.bot.get_channel(channel_id)
        if channel and channel.name != new_name:
            try:
                await channel.edit(name=new_name)
            except Exception as e:
                print(f"Error updating channel {channel_key}: {e}")
    
    # Removed automatic logging function - only manual refreshes are logged now
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Track daily joins"""
        if member.guild.id == self.fckr_server_id:
            self.daily_joins += 1
    
    @commands.command(name='stats')
    async def manual_stats(self, ctx):
        """Manually display current server statistics"""
        guild = ctx.guild
        if guild.id != self.fckr_server_id:
            await ctx.send("This command can only be used on the FCKR server.")
            return
        
        total_members = guild.member_count
        boost_count = guild.premium_subscription_count or 0
        
        embed = discord.Embed(
            title="📊 FCKR Server Statistics",
            color=0x00ff00,
            timestamp=datetime.now(self.berlin_tz)
        )
        
        embed.add_field(name="👥 Total Members", value=str(total_members), inline=True)
        embed.add_field(name="🚀 Boosts", value=str(boost_count), inline=True)
        
        embed.set_footer(text="Statistics updated every 4 minutes")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='refresh')
    @commands.has_permissions(administrator=True)
    async def refresh_stats(self, ctx):
        """Manually refresh voice channel statistics (Admin only)"""
        if ctx.guild.id != self.fckr_server_id:
            await ctx.send("❌ This command can only be used on the FCKR server.")
            return
        
        # Manually trigger stats update
        guild = ctx.guild
        berlin_now = datetime.now(self.berlin_tz)
        
        # Reset daily joins if it's a new day
        if berlin_now.date() > self.last_reset:
            await self.count_todays_joins_from_audit_log()
            self.last_reset = berlin_now.date()
        
        # Get statistics
        total_members = guild.member_count
        boost_count = guild.premium_subscription_count or 0
        
        # Update channels
        await self.update_channel('total_members', f'👥 Total Members: {total_members}')
        await self.update_channel('boost_count', f'🚀 Boosts: {boost_count}')
        
        # Send combined confirmation and log to bot logging channel
        embed = discord.Embed(
            title="🔄 Manual Stats Refresh",
            description=f"Stats manually refreshed by {ctx.author.mention} - Voice channels updated!",
            color=0xffa500,
            timestamp=berlin_now
        )
        
        embed.add_field(name="👥 Total Members", value=str(total_members), inline=True)
        embed.add_field(name="🚀 Boosts", value=str(boost_count), inline=True)
        
        await ctx.send(embed=embed)
    
    # Manual refresh logging is now handled directly in the refresh_stats command

def setup(bot):
    bot.add_cog(VoiceStatsCog(bot))