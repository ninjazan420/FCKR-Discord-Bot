#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ===== 1. IMPORTS =====
# Standard library imports
import os
import json
import asyncio
import datetime
from collections import defaultdict

# Third party imports
import discord
from discord.ext import commands, tasks
from discord import ButtonStyle, Interaction
from discord.ui import Button, View

# Local imports will be done after defining helper functions to avoid circular imports

# ===== 2. CONFIGURATION AND SETUP =====
# Environment variables
token = str(os.environ['DISCORD_API_TOKEN'])
decision_channel_id = int(os.environ['DECISION_CHANNEL'])
admin_user_id = int(os.environ['ADMIN_USER_ID'])

# Bot initialization
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(
    command_prefix=commands.when_mentioned_or("."),
    description='FCKR Discord Bot Version: 0.0.4\nCreated by: FCKR Team',
    intents=intents
)

# Shared variables
client.admin_user_id = admin_user_id
client.decision_channel_id = decision_channel_id
client.pending_applications = {}
client.authorized_mods = set()  # Set of user IDs that are authorized to make decisions
client.application_history = []  # List to store application history (last 10 applications)
client.dm_queue = asyncio.Queue()  # Queue for rate-limiting DMs
client.dm_lock = asyncio.Lock()  # Lock for DM sending

# ===== 3. HELPER FUNCTIONS =====
async def log_to_channel(message):
    """Log a message to the decision channel"""
    channel = client.get_channel(decision_channel_id)
    if channel:
        await channel.send(f"```\n{datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')} | {message}```")
    else:
        print(f"Warning: Decision channel with ID {decision_channel_id} not found!")

async def send_dm_with_rate_limit(user, content=None, embed=None, view=None):
    """Send a DM to a user with rate limiting to avoid Discord's rate limits"""
    # Create a task to be queued
    async def _send_dm_task():
        try:
            # Wait for the lock to be available (ensures we don't send DMs too quickly)
            async with client.dm_lock:
                # Add a small delay to avoid rate limits
                await asyncio.sleep(1.5)  # 1.5 seconds between DMs

                # Create a DM channel with the user
                dm_channel = await user.create_dm()

                # Send the message
                if content and embed and view:
                    await dm_channel.send(content=content, embed=embed, view=view)
                elif content and embed:
                    await dm_channel.send(content=content, embed=embed)
                elif content and view:
                    await dm_channel.send(content=content, view=view)
                elif embed and view:
                    await dm_channel.send(embed=embed, view=view)
                elif content:
                    await dm_channel.send(content=content)
                elif embed:
                    await dm_channel.send(embed=embed)
                elif view:
                    await dm_channel.send(view=view)

                return True, None
        except discord.Forbidden:
            return False, "User has DMs disabled"
        except Exception as e:
            return False, str(e)

    # Add the task to the queue
    task = asyncio.create_task(_send_dm_task())
    await client.dm_queue.put(task)

    # Return the task so the caller can await it if needed
    return task

async def process_dm_queue():
    """Process the DM queue in the background"""
    while True:
        try:
            # Get the next task from the queue
            task = await client.dm_queue.get()

            # Wait for the task to complete
            await task

            # Mark the task as done
            client.dm_queue.task_done()
        except Exception as e:
            print(f"Error processing DM queue: {e}")
            # Continue processing the queue even if there's an error
            await asyncio.sleep(1)

# Now import local modules after defining helper functions
from application_handler import register_application_commands, ApplicationView

# ===== 4. BOT EVENTS =====
@client.event
async def on_ready():
    # Set start time for uptime calculation
    client.start_time = datetime.datetime.now()

    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print(f"Connected to {len(client.guilds)} guilds")

    # Try to find the decision channel using fetch_channel first (more reliable)
    try:
        print(f"Attempting to fetch decision channel with ID {decision_channel_id}...")
        channel = await client.fetch_channel(decision_channel_id)
        print(f"Decision channel found via fetch_channel: {channel.name} (ID: {channel.id})")
    except Exception as e:
        print(f"Error fetching decision channel with fetch_channel: {e}")
        # Fallback to get_channel
        channel = client.get_channel(decision_channel_id)
        if channel:
            print(f"Decision channel found via get_channel: {channel.name} (ID: {channel.id})")
        else:
            channel = None
            print(f"⚠️ WARNING: Decision channel with ID {decision_channel_id} not found with either method!")

    # List all available channels for debugging
    print("Available channels:")
    available_channels = []
    for guild in client.guilds:
        print(f"Guild: {guild.name} (ID: {guild.id})")
        for ch in guild.text_channels:
            channel_info = f"- {ch.name} (ID: {ch.id})"
            print(channel_info)
            available_channels.append(f"{ch.name} (ID: {ch.id}) in {guild.name}")

    # If we found the channel, send startup messages
    if channel:
        try:
            await channel.send("```\n🔍 DEBUG: Checking decision channel configuration...```")
            await channel.send(f"```\nDecision channel found: {channel.name} (ID: {channel.id})```")
            await log_to_channel("🟢 Bot started - Version v0.0.4")

            # Send a test message to verify the channel is working
            test_message = await channel.send("🧪 Testing channel permissions and visibility...")
            await test_message.delete()
            print("Channel test successful - bot can send and delete messages")
        except Exception as e:
            print(f"Error sending messages to decision channel: {e}")
    else:
        print("⚠️ WARNING: Could not send startup messages to decision channel!")
        print(f"Available channels: {available_channels}")

    # Start the DM queue processor
    asyncio.create_task(process_dm_queue())

    # Set status
    await client.change_presence(activity=discord.Game(name="Managing applications"))

    # Check for pending members in all guilds
    await check_for_pending_members()

    # Sync application commands
    try:
        print("Syncing application commands...")
        await client.tree.sync()
        print("Application commands synced successfully")
    except Exception as e:
        print(f"Error syncing application commands: {e}")

    print("Bot initialization complete")
    print("------")

