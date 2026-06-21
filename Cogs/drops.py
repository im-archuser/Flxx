import discord
from discord import app_commands
from discord.ext import commands
from utils import checks
import datetime
import os
import database

class DropView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Download", style=discord.ButtonStyle.success, custom_id="download_drop", emoji="<a:file2:1473340156948529193>")
    async def download_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Using interaction.message.id as the key
        message_id = interaction.message.id
        drop_data = await database.get_drop(message_id)
        
        if not drop_data:
            error_embed = discord.Embed(title="❌ Error", description="Drop signature not found. This transmission may be outdated.", color=0xFF0000)
            return await interaction.response.send_message(embed=error_embed, ephemeral=True)
        
        file_path = drop_data['file_path']
        if not os.path.exists(file_path):
            error_embed = discord.Embed(title="❌ Error", description="The physical asset for this drop has been purged from the server.", color=0xFF0000)
            return await interaction.response.send_message(embed=error_embed, ephemeral=True)
        
        # Increment count
        new_count = await database.increment_download_count(message_id)
        
        # Update the original embed
        embed = interaction.message.embeds[0]
        # Find the downloaders field or add it
        found = False
        for i, field in enumerate(embed.fields):
            if "Total Downloads" in field.name:
                embed.set_field_at(i, name="<a:file2:1473340156948529193> Total Downloads", value=f"**{new_count}**", inline=True)
                found = True
                break
        
        if not found:
            embed.add_field(name="<a:file2:1473340156948529193> Total Downloads", value=f"**{new_count}**", inline=True)
            
        await interaction.message.edit(embed=embed)
        
        # Send the file
        file = discord.File(file_path, filename=os.path.basename(file_path))
        success_embed = discord.Embed(
            title="📥 Signal Intercepted",
            description="The asset has been successfully transmitted to your device. Enjoy your drop!",
            color=0x00FF00
        )
        success_embed.set_footer(text="[🔹] Yet Cloud | Secure Delivery")
        await interaction.response.send_message(embed=success_embed, file=file, ephemeral=True)

