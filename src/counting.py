import discord
from discord.ext import commands
import os
import re
from datetime import datetime

class CountingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fckr_server_id = int(os.getenv('FCKR_SERVER', 0))
        self.counting_channel_id = int(os.getenv('COUNTING_CHANNEL_ID', 0))
        self.current_count = 0
        self.last_user_id = None
        self.initialized = False
        
    @commands.Cog.listener()
    async def on_ready(self):
        """Initialize counting system when bot is ready"""
        if not self.initialized:
            await self.initialize_counting()
            self.initialized = True
    
    async def initialize_counting(self):
        """Read the last valid number from the counting channel"""
        guild = self.bot.get_guild(self.fckr_server_id)
        if not guild:
            print(f"❌ Guild with ID {self.fckr_server_id} not found")
            return
        
        counting_channel = guild.get_channel(self.counting_channel_id)
        if not counting_channel:
            print(f"❌ Counting channel with ID {self.counting_channel_id} not found")
            return
        
        print(f"🔢 Initializing counting system in {counting_channel.name}")
        
        # Read the last 100 messages to find the highest valid count
        try:
            async for message in counting_channel.history(limit=100):
                # Skip bot messages
                if message.author.bot:
                    continue
                
                # Check if message has green checkmark (valid count)
                has_checkmark = any(reaction.emoji == '✅' and reaction.me for reaction in message.reactions)
                
                if has_checkmark:
                    # Extract number from message
                    number = self.extract_number(message.content)
                    if number is not None:
                        self.current_count = number
                        self.last_user_id = message.author.id
                        print(f"✅ Found last valid count: {self.current_count} by {message.author.display_name}")
                        return
            
            # If no valid count found, start from 0
            self.current_count = 0
            self.last_user_id = None
            print(f"🔢 No valid count found, starting from 0")
            
        except Exception as e:
            print(f"❌ Error initializing counting: {e}")
            self.current_count = 0
            self.last_user_id = None
    
    def extract_number(self, content):
        """Extract the first number from a message"""
        # Look for numbers at the start of the message
        match = re.match(r'^(\d+)', content.strip())
        if match:
            return int(match.group(1))
        return None
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle counting messages"""
        # Skip if not in counting channel or from bot
        if (message.channel.id != self.counting_channel_id or 
            message.author.bot or 
            message.guild.id != self.fckr_server_id):
            return
        
        # Extract number from message
        number = self.extract_number(message.content)
        
        # If no number found, delete message
        if number is None:
            try:
                await message.delete()
                # Send ephemeral message to user
                await message.author.send(f"❌ Your message '{message.content[:50]}' was deleted because it didn't contain a valid number.")
                print(f"🗑️ Deleted non-numeric message from {message.author.display_name}: {message.content[:50]}")
            except Exception as e:
                print(f"❌ Error deleting message or sending DM: {e}")
            return
        
        # Check if it's the correct next number
        expected_number = self.current_count + 1
        
        if number == expected_number:
            # Check if same user posted twice in a row
            if self.last_user_id == message.author.id:
                try:
                    await message.delete()
                    # Send ephemeral message to user
                    await message.author.send("❌ You cannot count twice in a row. Wait for someone else to count.")
                    print(f"🗑️ Deleted message from {message.author.display_name}: same user can't count twice in a row")
                except Exception as e:
                    print(f"❌ Error deleting message or sending DM: {e}")
                return
            
            # Correct number! Add checkmark and update count
            try:
                await message.add_reaction('✅')
                self.current_count = number
                self.last_user_id = message.author.id
                print(f"✅ Valid count {number} by {message.author.display_name}")
            except Exception as e:
                print(f"❌ Error adding reaction: {e}")
        
        else:
            # Wrong number, delete message
            try:
                await message.delete()
                # Send ephemeral message to user
                await message.author.send(f"❌ Your number {number} was wrong. The next number should have been {expected_number}. Counting starts over!")
                print(f"🗑️ Deleted wrong number from {message.author.display_name}: {number} (expected {expected_number})")
                # Reset count if wrong number
                self.current_count = 0
                self.last_user_id = None
            except Exception as e:
                print(f"❌ Error deleting message or sending DM: {e}")
    
    @commands.command(name='count')
    @commands.has_permissions(administrator=True)
    async def count_status(self, ctx):
        """Show current counting status (Admin only)"""
        if ctx.guild.id != self.fckr_server_id:
            await ctx.send("❌ This command can only be used on the FCKR server.")
            return
        
        counting_channel = ctx.guild.get_channel(self.counting_channel_id)
        channel_name = counting_channel.name if counting_channel else "Unknown"
        
        last_user = ctx.guild.get_member(self.last_user_id) if self.last_user_id else None
        last_user_name = last_user.display_name if last_user else "None"
        
        embed = discord.Embed(
            title="🔢 Counting Status",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Current Count", value=str(self.current_count), inline=True)
        embed.add_field(name="Next Expected", value=str(self.current_count + 1), inline=True)
        embed.add_field(name="Last User", value=last_user_name, inline=True)
        embed.add_field(name="Channel", value=f"#{channel_name}", inline=True)
        embed.add_field(name="Initialized", value="✅ Yes" if self.initialized else "❌ No", inline=True)
        
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='reset_count')
    @commands.has_permissions(administrator=True)
    async def reset_count(self, ctx, new_count: int = 0):
        """Reset the counting to a specific number (Admin only)"""
        if ctx.guild.id != self.fckr_server_id:
            await ctx.send("❌ This command can only be used on the FCKR server.")
            return
        
        old_count = self.current_count
        self.current_count = new_count
        self.last_user_id = None
        
        embed = discord.Embed(
            title="🔄 Counting Reset",
            description=f"Count reset from {old_count} to {new_count}",
            color=0xffa500,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="New Count", value=str(new_count), inline=True)
        embed.add_field(name="Next Expected", value=str(new_count + 1), inline=True)
        embed.add_field(name="Reset by", value=ctx.author.display_name, inline=True)
        
        await ctx.send(embed=embed)
        print(f"🔄 Count reset from {old_count} to {new_count} by {ctx.author.display_name}")

def setup(bot):
    bot.add_cog(CountingCog(bot))