async def check_for_pending_members():
    """Check for members who have completed membership screening but are still pending approval"""
    print("Checking for pending members in all guilds...")

    for guild in client.guilds:
        try:
            # Check if the guild has membership screening enabled
            if "MEMBER_VERIFICATION_GATE_ENABLED" in guild.features:
                print(f"Guild {guild.name} has membership screening enabled")

                # Get all members with only the @everyone role
                pending_members = [m for m in guild.members if len(m.roles) == 1 and not m.bot]

                if pending_members:
                    print(f"Found {len(pending_members)} pending members in {guild.name}")

                    # Get the decision channel
                    decision_channel = client.get_channel(client.decision_channel_id)
                    if not decision_channel:
                        print(f"Error: Decision channel not found for pending members in {guild.name}")
                        continue

                    # Create a summary message
                    summary_embed = discord.Embed(
                        title=f"Pending Server Applications in {guild.name}",
                        description=f"Found {len(pending_members)} members who have completed membership screening and are waiting for approval.",
                        color=discord.Color.blue(),
                        timestamp=datetime.datetime.now()
                    )

                    await decision_channel.send(embed=summary_embed)

                    # Process each pending member
                    for member in pending_members:
                        # Skip if already in pending applications
                        if member.id in client.pending_applications:
                            continue

                        print(f"Processing pending member: {member.name} (ID: {member.id})")

                        # Create an embed for the application
                        embed = discord.Embed(
                            title=f"New Server Application from {member.name}",
                            description=f"User ID: {member.id}\n\nThis user has completed Discord's membership screening and is waiting for approval.",
                            color=discord.Color.gold(),
                            timestamp=datetime.datetime.now()
                        )

                        # Add user information
                        embed.set_author(name=f"{member.name}", icon_url=member.display_avatar.url)
                        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
                        embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)

                        # Create decision buttons
                        from application_handler import ApplicationDecisionView
                        view = ApplicationDecisionView(client, member.id)

                        # Send the application to the decision channel
                        try:
                            application_message = await decision_channel.send(embed=embed, view=view)

                            # Store the application in the pending applications
                            client.pending_applications[member.id] = {
                                "user_id": member.id,
                                "message_id": application_message.id,
                                "timestamp": datetime.datetime.now(),
                                "guild_id": guild.id,
                                "source": "membership_screening"
                            }

                            # Log the event
                            await log_to_channel(f"📝 Existing server application detected from {member.name} (ID: {member.id})")
                        except Exception as e:
                            print(f"Error sending application message for {member.name}: {e}")
                else:
                    print(f"No pending members found in {guild.name}")
        except Exception as e:
            print(f"Error checking pending members in guild {guild.name}: {e}")

