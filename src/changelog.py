import discord
from discord.ext import commands
from datetime import datetime

class ChangelogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Changelog data - format: version: {date, features, fixes, notes}
        self.changelog_data = {
            "1.3.2": {
                "date": "2025-06-26",
                "title": "🔧 Admin Mode Fix & Bot Response Optimization",
                "features": [
                    "Fixed admin mode to only respond to mentions and replies (not all messages)",
                    "Improved bot response logic for better user experience",
                    "Enhanced message handling to prevent spam responses",
                    "Added AI channel restriction - bot only responds in designated AI channel"
                ],
                "fixes": [
                    "Admin users no longer trigger bot responses on every message",
                    "Bot now only responds to @mentions or direct replies",
                    "Improved rate limiting and response filtering"
                ],
                "technical": [
                    "Updated handle_ai_chatbot_message function logic",
                    "Refined admin privilege handling",
                    "Added AI_CHANNEL_ID environment variable for channel restriction",
                    "Version bump to 1.3.2 across all components"
                ]
            },
            "1.3.1": {
                "date": "26 June 2025",
                "title": "🤖 AI Chatbot Character & Aww Command Improvements",
                "features": [
                    "Redesigned AI chatbot personality - now more cheeky, teasing, and playful",
                    "Removed coding-focused responses for more varied, unpredictable conversations",
                    "Updated emoji system to use text-based emojis (xd, :3, ^^, uwu, >:), :P)",
                    "Enhanced aww command to post direct images instead of URLs",
                    "Removed GIF support from aww command to prevent embedding issues"
                ],
                "fixes": [
                    "Fixed aww command image embedding by downloading and posting files directly",
                    "Improved AI chatbot response variety and personality consistency"
                ],
                "technical": [
                    "Modified AI system prompt to focus on playful teasing over technical expertise",
                    "Updated aww.py to use discord.File for direct image posting",
                    "Removed GIF endpoints from cataas.com integration",
                    "Enhanced character personality with sarcastic and witty response patterns"
                ]
            },
            "1.3.0": {
                "date": "25 June 2025",
                "title": "🤖 AI Chatbot with Memory & Statistics",
                "features": [
                    "Added interactive AI chatbot with personality (Fckr Chan) - playfully dominant and teasing character",
                    "Implemented conversation memory system that persists across bot restarts",
                    "Added rate limiting system (25 messages per hour per user) to prevent spam",
                    "Created `!fckr ai_stats` slash command to view chatbot usage statistics",
                    "Created `!fckr ai_memory` slash command to view personal conversation history",
                    "AI responds only to mentions, never to DMs for security",
                    "Comprehensive logging of all AI interactions in Discord channels"
                ],
                "fixes": [],
                "technical": [
                    "Integrated OpenRouter API for AI responses using Llama 3.1 8B model",
                    "Implemented session persistence with JSON file storage in `src/ai_chatbot/logs/`",
                    "Created modular AI system with character data loaded from `data/ai_chatbot.json`",
                    "Enhanced statistics tracking with user engagement metrics",
                    "Added `OPENROUTER_KEY` environment variable requirement",
                    "Built SessionManager class for conversation history and rate limiting",
                    "Implemented AIChatbotClient class for API communication and response generation"
                ]
            },
            "1.2.2": {
                "date": "23 June 2025",
                "title": "🐱 Random Cat Images & Aww Command",
                "features": [
                    "Added `!fckr aww` command to get random cat images from cataas.com",
                    "Integrated rate limiting (5 seconds cooldown) for aww command",
                    "Random cat ASCII art displayed with each aww command",
                    "Support for both static images and GIFs from cataas API"
                ],
                "fixes": [],
                "technical": [
                    "Created AwwCog in `aww.py` with aiohttp for API requests",
                    "Implemented user-based cooldown system with datetime tracking",
                    "Added multiple cataas.com endpoints for image variety",
                    "Integrated aww command into help system and main bot loader"
                ]
            },
            "1.2.1": {
                "date": "23 June 2025",
                "title": "🔧 Admin Permission Extensions",
                "features": [
                    "Extended admin checks to include bot admin status across all cogs",
                    "Bot admins can now access all administrative commands",
                    "Unified permission system between guild admins and bot admins"
                ],
                "fixes": [
                    "Fixed admin permission checks in multiple cogs",
                    "Improved consistency of admin access across all modules"
                ],
                "technical": [
                    "Modified admin permission checks in help.py and other admin cogs",
                    "Integrated AdminManagerCog.is_bot_admin() checks throughout codebase",
                    "Updated version numbering system for better tracking"
                ]
            },
            "1.2.0": {
                "date": "23 June 2025",
                "title": "👑 Bot Admin Management System",
                "features": [
                    "Added `!fckr admin add [user]` to grant bot admin privileges",
                    "Added `!fckr admin rm [user]` to revoke bot admin privileges",
                    "Added `!fckr admin list` to display all bot admins",
                    "Bot admins can now use all administrative commands"
                ],
                "fixes": [],
                "technical": [
                    "Created AdminManagerCog in `admin/addAdmin.py`",
                    "Admins are stored in `data/admins.json`",
                    "Integrated bot admin check into help command and other admin commands",
                    "Updated Docker configuration to persist admin data"
                ]
            },
            "1.1.1": {
                "date": "23 June 2025",
                "title": "🐱 Welcome Message Improvements & Bug Fixes",
                "features": [
                    "Added multiple random ASCII cat images to welcome messages for variety",
                    "Added links to server tag instructions and color selection guide",
                    "Enhanced welcome embed with comprehensive server navigation links"
                ],
                "fixes": [
                    "Fixed welcome message image display issues by removing problematic cat API integration",
                    "Removed excessive logging and debug messages from welcome system",
                    "Simplified welcome message logic for better reliability"
                ],
                "technical": [
                    "Replaced cat API with 15 different ASCII cat art variations",
                    "Added RULES_CHANNEL_ID, RANKING_CHANNEL_ID, SERVERTAG_CHANNEL_ID, and COLORS_CHANNEL_ID environment variables",
                    "Cleaned up cats.py code by removing unused imports and debug statements",
                    "Improved error handling in welcome message system"
                ]
            },
            "1.1.0": {
                "date": "19 June 2025",
                "title": "🐾 Welcome Cats & API Integration",
                "features": [
                    "Added an automatic welcome message for new members with a cute cat GIF from cataas API",
                    "Welcome embed includes links to rules, roles, and levels channels",
                    "User is pinged in the join log channel for a warm welcome"
                ],
                "fixes": [],
                "technical": [
                    "Created a new `cats.py` cog to handle the `on_member_join` event",
                    "Integrated `requests` to fetch data from the `cataas.com` API",
                    "Added `JOIN_LOG_CHANNEL` to environment variables for configuration",
                    "The color of the embed is randomized for a bit of fun"
                ]
            },
            "1.0.9": {
                "date": "18 June 2025",
                "title": "⚙️ Self-Check & Stability Enhancements",
                "features": [
                    "Added a self-check system that runs every 5 minutes to ensure cogs are initialized",
                    "Implemented a command anti-spam mechanism to prevent bot freezes",
                    "Replaced deleted counting messages with an informational embed"
                ],
                "fixes": [
                    "Reduced console noise by removing non-error feedback from the self-check system",
                    "Improved handling of deleted counting messages to maintain count integrity"
                ],
                "technical": [
                    "Created SelfCheckCog in admin/selfcheck.py with a 5-minute task loop",
                    "Added on_message_delete listener to CountingCog to handle deleted valid counts",
                    "Refined logging to only show warnings and errors for better monitoring"
                ]
            },
            "1.0.8": {
                "date": "16 June 2025",
                "title": "🔊 Live Voice Stats Updates",
                "features": [
                    "Voice channel statistics now update automatically when valid counting numbers are posted",
                    "Real-time counting display in voice channels without manual refresh",
                    "Seamless integration between counting system and voice stats"
                ],
                "fixes": [
                    "Eliminated need for manual !fckr refresh after counting",
                    "Improved user experience with instant stat updates"
                ],
                "technical": [
                    "Added voice stats update call to counting validation in counting.py",
                    "Integrated VoiceStatsCog.update_all_voice_stats() into counting workflow",
                    "Enhanced error handling for voice stats updates"
                ]
            },
            "1.0.7": {
                "date": "14 June 2025",
                "title": "🗑️ Message Purge System",
                "features": [
                    "Added !fckr purge command for administrators to delete messages",
                    "Configurable message deletion count (1-100 messages)",
                    "Admin-only access with permission validation",
                    "Auto-deleting confirmation messages for clean channels"
                ],
                "fixes": [
                    "Enhanced error handling for Discord API limitations",
                    "Proper permission checking before command execution",
                    "Graceful handling of missing permissions and API errors"
                ],
                "technical": [
                    "Created new PurgeCog in admin/purge.py",
                    "Integrated purge command into help system",
                    "Added comprehensive error handling and user feedback",
                    "Implemented Discord bulk delete with safety limits"
                ]
            },
            "1.0.6": {
                "date": "14 June 2025",
                "title": "🔢 Counting System Hotfix",
                "features": [
                    "Enhanced counting system initialization with 200 message history scan",
                    "Improved sequence validation for better restart detection",
                    "Added message ID tracking for debugging purposes"
                ],
                "fixes": [
                    "Fixed counting system resetting to 0 on wrong numbers - now maintains count",
                    "Replaced private messages with ephemeral channel messages (auto-delete after 10s)",
                    "Improved counting initialization to find correct sequence after bot restart",
                    "Enhanced error message clarity for counting violations"
                ],
                "technical": [
                    "Modified counting.py to use ephemeral messages instead of DMs",
                    "Removed count reset logic on wrong numbers - count persists",
                    "Enhanced initialize_counting() with better sequence detection",
                    "Increased message history scan from 100 to 200 messages",
                    "Added chronological sorting and sequence verification"
                ]
            },
            "1.0.5": {
                "date": "07 June 2025",
                "title": "🌐 Language Standardization & Message Policy Update",
                "features": [
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
        
        # Parse date with flexible format handling
        try:
            if len(data["date"].split()) == 3:  # "23 June 2025"
                timestamp = datetime.strptime(data["date"], "%d %B %Y")
            else:  # "December 2024"
                timestamp = datetime.strptime(data["date"], "%B %Y")
        except ValueError:
            timestamp = datetime.now()  # Fallback to current time
        
        embed = discord.Embed(
            title=f"📋 Changelog - Version {version}",
            description=data["title"],
            color=0x00ff00,
            timestamp=timestamp
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
        
        # Sort versions by date (newest first) with flexible date parsing
        def parse_date(date_str):
            try:
                if len(date_str.split()) == 3:  # "23 June 2025"
                    return datetime.strptime(date_str, "%d %B %Y")
                else:  # "December 2024"
                    return datetime.strptime(date_str, "%B %Y")
            except ValueError:
                return datetime.now()  # Fallback
        
        sorted_versions = sorted(
            self.changelog_data.items(),
            key=lambda x: parse_date(x[1]["date"]),
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