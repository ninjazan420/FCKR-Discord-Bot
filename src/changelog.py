import discord
from discord.ext import commands
from datetime import datetime

class ChangelogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Changelog data - format: version: {date, features, fixes, notes}
        self.changelog_data = {
            "1.0.5": {
                "date": "07 June 2025",
                "title": "🌐 Language Standardization & Message Policy Update",
                "features": [
                    "Replaced private messages with ephemeral channel messages",
                    "Enhanced user privacy with dismissible error messages",
                    "Improved message consistency across all modules",
                    "Updated project documentation to reflect new policies"
                ],
                "fixes": [
                    "Replaced private DMs with ephemeral messages for better UX",
                    "Improved error message clarity and consistency"
                ],
                "technical": [
                    "Modified color_roles.py to use English strings and ephemeral messages",
                    "Updated counting.py to send ephemeral error messages in channel",
                    "Implemented consistent embed-based error messaging"
                ]
            },
            "1.0.4": {
                "date": "07 June 2025",
                "title": "🎮 Counting Game & Voice Channel Enhancements",
                "features": [
                    "Added counting game system with automatic validation",
                    "Added #️⃣ Counting voice channel to display current count",
                    "Added GitHub repository and issue links to help command",
                    "Smart restart detection for counting system",
                    "Admin commands for counting management (!fckr count, !fckr reset_count)"
                ],
                "fixes": [
                    "Automatic deletion of invalid counting messages with private user notifications",
                    "Prevention of same user counting twice in a row with ephemeral feedback",
                    "Green checkmark reactions for valid counting messages",
                    "Private DM notifications for deletion reasons instead of public messages"
                ],
                "technical": [
                    "Implemented CountingCog with on_message listener",
                    "Added counting channel history parsing for restart detection",
                    "Extended voice statistics to include counting display",
                    "Added COUNTING_CHANNEL_ID environment variable support"
                ]
            },
            "1.0.3": {
                "date": "07 June 2025",
                "title": "🔧 Critical Bug Fixes & Enhancements",
                "features": [
                    "Enhanced bot startup message with ASCII art and admin mentions",
                    "Added detailed system stats to startup console output",
                    "Improved startup logging with comprehensive system information"
                ],
                "fixes": [
                    "Fixed color role feedback messages not appearing (payload.channel_id bug)",
                    "Fixed changelog command date format parsing issue",
                    "Extended ephemeral message duration to match 7.5s cooldown",
                    "Corrected reaction handler channel reference errors"
                ],
                "technical": [
                    "Replaced undefined payload.channel_id with reaction.message.channel",
                    "Updated date parsing format in changelog sorting",
                    "Enhanced error handling in color role system"
                ]
            },
            "1.0.2": {
                "date": "07 June 2025",
                "title": "🎨 Color Role System Overhaul",
                "features": [
                    "Implemented toggle functionality for color roles (click again to remove)",
                    "Positioned color roles above FCKR role for better visibility",
                    "Replaced static message IDs with dynamic message creation",
                    "Added detailed confirmation messages for role changes",
                    "Added ASCII art to help command and README"
                ],
                "fixes": [
                    "Fixed changelog command date format parsing issue",
                    "Added proper feedback messages for color role changes via DM",
                    "Implemented 7.5-second cooldown for color role changes",
                    "Fixed toggle functionality for color roles (click again to remove)",
                    "Improved error handling and user feedback",
                    "Clean up environment variables by removing unused color message IDs",
                    "Enhanced role positioning verification system"
                ],
                "technical": [
                    "Overhauled color role system architecture",
                    "Implemented dynamic message management",
                    "Added role position verification and auto-correction"
                ]
            },
            "1.0.1": {
                "date": "06 June 2025",
                "title": "🔧 Bug Fixes & Command Updates",
                "features": [
                    "Added `!fckr neofetch` command for detailed system statistics",
                    "Updated help command to include neofetch command"
                ],
                "fixes": [
                    "Removed 'Today Joins' voice channel from automatic creation",
                    "Changed admin command from `!fckr stats` to `!fckr neofetch`",
                    "Fixed command conflicts between stats and system statistics"
                ],
                "technical": [
                    "Cleaned up voice statistics module",
                    "Simplified admin command structure"
                ]
            },
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
            timestamp=datetime.strptime(data["date"], "%d %B %Y")
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
            key=lambda x: datetime.strptime(x[1]["date"], "%d %B %Y"),
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