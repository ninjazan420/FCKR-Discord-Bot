import discord
from discord.ext import commands
import os
from datetime import datetime

class ColorRolesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fckr_server_id = int(os.getenv('FCKR_SERVER', 0))
        self.roles_channel_id = int(os.getenv('ROLES_CHANNEL_ID', 0))
        
        # Get existing color message IDs from environment
        self.color_message_1_id = int(os.getenv('COLOR_MESSAGE_1', 0))
        self.color_message_2_id = int(os.getenv('COLOR_MESSAGE_2', 0))
        self.color_message_3_id = int(os.getenv('COLOR_MESSAGE_3', 0))
        
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
        
        # Get existing color roles
        existing_roles = {role.name: role for role in guild.roles if role.name in self.color_names}
        
        # Create missing roles
        for i, (color_name, color_hex) in enumerate(zip(self.color_names, self.color_palette)):
            if color_name not in existing_roles:
                try:
                    # Create role with high position (just below @everyone's highest role)
                    role = await guild.create_role(
                        name=color_name,
                        color=discord.Color(color_hex),
                        mentionable=False,
                        hoist=False,
                        reason="Color role system setup"
                    )
                    print(f"Created color role: {color_name}")
                    
                    # Move role to appropriate position (high up but below admin roles)
                    try:
                        await role.edit(position=len(guild.roles) - 10)
                    except:
                        pass  # Position editing might fail due to permissions
                        
                except Exception as e:
                    print(f"Error creating color role {color_name}: {e}")

    async def setup_roles_channel(self):
        """Set up the roles channel with color selection messages using predefined message IDs"""
        guild = self.bot.get_guild(self.fckr_server_id)
        if not guild:
            print(f"Guild with ID {self.fckr_server_id} not found")
            return
        
        roles_channel = guild.get_channel(self.roles_channel_id)
        if not roles_channel:
            print(f"Roles channel with ID {self.roles_channel_id} not found")
            return
        
        # Use predefined message IDs from environment variables
        message_ids = [self.color_message_1_id, self.color_message_2_id, self.color_message_3_id]
        self.color_message_ids = [msg_id for msg_id in message_ids if msg_id != 0]
        
        if not self.color_message_ids:
            print("No color message IDs found in environment variables")
            return
        
        # Create 3 messages with 10 colors each
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        color_groups = [
            list(zip(self.color_names[:10], self.color_palette[:10])),   # First 10 colors
            list(zip(self.color_names[10:20], self.color_palette[10:20])), # Next 10 colors
            list(zip(self.color_names[20:], self.color_palette[20:]))    # Remaining colors
        ]
        
        for i, color_group in enumerate(color_groups):
            if not color_group or i >= len(self.color_message_ids):  # Skip empty groups or if no message ID
                continue
                
            embed = discord.Embed(
                title=f"🎨 Color Roles - Group {i+1}",
                description="React with the corresponding number to get your color role!",
                color=0x00ff00
            )
            
            for j, (role_name, color_hex) in enumerate(color_group):
                emoji = number_emojis[j]
                embed.add_field(
                    name=f"{emoji} {role_name}",
                    value=f"Color: {hex(color_hex)}",
                    inline=True
                )
            
            # Update existing message using predefined ID
            try:
                message = await roles_channel.fetch_message(self.color_message_ids[i])
                await message.edit(embed=embed)
                print(f"Updated color roles message for group {i+1} (ID: {self.color_message_ids[i]})")
                
                # Add reactions if they don't exist
                existing_reactions = [str(reaction.emoji) for reaction in message.reactions]
                for j in range(len(color_group)):
                    if number_emojis[j] not in existing_reactions:
                        try:
                            await message.add_reaction(number_emojis[j])
                        except Exception as e:
                            print(f"Error adding reaction: {e}")
                            
            except Exception as e:
                print(f"Error updating message {self.color_message_ids[i]}: {e}")
        
        print("Color roles channel setup complete")
    
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
            return
        
        try:
            # Remove all existing color roles from user
            for role in member.roles:
                if role.name in self.color_names:
                    await member.remove_roles(role, reason="Color role change")
            
            # Add new color role
            await member.add_roles(desired_role, reason="Color role selection")
            
            # Send ephemeral confirmation message (only visible to user)
            try:
                # Create a temporary embed for confirmation
                confirm_embed = discord.Embed(
                    title="🎨 Color Changed!",
                    description=f"Your color has been changed to **{desired_role_name}**!",
                    color=self.color_palette[color_index]
                )
                
                # Create a view with a dismiss button for better UX
                class DismissView(discord.ui.View):
                    def __init__(self):
                        super().__init__(timeout=30)
                    
                    @discord.ui.button(label="Dismiss", style=discord.ButtonStyle.secondary, emoji="❌")
                    async def dismiss_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                        await interaction.response.edit_message(content="Color change confirmed!", embed=None, view=None)
                        await interaction.delete_original_response(delay=1)
                
                # Send as ephemeral followup message (only visible to the user who reacted)
                # We need to create a fake interaction for this to work properly
                # Since we can't send true ephemeral messages from reaction events,
                # we'll send a regular message that mentions the user and auto-deletes
                await reaction.message.channel.send(
                    f"<@{user.id}>", 
                    embed=confirm_embed,
                    view=DismissView(),
                    delete_after=30  # Auto-delete after 30 seconds if not dismissed
                )
            except Exception as e:
                print(f"Error sending confirmation message: {e}")
                
        except Exception as e:
            print(f"Error managing color roles for {user}: {e}")
    
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
        await ctx.send("✅ Color role system has been set up!")

def setup(bot):
    bot.add_cog(ColorRolesCog(bot))