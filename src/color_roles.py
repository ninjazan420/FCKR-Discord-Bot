import discord
from discord.ext import commands
import os
from datetime import datetime

class ColorRolesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fckr_server_id = int(os.getenv('FCKR_SERVER', 0))
        self.roles_channel_id = int(os.getenv('ROLES_CHANNEL_ID', 0))
        
        # Store message IDs dynamically (created at startup)
        self.color_message_ids = []
        
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
        """Set up the roles channel with fresh color selection messages"""
        guild = self.bot.get_guild(self.fckr_server_id)
        if not guild:
            print(f"❌ Guild with ID {self.fckr_server_id} not found")
            return
        
        roles_channel = guild.get_channel(self.roles_channel_id)
        if not roles_channel:
            print(f"❌ Roles channel with ID {self.roles_channel_id} not found")
            return
        
        print(f"🎨 Setting up fresh color role messages in {roles_channel.name}")
        
        # Clear old color messages (search for messages with "Color Roles" in title)
        try:
            async for message in roles_channel.history(limit=50):
                if (message.author == self.bot.user and 
                    message.embeds and 
                    "Color Roles" in message.embeds[0].title):
                    await message.delete()
                    print(f"🗑️ Deleted old color message: {message.id}")
        except Exception as e:
            print(f"⚠️ Could not clear old messages: {e}")
        
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
                # Send error message to user privately
                try:
                    await user.send(f"❌ Es gab ein Problem beim Zuweisen der Farbrolle {desired_role_name}. Bitte versuche es erneut oder kontaktiere einen Admin.")
                except:
                    pass
                return
        
        try:
            # Check if user already has this role (toggle functionality)
            user_has_role = desired_role in member.roles
            
            if user_has_role:
                # Remove the role (toggle off)
                await member.remove_roles(desired_role, reason="Color role toggle off")
                print(f"🎨 {member.name} removed color role {desired_role_name}")
                
                # Send ephemeral confirmation message
                try:
                    confirm_embed = discord.Embed(
                        title="🎨 Farbrolle entfernt!",
                        description=f"Deine Farbrolle **{desired_role_name}** wurde erfolgreich entfernt! 💫",
                        color=0x808080  # Gray color for removal
                    )
                    confirm_embed.set_footer(text="Du kannst jederzeit eine neue Farbe wählen! ✨")
                    
                    # Send ephemeral message that only the user can see
                    await payload.member.send(embed=confirm_embed, delete_after=10)
                except Exception as e:
                    print(f"⚠️ Error sending removal confirmation to {user}: {e}")
            else:
                # Remove all existing color roles from user first
                removed_roles = []
                for role in member.roles:
                    if role.name in self.color_names:
                        await member.remove_roles(role, reason="Color role change")
                        removed_roles.append(role.name)
                
                # Add new color role
                await member.add_roles(desired_role, reason="Color role selection")
                print(f"🎨 {member.name} changed color to {desired_role_name}")
                
                # Send ephemeral confirmation message
                try:
                    confirm_embed = discord.Embed(
                        title="🎨 Farbrolle geändert!",
                        description=f"Deine neue Farbe **{desired_role_name}** wurde erfolgreich zugewiesen! ✨",
                        color=self.color_palette[color_index]
                    )
                    
                    if removed_roles:
                        confirm_embed.add_field(
                            name="Vorherige Farbe entfernt",
                            value=f"**{removed_roles[0]}**",
                            inline=False
                        )
                    
                    confirm_embed.set_footer(text="Klicke erneut auf die gleiche Reaktion, um die Farbe zu entfernen! 💫")
                    
                    # Send ephemeral message that only the user can see
                    await payload.member.send(embed=confirm_embed, delete_after=10)
                except Exception as e:
                    print(f"⚠️ Error sending confirmation to {user}: {e}")
                
        except Exception as e:
            print(f"❌ Error managing color roles for {user}: {e}")
            # Send ephemeral error message to user
            try:
                error_embed = discord.Embed(
                    title="❌ Fehler",
                    description="Es gab ein Problem beim Verwalten deiner Farbrolle. Bitte versuche es erneut oder kontaktiere einen Admin.",
                    color=0xff0000
                )
                await payload.member.send(embed=error_embed, delete_after=10)
            except:
                pass
    
    @commands.command(name='colors')
    async def colors_command(self, ctx):
        """Direct users to the color roles channel"""
        embed = discord.Embed(
            title="🎨 Color Roles",
            description=f"Head over to <#{self.roles_channel_id}> to choose your username color!\n\n"
                       "You can pick from 30 different gradient colors to personalize your appearance in the server.",
            color=0x00ff00
        )
        
        embed.set_footer(text="Click the reactions in the roles channel to get your color!")
        await ctx.send(embed=embed)
    
    @commands.command(name='setup_colors')
    @commands.has_permissions(administrator=True)
    async def setup_colors_command(self, ctx):
        """Admin command to manually setup color roles"""
        await ctx.send("🎨 Setting up color roles...")
        await self.setup_color_roles()
        await self.setup_roles_channel()
        await ctx.send(f"✅ Color role system has been set up!\n📍 Created {len(self.color_message_ids)} messages with IDs: {self.color_message_ids}")

def setup(bot):
    bot.add_cog(ColorRolesCog(bot))