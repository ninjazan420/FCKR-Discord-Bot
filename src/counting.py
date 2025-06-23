import discord
from discord.ext import commands
import os
import re
import asyncio
from datetime import datetime

class CountingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fckr_server_id = int(os.getenv('FCKR_SERVER', 0))
        self.counting_channel_id = int(os.getenv('COUNTING_CHANNEL_ID', 0))
        self.current_count = 0
        self.last_user_id = None
        self.last_message_id = None  # Add this line
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
        
        # Read the last 200 messages to find the highest valid count
        valid_messages = []
        try:
            async for message in counting_channel.history(limit=200, oldest_first=False):
                # Skip bot messages
                if message.author.bot:
                    continue
                
                # Check if message has green checkmark (valid count)
                has_checkmark = any(reaction.emoji == '✅' and reaction.me for reaction in message.reactions)
                
                if has_checkmark:
                    # Extract number from message
                    number = self.extract_number(message.content)
                    if number is not None:
                        valid_messages.append((number, message.author.id, message.created_at, message.id))
            
            # Sort by creation time to get chronological order (newest first)
            valid_messages.sort(key=lambda x: x[2], reverse=True)
            
            # Find the most recent valid count
            if valid_messages:
                # Take the most recent valid message (first in sorted list)
                self.current_count, self.last_user_id, _, message_id = valid_messages[0]
                print(f"✅ Found last valid count: {self.current_count} by user ID {self.last_user_id} (message ID: {message_id})")
                
                # Verify this is actually the correct sequence by checking if it's the highest number
                # in a valid sequence
                max_valid_count = 0
                for number, user_id, created_at, msg_id in reversed(valid_messages):  # oldest first
                    if number == max_valid_count + 1:
                        max_valid_count = number
                        if number > self.current_count:
                            self.current_count = number
                            self.last_user_id = user_id
                
                print(f"✅ Verified count sequence, current count: {self.current_count}")
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
                # Send ephemeral error message
                error_embed = discord.Embed(
                    title="❌ Invalid Message",
                    description=f"Your message '{message.content[:50]}' was deleted because it didn't contain a valid number.",
                    color=0xff0000
                )
                # Try to send as ephemeral reply, fallback to delete_after
                try:
                    if hasattr(message, 'reply'):
                        await message.reply(embed=error_embed, ephemeral=True, delete_after=10)
                    else:
                        await message.channel.send(f"{message.author.mention}", embed=error_embed, delete_after=10)
                except:
                    await message.channel.send(f"{message.author.mention}", embed=error_embed, delete_after=10)
                print(f"🗑️ Deleted non-numeric message from {message.author.display_name}: {message.content[:50]}")
            except Exception as e:
                print(f"❌ Error deleting message or sending ephemeral message: {e}")
            return
        
        # Check if it's the correct next number
        expected_number = self.current_count + 1
        
        if number == expected_number:
            # Check if same user posted twice in a row
            if self.last_user_id == message.author.id:
                try:
                    await message.delete()
                    # Send ephemeral error message
                    error_embed = discord.Embed(
                        title="❌ Same User Twice",
                        description="You cannot count twice in a row. Wait for someone else to count.",
                        color=0xff0000
                    )
                    # Try to send as ephemeral reply, fallback to delete_after
                    try:
                        if hasattr(message, 'reply'):
                            await message.reply(embed=error_embed, ephemeral=True, delete_after=10)
                        else:
                            await message.channel.send(f"{message.author.mention}", embed=error_embed, delete_after=10)
                    except:
                        await message.channel.send(f"{message.author.mention}", embed=error_embed, delete_after=10)
                    print(f"🗑️ Deleted message from {message.author.display_name}: same user can't count twice in a row")
                except Exception as e:
                    print(f"❌ Error deleting message or sending ephemeral message: {e}")
                return
            
            # Correct number! Add checkmark and update count
            try:
                await message.add_reaction('✅')
                self.current_count = number
                self.last_user_id = message.author.id
                self.last_message_id = message.id  # Store the message ID
                print(f"✅ Valid count {number} by {message.author.display_name}")
                
                # Update voice stats immediately after valid count
                voice_stats_cog = self.bot.get_cog('VoiceStatsCog')
                if voice_stats_cog:
                    await voice_stats_cog.update_all_voice_stats()
                    print(f"🔊 Voice stats updated after count {number}")
            except Exception as e:
                print(f"❌ Error adding reaction or updating voice stats: {e}")
        
        else:
            # Wrong number, delete message but DON'T reset count
            try:
                await message.delete()
                # Send ephemeral error message
                error_embed = discord.Embed(
                    title="❌ Wrong Number",
                    description=f"Your number {number} was wrong. The next number should be {expected_number}.",
                    color=0xff0000
                )
                # Try to send as ephemeral reply, fallback to delete_after
                try:
                    if hasattr(message, 'reply'):
                        await message.reply(embed=error_embed, ephemeral=True, delete_after=10)
                    else:
                        await message.channel.send(f"{message.author.mention}", embed=error_embed, delete_after=10)
                except:
                    await message.channel.send(f"{message.author.mention}", embed=error_embed, delete_after=10)
                print(f"🗑️ Deleted wrong number from {message.author.display_name}: {number} (expected {expected_number})")
                # DON'T reset count - just continue with the current count
            except Exception as e:
                print(f"❌ Error deleting message or sending ephemeral message: {e}")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Handle deleted counting messages"""
        # Skip if not in counting channel or from bot
        if (message.channel.id != self.counting_channel_id or 
            message.author.bot or 
            message.guild.id != self.fckr_server_id):
            return

        # Check if the deleted message was the last valid count
        if message.id == self.last_message_id:
            # To be safe, re-fetch the last valid count before the deleted one
            await self.initialize_counting()

            deleted_number = self.current_count
            next_number = self.current_count + 1

            counting_channel = self.bot.get_channel(self.counting_channel_id)
            if counting_channel:
                embed = discord.Embed(
                    title="🔢 Count Interrupted",
                    description=f"A message by **{message.author.display_name}** with the number **{deleted_number}** was deleted.",
                    color=0xffa500, # Orange
                    timestamp=datetime.now()
                )
                embed.add_field(name="Last Correct Number", value=str(self.current_count), inline=True)
                embed.add_field(name="Next Number", value=str(next_number), inline=True)
                embed.set_footer(text="Please continue counting from the next number.")

                await counting_channel.send(embed=embed)
                print(f"ℹ️ A deleted message was handled. Last count was {self.current_count}, next is {next_number}.")

            return
        
        # Check if it's the correct next number
        expected_number = self.current_count + 1
        
        if number == expected_number:
            # Check if same user posted twice in a row
            if self.last_user_id == message.author.id:
                try:
                    await message.delete()
                    # Send ephemeral error message
                    error_embed = discord.Embed(
                        title="❌ Same User Twice",
                        description="You cannot count twice in a row. Wait for someone else to count.",
                        color=0xff0000
                    )
                    # Try to send as ephemeral reply, fallback to delete_after
                    try:
                        if hasattr(message, 'reply'):
                            await message.reply(embed=error_embed, ephemeral=True, delete_after=10)
                        else:
                            await message.channel.send(f"{message.author.mention}", embed=error_embed, delete_after=10)
                    except:
                        await message.channel.send(f"{message.author.mention}", embed=error_embed, delete_after=10)
                    print(f"🗑️ Deleted message from {message.author.display_name}: same user can't count twice in a row")
                except Exception as e:
                    print(f"❌ Error deleting message or sending ephemeral message: {e}")
                return
            
            # Correct number! Add checkmark and update count
            try:
                await message.add_reaction('✅')
                self.current_count = number
                self.last_user_id = message.author.id
                self.last_message_id = message.id  # Store the message ID
                print(f"✅ Valid count {number} by {message.author.display_name}")
                
                # Update voice stats immediately after valid count
                voice_stats_cog = self.bot.get_cog('VoiceStatsCog')
                if voice_stats_cog:
                    await voice_stats_cog.update_all_voice_stats()
                    print(f"🔊 Voice stats updated after count {number}")
            except Exception as e:
                print(f"❌ Error adding reaction or updating voice stats: {e}")
        
        else:
            # Wrong number, delete message but DON'T reset count
            try:
                await message.delete()
                # Send ephemeral error message
                error_embed = discord.Embed(
                    title="❌ Wrong Number",
                    description=f"Your number {number} was wrong. The next number should be {expected_number}.",
                    color=0xff0000
                )
                # Try to send as ephemeral reply, fallback to delete_after
                try:
                    if hasattr(message, 'reply'):
                        await message.reply(embed=error_embed, ephemeral=True, delete_after=10)
                    else:
                        await message.channel.send(f"{message.author.mention}", embed=error_embed, delete_after=10)
                except:
                    await message.channel.send(f"{message.author.mention}", embed=error_embed, delete_after=10)
                print(f"🗑️ Deleted wrong number from {message.author.display_name}: {number} (expected {expected_number})")
                # DON'T reset count - just continue with the current count
            except Exception as e:
                print(f"❌ Error deleting message or sending ephemeral message: {e}")
    
    @commands.command(name='count')
    async def count_status(self, ctx):
        """Show current counting status (Admin only)"""
        # Check if user has admin permissions
        admin_cog = self.bot.get_cog('AdminManagerCog')
        is_bot_admin = await admin_cog.is_bot_admin(ctx.author.id) if admin_cog else False
        is_admin = ctx.author.guild_permissions.administrator or is_bot_admin
        
        if not is_admin:
            await ctx.send("❌ You need administrator permissions to use this command.", delete_after=10)
            return
            
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
        
        # Send as ephemeral if possible
        try:
            await ctx.send(embed=embed, ephemeral=True)
        except:
            await ctx.send(embed=embed)
    
    @commands.command(name='reset_count')
    async def reset_count(self, ctx, new_count: int = 0):
        """Reset the counting to a specific number (Admin only)"""
        # Check if user has admin permissions
        admin_cog = self.bot.get_cog('AdminManagerCog')
        is_bot_admin = await admin_cog.is_bot_admin(ctx.author.id) if admin_cog else False
        is_admin = ctx.author.guild_permissions.administrator or is_bot_admin
        
        if not is_admin:
            await ctx.send("❌ You need administrator permissions to use this command.", delete_after=10)
            return
            
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
        
        # Send as ephemeral if possible
        try:
            await ctx.send(embed=embed, ephemeral=True)
        except:
            await ctx.send(embed=embed)
        print(f"🔄 Count reset from {old_count} to {new_count} by {ctx.author.display_name}")

def setup(bot):
    bot.add_cog(CountingCog(bot))