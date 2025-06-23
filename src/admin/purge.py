import discord
from discord.ext import commands
import asyncio

class PurgeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='purge')
    async def purge_command(self, ctx, amount: int = None):
        """Purge messages from the current channel (Admin only)"""
        
        # Check if user has admin permissions
        admin_cog = self.bot.get_cog('AdminManagerCog')
        is_bot_admin = await admin_cog.is_bot_admin(ctx.author.id) if admin_cog else False
        is_admin = ctx.author.guild_permissions.administrator or is_bot_admin
        
        if not is_admin:
            embed = discord.Embed(
                title="❌ Access Denied",
                description="You need administrator permissions to use this command.",
                color=0xff0000
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Check if amount is provided
        if amount is None:
            embed = discord.Embed(
                title="❌ Missing Parameter",
                description="Please specify the number of messages to delete.\n\n**Usage:** `!fckr purge <amount>`\n**Example:** `!fckr purge 15`",
                color=0xff0000
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Validate amount
        if amount < 1:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="Amount must be at least 1.",
                color=0xff0000
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        if amount > 100:
            embed = discord.Embed(
                title="❌ Amount Too Large",
                description="Cannot delete more than 100 messages at once due to Discord limitations.",
                color=0xff0000
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        try:
            # Delete the command message first
            await ctx.message.delete()
            
            # Purge the specified amount of messages
            deleted = await ctx.channel.purge(limit=amount)
            
            # Send confirmation message
            embed = discord.Embed(
                title="🗑️ Messages Purged",
                description=f"Successfully deleted **{len(deleted)}** messages from {ctx.channel.mention}.",
                color=0x00ff00
            )
            embed.set_footer(text=f"Purged by {ctx.author.display_name}")
            
            # Send confirmation and auto-delete after 5 seconds
            await ctx.send(embed=embed, delete_after=5)
            
            print(f"🗑️ Purged {len(deleted)} messages in {ctx.channel.name} by {ctx.author.display_name}")
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to delete messages in this channel.",
                color=0xff0000
            )
            await ctx.send(embed=embed, delete_after=10)
            
        except discord.HTTPException as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to delete messages: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=embed, delete_after=10)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Unexpected Error",
                description=f"An unexpected error occurred: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=embed, delete_after=10)
            print(f"❌ Error in purge command: {e}")

def setup(bot):
    bot.add_cog(PurgeCog(bot))