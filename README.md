# FCKR-Discord-Bot 1.0.0

A modular Discord bot for the FCKR Tag & Community server that provides automated voice channel statistics, color role management, and community features.

## Features

- **Automatic Voice Channel Statistics**: Real-time updates every 4 minutes showing total members, FCKR tag members, boost count, and daily joins
- **Color Role System**: 30 gradient colors with reaction-based selection in dedicated channel
- **System Monitoring**: Built-in system stats display (CPU, RAM, OS info)
- **Changelog System**: Complete version history and update tracking
- **Modular Architecture**: Clean cog-based structure for easy maintenance and expansion
- **Docker Support**: Ready-to-deploy containerized setup
- **Comprehensive Logging**: Startup logging with timestamps and bot activity tracking

## Setup

1. Clone this repository
2. Configure your environment variables in `docker-compose.yml`:
   - `DISCORD_API_TOKEN`: Your Discord bot token
   - `FCKR_SERVER`: Your Discord server ID
   - `BOT_LOGGING`: Channel ID for bot logging
   - `ROLES_CHANNEL_ID`: Channel ID for color role selection

3. Build and run the bot using Docker:

   ```bash
   docker-compose up -d
   ```

## Commands

### Core Commands
- `!fckr help` - Display help information with system stats
- `!fckr stats` - Show current server statistics
- `!fckr colors` - Get color roles in the designated channel
- `!fckr changelog [version]` - View bot version history

### Admin Commands
- `!fckr setup_colors` - Manually setup color role system (admin only)

## Development

This bot is built using discord.py with a modular cog-based architecture. To set up a development environment:

1. Create a virtual environment: `python -m venv venv`
2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file with your environment variables
5. Run the bot: `python src/main.py`

## Version History

**Version 1.0.0** (Current)
- Complete rewrite with modular architecture
- Automatic voice channel statistics
- Color role system with 30 gradient colors
- Enhanced help command with system monitoring
- Changelog system for version tracking
- Startup logging and comprehensive error handling

## License

This project is licensed under the GPL-3.0 License - see the LICENSE file for details.