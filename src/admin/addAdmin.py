import discord
from discord.ext import commands
import json
import os

ADMINS_FILE = os.path.join('data', 'admins.json')

class AdminManagerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.admins = self.load_admins()

    def load_admins(self):
        if os.path.exists(ADMINS_FILE):
            with open(ADMINS_FILE, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []
        return []

    def save_admins(self):
        with open(ADMINS_FILE, 'w') as f:
            json.dump(self.admins, f, indent=4)

    async def is_bot_admin(self, user_id):
        return user_id in self.admins

    @commands.group(name='admin')
    @commands.has_permissions(administrator=True)
    async def admin_group(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid admin command. Use `!fckr admin add`, `!fckr admin rm`, or `!fckr admin list`.', delete_after=10)

    @admin_group.command(name='add')
    async def add_admin(self, ctx, member: discord.Member):
        if member.id in self.admins:
            await ctx.send(f'{member.display_name} is already a bot admin.', delete_after=10)
            return

        self.admins.append(member.id)
        self.save_admins()
        await ctx.send(f'Successfully added {member.display_name} to the bot admin list.', delete_after=10)

    @admin_group.command(name='rm')
    async def remove_admin(self, ctx, member: discord.Member):
        if member.id not in self.admins:
            await ctx.send(f'{member.display_name} is not a bot admin.', delete_after=10)
            return

        self.admins.remove(member.id)
        self.save_admins()
        await ctx.send(f'Successfully removed {member.display_name} from the bot admin list.', delete_after=10)

    @admin_group.command(name='list')
    async def list_admins(self, ctx):
        if not self.admins:
            await ctx.send('There are no bot admins.', delete_after=10)
            return

        embed = discord.Embed(title="Bot Admins", color=0x00ff00)
        admin_users = []
        for admin_id in self.admins:
            user = await self.bot.fetch_user(admin_id)
            if user:
                admin_users.append(f'**{user.name}** (`{user.id}`)')
        
        embed.description = "\n".join(admin_users)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(AdminManagerCog(bot))