#!/usr/bin/env python
# -*- coding: utf-8 -*-

import discord
from discord import ButtonStyle, Interaction, TextStyle
from discord.ui import Button, View, Modal, TextInput
import datetime
import asyncio

class ApplicationModal(Modal):
    """Modal for submitting an application"""

    def __init__(self, client):
        super().__init__(title="Server Application")
        self.client = client

        # Add text inputs for the application
        self.add_item(
            TextInput(
                label="Why do you want to join this server?",
                placeholder="Explain your reasons for wanting to join...",
                style=TextStyle.paragraph,
                required=True,
                max_length=1000,
                custom_id="reason"
            )
        )

        self.add_item(
            TextInput(
                label="Tell us about yourself",
                placeholder="Share some information about yourself...",
                style=TextStyle.paragraph,
                required=True,
                max_length=1000,
                custom_id="about"
            )
        )

        self.add_item(
            TextInput(
                label="How did you find this server?",
                placeholder="Where did you hear about us?",
                style=TextStyle.short,
                required=True,
                max_length=300,
                custom_id="source"
            )
        )

    async def on_submit(self, interaction: Interaction):
        """Handle the submission of the application form"""
        try:
            # Get the values from the form
            reason = self.children[0].value
            about = self.children[1].value
            source = self.children[2].value

            # Get user information
            user = interaction.user

            # Log the application attempt
            print(f"Application submission attempt from {user.name} (ID: {user.id})")

            # Create an embed for the application
            embed = discord.Embed(
                title=f"New Application from {user.name}",
                description=f"User ID: {user.id}",
                color=discord.Color.gold(),
                timestamp=datetime.datetime.now()
            )

            # Add user information
            embed.set_author(name=f"{user.name}", icon_url=user.display_avatar.url)
            embed.add_field(name="Account Created", value=f"<t:{int(user.created_at.timestamp())}:R>", inline=True)

            # Add application details
            embed.add_field(name="Why they want to join", value=reason, inline=False)
            embed.add_field(name="About them", value=about, inline=False)
            embed.add_field(name="How they found the server", value=source, inline=False)

            # Create decision buttons
            view = ApplicationDecisionView(self.client, user.id)

            # Get the decision channel - first try with fetch_channel which is more reliable
            try:
                decision_channel = await self.client.fetch_channel(self.client.decision_channel_id)
            except Exception as e:
                print(f"Error fetching decision channel with fetch_channel: {e}")
                # Fallback to get_channel
                decision_channel = self.client.get_channel(self.client.decision_channel_id)

            if decision_channel:
                print(f"Decision channel found: {decision_channel.name} (ID: {decision_channel.id})")

                # Send the application to the decision channel
                try:
                    application_message = await decision_channel.send(embed=embed, view=view)
                    print(f"Application message sent with ID: {application_message.id}")

                    # Store the application in the pending applications
                    self.client.pending_applications[user.id] = {
                        "user_id": user.id,
                        "message_id": application_message.id,
                        "timestamp": datetime.datetime.now(),
                        "guild_id": interaction.guild.id if interaction.guild else None
                    }

                    print(f"Application stored in pending_applications. Current count: {len(self.client.pending_applications)}")

                    # Send a more visible notification message
                    await decision_channel.send(
                        f"@here 📝 **NEW APPLICATION RECEIVED** from {user.name} (ID: {user.id}). Please review it above."
                    )

                    # Acknowledge the submission
                    await interaction.response.send_message(
                        "Your application has been submitted! The administrators will review it soon.",
                        ephemeral=True
                    )
                except Exception as e:
                    print(f"Error sending application message: {e}")
                    await interaction.response.send_message(
                        "There was an error submitting your application. Please try again later or contact a server administrator.",
                        ephemeral=True
                    )
            else:
                # If the decision channel doesn't exist, inform the user and log the error
                print(f"ERROR: Decision channel with ID {self.client.decision_channel_id} not found!")
                print(f"Available channels:")
                for guild in self.client.guilds:
                    for ch in guild.text_channels:
                        print(f"- {ch.name} (ID: {ch.id}) in {guild.name}")

                await interaction.response.send_message(
                    "There was an error submitting your application. Please contact a server administrator.",
                    ephemeral=True
                )
        except Exception as e:
            # Catch any other exceptions
            print(f"Unexpected error in application submission: {e}")
            try:
                await interaction.response.send_message(
                    "An unexpected error occurred. Please try again later or contact a server administrator.",
                    ephemeral=True
                )
            except:
                # If we can't respond to the interaction, it might have already been responded to or timed out
                pass

