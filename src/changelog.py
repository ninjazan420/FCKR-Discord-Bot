import discord
from discord.ext import commands
from datetime import datetime

class ChangelogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Changelog data - format: version: {date, features, fixes, notes}
        self.changelog_data = {
            "1.0.0": {
                "date": "06 June 2025",
                "title": "🎉 Initial Release - Complete Rewrite",
                "features": [
                    "Clean modular architecture with cog-based system",
                    "Automatic voice channel statistics (Total Members, FCKR Members, Boosts, Daily Joins)",
                    "Real-time stats updates every 4 minutes",
                    "Enhanced help command with system monitoring",
                    "Color role system with 30 gradient colors",
                    "Reaction-based role selection in dedicated channel",
                    "Startup logging with timestamp and version info",
                    "Boost encouragement integration"
                ],
                "fixes": [
                    "Complete project restructure for better maintainability",
                    "Improved error handling and logging",
                    "Docker configuration optimization",
                    "Environment variable management"
                ],
                "technical": [
                    "Discord.py 2.5.2+ support",
                    "Psutil integration for system stats",
                    "Modular src/module structure",
                    "Automatic role hierarchy management"
                ]
            }
        }
    
    @commands.command(name='changelog')
    async def changelog_command(self, ctx, version=None):
        """Display changelog for specific version or latest versions"""
        
        if version:
            # Show specific version
            if version in self.changelog_data:
                await self.send_version_changelog(ctx, version)
            else:
                embed = discord.Embed(
                    title="❌ Version Not Found",
                    description=f"Version `{version}` not found in changelog.\n\nAvailable versions: {', '.join(self.changelog_data.keys())}",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
        else:
            # Show overview of all versions
            await self.send_changelog_overview(ctx)
    
    async def send_version_changelog(self, ctx, version):
        """Send detailed changelog for a specific version"""
        data = self.changelog_data[version]
        
        embed = discord.Embed(
            title=f"📋 Changelog - Version {version}",
            description=data["title"],
            color=0x00ff00,
            timestamp=datetime.strptime(data["date"], "%Y-%m-%d")
        )
        
        # Features
        if data.get("features"):
            features_text = "\n".join([f"• {feature}" for feature in data["features"]])
            embed.add_field(
                name="✨ New Features",
                value=features_text[:1024],  # Discord field limit
                inline=False
            )
        
        # Fixes
        if data.get("fixes"):
            fixes_text = "\n".join([f"• {fix}" for fix in data["fixes"]])
            embed.add_field(
                name="🔧 Improvements & Fixes",
                value=fixes_text[:1024],
                inline=False
            )
        
        # Technical
        if data.get("technical"):
            technical_text = "\n".join([f"• {tech}" for tech in data["technical"]])
            embed.add_field(
                name="⚙️ Technical Changes",
                value=technical_text[:1024],
                inline=False
            )
        
        embed.set_footer(text=f"FCKR Bot v{version} | Released on {data['date']}")
        await ctx.send(embed=embed)
    
    async def send_changelog_overview(self, ctx):
        """Send overview of all versions"""
        embed = discord.Embed(
            title="📋 FCKR Bot Changelog",
            description="Here's the complete version history of the FCKR Discord Bot.\n\nUse `!fckr changelog <version>` for detailed information.",
            color=0x00ff00
        )
        
        # Sort versions by date (newest first)
        sorted_versions = sorted(
            self.changelog_data.items(),
            key=lambda x: datetime.strptime(x[1]["date"], "%Y-%m-%d"),
            reverse=True
        )
        
        for version, data in sorted_versions:
            feature_count = len(data.get("features", []))
            fix_count = len(data.get("fixes", []))
            
            embed.add_field(
                name=f"🏷️ Version {version}",
                value=f"**{data['title']}**\n"
                      f"📅 Released: {data['date']}\n"
                      f"✨ {feature_count} new features\n"
                      f"🔧 {fix_count} improvements\n"
                      f"`!fckr changelog {version}` for details",
                inline=True
            )
        
        embed.add_field(
            name="🔗 Links",
            value="[GitHub Repository](https://github.com/ninjazan420/FCKR-Discord-Bot)\n"
                  "[Report Issues](https://github.com/ninjazan420/FCKR-Discord-Bot/issues)",
            inline=False
        )
        
        embed.set_footer(text="FCKR Community Bot | Made with ❤️ by ninjazan420")
        await ctx.send(embed=embed)
    
    def add_version(self, version, date, title, features=None, fixes=None, technical=None):
        """Add a new version to changelog (for future updates)"""
        self.changelog_data[version] = {
            "date": date,
            "title": title,
            "features": features or [],
            "fixes": fixes or [],
            "technical": technical or []
        }

def setup(bot):
    bot.add_cog(ChangelogCog(bot))