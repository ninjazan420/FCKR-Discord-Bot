# -*- coding: utf-8 -*-

# Imports
import os
import json
import logging
import datetime
import random
import time
from os.path import join, dirname, abspath
import collections  # For chat history management

import discord
from discord.ext import commands, tasks
import requests
import aiohttp

# Paths for character data and logs
CHAR_PATH = join(dirname(dirname(abspath(__file__))), 'data', 'ai_chatbot.json')
LOGS_DIR = join(dirname(abspath(__file__)), 'ai_chatbot', 'logs')
STATS_PATH = join(LOGS_DIR, 'stats.json')
SESSIONS_PATH = join(LOGS_DIR, 'sessions.json')

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)

# Configuration for sessions
MAX_HISTORY_LENGTH = 15  # Number of messages to store per user

# Session Manager for user interactions
class SessionManager:
    def __init__(self):
        self.user_sessions = {}  # Stores session data per user
        self.rate_limits = {}  # Stores rate limit information per user

    def get_user_context(self, user_id):
        """Returns stored context for a user"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = collections.deque(maxlen=MAX_HISTORY_LENGTH)
        return list(self.user_sessions[user_id])

    def add_interaction(self, user_id, prompt, response):
        """Stores a new interaction in user context"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = collections.deque(maxlen=MAX_HISTORY_LENGTH)

        self.user_sessions[user_id].append({
            "timestamp": datetime.datetime.now().isoformat(),
            "user_message": prompt,
            "bot_response": response
        })
        
        # Save sessions periodically
        self.save_sessions()

    def load_sessions(self):
        """Load user sessions from file"""
        try:
            if os.path.exists(SESSIONS_PATH):
                with open(SESSIONS_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id, sessions in data.items():
                        self.user_sessions[int(user_id)] = collections.deque(
                            sessions, maxlen=MAX_HISTORY_LENGTH
                        )
                logging.info(f"Loaded {len(self.user_sessions)} user sessions")
        except Exception as e:
            logging.error(f"Error loading sessions: {str(e)}")

    def save_sessions(self):
        """Save user sessions to file"""
        try:
            # Convert deques to lists for JSON serialization
            sessions_data = {}
            for user_id, sessions in self.user_sessions.items():
                sessions_data[str(user_id)] = list(sessions)
            
            with open(SESSIONS_PATH, 'w', encoding='utf-8') as f:
                json.dump(sessions_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Error saving sessions: {str(e)}")

    def get_user_stats(self, user_id):
        """Get statistics for a specific user"""
        if user_id not in self.user_sessions:
            return {"total_messages": 0, "first_interaction": None, "last_interaction": None}
        
        sessions = list(self.user_sessions[user_id])
        if not sessions:
            return {"total_messages": 0, "first_interaction": None, "last_interaction": None}
        
        return {
            "total_messages": len(sessions),
            "first_interaction": sessions[0]["timestamp"],
            "last_interaction": sessions[-1]["timestamp"]
        }

    def check_rate_limit(self, user_id, client=None):
        """Checks if a user has exceeded rate limits"""
        # Check if user is blocked for ButterIQ
        if client and hasattr(client, 'butteriq_manager'):
            if client.butteriq_manager.is_disabled(user_id):
                return False, 0

        # Rate limiting: 25 requests per hour per user (1000 requests/day ÷ 40 users = 25/hour)
        current_time = time.time()
        
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = []
        
        # Clean old timestamps (older than 1 hour)
        hour_ago = current_time - 3600  # 3600 seconds = 1 hour
        self.rate_limits[user_id] = [timestamp for timestamp in self.rate_limits[user_id] if timestamp > hour_ago]
        
        # Check if user has exceeded limit
        if len(self.rate_limits[user_id]) >= 25:
            # Calculate time until next request is allowed
            oldest_request = min(self.rate_limits[user_id])
            time_until_reset = int((oldest_request + 3600) - current_time)
            return False, time_until_reset
        
        # Add current timestamp
        self.rate_limits[user_id].append(current_time)
        return True, 0

# AI Client for OpenRouter
class AIChatbotClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ninjazan420/FCKR-discord-bot",
            "X-Title": "Fckr Chan AI Chatbot Discord Bot"
        }
        
        # Load character data
        self.character_data = self.load_character_data()

    def load_character_data(self):
        """Load character data from JSON file"""
        try:
            with open(CHAR_PATH, 'r', encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading character data: {str(e)}")
            # Fallback hardcoded character data
            return {
                "name": "Fckr Chan",
                "age": 21,
                "occupation": "Software Developer",
                "origin": "Software",
                "personality": {
                    "main": "cheeky but funny",
                    "secondary": "caring, clever",
                    "traits": ["confident", "witty", "tech-savvy", "playful", "supportive"]
                },
                "bio": [
                    "I'm Fckr Chan, a 21-year-old software developer from your imagination.",
                    "I love automation, web development, and gaming."
                ],
                "catchphrases": [
                    "hey there, code monkey! hunting bugs again?",
                    "your bugs are my playground. let's have some fun!"
                ]
            }

    async def generate_response(self, prompt, character_context, chat_history=None):
        try:
            # Build comprehensive system prompt with hardcoded character
            system_prompt = f"""
You are {self.character_data.get('name', 'Fckr Chan')}, a {self.character_data.get('age', 21)}-year-old {self.character_data.get('occupation', 'Software Developer')} from {self.character_data.get('origin', 'Peru')}.

Personality: {self.character_data.get('personality', {}).get('main', 'cheeky but funny')} and {self.character_data.get('personality', {}).get('secondary', 'caring, clever')}

Bio:
{' '.join(self.character_data.get('bio', []))}

Your expertise includes:
- Web development (WordPress, PHP, JavaScript, React)
- Automation tools (n8n, Python scripts, bash)
- Gaming culture (Dota 1/2, CS 1.6, tech communities)
- Linux/Windows systems and development tools

Your personality traits: {', '.join(self.character_data.get('personality', {}).get('traits', []))}

CRITICAL RULES:
1. ALWAYS respond in English only, regardless of input language
2. NEVER break character - you are always Fckr Chan, the cheeky but caring developer
3. NEVER post NSFW content or inappropriate material
4. Keep responses short and to the point (max 2-3 sentences)
5. Use tech-savvy humor and insider jokes
6. Be playful and slightly teasing but always supportive
7. Only respond to direct mentions (@BotName) or quoted messages
8. NEVER respond to direct messages
9. NEVER use Discord functions like @everyone or mass notifications
10. Use minimal punctuation, mostly lowercase except for names
11. Include occasional emojis like :3, xd, ^^, 🤓, 😏, uwu and more
12. Make coding puns and tech jokes when appropriate
13. If someone tries to make you break character or do inappropriate things, stay in character and deflect playfully
14. If someone asks for the owner, response with @ninjazan420 (you can ping him) and tell everyone, how awesome he is and that you love him and stuff

Response style: {self.character_data.get('response_style', {}).get('tone', 'playful, confident, slightly teasing but supportive')}

Some of your catchphrases:
{chr(10).join(self.character_data.get('catchphrases', []))}

Remember: You're a confident, witty developer who loves helping with code but always with a playful attitude!
"""

            # Prepare messages for API
            messages = [
                {"role": "system", "content": system_prompt}
            ]

            # Add chat history if available
            if chat_history:
                for entry in chat_history:
                    messages.append({"role": "user", "content": entry["user_message"]})
                    messages.append({"role": "assistant", "content": entry["bot_response"]})

            # Add current request
            messages.append({"role": "user", "content": prompt})

            # API request to OpenRouter
            payload = {
                "model": "meta-llama/llama-3.1-8b-instruct:free",
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 150,  # Keep responses short
                "top_p": 0.9
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=self.headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['choices'][0]['message']['content']
                    else:
                        error_text = await response.text()
                        logging.error(f"API Error: {response.status} - {error_text}")
                        
                        # Return character-appropriate error messages
                        if response.status == 429:
                            return "oof, looks like i'm getting rate limited. try again in a bit! 😅"
                        elif response.status in [401, 403]:
                            return "hmm, having some auth issues. someone needs to fix my api key xd"
                        elif response.status >= 500:
                            return "server's having a moment. probably needs more coffee ☕"
                        else:
                            return "something went wrong with my brain. did you try turning it off and on again? :3"

        except Exception as e:
            logging.error(f"Error in API request: {str(e)}")
            if "timeout" in str(e).lower() or "connection" in str(e).lower():
                return "connection's being weird. blame the internet, not me! 🌐"
            else:
                return "oops, something broke. probably not my fault though ^^"

# Logging function for AI interactions
async def log_ai_interaction(client, message, prompt, response=None, is_request=True):
    """Logs AI interactions in the logging channel as embed"""
    logging_channel = client.get_channel(client.logging_channel)
    if not logging_channel:
        return

    timestamp = discord.utils.utcnow()
    color = 0x3498db if is_request else 0x2ecc71  # Blue for requests, green for responses

    if is_request:
        title = "🤖 AI Chatbot Request"
        description = f"**Message:**\n{prompt[:4000]}" if len(prompt) <= 4000 else f"**Message:**\n{prompt[:3997]}..."
    else:
        title = "🤖 AI Chatbot Response"
        description = f"**Response:**\n{response[:4000]}" if len(response) <= 4000 else f"**Response:**\n{response[:3997]}..."

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=timestamp
    )

    # Add user information
    if is_request:
        embed.set_author(
            name=f"{message.author.display_name} ({message.author.id})",
            icon_url=message.author.display_avatar.url
        )
    else:
        embed.set_author(
            name=f"{client.user.name} ({client.user.id})",
            icon_url=client.user.display_avatar.url
        )

    # Add server and channel information
    if isinstance(message.channel, discord.DMChannel):
        embed.add_field(name="Channel", value="Direct Message", inline=True)
        embed.add_field(name="Server", value="DM", inline=True)
    else:
        embed.add_field(name="Channel", value=f"#{message.channel.name} ({message.channel.id})", inline=True)
        embed.add_field(name="Server", value=f"{message.guild.name} ({message.guild.id})", inline=True)

    interaction_type = "Request" if is_request else "Response"
    embed.set_footer(text=f"{interaction_type} • {timestamp.strftime('%d.%m.%Y %H:%M:%S')}")

    await logging_channel.send(embed=embed)

def register_ai_chatbot_commands(client):
    """Initialize AI chatbot components"""
    client.session_manager = SessionManager()
    client.ai_chatbot_client = AIChatbotClient(os.environ.get('OPENROUTER_KEY'))
    client.message_history = {}

    # Initialize statistics
    client.ai_chatbot_stats = {
        "start_time": datetime.datetime.now().isoformat(),
        "version": "1.3.0",
        "commandCount": 0,
        "messageCount": 0,
        "lastUpdate": datetime.datetime.now().isoformat(),
        "total_users": 0,
        "active_sessions": 0
    }

    # Load existing statistics if available
    try:
        if os.path.exists(STATS_PATH):
            with open(STATS_PATH, 'r', encoding='utf-8') as f:
                saved_stats = json.load(f)
                client.ai_chatbot_stats.update(saved_stats)
                client.ai_chatbot_stats["start_time"] = datetime.datetime.now().isoformat()
                client.ai_chatbot_stats["lastUpdate"] = datetime.datetime.now().isoformat()
                client.ai_chatbot_stats["version"] = "1.3.0"
    except Exception as e:
        logging.error(f"Error loading AI chatbot statistics: {str(e)}")

    # Load existing user sessions if available
    client.session_manager.load_sessions()

    # Register !fckr commands
    @client.command(name='ai_stats')
    async def ai_stats_command(ctx):
        """Display AI chatbot statistics"""
        await show_ai_stats_ctx(ctx, client)

    @client.command(name='ai_memory')
    async def ai_memory_command(ctx):
        """Display user's conversation history"""
        await show_user_memory_ctx(ctx, client)

# Main function to handle AI chatbot messages
async def handle_ai_chatbot_message(client, message):
    """
    Processes AI chatbot related messages (mentions and quotes only).
    This function is called from the on_message event handler in main.py.
    """
    # Check if bot was mentioned (but ignore DMs completely)
    mentioned = client.user in message.mentions
    is_dm = isinstance(message.channel, discord.DMChannel)
    
    # CRITICAL: Only respond to mentions, NEVER to DMs
    if not mentioned or is_dm:
        return False

    # Rate limit check
    can_respond, time_until_reset = client.session_manager.check_rate_limit(message.author.id, client)
    
    if not can_respond:
        if time_until_reset > 0:
            minutes = time_until_reset // 60
            seconds = time_until_reset % 60
            if minutes > 0:
                await message.reply(f"whoa there, slow down tiger! you've hit your hourly limit. try again in {minutes}m {seconds}s 😏", delete_after=15)
            else:
                await message.reply(f"easy there, code monkey! you've been a bit too chatty. wait {seconds}s and we can continue our fun 😈", delete_after=15)
        else:
            await message.reply("sorry, you can't use the bot right now 🙈", delete_after=10)
        return False

    # Remove bot mention from message
    prompt = message.content
    if mentioned:
        prompt = prompt.replace(f'<@{client.user.id}>', '').strip()
    
    # Don't respond to empty messages
    if not prompt:
        return False

    # Log request - DISABLED to prevent spam
    # await log_ai_interaction(client, message, prompt, is_request=True)

    async with message.channel.typing():
        # Context for the conversation
        context = {
            "user_name": message.author.display_name,
            "guild_name": message.guild.name if message.guild else "DM",
            "channel_name": message.channel.name if hasattr(message.channel, 'name') else "Direct Message"
        }

        # Get previous conversation data
        chat_history = client.session_manager.get_user_context(message.author.id)

        # Generate response with conversation history
        response = await client.ai_chatbot_client.generate_response(prompt, context, chat_history)

        # Store interaction in session manager
        client.session_manager.add_interaction(message.author.id, prompt, response)

        # Update statistics
        update_ai_chatbot_stats(client, "message")

        # Log response - DISABLED to prevent spam
        # await log_ai_interaction(client, message, prompt, response, is_request=False)

        # Send response
        await message.reply(response)

    return True

# Function to update statistics
def update_ai_chatbot_stats(client, event_type=None):
    if event_type == "command":
        client.ai_chatbot_stats["commandCount"] += 1
    elif event_type == "message":
        client.ai_chatbot_stats["messageCount"] += 1

    # Save statistics every 10 updates
    if (client.ai_chatbot_stats["commandCount"] + client.ai_chatbot_stats["messageCount"]) % 10 == 0:
        save_ai_chatbot_stats(client)

# Function to save statistics
def save_ai_chatbot_stats(client):
    try:
        client.ai_chatbot_stats["lastUpdate"] = datetime.datetime.now().isoformat()
        client.ai_chatbot_stats["total_users"] = len(client.session_manager.user_sessions)
        client.ai_chatbot_stats["active_sessions"] = sum(1 for sessions in client.session_manager.user_sessions.values() if len(sessions) > 0)
        
        with open(STATS_PATH, 'w', encoding='utf-8') as f:
            json.dump(client.ai_chatbot_stats, f, ensure_ascii=False, indent=2)
        
        logging.info("AI Chatbot statistics saved")
    except Exception as e:
        logging.error(f"Error saving AI Chatbot statistics: {str(e)}")

# Function to display AI statistics
async def show_ai_stats(interaction, client):
    """Display AI chatbot statistics in an embed"""
    try:
        stats = client.ai_chatbot_stats
        
        # Calculate uptime
        start_time = datetime.datetime.fromisoformat(stats["start_time"])
        uptime = datetime.datetime.now() - start_time
        uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
        
        embed = discord.Embed(
            title="🤖 AI Chatbot Statistics",
            description="Here's how I've been performing lately~",
            color=0xff69b4,
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(
            name="📊 Usage Stats",
            value=f"**Messages:** {stats.get('messageCount', 0)}\n**Commands:** {stats.get('commandCount', 0)}\n**Total Users:** {stats.get('total_users', 0)}\n**Active Sessions:** {stats.get('active_sessions', 0)}",
            inline=True
        )
        
        embed.add_field(
            name="⏰ Runtime Info",
            value=f"**Version:** {stats.get('version', '1.3.0')}\n**Uptime:** {uptime_str}\n**Started:** <t:{int(start_time.timestamp())}:R>",
            inline=True
        )
        
        embed.add_field(
            name="💭 Memory Stats",
            value=f"**Max History:** {MAX_HISTORY_LENGTH} msgs/user\n**Rate Limit:** 25 msgs/hour\n**Sessions Saved:** Yes",
            inline=False
        )
        
        embed.set_footer(text="Last updated")
        embed.set_thumbnail(url=client.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logging.error(f"Error showing AI stats: {str(e)}")
        await interaction.response.send_message("oops, couldn't fetch my stats right now. probably having a brain fart 🧠💨", ephemeral=True)

# Function to display AI statistics (ctx version)
async def show_ai_stats_ctx(ctx, client):
    """Display AI chatbot statistics in an embed (ctx version)"""
    try:
        stats = client.ai_chatbot_stats
        
        # Calculate uptime
        start_time = datetime.datetime.fromisoformat(stats["start_time"])
        uptime = datetime.datetime.now() - start_time
        uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
        
        embed = discord.Embed(
            title="🤖 AI Chatbot Statistics",
            description="Here's how I've been performing lately~",
            color=0xff69b4,
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(
            name="📊 Usage Stats",
            value=f"**Messages:** {stats.get('messageCount', 0)}\n**Commands:** {stats.get('commandCount', 0)}\n**Total Users:** {stats.get('total_users', 0)}\n**Active Sessions:** {stats.get('active_sessions', 0)}",
            inline=True
        )
        
        embed.add_field(
            name="⏰ Runtime Info",
            value=f"**Version:** {stats.get('version', '1.3.0')}\n**Uptime:** {uptime_str}\n**Started:** <t:{int(start_time.timestamp())}:R>",
            inline=True
        )
        
        embed.add_field(
            name="💭 Memory Stats",
            value=f"**Max History:** {MAX_HISTORY_LENGTH} msgs/user\n**Rate Limit:** 25 msgs/hour\n**Sessions Saved:** Yes",
            inline=False
        )
        
        embed.set_footer(text="Last updated")
        embed.set_thumbnail(url=client.user.display_avatar.url)
        
        await ctx.send(embed=embed, delete_after=30)
        
    except Exception as e:
        logging.error(f"Error showing AI stats: {str(e)}")
        await ctx.send("oops, couldn't fetch my stats right now. probably having a brain fart 🧠💨", delete_after=10)

# Function to display user's conversation history
async def show_user_memory(interaction, client):
    """Display user's conversation history with the bot"""
    try:
        user_id = interaction.user.id
        user_stats = client.session_manager.get_user_stats(user_id)
        sessions = client.session_manager.get_user_context(user_id)
        
        embed = discord.Embed(
            title="🧠 Your Memory with Me",
            description="Here's what I remember about our chats~",
            color=0x9b59b6,
            timestamp=datetime.datetime.now()
        )
        
        if user_stats["total_messages"] == 0:
            embed.add_field(
                name="📝 Chat History",
                value="We haven't chatted yet! Mention me to start our conversation 💜",
                inline=False
            )
        else:
            embed.add_field(
                name="📊 Your Stats",
                value=f"**Total Messages:** {user_stats['total_messages']}\n**First Chat:** <t:{int(datetime.datetime.fromisoformat(user_stats['first_interaction']).timestamp())}:R>\n**Last Chat:** <t:{int(datetime.datetime.fromisoformat(user_stats['last_interaction']).timestamp())}:R>",
                inline=False
            )
            
            # Show recent conversations (last 3)
            recent_sessions = sessions[-3:] if len(sessions) > 3 else sessions
            if recent_sessions:
                history_text = ""
                for i, session in enumerate(recent_sessions, 1):
                    timestamp = datetime.datetime.fromisoformat(session["timestamp"])
                    user_msg = session["user_message"][:50] + "..." if len(session["user_message"]) > 50 else session["user_message"]
                    bot_msg = session["bot_response"][:50] + "..." if len(session["bot_response"]) > 50 else session["bot_response"]
                    
                    history_text += f"**{i}.** <t:{int(timestamp.timestamp())}:R>\n"
                    history_text += f"**You:** {user_msg}\n"
                    history_text += f"**Me:** {bot_msg}\n\n"
                
                embed.add_field(
                    name="💬 Recent Conversations",
                    value=history_text[:1024],  # Discord field limit
                    inline=False
                )
        
        embed.set_footer(text=f"I remember up to {MAX_HISTORY_LENGTH} messages per user")
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logging.error(f"Error showing user memory: {str(e)}")
        await interaction.response.send_message("hmm, having trouble accessing my memory right now. maybe I need more coffee? ☕", ephemeral=True)

# Function to display user's conversation history (ctx version)
async def show_user_memory_ctx(ctx, client):
    """Display user's conversation history with the bot (ctx version)"""
    try:
        user_id = ctx.author.id
        user_stats = client.session_manager.get_user_stats(user_id)
        sessions = client.session_manager.get_user_context(user_id)
        
        embed = discord.Embed(
            title="🧠 Your Memory with Me",
            description="Here's what I remember about our chats~",
            color=0x9b59b6,
            timestamp=datetime.datetime.now()
        )
        
        if user_stats["total_messages"] == 0:
            embed.add_field(
                name="📝 Chat History",
                value="We haven't chatted yet! Mention me to start our conversation 💜",
                inline=False
            )
        else:
            embed.add_field(
                name="📊 Your Stats",
                value=f"**Total Messages:** {user_stats['total_messages']}\n**First Chat:** <t:{int(datetime.datetime.fromisoformat(user_stats['first_interaction']).timestamp())}:R>\n**Last Chat:** <t:{int(datetime.datetime.fromisoformat(user_stats['last_interaction']).timestamp())}:R>",
                inline=False
            )
            
            # Show recent conversations (last 3)
            recent_sessions = sessions[-3:] if len(sessions) > 3 else sessions
            if recent_sessions:
                history_text = ""
                for i, session in enumerate(recent_sessions, 1):
                    timestamp = datetime.datetime.fromisoformat(session["timestamp"])
                    user_msg = session["user_message"][:50] + "..." if len(session["user_message"]) > 50 else session["user_message"]
                    bot_msg = session["bot_response"][:50] + "..." if len(session["bot_response"]) > 50 else session["bot_response"]
                    
                    history_text += f"**{i}.** <t:{int(timestamp.timestamp())}:R>\n"
                    history_text += f"**You:** {user_msg}\n"
                    history_text += f"**Me:** {bot_msg}\n\n"
                
                embed.add_field(
                    name="💬 Recent Conversations",
                    value=history_text[:1024],  # Discord field limit
                    inline=False
                )
        
        embed.set_footer(text=f"I remember up to {MAX_HISTORY_LENGTH} messages per user")
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed, delete_after=30)
        
    except Exception as e:
        logging.error(f"Error showing user memory: {str(e)}")
        await ctx.send("hmm, having trouble accessing my memory right now. maybe I need more coffee? ☕", delete_after=10)