class ApplicationView(View):
    """View with a button to open the application modal"""

    def __init__(self, client):
        super().__init__(timeout=None)  # No timeout for this view
        self.client = client

    async def interaction_check(self, interaction: Interaction) -> bool:
        """Check if the interaction is valid"""
        return True

    @discord.ui.button(label="Apply for Membership", style=ButtonStyle.primary, emoji="📝", custom_id="apply_button")
    async def apply_button_callback(self, interaction: Interaction, button: Button):
        """Handle the apply button click"""
        # Show the application modal
        await interaction.response.send_modal(ApplicationModal(self.client))

class ApplicationDecisionView(View):
    """View with buttons for approving, rejecting, or interviewing an applicant"""

    def __init__(self, client, applicant_id):
        super().__init__(timeout=None)  # No timeout for this view
        self.client = client
        self.applicant_id = applicant_id

        # Add buttons with unique custom_ids based on applicant_id
        approve_button = Button(style=ButtonStyle.success, label="Approve", emoji="✅", custom_id=f"approve_button_{applicant_id}")
        reject_button = Button(style=ButtonStyle.danger, label="Reject", emoji="❌", custom_id=f"reject_button_{applicant_id}")
        interview_button = Button(style=ButtonStyle.primary, label="Interview", emoji="🗣️", custom_id=f"interview_button_{applicant_id}")

        # Set callbacks for buttons
        approve_button.callback = self.approve_button_callback
        reject_button.callback = self.reject_button_callback
        interview_button.callback = self.interview_button_callback

        # Add buttons to view
        self.add_item(approve_button)
        self.add_item(reject_button)
        self.add_item(interview_button)

    async def interaction_check(self, interaction: Interaction) -> bool:
        """Check if the interaction is valid"""
        return self._has_permission(interaction.user)

    async def approve_button_callback(self, interaction: Interaction):
        """Handle the approve button click"""
        # Get the applicant
        try:
            # Try to get the user object
            applicant = await self.client.fetch_user(self.applicant_id)

            # Get the guild from the pending applications
            guild_id = self.client.pending_applications.get(self.applicant_id, {}).get("guild_id")
            if not guild_id:
                await interaction.response.send_message(
                    "Error: Could not find the guild for this application.",
                    ephemeral=True
                )
                return

            guild = self.client.get_guild(guild_id)
            if not guild:
                await interaction.response.send_message(
                    "Error: Could not find the guild for this application.",
                    ephemeral=True
                )
                return

            # Update the embed to show the decision
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.green()

            # Get the current time
            decision_time = datetime.datetime.now()

            embed.add_field(
                name="Decision",
                value=f"✅ Approved by {interaction.user.name} on {decision_time.strftime('%Y-%m-%d %H:%M:%S')}",
                inline=False
            )

            # Disable the buttons
            for item in self.children:
                item.disabled = True

            # Update the message
            await interaction.message.edit(embed=embed, view=self)

            # Send a DM to the applicant using rate limiting
            import sys
            sys.path.append('src')
            import main

            # Create the approval message
            approval_message = f"Congratulations! Your application to join **{guild.name}** has been approved. You can now access the server."

            # Send the DM with rate limiting
            dm_task = await main.send_dm_with_rate_limit(applicant, content=approval_message)
            success, error_message = await dm_task

            if not success:
                # Log the error
                decision_channel = self.client.get_channel(self.client.decision_channel_id)
                if decision_channel:
                    await decision_channel.send(
                        f"⚠️ Could not send approval message to {applicant.name}: {error_message}"
                    )

            # Add to application history
            application_data = {
                "user_id": self.applicant_id,
                "user_name": applicant.name,
                "decision": "approved",
                "decided_by": interaction.user.name,
                "decided_by_id": interaction.user.id,
                "timestamp": decision_time,
                "guild_id": guild.id,
                "guild_name": guild.name,
                "application_text": embed.fields[1].value if len(embed.fields) > 1 else "N/A"  # Why they want to join
            }

            # Add to history and keep only the last 10 entries
            self.client.application_history.insert(0, application_data)
            if len(self.client.application_history) > 10:
                self.client.application_history = self.client.application_history[:10]

            # Remove from pending applications
            if self.applicant_id in self.client.pending_applications:
                del self.client.pending_applications[self.applicant_id]

            # Acknowledge the action in the decision channel
            decision_channel = self.client.get_channel(self.client.decision_channel_id)
            if decision_channel:
                await decision_channel.send(
                    f"✅ Application from {applicant.name} has been approved by {interaction.user.name}."
                )

            # Acknowledge the interaction
            await interaction.response.send_message(
                f"Application from {applicant.name} has been approved.",
                ephemeral=True
            )

        except discord.NotFound:
            await interaction.response.send_message(
                "Error: Could not find the applicant. They may have left Discord.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred: {str(e)}",
                ephemeral=True
            )

    async def reject_button_callback(self, interaction: Interaction):
        """Handle the reject button click"""
        # Get the applicant
        try:
            # Try to get the user object
            applicant = await self.client.fetch_user(self.applicant_id)

            # Get the guild from the pending applications
            guild_id = self.client.pending_applications.get(self.applicant_id, {}).get("guild_id")
            if not guild_id:
                await interaction.response.send_message(
                    "Error: Could not find the guild for this application.",
                    ephemeral=True
                )
                return

            guild = self.client.get_guild(guild_id)
            if not guild:
                await interaction.response.send_message(
                    "Error: Could not find the guild for this application.",
                    ephemeral=True
                )
                return

            # Update the embed to show the decision
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.red()

            # Get the current time
            decision_time = datetime.datetime.now()

            embed.add_field(
                name="Decision",
                value=f"❌ Rejected by {interaction.user.name} on {decision_time.strftime('%Y-%m-%d %H:%M:%S')}",
                inline=False
            )

            # Disable the buttons
            for item in self.children:
                item.disabled = True

            # Update the message
            await interaction.message.edit(embed=embed, view=self)

            # Send a DM to the applicant using rate limiting
            import sys
            sys.path.append('src')
            import main

            # Create the rejection message
            rejection_message = f"We're sorry, but your application to join **{guild.name}** has been rejected. You may try again in the future."

            # Send the DM with rate limiting
            dm_task = await main.send_dm_with_rate_limit(applicant, content=rejection_message)
            success, error_message = await dm_task

            if not success:
                # Log the error
                decision_channel = self.client.get_channel(self.client.decision_channel_id)
                if decision_channel:
                    await decision_channel.send(
                        f"⚠️ Could not send rejection message to {applicant.name}: {error_message}"
                    )

            # Add to application history
            application_data = {
                "user_id": self.applicant_id,
                "user_name": applicant.name,
                "decision": "rejected",
                "decided_by": interaction.user.name,
                "decided_by_id": interaction.user.id,
                "timestamp": decision_time,
                "guild_id": guild.id,
                "guild_name": guild.name,
                "application_text": embed.fields[1].value if len(embed.fields) > 1 else "N/A"  # Why they want to join
            }

            # Add to history and keep only the last 10 entries
            self.client.application_history.insert(0, application_data)
            if len(self.client.application_history) > 10:
                self.client.application_history = self.client.application_history[:10]

            # Remove from pending applications
            if self.applicant_id in self.client.pending_applications:
                del self.client.pending_applications[self.applicant_id]

            # Acknowledge the action in the decision channel
            decision_channel = self.client.get_channel(self.client.decision_channel_id)
            if decision_channel:
                await decision_channel.send(
                    f"❌ Application from {applicant.name} has been rejected by {interaction.user.name}."
                )

            # Acknowledge the interaction
            await interaction.response.send_message(
                f"Application from {applicant.name} has been rejected.",
                ephemeral=True
            )

        except discord.NotFound:
            await interaction.response.send_message(
                "Error: Could not find the applicant. They may have left Discord.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred: {str(e)}",
                ephemeral=True
            )

    async def interview_button_callback(self, interaction: Interaction):
        """Handle the interview button click"""
        # Get the applicant
        try:
            # Try to get the user object
            applicant = await self.client.fetch_user(self.applicant_id)

            # Get the guild from the pending applications
            guild_id = self.client.pending_applications.get(self.applicant_id, {}).get("guild_id")
            if not guild_id:
                await interaction.response.send_message(
                    "Error: Could not find the guild for this application.",
                    ephemeral=True
                )
                return

            guild = self.client.get_guild(guild_id)
            if not guild:
                await interaction.response.send_message(
                    "Error: Could not find the guild for this application.",
                    ephemeral=True
                )
                return

            # Update the embed to show the decision
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.blue()

            # Get the current time
            decision_time = datetime.datetime.now()

            embed.add_field(
                name="Decision",
                value=f"🗣️ Interview requested by {interaction.user.name} on {decision_time.strftime('%Y-%m-%d %H:%M:%S')}",
                inline=False
            )

            # Disable the buttons
            for item in self.children:
                item.disabled = True

            # Update the message
            await interaction.message.edit(embed=embed, view=self)

            # Send a DM to the applicant using rate limiting
            import sys
            sys.path.append('src')
            import main

            # Create the interview message
            interview_message = f"The administrators of **{guild.name}** would like to interview you before making a decision on your application. Please wait for them to contact you."

            # Send the DM with rate limiting
            dm_task = await main.send_dm_with_rate_limit(applicant, content=interview_message)
            success, error_message = await dm_task

            if not success:
                # Log the error
                decision_channel = self.client.get_channel(self.client.decision_channel_id)
                if decision_channel:
                    await decision_channel.send(
                        f"⚠️ Could not send interview message to {applicant.name}: {error_message}"
                    )

            # Add to application history
            application_data = {
                "user_id": self.applicant_id,
                "user_name": applicant.name,
                "decision": "interview",
                "decided_by": interaction.user.name,
                "decided_by_id": interaction.user.id,
                "timestamp": decision_time,
                "guild_id": guild.id,
                "guild_name": guild.name,
                "application_text": embed.fields[1].value if len(embed.fields) > 1 else "N/A"  # Why they want to join
            }

            # Add to history and keep only the last 10 entries
            self.client.application_history.insert(0, application_data)
            if len(self.client.application_history) > 10:
                self.client.application_history = self.client.application_history[:10]

            # Mark the application as in interview status but don't remove it
            if self.applicant_id in self.client.pending_applications:
                self.client.pending_applications[self.applicant_id]["status"] = "interview"

            # Acknowledge the action in the decision channel
            decision_channel = self.client.get_channel(self.client.decision_channel_id)
            if decision_channel:
                await decision_channel.send(
                    f"🗣️ Interview requested for {applicant.name} by {interaction.user.name}. "
                    f"Please contact the applicant to arrange the interview."
                )

            # Acknowledge the interaction
            await interaction.response.send_message(
                f"Interview requested for {applicant.name}.",
                ephemeral=True
            )

        except discord.NotFound:
            await interaction.response.send_message(
                "Error: Could not find the applicant. They may have left Discord.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred: {str(e)}",
                ephemeral=True
            )

    def _has_permission(self, user):
        """Check if a user has permission to make decisions on applications"""
        # Check if the user is an admin or has the admin user ID
        if user.id == self.client.admin_user_id:
            return True

        # Check if the user is in the authorized moderators list
        if hasattr(self.client, 'authorized_mods') and user.id in self.client.authorized_mods:
            return True

        # Check if the user has administrator permissions
        if user.guild_permissions and user.guild_permissions.administrator:
            return True

        return False