@client.event
async def on_member_join(member):
    """Send a welcome message with application instructions when a new member joins"""
    print(f"New member joined: {member.name} (ID: {member.id})")

    # Check if the server is set to private (requires application)
    guild = member.guild

    # Check if the guild has membership screening enabled
    has_screening = "MEMBER_VERIFICATION_GATE_ENABLED" in guild.features
    print(f"Guild {guild.name} has membership screening enabled: {has_screening}")

    # Check if the member is already in pending applications
    already_pending = member.id in client.pending_applications
    print(f"Member {member.name} already in pending_applications: {already_pending}")

    # If the member is not already in pending applications, create an application
    if not already_pending:
        # Check if the member has no roles (only @everyone)
        is_pending = len(member.roles) == 1 and not member.bot
        print(f"Member {member.name} (ID: {member.id}) is pending: {is_pending}")

        if is_pending:
            print(f"Creating application for new member: {member.name} (ID: {member.id})")

            # Create an embed for the application
            embed = discord.Embed(
                title=f"New Server Application from {member.name}",
                description=f"User ID: {member.id}\n\nThis user has just joined the server and is waiting for approval.",
                color=discord.Color.gold(),
                timestamp=datetime.datetime.now()
            )

            # Add user information
            embed.set_author(name=f"{member.name}", icon_url=member.display_avatar.url)
            embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
            embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)

            # Create decision buttons
            from application_handler import ApplicationDecisionView
            view = ApplicationDecisionView(client, member.id)

            # Try to fetch the channel using fetch_channel first (more reliable)
            try:
                decision_channel = await client.fetch_channel(client.decision_channel_id)
                print(f"Decision channel found via fetch_channel: {decision_channel.name} (ID: {decision_channel.id})")
            except Exception as e:
                print(f"Error fetching decision channel with fetch_channel: {e}")
                # Fallback to get_channel
                decision_channel = client.get_channel(client.decision_channel_id)
                if decision_channel:
                    print(f"Decision channel found via get_channel: {decision_channel.name} (ID: {decision_channel.id})")
                else:
                    print(f"⚠️ WARNING: Decision channel with ID {client.decision_channel_id} not found!")

            # Send the application to the decision channel
            if decision_channel:
                try:
                    print(f"Sending application message for {member.name} (ID: {member.id}) to decision channel")
                    application_message = await decision_channel.send(embed=embed, view=view)
                    print(f"Application message sent with ID: {application_message.id}")

                    # Store the application in the pending applications
                    client.pending_applications[member.id] = {
                        "user_id": member.id,
                        "message_id": application_message.id,
                        "timestamp": datetime.datetime.now(),
                        "guild_id": guild.id,
                        "source": "member_join"
                    }
                    print(f"Application stored in pending_applications. Current count: {len(client.pending_applications)}")

                    # Also send a notification message to make sure new applications are visible
                    await decision_channel.send(
                        f"@here 📝 **NEW SERVER APPLICATION** from {member.name} (ID: {member.id}). Please review it above."
                    )
                    print(f"Notification message sent for {member.name} (ID: {member.id})")

                    # Log the event
                    await log_to_channel(f"📝 New server application detected from {member.name} (ID: {member.id}) on join")
                except Exception as e:
                    print(f"Error sending application message: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"⚠️ ERROR: Could not find decision channel with ID {client.decision_channel_id}")

    # For now, we'll assume all servers using this bot are private and require applications
    # In a future version, this could be configurable per server

    # Create the application button
    view = ApplicationView(client)

    # Create welcome message with application button
    embed = discord.Embed(
        title=f"Welcome to {guild.name}!",
        description="This is a private server. Please apply for membership by clicking the button below.",
        color=discord.Color.blue()
    )

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    embed.add_field(
        name="Application Process",
        value="After submitting your application, the server administrators will review it and make a decision."
    )

    # Use the rate-limited DM sender
    dm_task = await send_dm_with_rate_limit(member, embed=embed, view=view)
    success, error_message = await dm_task

    if success:
        # Log the event
        await log_to_channel(f"📥 New member joined: {member.name} (ID: {member.id}). Application instructions sent.")
    else:
        # Log the error
        if error_message == "User has DMs disabled":
            await log_to_channel(f"⚠️ Could not send application instructions to {member.name} (ID: {member.id}). User has DMs disabled.")
        else:
            await log_to_channel(f"❌ Error sending application instructions to {member.name} (ID: {member.id}): {error_message}")

@client.event
async def on_member_update(before, after):
    """Handle member updates, particularly for tracking moderation decisions and membership screening"""
    print(f"Member update detected: {after.name} (ID: {after.id})")
    print(f"Before roles: {[r.name for r in before.roles]}")
    print(f"After roles: {[r.name for r in after.roles]}")

    # Check if the member's roles have changed
    if before.roles != after.roles:
        print(f"Role change detected for {after.name} (ID: {after.id})")

        # Check if this user has a pending application
        if after.id in client.pending_applications:
            print(f"User {after.name} (ID: {after.id}) has a pending application and roles changed")
            # Get the guild
            guild = after.guild

            # Determine if the user has been approved or rejected
            # This depends on how your server is set up - typically there's a "Member" role or similar
            # that gets added when a user is approved

            # Check for new roles that weren't there before
            new_roles = [role for role in after.roles if role not in before.roles]
            print(f"New roles added: {[r.name for r in new_roles]}")

            # If there are new roles, the user might have been approved
            if new_roles:
                print(f"User {after.name} (ID: {after.id}) received new roles, likely approved")
                # Get the current time for the decision
                decision_time = datetime.datetime.now()

                # Get application data if available
                app_data = client.pending_applications.get(after.id, {})
                message_id = app_data.get("message_id")
                print(f"Application data: {app_data}")

                # Try to update the application message if it exists
                if message_id:
                    try:
                        # Try to fetch the channel using fetch_channel first (more reliable)
                        try:
                            channel = await client.fetch_channel(client.decision_channel_id)
                            print(f"Decision channel found via fetch_channel: {channel.name} (ID: {channel.id})")
                        except Exception as e:
                            print(f"Error fetching decision channel with fetch_channel: {e}")
                            # Fallback to get_channel
                            channel = client.get_channel(client.decision_channel_id)
                            if channel:
                                print(f"Decision channel found via get_channel: {channel.name} (ID: {channel.id})")
                            else:
                                print(f"⚠️ WARNING: Decision channel with ID {client.decision_channel_id} not found!")

                        if channel:
                            try:
                                message = await channel.fetch_message(message_id)
                                if message:
                                    print(f"Found application message with ID: {message_id}")
                                    # Update the embed to show the decision
                                    embed = message.embeds[0]
                                    embed.color = discord.Color.green()

                                    embed.add_field(
                                        name="Decision",
                                        value=f"✅ Approved via Discord Moderation Panel on {decision_time.strftime('%Y-%m-%d %H:%M:%S')}",
                                        inline=False
                                    )

                                    # Update the message (without buttons since it's already decided)
                                    await message.edit(embed=embed, view=None)
                                    print(f"Updated application message for {after.name} (ID: {after.id})")
                            except discord.NotFound:
                                print(f"Message with ID {message_id} not found in channel {channel.name} (ID: {channel.id})")
                            except Exception as e:
                                print(f"Error updating application message: {e}")
                    except Exception as e:
                        print(f"Error updating application message: {e}")

                # Add to application history
                application_data = {
                    "user_id": after.id,
                    "user_name": after.name,
                    "decision": "approved",
                    "decided_by": "Discord Moderation Panel",
                    "decided_by_id": 0,  # We don't know the ID
                    "timestamp": decision_time,
                    "guild_id": guild.id,
                    "guild_name": guild.name,
                    "application_text": "N/A"  # We don't have this information
                }

                # Add to history and keep only the last 10 entries
                client.application_history.insert(0, application_data)
                if len(client.application_history) > 10:
                    client.application_history = client.application_history[:10]

                # Remove from pending applications
                del client.pending_applications[after.id]
                print(f"Removed {after.name} (ID: {after.id}) from pending applications")

                # Log the action
                await log_to_channel(f"✅ Application from {after.name} (ID: {after.id}) has been approved via Discord Moderation Panel.")

                # Try to send a DM to the user
                embed = discord.Embed(
                    title="Application Approved",
                    description=f"Congratulations! Your application to join **{guild.name}** has been approved. You can now access the server.",
                    color=discord.Color.green()
                )

                dm_task = await send_dm_with_rate_limit(after, embed=embed)
                success, error_message = await dm_task

                if not success:
                    await log_to_channel(f"⚠️ Could not send approval message to {after.name} (ID: {after.id}): {error_message}")

    # Check for membership screening status changes
    # This detects when a member completes the membership screening but is still pending approval
    try:
        # Check if the guild has membership screening enabled
        guild = after.guild

        # Debug guild features
        print(f"Guild features for {guild.name}: {guild.features}")

        # Check if the member is pending (has no roles except @everyone)
        is_pending = len(after.roles) == 1 and not after.bot
        print(f"Member {after.name} (ID: {after.id}) is pending: {is_pending}")
        print(f"Member {after.name} already in pending_applications: {after.id in client.pending_applications}")

        if "MEMBER_VERIFICATION_GATE_ENABLED" in guild.features:
            print(f"Guild {guild.name} has membership screening enabled")

            # Check if the member is pending (has no roles except @everyone)
            if is_pending and after.id not in client.pending_applications:
                print(f"Detected member in pending state: {after.name} (ID: {after.id})")

                # Create an embed for the application
                embed = discord.Embed(
                    title=f"New Server Application from {after.name}",
                    description=f"User ID: {after.id}\n\nThis user has completed Discord's membership screening and is waiting for approval.",
                    color=discord.Color.gold(),
                    timestamp=datetime.datetime.now()
                )

                # Add user information
                embed.set_author(name=f"{after.name}", icon_url=after.display_avatar.url)
                embed.add_field(name="Account Created", value=f"<t:{int(after.created_at.timestamp())}:R>", inline=True)
                embed.add_field(name="Joined Server", value=f"<t:{int(after.joined_at.timestamp())}:R>", inline=True)

                # Create decision buttons
                from application_handler import ApplicationDecisionView
                view = ApplicationDecisionView(client, after.id)

                # Try to fetch the channel using fetch_channel first (more reliable)
                try:
                    decision_channel = await client.fetch_channel(client.decision_channel_id)
                    print(f"Decision channel found via fetch_channel: {decision_channel.name} (ID: {decision_channel.id})")
                except Exception as e:
                    print(f"Error fetching decision channel with fetch_channel: {e}")
                    # Fallback to get_channel
                    decision_channel = client.get_channel(client.decision_channel_id)
                    if decision_channel:
                        print(f"Decision channel found via get_channel: {decision_channel.name} (ID: {decision_channel.id})")
                    else:
                        print(f"⚠️ WARNING: Decision channel with ID {client.decision_channel_id} not found!")

                # Send the application to the decision channel
                if decision_channel:
                    try:
                        print(f"Sending application message for {after.name} (ID: {after.id}) to decision channel")
                        application_message = await decision_channel.send(embed=embed, view=view)
                        print(f"Application message sent with ID: {application_message.id}")

                        # Store the application in the pending applications
                        client.pending_applications[after.id] = {
                            "user_id": after.id,
                            "message_id": application_message.id,
                            "timestamp": datetime.datetime.now(),
                            "guild_id": guild.id,
                            "source": "membership_screening"
                        }
                        print(f"Application stored in pending_applications. Current count: {len(client.pending_applications)}")

                        # Also send a notification message to make sure new applications are visible
                        await decision_channel.send(
                            f"@here 📝 **NEW SERVER APPLICATION** from {after.name} (ID: {after.id}). Please review it above."
                        )
                        print(f"Notification message sent for {after.name} (ID: {after.id})")

                        # Log the event
                        await log_to_channel(f"📝 New server application detected from {after.name} (ID: {after.id})")
                    except Exception as e:
                        print(f"Error sending application message: {e}")
                else:
                    print(f"⚠️ ERROR: Could not find decision channel with ID {client.decision_channel_id}")
        else:
            # Even if membership screening is not enabled, we should still check for pending members
            if is_pending and after.id not in client.pending_applications:
                print(f"Detected member in pending state without membership screening: {after.name} (ID: {after.id})")

                # Create an embed for the application
                embed = discord.Embed(
                    title=f"New Server Application from {after.name}",
                    description=f"User ID: {after.id}\n\nThis user is waiting for approval.",
                    color=discord.Color.gold(),
                    timestamp=datetime.datetime.now()
                )

                # Add user information
                embed.set_author(name=f"{after.name}", icon_url=after.display_avatar.url)
                embed.add_field(name="Account Created", value=f"<t:{int(after.created_at.timestamp())}:R>", inline=True)
                embed.add_field(name="Joined Server", value=f"<t:{int(after.joined_at.timestamp())}:R>", inline=True)

                # Create decision buttons
                from application_handler import ApplicationDecisionView
                view = ApplicationDecisionView(client, after.id)

                # Try to fetch the channel using fetch_channel first (more reliable)
                try:
                    decision_channel = await client.fetch_channel(client.decision_channel_id)
                    print(f"Decision channel found via fetch_channel: {decision_channel.name} (ID: {decision_channel.id})")
                except Exception as e:
                    print(f"Error fetching decision channel with fetch_channel: {e}")
                    # Fallback to get_channel
                    decision_channel = client.get_channel(client.decision_channel_id)

                # Send the application to the decision channel
                if decision_channel:
                    try:
                        print(f"Sending application message for {after.name} (ID: {after.id}) to decision channel")
                        application_message = await decision_channel.send(embed=embed, view=view)
                        print(f"Application message sent with ID: {application_message.id}")

                        # Store the application in the pending applications
                        client.pending_applications[after.id] = {
                            "user_id": after.id,
                            "message_id": application_message.id,
                            "timestamp": datetime.datetime.now(),
                            "guild_id": guild.id,
                            "source": "manual_detection"
                        }
                        print(f"Application stored in pending_applications. Current count: {len(client.pending_applications)}")

                        # Also send a notification message to make sure new applications are visible
                        await decision_channel.send(
                            f"@here 📝 **NEW SERVER APPLICATION** from {after.name} (ID: {after.id}). Please review it above."
                        )

                        # Log the event
                        await log_to_channel(f"📝 New server application detected from {after.name} (ID: {after.id})")
                    except Exception as e:
                        print(f"Error sending application message: {e}")
    except Exception as e:
        print(f"Error checking membership screening status: {e}")
        import traceback
        traceback.print_exc()

@client.event
async def on_member_remove(member):
    """Handle member leaving, which could be a rejection via Discord Moderation Panel"""
    # Check if this user has a pending application
    if member.id in client.pending_applications:
        # Get the guild
        guild = member.guild

        # Get the current time for the decision
        decision_time = datetime.datetime.now()

        # Get application data if available
        app_data = client.pending_applications.get(member.id, {})
        message_id = app_data.get("message_id")

        # Try to update the application message if it exists
        if message_id:
            try:
                channel = client.get_channel(client.decision_channel_id)
                if channel:
                    message = await channel.fetch_message(message_id)
                    if message:
                        # Update the embed to show the decision
                        embed = message.embeds[0]
                        embed.color = discord.Color.red()

                        embed.add_field(
                            name="Decision",
                            value=f"❌ Rejected via Discord Moderation Panel on {decision_time.strftime('%Y-%m-%d %H:%M:%S')}",
                            inline=False
                        )

                        # Update the message (without buttons since it's already decided)
                        await message.edit(embed=embed, view=None)
            except Exception as e:
                print(f"Error updating application message: {e}")

        # Add to application history
        application_data = {
            "user_id": member.id,
            "user_name": member.name,
            "decision": "rejected",
            "decided_by": "Discord Moderation Panel",
            "decided_by_id": 0,  # We don't know the ID
            "timestamp": decision_time,
            "guild_id": guild.id,
            "guild_name": guild.name,
            "application_text": "N/A"  # We don't have this information
        }

        # Add to history and keep only the last 10 entries
        client.application_history.insert(0, application_data)
        if len(client.application_history) > 10:
            client.application_history = client.application_history[:10]

        # Remove from pending applications
        del client.pending_applications[member.id]

        # Log the action
        await log_to_channel(f"❌ Application from {member.name} (ID: {member.id}) has been rejected via Discord Moderation Panel (user left or was kicked).")

@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author.bot:
        return

    # Process commands
    await client.process_commands(message)

# ===== 5. BASIC COMMANDS =====
@client.command(name='fcping')
async def fcping(ctx):
    """Simple command to check if the bot is responsive"""
    await ctx.send(f"Pong! Latency: {round(client.latency * 1000)}ms")

@client.command(name='fcdebug')
async def fcdebug(ctx):
    """Debug command to check the status of the bot's data structures"""
    # Check if the command is used by an admin or authorized mod
    if ctx.author.id != client.admin_user_id and ctx.author.id not in client.authorized_mods and not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permission to use this command.")
        return

    # Create an embed for the debug info
    embed = discord.Embed(
        title="Debug Information",
        description="Current state of the bot's data structures",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.now()
    )

    # Add bot version and uptime
    uptime = datetime.datetime.now() - client.start_time
    days, remainder = divmod(int(uptime.total_seconds()), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    embed.add_field(
        name="Bot Information",
        value=f"Version: 0.0.4\nUptime: {days}d {hours}h {minutes}m {seconds}s\nConnected to {len(client.guilds)} guilds",
        inline=False
    )

    # Add pending applications info
    pending_count = len(client.pending_applications)
    pending_details = ""

    if pending_count > 0:
        for user_id, app_data in client.pending_applications.items():
            try:
                user = await client.fetch_user(user_id)
                user_name = user.name
            except:
                user_name = f"Unknown User (ID: {user_id})"

            # Format timestamp
            timestamp = app_data.get('timestamp', 'N/A')
            if isinstance(timestamp, datetime.datetime):
                timestamp_str = f"<t:{int(timestamp.timestamp())}:R>"
            else:
                timestamp_str = str(timestamp)

            pending_details += f"• {user_name} (ID: {user_id})\n"
            pending_details += f"  - Message ID: {app_data.get('message_id', 'N/A')}\n"
            pending_details += f"  - Timestamp: {timestamp_str}\n"
            pending_details += f"  - Guild ID: {app_data.get('guild_id', 'N/A')}\n"
            pending_details += f"  - Source: {app_data.get('source', 'unknown')}\n"
            pending_details += f"  - Status: {app_data.get('status', 'pending')}\n\n"
    else:
        pending_details = "No pending applications"

    embed.add_field(name=f"Pending Applications ({pending_count})", value=pending_details or "None", inline=False)

    # Add decision channel info
    # Try to fetch the channel using fetch_channel first (more reliable)
    try:
        channel = await client.fetch_channel(client.decision_channel_id)
        channel_info = f"Found via fetch_channel: {channel.name} (ID: {channel.id})"
    except Exception as e:
        # Fallback to get_channel
        channel = client.get_channel(client.decision_channel_id)
        if channel:
            channel_info = f"Found via get_channel: {channel.name} (ID: {channel.id})"
        else:
            channel_info = f"⚠️ Not found! ID: {client.decision_channel_id}"

            # Try to list available channels
            available_channels = []
            for guild in client.guilds:
                for ch in guild.text_channels:
                    if ch.permissions_for(guild.me).send_messages:
                        available_channels.append(f"{ch.name} (ID: {ch.id}) in {guild.name}")

            if available_channels:
                channel_info += "\n\nAvailable channels with send permissions:\n" + "\n".join(available_channels[:10])
                if len(available_channels) > 10:
                    channel_info += f"\n...and {len(available_channels) - 10} more"

    embed.add_field(name="Decision Channel", value=channel_info, inline=False)

    # Add guild membership screening info
    guild = ctx.guild
    has_screening = "MEMBER_VERIFICATION_GATE_ENABLED" in guild.features
    screening_status = "✅ Enabled" if has_screening else "❌ Disabled"

    # Count members with only @everyone role (potential pending members)
    members_without_roles = [m for m in guild.members if len(m.roles) == 1 and not m.bot]
    pending_members_count = len(members_without_roles)

    embed.add_field(
        name="Server Information",
        value=f"Name: {guild.name}\nID: {guild.id}\nMembership Screening: {screening_status}\nMembers Without Roles: {pending_members_count}",
        inline=False
    )

    # Add authorized mods info
    mod_count = len(client.authorized_mods)
    mod_details = ""

    if mod_count > 0:
        for mod_id in client.authorized_mods:
            try:
                mod = await client.fetch_user(mod_id)
                mod_details += f"• {mod.name} (ID: {mod_id})\n"
            except:
                mod_details += f"• Unknown User (ID: {mod_id})\n"
    else:
        mod_details = "No authorized moderators"

    embed.add_field(name=f"Authorized Moderators ({mod_count})", value=mod_details or "None", inline=False)

    # Add help info
    embed.add_field(
        name="Troubleshooting Commands",
        value=(
            "• `.fcrefresh` - Manually check for pending applications\n"
            "• `.fcchannel [channel_id]` - Check or update the decision channel\n"
            "• `/apply` - Open the application form\n"
            "• `/pending` - List all pending applications"
        ),
        inline=False
    )

    # Send the debug info
    await ctx.send(embed=embed)

    # Send a second message with detailed server information
    server_embed = discord.Embed(
        title=f"Server Details: {guild.name}",
        description="Detailed information about the server configuration",
        color=discord.Color.green(),
        timestamp=datetime.datetime.now()
    )

    # Add server icon if available
    if guild.icon:
        server_embed.set_thumbnail(url=guild.icon.url)

    # Add basic server info
    server_embed.add_field(
        name="Server Information",
        value=f"Owner: {guild.owner.name} (ID: {guild.owner.id})\nCreated: <t:{int(guild.created_at.timestamp())}:F>\nMembers: {guild.member_count}",
        inline=False
    )

    # Add server features
    if guild.features:
        server_embed.add_field(
            name="Server Features",
            value=", ".join(guild.features),
            inline=False
        )

    # Add membership screening info
    if has_screening:
        server_embed.add_field(
            name="Membership Screening",
            value=(
                "This server has Discord's Membership Screening enabled.\n"
                "New members must complete the screening before they can access the server.\n"
                "The bot will automatically detect these applications and post them to the decision channel."
            ),
            inline=False
        )

    # Send the server info
    await ctx.send(embed=server_embed)

@client.command(name='fcrefresh')
async def fcrefresh(ctx):
    """Manually refresh the pending applications by checking server members"""
    # Check if the command is used by an admin or authorized mod
    if ctx.author.id != client.admin_user_id and ctx.author.id not in client.authorized_mods and not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permission to use this command.")
        return

    # Send initial message
    status_message = await ctx.send("🔄 Refreshing pending applications...")

    # Get all guild members who don't have roles (likely pending approval)
    guild = ctx.guild
    members_without_roles = [m for m in guild.members if len(m.roles) == 1]  # Only @everyone role

    print(f"Found {len(members_without_roles)} members without roles in {guild.name}")

    # Count before refresh
    old_pending_count = len(client.pending_applications)
    print(f"Current pending applications count: {old_pending_count}")

    # Check if any members without roles are not in pending applications
    new_applications = 0
    new_server_applications = 0

    # Check if the guild has membership screening enabled
    has_screening = "MEMBER_VERIFICATION_GATE_ENABLED" in guild.features
    print(f"Guild {guild.name} has membership screening enabled: {has_screening}")

    if has_screening:
        await status_message.edit(content=f"🔄 Refreshing pending applications...\n\n📋 Server has membership screening enabled. Checking for pending members...")

    for member in members_without_roles:
        if member.id not in client.pending_applications and not member.bot:
            # This member might have a pending application that wasn't tracked
            print(f"Found member without roles who is not in pending applications: {member.name} (ID: {member.id})")

            # Create an embed for the application
            embed = discord.Embed(
                title=f"New Server Application from {member.name}",
                description=f"User ID: {member.id}\n\nThis user is waiting for approval.",
                color=discord.Color.gold(),
                timestamp=datetime.datetime.now()
            )

            # Add user information
            embed.set_author(name=f"{member.name}", icon_url=member.display_avatar.url)
            embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
            embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)

            # Create decision buttons
            from application_handler import ApplicationDecisionView
            view = ApplicationDecisionView(client, member.id)

            # Try to fetch the channel using fetch_channel first (more reliable)
            try:
                decision_channel = await client.fetch_channel(client.decision_channel_id)
                print(f"Decision channel found via fetch_channel: {decision_channel.name} (ID: {decision_channel.id})")
            except Exception as e:
                print(f"Error fetching decision channel with fetch_channel: {e}")
                # Fallback to get_channel
                decision_channel = client.get_channel(client.decision_channel_id)
                if decision_channel:
                    print(f"Decision channel found via get_channel: {decision_channel.name} (ID: {decision_channel.id})")
                else:
                    print(f"⚠️ WARNING: Decision channel with ID {client.decision_channel_id} not found!")
                    await status_message.edit(content=f"❌ Error: Could not find decision channel with ID {client.decision_channel_id}")
                    return

            # Send the application to the decision channel
            if decision_channel:
                try:
                    print(f"Sending application message for {member.name} (ID: {member.id}) to decision channel")
                    application_message = await decision_channel.send(embed=embed, view=view)
                    print(f"Application message sent with ID: {application_message.id}")

                    # Store the application in the pending applications
                    client.pending_applications[member.id] = {
                        "user_id": member.id,
                        "message_id": application_message.id,
                        "timestamp": datetime.datetime.now(),
                        "guild_id": guild.id,
                        "source": "fcrefresh_command"
                    }
                    print(f"Application stored in pending_applications. Current count: {len(client.pending_applications)}")

                    # Also send a notification message to make sure new applications are visible
                    await decision_channel.send(
                        f"📝 **NEW SERVER APPLICATION** from {member.name} (ID: {member.id}). Please review it above."
                    )
                    print(f"Notification message sent for {member.name} (ID: {member.id})")

                    new_server_applications += 1

                    # Log the event
                    await log_to_channel(f"📝 New server application detected from {member.name} (ID: {member.id}) during refresh")
                except Exception as e:
                    print(f"Error sending application message: {e}")
                    import traceback
                    traceback.print_exc()

                    # Create a placeholder application instead
                    client.pending_applications[member.id] = {
                        "user_id": member.id,
                        "message_id": None,  # We don't have a message ID
                        "timestamp": datetime.datetime.now(),
                        "guild_id": guild.id,
                        "status": "pending",
                        "auto_detected": True
                    }

                    new_applications += 1

                    # Log this action
                    await log_to_channel(f"🔍 Auto-detected potential pending application from {member.name} (ID: {member.id})")
            else:
                print(f"⚠️ ERROR: Could not find decision channel with ID {client.decision_channel_id}")
                await status_message.edit(content=f"❌ Error: Could not find decision channel with ID {client.decision_channel_id}")
                return

    # Check if any pending applications are for members who are no longer in the server or now have roles
    removed_applications = 0
    to_remove = []

    for user_id in client.pending_applications.keys():
        # Try to get the member
        member = guild.get_member(user_id)

        # If member is not in the server or has roles, mark for removal
        if member is None or len(member.roles) > 1:
            to_remove.append(user_id)
            print(f"Marking application for removal: User ID {user_id}")

    # Remove the marked applications
    for user_id in to_remove:
        try:
            user = await client.fetch_user(user_id)
            user_name = user.name
        except:
            user_name = f"Unknown User (ID: {user_id})"

        del client.pending_applications[user_id]
        removed_applications += 1
        print(f"Removed application for {user_name} (ID: {user_id})")

        # Log this action
        await log_to_channel(f"🧹 Removed outdated pending application from {user_name} (ID: {user_id})")

    # Update the status message
    new_pending_count = len(client.pending_applications)
    print(f"New pending applications count: {new_pending_count}")

    # Create a more detailed status message
    status_content = f"✅ Refresh complete!\n"
    status_content += f"• Before: {old_pending_count} pending applications\n"
    status_content += f"• Added: {new_applications + new_server_applications} new applications\n"

    if new_server_applications > 0:
        status_content += f"  - {new_server_applications} applications with decision buttons\n"

    if new_applications > 0:
        status_content += f"  - {new_applications} auto-detected applications\n"

    status_content += f"• Removed: {removed_applications} outdated applications\n"
    status_content += f"• After: {new_pending_count} pending applications\n\n"

    if has_screening:
        status_content += f"📋 This server has membership screening enabled. Server applications have been posted to the decision channel with approval buttons.\n\n"

    status_content += f"Use `.fcdebug` to see detailed information about pending applications."

    await status_message.edit(content=status_content)

@client.command(name='fcinfo')
async def fcinfo(ctx):
    """Display detailed information about the bot and server"""
    # Check if the command is used in a guild
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return

    # Basic bot info embed
    bot_embed = discord.Embed(
        title="FCKR Discord Bot",
        description="A bot to manage applications for private Discord servers",
        color=discord.Color.blue()
    )

    # Calculate uptime
    uptime = datetime.datetime.now() - client.start_time
    days, remainder = divmod(int(uptime.total_seconds()), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    bot_embed.add_field(name="Version", value="0.0.4", inline=True)
    bot_embed.add_field(name="Uptime", value=f"{days}d {hours}h {minutes}m {seconds}s", inline=True)
    bot_embed.add_field(name="Servers", value=str(len(client.guilds)), inline=True)

    # Send the basic info embed
    await ctx.send(embed=bot_embed)

    # If the user is an admin or authorized mod, send detailed server info
    if ctx.author.id == client.admin_user_id or ctx.author.id in client.authorized_mods or ctx.author.guild_permissions.administrator:
        # Server info embed
        server_embed = discord.Embed(
            title=f"Server Information: {ctx.guild.name}",
            description=f"ID: {ctx.guild.id}",
            color=discord.Color.green()
        )

        # Add server icon if available
        if ctx.guild.icon:
            server_embed.set_thumbnail(url=ctx.guild.icon.url)

        # Add basic server info
        server_embed.add_field(name="Owner", value=f"{ctx.guild.owner.name} (ID: {ctx.guild.owner.id})", inline=False)
        server_embed.add_field(name="Created On", value=f"<t:{int(ctx.guild.created_at.timestamp())}:F>", inline=True)
        server_embed.add_field(name="Region", value=ctx.guild.region if hasattr(ctx.guild, 'region') else "Unknown", inline=True)

        # Member counts
        total_members = ctx.guild.member_count
        online_members = len([m for m in ctx.guild.members if m.status != discord.Status.offline]) if hasattr(ctx.guild.members[0], 'status') else "Unknown"
        bot_count = len([m for m in ctx.guild.members if m.bot])

        server_embed.add_field(name="Members", value=f"Total: {total_members}\nOnline: {online_members}\nBots: {bot_count}", inline=True)

        # Channel counts
        text_channels = len(ctx.guild.text_channels)
        voice_channels = len(ctx.guild.voice_channels)
        categories = len(ctx.guild.categories)

        server_embed.add_field(name="Channels", value=f"Text: {text_channels}\nVoice: {voice_channels}\nCategories: {categories}", inline=True)

        # Role count
        server_embed.add_field(name="Roles", value=str(len(ctx.guild.roles) - 1), inline=True)  # -1 to exclude @everyone

        # Server features
        if ctx.guild.features:
            server_embed.add_field(name="Features", value=", ".join(ctx.guild.features), inline=False)

        # Emoji counts
        emoji_count = len(ctx.guild.emojis)
        animated_emoji_count = len([e for e in ctx.guild.emojis if e.animated])

        server_embed.add_field(name="Emojis", value=f"Regular: {emoji_count - animated_emoji_count}\nAnimated: {animated_emoji_count}\nTotal: {emoji_count}", inline=True)

        # Boost status
        if hasattr(ctx.guild, 'premium_tier'):
            server_embed.add_field(name="Boost Tier", value=f"Level {ctx.guild.premium_tier}", inline=True)
            if hasattr(ctx.guild, 'premium_subscription_count'):
                server_embed.add_field(name="Boosts", value=str(ctx.guild.premium_subscription_count), inline=True)

        # Send the detailed server info embed
        await ctx.send(embed=server_embed)

        # Application stats
        app_embed = discord.Embed(
            title="Application Statistics",
            color=discord.Color.gold()
        )

        # Count pending applications
        pending_count = len(client.pending_applications)

        # Check if the guild has membership screening enabled
        has_screening = "MEMBER_VERIFICATION_GATE_ENABLED" in ctx.guild.features
        screening_status = "✅ Enabled" if has_screening else "❌ Disabled"

        # Count members with only @everyone role (potential pending members)
        pending_members_count = len([m for m in ctx.guild.members if len(m.roles) == 1 and not m.bot])

        # Add application stats
        app_embed.add_field(name="Pending Applications", value=str(pending_count), inline=True)
        app_embed.add_field(name="Decision Channel", value=f"<#{client.decision_channel_id}>", inline=True)
        app_embed.add_field(name="Membership Screening", value=screening_status, inline=True)
        app_embed.add_field(name="Members Without Roles", value=str(pending_members_count), inline=True)

        # Add membership screening information if enabled
        if has_screening:
            app_embed.add_field(
                name="Membership Screening Information",
                value=(
                    "This server has Discord's Membership Screening enabled. "
                    "New members must complete the screening before they can access the server. "
                    "The bot will automatically detect these applications and post them to the decision channel."
                ),
                inline=False
            )

            # Add instructions for refreshing applications
            app_embed.add_field(
                name="Managing Server Applications",
                value=(
                    "Use `.fcrefresh` to manually check for pending server applications.\n"
                    "Use `.fcdebug` to see detailed information about all pending applications."
                ),
                inline=False
            )

        # Add authorized moderators
        if client.authorized_mods:
            mod_list = []
            for mod_id in client.authorized_mods:
                try:
                    mod = await client.fetch_user(mod_id)
                    mod_list.append(f"{mod.name} (ID: {mod.id})")
                except:
                    mod_list.append(f"Unknown User (ID: {mod_id})")

            app_embed.add_field(name="Authorized Moderators", value="\n".join(mod_list) if mod_list else "None", inline=False)
        else:
            app_embed.add_field(name="Authorized Moderators", value="None", inline=False)

        # Send the application stats embed
        await ctx.send(embed=app_embed)

@client.command(name='fcadd')
async def fcadd(ctx, user_id: int = None):
    """Add a user to the authorized moderators list"""
    # Check if the command is used by the admin
    if ctx.author.id != client.admin_user_id and not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permission to use this command.")
        return

    # Check if a user ID was provided
    if user_id is None:
        await ctx.send("Please provide a user ID. Usage: `.fcadd <user_id>`")
        return

    # Add the user to the authorized moderators list
    client.authorized_mods.add(user_id)

    # Try to get the user's name
    try:
        user = await client.fetch_user(user_id)
        user_name = user.name
    except:
        user_name = f"User with ID {user_id}"

    # Send confirmation
    await ctx.send(f"✅ {user_name} has been added to the authorized moderators list.")

    # Log the action
    await log_to_channel(f"👮 {ctx.author.name} added {user_name} (ID: {user_id}) to the authorized moderators list.")

@client.command(name='fcrm')
async def fcrm(ctx, user_id: int = None):
    """Remove a user from the authorized moderators list"""
    # Check if the command is used by the admin
    if ctx.author.id != client.admin_user_id and not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permission to use this command.")
        return

    # Check if a user ID was provided
    if user_id is None:
        await ctx.send("Please provide a user ID. Usage: `.fcrm <user_id>`")
        return

    # Check if the user is in the authorized moderators list
    if user_id not in client.authorized_mods:
        await ctx.send("This user is not in the authorized moderators list.")
        return

    # Remove the user from the authorized moderators list
    client.authorized_mods.remove(user_id)

    # Try to get the user's name
    try:
        user = await client.fetch_user(user_id)
        user_name = user.name
    except:
        user_name = f"User with ID {user_id}"

    # Send confirmation
    await ctx.send(f"✅ {user_name} has been removed from the authorized moderators list.")

    # Log the action
    await log_to_channel(f"🚫 {ctx.author.name} removed {user_name} (ID: {user_id}) from the authorized moderators list.")

@client.command(name='fcchannel')
async def fcchannel(ctx, channel_id: int = None):
    """Check or update the decision channel"""
    # Check if the command is used by the admin
    if ctx.author.id != client.admin_user_id and not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permission to use this command.")
        return

    # If no channel ID is provided, just check the current channel
    if channel_id is None:
        # Try to get the current decision channel
        try:
            channel = await client.fetch_channel(client.decision_channel_id)
            await ctx.send(f"✅ Current decision channel is: {channel.name} (ID: {channel.id})")

            # Send a test message to the channel
            test_message = await channel.send("🧪 Testing channel - this message will be deleted automatically.")
            await test_message.delete()

            await ctx.send("✅ Channel test successful - bot can send and delete messages in the decision channel.")
        except Exception as e:
            await ctx.send(f"❌ Error with current decision channel (ID: {client.decision_channel_id}): {str(e)}")

            # List available channels
            available_channels = []
            for guild in client.guilds:
                for ch in guild.text_channels:
                    if ch.permissions_for(guild.me).send_messages:
                        available_channels.append(f"{ch.name} (ID: {ch.id}) in {guild.name}")

            if available_channels:
                channels_text = "\n".join(available_channels[:10])
                if len(available_channels) > 10:
                    channels_text += f"\n...and {len(available_channels) - 10} more"

                await ctx.send(f"Available channels with send permissions:\n```\n{channels_text}\n```\nUse `.fcchannel <channel_id>` to update the decision channel.")

        return

    # If a channel ID is provided, try to update the decision channel
    try:
        # Try to fetch the channel
        new_channel = await client.fetch_channel(channel_id)

        # Check if the bot has permissions to send messages in this channel
        if not new_channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(f"❌ Bot does not have permission to send messages in {new_channel.name}. Please update channel permissions and try again.")
            return

        # Update the decision channel ID
        old_channel_id = client.decision_channel_id
        client.decision_channel_id = channel_id

        # Send a test message to the new channel
        test_message = await new_channel.send(f"🧪 This channel has been set as the new decision channel by {ctx.author.name}.")

        # Log the change
        await log_to_channel(f"📢 Decision channel updated from ID {old_channel_id} to {channel_id} ({new_channel.name}) by {ctx.author.name}")

        # Confirm the change
        await ctx.send(f"✅ Decision channel updated to: {new_channel.name} (ID: {channel_id})")

    except Exception as e:
        await ctx.send(f"❌ Error updating decision channel: {str(e)}")
        await ctx.send("Please make sure the channel ID is valid and the bot has access to it.")

@client.command(name='fclog')
async def fclog(ctx):
    """Display the last 10 application decisions"""
    # Check if the command is used by an admin or authorized mod
    if ctx.author.id != client.admin_user_id and ctx.author.id not in client.authorized_mods and not ctx.author.guild_permissions.administrator:
        await ctx.send("You don't have permission to use this command.")
        return

    # Check if there's any application history
    if not client.application_history:
        await ctx.send("No application history found.")
        return

    # Create an embed for the application history
    embed = discord.Embed(
        title="Application History",
        description="Last 10 application decisions",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.now()
    )

    # Add each application to the embed
    for i, app in enumerate(client.application_history):
        # Format the decision with an emoji
        if app["decision"] == "approved":
            decision_emoji = "✅"
        elif app["decision"] == "rejected":
            decision_emoji = "❌"
        else:  # interview
            decision_emoji = "🗣️"

        # Format the timestamp
        timestamp_str = app["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

        # Create a field for each application
        embed.add_field(
            name=f"{i+1}. {app['user_name']} (ID: {app['user_id']})",
            value=(
                f"**Decision:** {decision_emoji} {app['decision'].capitalize()}\n"
                f"**By:** {app['decided_by']} (ID: {app['decided_by_id']})\n"
                f"**When:** {timestamp_str}\n"
                f"**Server:** {app['guild_name']}\n"
                f"**Reason for joining:** {app['application_text'][:100]}..." if len(app['application_text']) > 100 else app['application_text']
            ),
            inline=False
        )

    # Send the embed
    await ctx.send(embed=embed)

# ===== 6. REGISTER COMMANDS =====
# Register application commands
register_application_commands(client)

# ===== 7. BOT START =====
# Function to properly shut down the bot
async def shutdown():
    """Properly shut down the bot and stop all services"""
    # Add any cleanup tasks here

    # Close the bot
    await client.close()

# Add signal handlers for SIGINT (Ctrl+C) and SIGTERM
import signal

# Simplified signal handler without asyncio
def signal_handler(sig, _):
    """Signal handler for SIGINT and SIGTERM"""
    print(f"Signal {sig} received, shutting down bot...")
    # We can't directly call asyncio functions here,
    # instead we terminate the process and let the finally block handle cleanup
    raise KeyboardInterrupt

# Register signal handlers
try:
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
except (ValueError, AttributeError):
    # On some platforms or in certain environments, signals can't be registered
    print("Warning: Signal handlers could not be registered")

# Start the bot
try:
    client.run(token)
except KeyboardInterrupt:
    print("Keyboard Interrupt received, shutting down bot...")
    client.loop.run_until_complete(shutdown())
finally:
    print("Bot has been shut down.")