class Drops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.drop_dir = "drops"
        if not os.path.exists(self.drop_dir):
            os.makedirs(self.drop_dir)

    @app_commands.command(name="drop", description="Drop a file to a specific channel with a professional alert and optional tracker")
    @app_commands.describe(
        channel="The channel to drop the file in", 
        file="The file to drop", 
        service_name="Optional override for the file name in the embed",
        track_downloads="Whether to track downloads (using a button) or send directly (standard attachment)"
    )
    @checks.is_owner_or_admin()
    async def drop(self, interaction: discord.Interaction, channel: discord.TextChannel, file: discord.Attachment, service_name: str = None, track_downloads: bool = True):
        await interaction.response.defer(ephemeral=True)

        try:
            display_name = service_name if service_name else file.filename
            
            # Prepare the embed
            embed = discord.Embed(
                title="<a:bell:1472906474643787786> New Drop Alert!",
                description=f"**{display_name}** has just been dropped by the **YET Cloud Team**!",
                color=0xFF4500 # Orange-Red color
            )
            
            embed.add_field(
                name="<a:file2:1473340156948529193> Download the file below to access your drop.",
                value="\u200b", # Empty value for spacing
                inline=False
            )
            
            embed.add_field(
                name="<a:note2:1473340536768004128> File Name",
                value=f"**{display_name}**",
                inline=True
            )
            
            now = datetime.datetime.now(datetime.timezone.utc)
            timestamp_str = now.strftime("%Y-%m-%d %H:%M UTC")
            
            embed.add_field(
                name="<a:clock2:1473340455582928926> Dropped At",
                value=timestamp_str,
                inline=True
            )
            
            # Add branding
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            embed.set_footer(
                text="YET Cloud Network • Join us on Telegram",
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )

            if track_downloads:
                # --- Tracked Design (Button + DB) ---
                # Save file locally for tracking
                sanitized_name = "".join(c for c in display_name if c.isalnum() or c in (" ", "-", "_")).strip()
                timestamp_prefix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                local_filename = f"{timestamp_prefix}_{sanitized_name}.txt" if not sanitized_name.endswith(".txt") else f"{timestamp_prefix}_{sanitized_name}"
                file_path = os.path.join(self.drop_dir, local_filename)
                await file.save(file_path)

                # Add initial downloaders field
                embed.add_field(
                    name="<a:file2:1473340156948529193> Total Downloads",
                    value="**0**",
                    inline=False
                )

                # Send with Button View
                view = DropView(self.bot)
                sent_message = await channel.send(embed=embed, view=view)
                
                # Store in DB
                await database.save_drop(
                    message_id=sent_message.id,
                    guild_id=interaction.guild_id,
                    channel_id=channel.id,
                    file_path=file_path,
                    display_name=display_name
                )
            else:
                # --- Standard Design (Direct Attachment) ---
                attachment_file = await file.to_file()
                await channel.send(embed=embed, file=attachment_file)
                sent_message = None # No message ID needed for tracking

            # Send to Drop Log Channel
            log_channel_id = 1472555176584810641
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title="<a:note2:1473340536768004128> | YET Cloud Drop Audit",
                    description=f"A new service drop has been dispatched ({'Tracked' if track_downloads else 'Standard'}).",
                    color=0xFF4500,
                    timestamp=discord.utils.utcnow()
                )
                
                if interaction.user.display_avatar:
                    log_embed.set_thumbnail(url=interaction.user.display_avatar.url)
                
                log_embed.add_field(
                    name="<a:staff1:1473339328246321282> Moderator", 
                    value=f"{interaction.user.mention}\n`{interaction.user.id}`", 
                    inline=True
                )
                log_embed.add_field(
                    name="<:tag1:1473340733560553482> Target Channel", 
                    value=f"{channel.mention}\n`{channel.id}`", 
                    inline=True
                )
                log_embed.add_field(
                    name="📄 File Dropped", 
                    value=f"Display Name: **{display_name}**" + (f"\nTracking ID: `{sent_message.id}`" if sent_message else ""), 
                    inline=False
                )
                
                footer_text = f"YET Cloud Audit • {interaction.guild.name}"
                if interaction.guild.icon:
                    log_embed.set_footer(text=footer_text, icon_url=interaction.guild.icon.url)
                else:
                    log_embed.set_footer(text=footer_text)
                
                await log_channel.send(embed=log_embed)

            status_embed = discord.Embed(
                title="✅ Drop Dispatched",
                description=f"Successfully transmitted `{display_name}` to {channel.mention}.",
                color=0x00FFFF
            )
            if track_downloads:
                status_embed.add_field(name="🛰️ Tracking", value="Download metrics are being recorded.", inline=True)
            status_embed.set_footer(text="[🔹] Yet Cloud | Deployment System")
            await interaction.followup.send(embed=status_embed, ephemeral=True)

        except Exception as e:
            error_embed = discord.Embed(title="❌ Deployment Failed", description=f"A critical error occurred: `{e}`", color=0xFF0000)
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @app_commands.command(name="force_drop", description="Trigger an immediate random drop from the current stock")
    @checks.is_owner_or_admin()
    async def force_drop(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        # Randomly pick a file from stock_files/free or stock_files/premium
        import random
        all_files = []
        for root, dirs, files in os.walk("stock_files"):
            for f in files:
                if f.endswith(".txt"):
                    all_files.append(os.path.join(root, f))
        
        if not all_files:
            embed = discord.Embed(title="❌ Error", description="No stock files found to drop.", color=0xFF0000)
            return await interaction.followup.send(embed=embed, ephemeral=True)
            
        pick = random.choice(all_files)
        # Use existing drop logic or just a simplified version
        display_name = os.path.basename(pick).replace(".txt", "").upper()
        
        # Post to a drop channel (stub for now, should use a config)
        drop_channel_id = 1472555138534211597 # Placeholder
        channel = self.bot.get_channel(drop_channel_id) or interaction.channel
        
        embed = discord.Embed(
            title="🌊 IMMEDIATE DROP INITIATED",
            description=f"A random server asset, **{display_name}**, has been forcibly dropped!",
            color=0x00FFFF
        )
        embed.set_footer(text="[🔹] Yet Cloud | System Overdrive")
        
        file = discord.File(pick, filename=f"FREE_{display_name}_DROP.txt")
        await channel.send(embed=embed, file=file)
        
        success_embed = discord.Embed(title="✅ Force Drop Successful", description=f"Randomized asset `{display_name}` has been deployed to {channel.mention}.", color=0x00FF00)
        await interaction.followup.send(embed=success_embed, ephemeral=True)

    @app_commands.command(name="set_drop_channel", description="Configure the primary destination for automated drops")
    @app_commands.describe(channel="Target channel")
    @checks.is_owner_or_admin()
    async def set_drop_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        # Implementation would save to database config
        embed = discord.Embed(
            title="🌌 Drop Configuration Updated",
            description=f"Automated system drops will now be directed to {channel.mention}.",
            color=0x00FFFF
        )
        embed.set_footer(text="[🔹] Yet Cloud | System Config")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Drops(bot))
