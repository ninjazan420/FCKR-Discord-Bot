import discord
from discord.ext import commands
import os
import requests
import random

class Cats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        join_log_channel_id = os.getenv("JOIN_LOG_CHANNEL")
        if not join_log_channel_id:
            return

        channel = self.bot.get_channel(int(join_log_channel_id))
        if not channel:
            return

        # Fetch a random cat gif with text
        welcome_text = "Welcome to FCKR Tag & Giveaway server"
        url = f"https://cataas.com/cat/gif/says/{welcome_text.replace(' ', '%20')}?json=true"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes
            cat_data = response.json()
            cat_url = f"https://cataas.com{cat_data['url']}"

            # Create embed
            embed = discord.Embed(
                title=f"Welcome {member.name}!",
                description=f"Hey {member.mention}, welcome to the FCKR server! We're happy to have you here. 💖\n\n"
                            f"Please take a moment to read our [rules](https://discord.com/channels/1369072140195860512/1371417622570336317). \n"
                            f"You can get your roles in the [roles](https://discord.com/channels/1369072140195860512/1371453802431123546) channel and check your [levels](https://discord.com/channels/1369072140195860512/1371483267848732691) here.",
                color=discord.Color.random()
            )
            embed.set_image(url=cat_url)
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="Have a great time!")

            await channel.send(embed=embed)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching cat from cataas: {e}")
            # Fallback message if API fails
            await channel.send(f"Welcome {member.mention}! The cat delivery service is currently sleeping, but we're happy to have you!")

async def setup(bot):
    await bot.add_cog(Cats(bot))