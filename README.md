# FCKR-Discord-Bot

A Discord bot to make the application process of private servers easier for admins.

## Features

- Automatically sends application instructions to new members
- Collects application information through a user-friendly form
- **Supports Discord's native membership screening applications**
- Posts applications to a dedicated admin channel with approve/reject/interview buttons
- Logs all application activity in the decision channel
- Notifies users of application decisions
- Admin commands to manage moderator permissions
- Automatic detection of pending applications
- Detailed debugging and troubleshooting tools

## Setup

1. Clone this repository
2. Configure your environment variables in `docker-compose.yml`:
   - `DISCORD_API_TOKEN`: Your Discord bot token
   - `DECISION_CHANNEL`: Channel ID where applications will be posted
   - `ADMIN_USER_ID`: User ID of the admin who can manage applications

3. Build and run the bot using Docker:

   ```bash
   docker-compose up -d
   ```

## Usage

When a new user joins your server, the bot will automatically send them a DM with application instructions. Admins can review applications in the designated decision channel and approve or reject them with a single click.

### Commands

#### Application Commands
- `/apply` - Opens the application form (can be used if the automatic DM was missed)
- `/pending` - Lists all pending applications (admin only)

#### Basic Commands
- `.fcping` - Checks if the bot is responsive
- `.fcinfo` - Displays detailed information about the bot and server (admin/mod only)

#### Moderation Commands
- `.fcadd <user_id>` - Adds a user to the authorized moderators list (admin only)
- `.fcrm <user_id>` - Removes a user from the authorized moderators list (admin only)
- `.fclog` - Shows the last 10 application decisions with details (admin/mod only)

#### Troubleshooting Commands
- `.fcdebug` - Shows detailed debug information about the bot's state (admin/mod only)
- `.fcrefresh` - Manually refreshes the pending applications list by checking server members (admin/mod only)
- `.fcchannel [channel_id]` - Checks or updates the decision channel (admin only)

## Development

This bot is built using discord.py. To set up a development environment:

1. Create a virtual environment: `python -m venv venv`
2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the bot: `python src/main.py`

## License

This project is licensed under the GPL-3.0 License - see the LICENSE file for details.