def register_application_commands(client):
    """Register application-related commands with the bot"""

    @client.tree.command(name="apply", description="Apply to join this server")
    async def apply_command(interaction: Interaction):
        """Command to apply for server membership"""
        # Show the application modal
        await interaction.response.send_modal(ApplicationModal(client))

    @client.tree.command(name="pending", description="List all pending applications")
    async def pending_command(interaction: Interaction):
        """Command to list all pending applications"""
        # Check if the user has permission to view pending applications
        if not interaction.user.guild_permissions.administrator and interaction.user.id != client.admin_user_id:
            await interaction.response.send_message(
                "You don't have permission to view pending applications.",
                ephemeral=True
            )
            return

        # Check if there are any pending applications
        if not client.pending_applications:
            await interaction.response.send_message(
                "There are no pending applications.",
                ephemeral=True
            )
            return

        # Create an embed to list the pending applications
        embed = discord.Embed(
            title="Pending Applications",
            description=f"There are {len(client.pending_applications)} pending applications.",
            color=discord.Color.blue()
        )

        # Add each application to the embed
        for app_id, app_data in client.pending_applications.items():
            try:
                user = await client.fetch_user(app_id)
                embed.add_field(
                    name=f"{user.name} (ID: {user.id})",
                    value=f"Submitted: <t:{int(app_data['timestamp'].timestamp())}:R>",
                    inline=False
                )
            except discord.NotFound:
                embed.add_field(
                    name=f"Unknown User (ID: {app_id})",
                    value=f"Submitted: <t:{int(app_data['timestamp'].timestamp())}:R>",
                    inline=False
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)
