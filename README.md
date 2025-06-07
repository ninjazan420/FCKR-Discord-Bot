# FCKR-Discord-Bot 1.0.3

```
▄████  ▄█▄    █  █▀ █▄▄▄▄ 
█▀   ▀ █▀ ▀▄  █▄█   █  ▄▀ 
█▀▀    █   ▀  █▀▄   █▀▀▌  
█      █▄  ▄▀ █  █  █  █  
 █     ▀███▀    █     █   
  ▀            ▀     ▀    
                           
```

A modular Discord bot for the FCKR Tag & Community server that provides automated voice channel statistics, color role management, and community features.

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Docker Commands](#-docker-commands)
- [Commands](#-commands)
- [Development](#-development)
- [Environment Variables](#-environment-variables)
- [Version History](#-version-history)
- [License](#license)

## ✨ Features

- **🔄 Automatic Voice Channel Statistics**: Real-time updates every 4 minutes showing total members, FCKR tag members, boost count, and daily joins
- **🎨 Color Role System**: 30 gradient colors with reaction-based selection in dedicated channel
- **📊 System Monitoring**: Built-in system stats display (CPU, RAM, OS info)
- **📋 Changelog System**: Complete version history and update tracking
- **🧩 Modular Architecture**: Clean cog-based structure for easy maintenance and expansion
- **🐳 Docker Support**: Ready-to-deploy containerized setup
- **📝 Comprehensive Logging**: Startup logging with timestamps and bot activity tracking

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/ninjazan420/FCKR-Discord-Bot.git
   cd FCKR-Discord-Bot
   ```

2. **Configure environment variables**
   Edit `docker-compose.yml` and set your values:
   ```yaml
   environment:
     - DISCORD_API_TOKEN=your_bot_token_here
     - FCKR_SERVER=your_server_id_here
     - BOT_LOGGING=your_logging_channel_id_here
     - ROLES_CHANNEL_ID=your_roles_channel_id_here
   ```

3. **Start the bot**
   ```bash
   docker-compose up -d
   ```

## 🐳 Docker Commands

| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Start the bot in detached mode |
| `docker-compose down` | Stop and remove the bot container |
| `docker-compose restart` | Restart the bot |
| `docker-compose logs -f` | View live logs |
| `docker-compose pull` | Pull latest image updates |
| `docker-compose build` | Rebuild the container |
| `docker-compose ps` | Show container status |

## 🎮 Commands

### Core Commands
| Command | Description |
|---------|-------------|
| `!fckr help` | Display help information with system stats |
| `!fckr stats` | Show current server statistics |
| `!fckr colors` | Get color roles in the designated channel |
| `!fckr changelog [version]` | View bot version history |

### Admin Commands
| Command | Description | Permission |
|---------|-------------|------------|
| `!fckr setup_colors` | Manually setup color role system | Administrator |
| `!fckr refresh` | Manually refresh voice channel statistics | Administrator |
| `!fckr neofetch` | Show detailed system stats | Administrator |

## 💻 Development

This bot is built using discord.py with a modular cog-based architecture.

### Local Development Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

2. **Activate virtual environment**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r src/requirements.txt
   ```

4. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

5. **Run the bot**
   ```bash
   python src/main.py
   ```

### Project Structure
```
FCKR-Discord-Bot/
├── src/
│   ├── admin/
│   │   ├── help.py          # Help command
│   │   ├── system_stats.py  # System statistics
│   │   └── voice_stats.py   # Voice channel stats
│   ├── changelog.py         # Version history
│   ├── color_roles.py       # Color role system
│   ├── main.py             # Bot entry point
│   └── requirements.txt    # Python dependencies
├── docker-compose.yml      # Docker configuration
├── Dockerfile             # Container build file
└── README.md              # This file
```

## 🔧 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_API_TOKEN` | Your Discord bot token | ✅ |
| `FCKR_SERVER` | Your Discord server ID | ✅ |
| `BOT_LOGGING` | Channel ID for bot logging | ✅ |
| `ROLES_CHANNEL_ID` | Channel ID for color role selection | ✅ |

## 📈 Version History

<details open>
<summary><strong>Version 1.0.3</strong> (Current) - 🔧 Critical Bug Fixes & Enhancements</summary>

**🆕 Features:**
- Enhanced bot startup message with ASCII art and admin mentions
- Added detailed system stats to startup console output
- Improved startup logging with comprehensive system information

**🔧 Fixes:**
- Fixed color role feedback messages not appearing (payload.channel_id bug)
- Fixed changelog command date format parsing issue
- Extended ephemeral message duration to match 7.5s cooldown
- Corrected reaction handler channel reference errors

**⚙️ Technical:**
- Replaced undefined payload.channel_id with reaction.message.channel
- Updated date parsing format in changelog sorting
- Enhanced error handling in color role system

</details>

<details>
<summary><strong>Version 1.0.2</strong> - 🎨 Color Role System Overhaul</summary>

**🆕 Features:**
- Implemented toggle functionality for color roles (click again to remove)
- Positioned color roles above FCKR role for better visibility
- Replaced static message IDs with dynamic message creation
- Added detailed confirmation messages for role changes
- Added ASCII art to help command and README

**🔧 Fixes:**
- Improved error handling and user feedback
- Clean up environment variables by removing unused color message IDs
- Enhanced role positioning verification system

</details>

<details>
<summary><strong>Version 1.0.1</strong> - 🔧 Bug Fixes & Command Updates</summary>

**🆕 Features:**
- Added `!fckr neofetch` command for detailed system statistics
- Updated help command to include neofetch command

**🔧 Fixes:**
- Removed 'Today Joins' voice channel from automatic creation
- Changed admin command from `!fckr stats` to `!fckr neofetch`
- Fixed command conflicts between stats and system statistics

</details>

<details>
<summary><strong>Version 1.0.0</strong> - 🎉 Initial Release</summary>

**🆕 Features:**
- Complete rewrite with modular architecture
- Automatic voice channel statistics
- Color role system with 30 gradient colors
- System monitoring and logging
- Changelog system for version tracking
- Startup logging and comprehensive error handling

</details>

## 📄 License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ by [ninjazan420](https://github.com/ninjazan420)**

[Report Bug](https://github.com/ninjazan420/FCKR-Discord-Bot/issues) • [Request Feature](https://github.com/ninjazan420/FCKR-Discord-Bot/issues)

</div>