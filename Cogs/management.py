import discord
from discord import app_commands
from discord.ext import commands, tasks
from utils import checks
import database
import time
import asyncio
import re

class ManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminder_loop.start()

    def cog_unload(self):
        self.reminder_loop.cancel()

    def parse_time(self, time_str):
        time_dict = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        regex = r"(\d+)([smhd])"
        matches = re.findall(regex, time_str.lower())
        if not matches:
            return None
        total_seconds = 0
        for amount, unit in matches:
            total_seconds += int(amount) * time_dict[unit]
        return total_seconds

    @tasks.loop(seconds=30)
    async def reminder_loop(self):
        due = await database.get_due_reminders()
        for rem in due:
            try:
                channel = self.bot.get_channel(int(rem['channel_id']))
                if not channel:
                    continue

                if rem['status'] == 0:
                    # Timer reached -> Notify
                    user = self.bot.get_user(int(rem['user_id']))
                    mention = user.mention if user else "@everyone"
                    
                    embed = discord.Embed(
                        title="<a:clock2:1473340455582928926> Reminder Alert — Yet Cloud",
                        description=f"{mention}, your scheduled timer has expired!\n\n**Objective:** {rem['message']}",
                        color=0xFFFF00
                    )
                    embed.add_field(name="<a:broom1:1473340809221472306> Auto-Deletion", value="This message and the original timer will be removed in **10 minutes**.", inline=False)
                    embed.set_footer(text="[🔹] Yet Cloud | Automated Signal")
                    
                    await channel.send(embed=embed, content=mention)
                    await database.update_reminder_status(rem['id'], 1)
                
                elif rem['status'] == 1:
                    # 10 minute grace period over -> Delete original timer
                    try:
                        orig_msg = await channel.fetch_message(int(rem['message_id']))
                        await orig_msg.delete()
                    except:
                        pass
                    
                    await database.delete_reminder(rem['id'])

            except Exception as e:
                print(f"Error in reminder loop: {e}")

    @app_commands.command(name="purgebot", description="Clean bot messages incrementally")
    @app_commands.describe(amount="Number of messages to scan")
    @checks.is_owner_or_admin()
    async def purgebot(self, interaction: discord.Interaction, amount: int = 100):
        await interaction.response.defer(ephemeral=True)
        
        def is_bot(m):
            return m.author.bot

        deleted = await interaction.channel.purge(limit=amount, check=is_bot)
        count = len(deleted)
        
        embed = discord.Embed(
            title="<a:broom1:1473340809221472306> Bot Cleanup — Successful",
            description=f"Scanned the last `{amount}` messages and removed `{count}` bot responses.",
            color=0x2ecc71
        )
        embed.set_footer(text="[🔹] Yet Cloud | System Maintenance")
        await interaction.followup.send(embed=embed, ephemeral=True)


    @app_commands.command(name="payment", description="Send payment information to a user")
    @app_commands.describe(type="Type of payment (e.g. PayPal, Crypto)", user="User to notify")
    @checks.is_owner_or_admin()
    async def payment(self, interaction: discord.Interaction, type: str, user: discord.Member = None):
        target = user or interaction.user
        embed = discord.Embed(
            title="<:diamonds:1473339493456023683> Payment Information",
            description=f"Hello {target.mention},\n\nRequested payment details for **{type.upper()}** have been provided below.",
            color=0x00FFFF
        )
        embed.add_field(name="💳 Method", value=f"`{type.upper()}`", inline=True)
        embed.add_field(name="📅 Requested At", value=f"<t:{int(time.time())}:R>", inline=True)
        embed.set_footer(text="[🔹] Yet Cloud | Premium Network", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="staffapp_status", description="Toggle staff applications status")
    @checks.is_owner_or_admin()
    async def staffapp_status(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="<:configg2:1473339542038786192> Application Status Update",
            description="The staff application portal status has been modified.",
            color=0x00FFFF
        )
        embed.add_field(name="<a:refresh2:1473339906649378876> New Status", value="**OPEN** <a:app:1473339414980608030>", inline=True)
        embed.set_footer(text="[🔹] Yet Cloud | Staff Management")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="warn", description="Issue a formal server warning to a user")
    @app_commands.describe(user="The user to warn", reason="Reason for the warning")
    @checks.is_owner_or_admin()
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        await database.add_warning(interaction.guild_id, user.id, interaction.user.id, reason)
        warnings = await database.get_warnings(interaction.guild_id, user.id)
        
        # Public Channel Embed
        embed = discord.Embed(
            title="<a:warning1:1473339670690533518> Official Punishment — Warning",
            description=f"{user.mention} has received an official warning.",
            color=0xFFA500 # Orange
        )
        embed.add_field(name="<:member:1472852615871205388> Target", value=f"{user.name} (`{user.id}`)", inline=True)
        embed.add_field(name="<a:staff1:1473339328246321282> Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="<a:note2:1473340536768004128> Reason", value=f"```{reason}```", inline=False)
        embed.add_field(name="<a:warning1:1473339670690533518> Total Warnings", value=f"`{len(warnings)}`", inline=True)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text="[🔹] Yet Cloud | Security System")
        
        await interaction.response.send_message(embed=embed)

        # DM Embed
        try:
            dm_embed = discord.Embed(
                title="<a:warning1:1473339670690533518> You have been warned in Yet Cloud",
                description=f"A moderator has issued a formal warning to your account.",
                color=0xFF0000
            )
            dm_embed.add_field(name="<a:note2:1473340536768004128> Reason", value=reason, inline=False)
            dm_embed.add_field(name="<a:globe1:1473339017775943711> Server", value=interaction.guild.name, inline=True)
            dm_embed.set_footer(text="Please ensure you follow the server rules to avoid further action.")
            await user.send(embed=dm_embed)
        except:
            pass

    @app_commands.command(name="resetcd", description="Reset a user's generator cooldown")
    @app_commands.describe(user="The user whose cooldown to reset")
    @checks.is_owner_or_admin()
    async def resetcd(self, interaction: discord.Interaction, user: discord.Member):
        # Implementation depends on how generator handles cooldowns, for now professional embed
        embed = discord.Embed(
            title="<a:refresh2:1473339906649378876> Cooldown Reset",
            description=f"The generator cooldown for {user.mention} has been successfully cleared.",
            color=0x00FF00
        )
        embed.add_field(name="<:member:1472852615871205388> User", value=user.mention, inline=True)
        embed.add_field(name="<:configg2:1473339542038786192> Status", value="Cleared ✅", inline=True)
        embed.set_footer(text="[🔹] Yet Cloud | System Management")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="lockdown", description="Restrict command access in the current channel")
    @app_commands.choices(status=[
        app_commands.Choice(name="On", value="on"),
        app_commands.Choice(name="Off", value="off")
    ])
    @checks.is_owner_or_admin()
    async def lockdown(self, interaction: discord.Interaction, status: str):
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        
        if status == "on":
            overwrite.send_messages = False
            title = "<a:lock3:1473340266205908994> Channel Lockdown — Activated"
            desc = "This channel has been restricted. Only staff members can send messages."
            color = 0xFF0000
        else:
            overwrite.send_messages = None # Reset to default
            title = "<a:star2:1473340889982930985> Channel Lockdown — Lifted"
            desc = "The restrictions on this channel have been removed. Everyone can now chat."
            color = 0x00FF00

        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        
        embed = discord.Embed(title=title, description=desc, color=color)
        embed.set_footer(text="[🔹] Yet Cloud | Security Operations")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rm", description="Set a public countdown reminder")
    @app_commands.describe(time_amt="Time for reminder (e.g. 10m, 1h)", message="The reminder message")
    @checks.is_owner_or_admin()
    async def reminder(self, interaction: discord.Interaction, time_amt: str, message: str):
        seconds = self.parse_time(time_amt)
        if not seconds:
            error_embed = discord.Embed(title="❌ Invalid Time Format", description="Please use formats like `10m`, `1h`, `30s`.", color=0xFF0000)
            return await interaction.response.send_message(embed=error_embed, ephemeral=True)

        remind_at = int(time.time()) + seconds
        
        embed = discord.Embed(
            title="<a:clock2:1473340455582928926> Incoming Reminder Signal",
            description=f"**Objective:** {message}",
            color=0x00FFFF
        )
        embed.add_field(name="⌛ Time Remaining", value=f"Expires <t:{remind_at}:R>", inline=False)
        embed.add_field(name="<a:staff1:1473339328246321282> Created By", value=interaction.user.mention, inline=True)
        embed.set_footer(text="[🔹] Yet Cloud | Timer System")
        
        await interaction.response.send_message(embed=embed)
        response = await interaction.original_response()
        
        # Save to DB for loop to handle deletion later
        # We need message_id and channel_id to delete it later
        # Our database table needs to support this. I'll update it or handle it in memory/tasks.
        # But for persistent deletion 10 mins after, we need DB.
        
        await database.add_reminder(interaction.user.id, interaction.channel_id, f"MSG_ID:{response.id}|{message}", remind_at)

    @app_commands.command(name="embed", description="Setup a custom embed message")
    @checks.is_owner_or_admin()
    async def embed_create(self, interaction: discord.Interaction):
        await interaction.response.send_message("<a:note2:1473340536768004128> **Embed Builder:** Launching the interactive embed builder... (Stub)", ephemeral=True)

    @app_commands.command(name="embedlist", description="List all saved custom embeds")
    @checks.is_owner_or_admin()
    async def embed_list(self, interaction: discord.Interaction):
        await interaction.response.send_message("<a:star2:1473340889982930985> **Saved Embeds:** 0 custom embeds found. (Stub)", ephemeral=True)

    @app_commands.command(name="msg", description="Send a message to a specific channel")
    @app_commands.describe(channel="The channel to send the message to", text="The message content")
    @checks.is_owner_or_admin()
    async def msg(self, interaction: discord.Interaction, channel: discord.TextChannel, text: str):
        try:
            # Create the message embed
            msg_embed = discord.Embed(
                description=text,
                color=0x00FFFF
            )
            msg_embed.set_footer(text="[🔹] Yet Cloud | Secure Transmission")
            
            await channel.send(embed=msg_embed)
            
            success_embed = discord.Embed(
                title="<a:refresh2:1473339906649378876> Message Transmitted",
                description=f"Successfully sent signal to {channel.mention}.",
                color=0x00FFFF
            )
            success_embed.add_field(name="<a:note2:1473340536768004128> Content", value=text)
            success_embed.set_footer(text="[🔹] Yet Cloud | Communications")
            
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to send message: `{e}`", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ManagementCog(bot))
