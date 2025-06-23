import discord
from discord.ext import commands
import aiohttp
import random
import asyncio
from datetime import datetime, timedelta

class AwwCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_used = {}
        self.cooldown_seconds = 5
        
        # Collection of random cat ASCII art (same as cats.py)
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

    def check_cooldown(self, user_id):
        """Check if user is on cooldown"""
        now = datetime.now()
        if user_id in self.last_used:
            time_diff = now - self.last_used[user_id]
            if time_diff.total_seconds() < self.cooldown_seconds:
                remaining = self.cooldown_seconds - time_diff.total_seconds()
                return False, remaining
        return True, 0

    @commands.command(name='aww')
    async def aww_command(self, ctx):
        """Get a random cute cat image from cataas.com"""
        
        # Check cooldown
        can_use, remaining = self.check_cooldown(ctx.author.id)
        if not can_use:
            await ctx.send(f"Meow! Please wait {remaining:.1f} more seconds before getting another cat! {random.choice(self.cat_ascii)}", delete_after=5)
            return
        
        # Update last used time
        self.last_used[ctx.author.id] = datetime.now()
        
        try:
            # Get random cat from cataas.com
            async with aiohttp.ClientSession() as session:
                # Try different endpoints for variety
                endpoints = [
                    "https://cataas.com/cat",
                    "https://cataas.com/cat/gif",
                    "https://cataas.com/cat/cute",
                    "https://cataas.com/cat/kitten"
                ]
                
                selected_endpoint = random.choice(endpoints)
                
                async with session.get(selected_endpoint) as response:
                    if response.status == 200:
                        # Get random cat ASCII
                        random_cat = random.choice(self.cat_ascii)
                        
                        # Send the image URL directly (no embed needed)
                        await ctx.send(f"{random_cat} Here's your random cat!\n{selected_endpoint}")
                    else:
                        # Fallback message
                        random_cat = random.choice(self.cat_ascii)
                        await ctx.send(f"Oops! The cat delivery service is having issues right now {random_cat} Try again later!")
                        
        except Exception as e:
            # Error fallback
            random_cat = random.choice(self.cat_ascii)
            await ctx.send(f"Meow! Something went wrong with the cat delivery {random_cat} Please try again later!")
            print(f"Error in aww command: {e}")

async def setup(bot):
    await bot.add_cog(AwwCog(bot))