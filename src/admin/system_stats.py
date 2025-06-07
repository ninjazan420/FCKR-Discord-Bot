import discord
from discord.ext import commands
import psutil
import platform
import os
from datetime import datetime, timedelta
import sys

class SystemStatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.now()
    
    @commands.command(name='fckr')
    @commands.has_permissions(administrator=True)
    async def fckr_stats(self, ctx, subcommand: str = None):
        """Admin command for FCKR system statistics"""
        if subcommand == 'stats':
            await self.show_system_stats(ctx)
        else:
            embed = discord.Embed(
                title="🤖 FCKR Admin Commands",
                description="Available subcommands:",
                color=0x00ff00
            )
            embed.add_field(
                name="📊 `!fckr stats`",
                value="Show detailed system and bot statistics",
                inline=False
            )
            embed.set_footer(text="Admin only commands")
            await ctx.send(embed=embed)
    
    async def show_system_stats(self, ctx):
        """Display comprehensive system statistics"""
        try:
            # Get system information
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get bot uptime
            uptime = datetime.now() - self.start_time
            uptime_str = str(uptime).split('.')[0]  # Remove microseconds
            
            # Get system uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            system_uptime = datetime.now() - boot_time
            system_uptime_str = str(system_uptime).split('.')[0]
            
            # Get Python and discord.py versions
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            discord_version = discord.__version__
            
            # Get process information
            process = psutil.Process(os.getpid())
            bot_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Create main embed
            embed = discord.Embed(
                title="🤖 FCKR Bot System Statistics",
                description="Comprehensive system and bot information",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            # System Information
            embed.add_field(
                name="💻 System Information",
                value=f"**OS:** {platform.system()} {platform.release()}\n"
                      f"**Architecture:** {platform.machine()}\n"
                      f"**Hostname:** {platform.node()}\n"
                      f"**Python:** {python_version}\n"
                      f"**discord.py:** {discord_version}",
                inline=True
            )
            
            # Performance Metrics
            embed.add_field(
                name="📈 Performance Metrics",
                value=f"**CPU Usage:** {cpu_percent}%\n"
                      f"**RAM Usage:** {memory.percent}%\n"
                      f"**RAM Used:** {memory.used / 1024 / 1024 / 1024:.1f}GB\n"
                      f"**RAM Total:** {memory.total / 1024 / 1024 / 1024:.1f}GB\n"
                      f"**Bot Memory:** {bot_memory:.1f}MB",
                inline=True
            )
            
            # Storage Information
            embed.add_field(
                name="💾 Storage Information",
                value=f"**Disk Usage:** {disk.percent}%\n"
                      f"**Disk Used:** {disk.used / 1024 / 1024 / 1024:.1f}GB\n"
                      f"**Disk Total:** {disk.total / 1024 / 1024 / 1024:.1f}GB\n"
                      f"**Disk Free:** {disk.free / 1024 / 1024 / 1024:.1f}GB",
                inline=True
            )
            
            # Bot Statistics
            embed.add_field(
                name="🤖 Bot Statistics",
                value=f"**Bot Uptime:** {uptime_str}\n"
                      f"**System Uptime:** {system_uptime_str}\n"
                      f"**Guilds:** {len(self.bot.guilds)}\n"
                      f"**Users:** {len(self.bot.users)}\n"
                      f"**Latency:** {round(self.bot.latency * 1000)}ms",
                inline=True
            )
            
            # Network Information
            try:
                net_io = psutil.net_io_counters()
                embed.add_field(
                    name="🌐 Network Statistics",
                    value=f"**Bytes Sent:** {net_io.bytes_sent / 1024 / 1024:.1f}MB\n"
                          f"**Bytes Received:** {net_io.bytes_recv / 1024 / 1024:.1f}MB\n"
                          f"**Packets Sent:** {net_io.packets_sent:,}\n"
                          f"**Packets Received:** {net_io.packets_recv:,}",
                    inline=True
                )
            except:
                embed.add_field(
                    name="🌐 Network Statistics",
                    value="Network stats unavailable",
                    inline=True
                )
            
            # Dependencies Information
            try:
                import pkg_resources
                installed_packages = [d for d in pkg_resources.working_set]
                key_packages = ['discord.py', 'psutil', 'python-dotenv']
                
                deps_info = []
                for pkg in installed_packages:
                    if any(key in pkg.project_name.lower() for key in ['discord', 'psutil', 'dotenv']):
                        deps_info.append(f"**{pkg.project_name}:** {pkg.version}")
                
                if deps_info:
                    embed.add_field(
                        name="📦 Key Dependencies",
                        value="\n".join(deps_info[:5]),  # Limit to 5 to avoid embed limits
                        inline=True
                    )
            except:
                pass
            
            # Add footer with additional info
            embed.set_footer(
                text=f"Requested by {ctx.author.display_name} • PID: {os.getpid()}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else None
            )
            
            # Add thumbnail
            if self.bot.user.avatar:
                embed.set_thumbnail(url=self.bot.user.avatar.url)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to retrieve system statistics:\n```{str(e)}```",
                color=0xff0000
            )
            await ctx.send(embed=error_embed)

def setup(bot):
    bot.add_cog(SystemStatsCog(bot))