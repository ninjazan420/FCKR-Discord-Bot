import discord
from discord.ext import commands
import os
import time
from datetime import datetime

class ColorRolesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fckr_server_id = int(os.getenv('FCKR_SERVER', 0))
        self.roles_channel_id = int(os.getenv('ROLES_CHANNEL_ID', 0))
        
        # Store message IDs dynamically (created at startup)
        self.color_message_ids = []
        self.user_cooldowns = {}  # Store user cooldowns for color role changes
        self.role_update_locks = {} # To prevent race conditions
        
        # 30 gradient colors from red to purple
        self.color_palette = [
            0xFF0000, 0xFF1A00, 0xFF3300, 0xFF4D00, 0xFF6600,  # Red to Orange
            0xFF8000, 0xFF9900, 0xFFB300, 0xFFCC00, 0xFFE600,  # Orange to Yellow
            0xFFFF00, 0xE6FF00, 0xCCFF00, 0xB3FF00, 0x99FF00,  # Yellow to Green
            0x80FF00, 0x66FF00, 0x4DFF00, 0x33FF00, 0x1AFF00,  # Green
            0x00FF00, 0x00FF33, 0x00FF66, 0x00FF99, 0x00FFCC,  # Green to Cyan
            0x00FFFF, 0x0099FF, 0x0066FF, 0x0033FF, 0x0000FF   # Cyan to Blue to Purple
        ]
        
        self.color_names = [
            "🔴 Crimson Red", "🟠 Flame Orange", "🟡 Sunset Orange", "🟤 Amber", "🟠 Tangerine",
            "🟠 Pumpkin", "🟡 Marigold", "🟡 Golden", "🟡 Lemon", "🟡 Canary",
            "🟢 Lime", "🟢 Spring Green", "🟢 Mint", "🟢 Emerald", "🟢 Forest",
            "🟢 Jade", "🟢 Neon Green", "🟢 Electric Green", "🟢 Bright Green", "🟢 Vivid Green",
            "🟢 Pure Green", "🟢 Seafoam", "🔵 Aqua", "🔵 Turquoise", "🔵 Cyan",
            "🔵 Sky Blue", "🔵 Ocean Blue", "🔵 Royal Blue", "🔵 Electric Blue", "🟣 Deep Blue"
        ]
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Setup color roles and channel message when bot is ready"""
        await self.setup_color_roles()
        await self.setup_roles_channel()
    
    async def setup_color_roles(self):
        """Create or update color roles in the server"""
        guild = self.bot.get_guild(self.fckr_server_id)
        if not guild:
            print(f"Guild with ID {self.fckr_server_id} not found")
            return
        
        # Find the FCKR role to position color roles above it
        fckr_role = discord.utils.get(guild.roles, id=1371442861069041665)
        if not fckr_role:
            print(f"❌ FCKR role with ID 1371442861069041665 not found")
            return
            
        target_position = fckr_role.position + 1
        
        print(f"🎨 Setting up color roles above FCKR role (position {target_position})")
        
        # Get existing color roles
        existing_roles = {role.name: role for role in guild.roles if role.name in self.color_names}
        
        # Create missing roles and position them correctly
        for i, (color_name, color_hex) in enumerate(zip(self.color_names, self.color_palette)):
            if color_name not in existing_roles:
                try:
                    # Create role
                    role = await guild.create_role(
                        name=color_name,
                        color=discord.Color(color_hex),
                        mentionable=False,
                        hoist=False,
                        reason="Color role system setup"
                    )
                    print(f"✅ Created color role: {color_name}")
                    
                    # Move role above FCKR role
                    try:
                        await role.edit(position=target_position + i)
                        print(f"📍 Positioned {color_name} at position {target_position + i}")
                    except Exception as e:
                        print(f"⚠️ Could not position role {color_name}: {e}")
                        
                except Exception as e:
                    print(f"❌ Error creating color role {color_name}: {e}")
            else:
                # Move existing role to correct position
                try:
                    existing_role = existing_roles[color_name]
                    current_pos = existing_role.position
                    desired_pos = target_position + i
                    
                    if current_pos != desired_pos:
                        await existing_role.edit(position=desired_pos)
                        print(f"📍 Repositioned {color_name} from {current_pos} to {desired_pos}")
                    else:
                        print(f"✅ {color_name} already at correct position {current_pos}")
                except Exception as e:
                    print(f"⚠️ Could not reposition role {color_name}: {e}")
        
        # Verify all color roles are above FCKR role
        await self.verify_color_role_positions(guild, fckr_role)

    async def setup_roles_channel(self):
        """Set up the roles channel with color selection messages (reuse existing if found)"""
        guild = self.bot.get_guild(self.fckr_server_id)
        if not guild:
            print(f"❌ Guild with ID {self.fckr_server_id} not found")
            return
        
        roles_channel = guild.get_channel(self.roles_channel_id)
        if not roles_channel:
            print(f"❌ Roles channel with ID {self.roles_channel_id} not found")
            return
        
        print(f"🎨 Setting up color role messages in {roles_channel.name}")
        
        # Look for existing color role messages
        existing_messages = []
        try:
            async for message in roles_channel.history(limit=50):
                if (message.author == self.bot.user and 
                    message.embeds and 
                    "Color Roles" in message.embeds[0].title):
                    existing_messages.append(message)
                    print(f"✅ Found existing color message: {message.id}")
        except Exception as e:
            print(f"⚠️ Could not search for existing messages: {e}")
        
        # If we have exactly 3 existing messages, reuse them
        if len(existing_messages) == 3:
            print(f"🔄 Reusing {len(existing_messages)} existing color role messages")
            # Sort by creation time to maintain order
            existing_messages.sort(key=lambda m: m.created_at)
            self.color_message_ids = [msg.id for msg in existing_messages]
            print(f"📍 Reusing Message IDs: {self.color_message_ids}")
            return
        
        # Clear old messages if we don't have exactly 3
        if existing_messages:
            print(f"🗑️ Clearing {len(existing_messages)} old color messages")
            for message in existing_messages:
                try:
                    await message.delete()
                    print(f"🗑️ Deleted old color message: {message.id}")
                except Exception as e:
                    print(f"⚠️ Could not delete message {message.id}: {e}")
        
        # Create 3 new messages with 10 colors each
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        color_groups = [
            list(zip(self.color_names[:10], self.color_palette[:10])),   # First 10 colors
            list(zip(self.color_names[10:20], self.color_palette[10:20])), # Next 10 colors
            list(zip(self.color_names[20:], self.color_palette[20:]))    # Remaining colors
        ]
        
        self.color_message_ids = []  # Reset message IDs
        
        for i, color_group in enumerate(color_groups):
            if not color_group:
                continue
                
            embed = discord.Embed(
                title=f"🎨 Color Roles - Group {i+1}",
                description="React with the corresponding number to get your color role!\n\n" +
                           "**Note:** Color roles are positioned above the FCKR role for visibility.",
                color=0x00ff00
            )
            
            for j, (role_name, color_hex) in enumerate(color_group):
                emoji = number_emojis[j]
                embed.add_field(
                    name=f"{emoji} {role_name}",
                    value=f"Color: {hex(color_hex)}",
                    inline=True
                )
            
            # Create new message
            try:
                message = await roles_channel.send(embed=embed)
                self.color_message_ids.append(message.id)
                print(f"✅ Created color roles message for group {i+1} (ID: {message.id})")
                
                # Add reactions
                for j in range(len(color_group)):
                    try:
                        await message.add_reaction(number_emojis[j])
                    except Exception as e:
                        print(f"❌ Error adding reaction {number_emojis[j]}: {e}")
                        
            except Exception as e:
                print(f"❌ Error creating message for group {i+1}: {e}")
        
        print(f"🎨 Color roles channel setup complete! Created {len(self.color_message_ids)} messages")
        print(f"📍 Message IDs: {self.color_message_ids}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle reaction-based role assignments on specified messages."""
        # Ignore reactions from the bot itself
        if payload.user_id == self.bot.user.id:
            return

        # Check if the reaction is on one of the color role messages
        if payload.message_id not in self.color_message_ids:
            return

        # Check if the event is in the correct server
        if payload.guild_id != self.fckr_server_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id)
        if not member:
            return

        # Prevent race conditions for the same user
        if member.id in self.role_update_locks and self.role_update_locks[member.id]:
            return  # Another update is in progress
        self.role_update_locks[member.id] = True

        try:
            # Cooldown check
            now = time.time()
            if member.id in self.user_cooldowns and now - self.user_cooldowns[member.id] < 5:
                # Send ephemeral cooldown message
                channel = self.bot.get_channel(payload.channel_id)
                if channel:
                    await channel.send(f"{member.mention}, please wait a moment before changing colors again.", delete_after=5)
                return
            self.user_cooldowns[member.id] = now

            # Map emoji to role index
            number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            try:
                emoji_index = number_emojis.index(str(payload.emoji))
            except ValueError:
                return # Not a valid number emoji

            # Determine which message was reacted to and calculate role index
            message_index = self.color_message_ids.index(payload.message_id)
            role_index = message_index * 10 + emoji_index

            if role_index >= len(self.color_names):
                return # Invalid index

            role_name = self.color_names[role_index]
            role_to_assign = discord.utils.get(guild.roles, name=role_name)

            if not role_to_assign:
                print(f"❌ Role '{role_name}' not found in server.")
                return

            # Get all color roles for easy removal
            all_color_roles = [r for r in guild.roles if r.name in self.color_names]
            member_color_roles = [r for r in member.roles if r in all_color_roles]

            channel = self.bot.get_channel(payload.channel_id)

            # If user already has the role, remove it (toggle off)
            if role_to_assign in member.roles:
                await member.remove_roles(role_to_assign, reason="Toggled color role off")
                if channel:
                    await channel.send(f"{member.mention}, your color role **{role_name}** has been removed.", delete_after=7)
                print(f"🎨 Removed color role '{role_name}' from {member.display_name}")
            else:
                # Remove all other color roles first
                if member_color_roles:
                    await member.remove_roles(*member_color_roles, reason="Changing color role")
                
                # Add the new role
                await member.add_roles(role_to_assign, reason="Selected new color role")
                if channel:
                    await channel.send(f"{member.mention}, you've been given the **{role_name}** color!", delete_after=7)
                print(f"🎨 Assigned color role '{role_name}' to {member.display_name}")

        finally:
            # Remove the reaction to keep the message clean
            channel = self.bot.get_channel(payload.channel_id)
            if channel:
                message = await channel.fetch_message(payload.message_id)
                await message.remove_reaction(payload.emoji, member)
            
            # Release the lock
            self.role_update_locks[member.id] = False
    
    async def verify_color_role_positions(self, guild, fckr_role):
        """Verify that all color roles are positioned above the FCKR role"""
        mispositioned_roles = []
        
        for color_name in self.color_names:
            color_role = discord.utils.get(guild.roles, name=color_name)
            if color_role and color_role.position <= fckr_role.position:
                mispositioned_roles.append(color_role)
        
        if mispositioned_roles:
            print(f"⚠️ Found {len(mispositioned_roles)} color roles below FCKR role, repositioning...")
            target_position = fckr_role.position + 1
            
            for i, role in enumerate(mispositioned_roles):
                try:
                    await role.edit(position=target_position + i)
                    print(f"📍 Fixed position for {role.name}")
                except Exception as e:
                    print(f"❌ Failed to reposition {role.name}: {e}")
        else:
            print("✅ All color roles are correctly positioned above FCKR role")
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle color role reactions across multiple messages"""
        if user.bot:
            return
        
        # Check cooldown (7.5 seconds)
        current_time = time.time()
        if user.id in self.user_cooldowns:
            time_since_last = current_time - self.user_cooldowns[user.id]
            if time_since_last < 7.5:
                remaining = 7.5 - time_since_last
                try:
                    channel = reaction.message.channel
                    if channel:
                        cooldown_embed = discord.Embed(
                            title="⏰ Cooldown Active",
                            description=f"You need to wait **{remaining:.1f} seconds** before you can change your color again.",
                            color=0xffa500
                        )
                        cooldown_embed.set_footer(text="Please wait a moment! ⏳")
                        await user.send(embed=cooldown_embed)
                except:
                    pass
                return
        
        # Set cooldown for user
        self.user_cooldowns[user.id] = current_time
            
        # Check if it's in the roles channel and one of our messages
        if (reaction.message.channel.id != self.roles_channel_id or 
            not hasattr(self, 'color_message_ids') or 
            reaction.message.id not in self.color_message_ids):
            return
        
        # Map emoji to relative index (0-9 for each message)
        emoji_to_relative_index = {
            "1️⃣": 0, "2️⃣": 1, "3️⃣": 2, "4️⃣": 3, "5️⃣": 4,
            "6️⃣": 5, "7️⃣": 6, "8️⃣": 7, "9️⃣": 8, "🔟": 9
        }
        
        if str(reaction.emoji) not in emoji_to_relative_index:
            return
        
        # Calculate absolute color index based on which message was reacted to
        message_index = self.color_message_ids.index(reaction.message.id)
        relative_index = emoji_to_relative_index[str(reaction.emoji)]
        color_index = (message_index * 10) + relative_index
        
        if color_index >= len(self.color_names):
            return
            
        guild = reaction.message.guild
        member = guild.get_member(user.id)
        if not member:
            return
        
        # Get the desired color role
        desired_role_name = self.color_names[color_index]
        desired_role = discord.utils.get(guild.roles, name=desired_role_name)
        
        if not desired_role:
            print(f"❌ Role '{desired_role_name}' not found in guild")
            return
        
        # Verify the role is above FCKR role before proceeding
        fckr_role = discord.utils.get(guild.roles, id=1371442861069041665)
        if fckr_role and desired_role.position <= fckr_role.position:
            print(f"⚠️ Color role {desired_role_name} is not above FCKR role, repositioning...")
            try:
                await desired_role.edit(position=fckr_role.position + 1)
                print(f"✅ Repositioned {desired_role_name} above FCKR role")
            except Exception as e:
                print(f"❌ Failed to reposition {desired_role_name}: {e}")
                # Send error message to user via ephemeral message
                try:
                    channel = reaction.message.channel
                    if channel:
                        error_embed = discord.Embed(
                            title="❌ Error",
                            description=f"There was a problem assigning the color role {desired_role_name}. Please try again or contact an admin.",
                            color=0xff0000
                        )
                        await user.send(embed=error_embed)
                except:
                    pass
                return
        
        try:
            # Check if user already has this role (toggle functionality)
            user_has_role = desired_role in member.roles
            
            if user_has_role:
                # Remove the role (toggle off)
                await member.remove_roles(desired_role, reason="Color role toggle off")
                print(f"🎨 {user.name} removed color role {desired_role_name}")
                
                # Send ephemeral confirmation message
                try:
                    # Get the channel from the reaction
                    channel = reaction.message.channel
                    if channel:
                        confirm_embed = discord.Embed(
                            title="🎨 Color Role Removed!",
                            description=f"Your color role **{desired_role_name}** has been successfully removed! 💫",
                            color=0x808080  # Gray color for removal
                        )
                        confirm_embed.set_footer(text="You can choose a new color anytime! ✨")
                        
                        # Send ephemeral message in channel
                        await user.send(embed=confirm_embed)
                except Exception as e:
                    print(f"⚠️ Error sending removal confirmation to {user.name}: {e}")
            else:
                # Remove all existing color roles from user first
                removed_roles = []
                for role in member.roles:
                    if role.name in self.color_names:
                        await member.remove_roles(role, reason="Color role change")
                        removed_roles.append(role.name)
                
                # Add new color role
                await member.add_roles(desired_role, reason="Color role selection")
                print(f"🎨 {user.name} changed color to {desired_role_name}")
                
                # Send ephemeral confirmation message
                try:
                    # Get the channel from the reaction
                    channel = reaction.message.channel
                    if channel:
                        confirm_embed = discord.Embed(
                            title="🎨 Color Role Changed!",
                            description=f"Your new color **{desired_role_name}** has been successfully assigned! ✨",
                            color=self.color_palette[color_index]
                        )
                        
                        if removed_roles:
                            confirm_embed.add_field(
                                name="Previous Color Removed",
                                value=f"**{removed_roles[0]}**",
                                inline=False
                            )
                        
                        confirm_embed.set_footer(text="Click the same reaction again to remove the color! 💫")
                        
                        # Send ephemeral message in channel
                        await user.send(embed=confirm_embed)
                except Exception as e:
                    print(f"⚠️ Error sending confirmation to {user.name}: {e}")
                
        except Exception as e:
            print(f"❌ Error managing color roles for {user.name}: {e}")
            # Send ephemeral error message to user
            try:
                channel = reaction.message.channel
                if channel:
                    error_embed = discord.Embed(
                        title="❌ Error",
                        description="There was a problem managing your color role. Please try again or contact an admin.",
                        color=0xff0000
                    )
                    await channel.send(f"<@{user.id}>", embed=error_embed, delete_after=7.5)
            except:
                pass
    
    @commands.command(name='colors')
    async def colors_command(self, ctx):
        """Admin command to direct users to the color roles channel"""
        # Check if user has admin permissions
        admin_cog = self.bot.get_cog('AdminManagerCog')
        is_bot_admin = await admin_cog.is_bot_admin(ctx.author.id) if admin_cog else False
        is_admin = ctx.author.guild_permissions.administrator or is_bot_admin
        
        if not is_admin:
            await ctx.send("❌ You need administrator permissions to use this command.", delete_after=10)
            return
            
        embed = discord.Embed(
            title="🎨 Color Roles",
            description=f"Head over to <#{self.roles_channel_id}> to choose your username color!\n\n"
                       "You can pick from 30 different gradient colors to personalize your appearance in the server.",
            color=0x00ff00
        )
        
        embed.set_footer(text="Click the reactions in the roles channel to get your color!")
        await ctx.send(embed=embed)
    
    @commands.command(name='setup_colors')
    async def setup_colors_command(self, ctx):
        """Admin command to manually setup color roles"""
        # Check if user has admin permissions
        admin_cog = self.bot.get_cog('AdminManagerCog')
        is_bot_admin = await admin_cog.is_bot_admin(ctx.author.id) if admin_cog else False
        is_admin = ctx.author.guild_permissions.administrator or is_bot_admin
        
        if not is_admin:
            await ctx.send("❌ You need administrator permissions to use this command.", delete_after=10)
            return
            
        await ctx.send("🎨 Setting up color roles...")
        await self.setup_color_roles()
        await self.setup_roles_channel()
        await ctx.send(f"✅ Color role system has been set up!\n📍 Created {len(self.color_message_ids)} messages with IDs: {self.color_message_ids}")

def setup(bot):
    bot.add_cog(ColorRolesCog(bot))