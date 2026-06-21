import discord
from discord import app_commands
from discord.ext import commands
import config
import base64
import json
import urllib.parse

class VerificationView(discord.ui.View):
    def __init__(self, oauth_url):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Verify", style=discord.ButtonStyle.link, url=oauth_url))

from utils import checks

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup-verification", description="Sets up the verification panel")
    @checks.is_owner_or_admin()
    @app_commands.describe(role="The Verified Role", unverified_role="The Unverified/Auto Join Role", channel="The channel to send to", title="Embed Title", description="Embed Description", color="Hex color (e.g. 00FFFF)", image="Image URL", thumbnail="Thumbnail URL", footer="Custom footer text", verify_emoji="Custom Verify Emoji", dot_emoji="Custom Dot Emoji", support_channel="Support Channel")
    async def setup_verification(self, interaction: discord.Interaction, role: discord.Role, unverified_role: discord.Role, channel: discord.TextChannel, title: str = None, description: str = None, color: str = "00FFFF", image: str = None, thumbnail: str = None, footer: str = None, verify_emoji: str = "<a:star2:1473340889982930985>", dot_emoji: str = "<a:arrow:1472906559024664750>", support_channel: discord.TextChannel = None):

        
        # Permission Setup
        # 1. Lockdown the Unverified Role Globally
        try:
            u_perms = unverified_role.permissions
            if u_perms.view_channel:
                u_perms.update(view_channel=False)
                await unverified_role.edit(permissions=u_perms)
                await interaction.channel.send(f"Locked down {unverified_role.name}: Disabled 'View Channel' globally.")
        except Exception as e:
            print(f"Failed to edit unverified role: {e}")

        # 2. Allow Unverified Role to see Verification Channel
        try:
            await channel.set_permissions(unverified_role, view_channel=True, send_messages=False)
        except Exception as e:
            print(f"Failed to set perms for verify channel: {e}")

        # 3. Allow Unverified Role to see Support Channel
        if support_channel:
            try:
                await support_channel.set_permissions(unverified_role, view_channel=True, send_messages=True)
            except Exception as e:
                print(f"Failed to set perms for support channel: {e}")

        # 4. Ensure Verified Role has global view (Optional, but good practice if not set)
        try:
            v_perms = role.permissions
            if not v_perms.view_channel:
                v_perms.update(view_channel=True)
                await role.edit(permissions=v_perms)
        except Exception as e:
            print(f"Failed to edit verified role: {e}")

        v_emoji = verify_emoji 
        d_emoji = dot_emoji
        
        # Link to support channel in description
        support_mention = support_channel.mention if support_channel else "<#1472555057298935940>"

        embed_title = title or f"{v_emoji}・YETCloud Verification"
        embed_desc = description or (
            f"{d_emoji} For any kind of help, use {support_mention}.\n"
            f"{d_emoji} Verifying is 100% safe — we do not own the bot.\n"
            f"{d_emoji} No alt accounts are allowed in the server.\n"
            f"{d_emoji} If you want to alt-boost the server, boost it — you'll automatically gain access."
        )
        
        try:
            embed_color = int(color.replace("#", ""), 16)
        except ValueError:
            embed_color = 0x00FFFF

        embed = discord.Embed(title=embed_title, description=embed_desc, color=embed_color)
        embed.set_footer(text=footer or "YET Cloud", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.timestamp = interaction.created_at

        if image:
            embed.set_image(url=image)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        else:
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)

        # Generate OAuth URL
        # Generate OAuth URL
        state_data = json.dumps({
            'g': str(interaction.guild.id), 
            'r': str(role.id),
            'u': str(unverified_role.id)
        })
        encoded_state = base64.b64encode(state_data.encode('utf-8')).decode('utf-8')
        
        params = {
            'client_id': config.CLIENT_ID,
            'redirect_uri': config.REDIRECT_URI,
            'response_type': 'code',
            'scope': 'identify guilds.join',
            'state': encoded_state
        }
        oauth_url = f"https://discord.com/api/oauth2/authorize?{urllib.parse.urlencode(params)}"

        view = VerificationView(oauth_url)
        
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"Verification panel sent to {channel.mention}!\nPermissions updated to lock down other channels.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Verification(bot))
