import discord
from discord import app_commands
from discord.ext import commands
from utils import checks

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="Permanently ban a user from the server")
    @app_commands.describe(user="The user to ban", reason="The reason for the ban")
    @checks.is_owner_or_admin()
    async def ban(self, interaction: discord.Interaction, user: discord.User, reason: str = "No reason provided"):
        if user == interaction.user:
            error_embed = discord.Embed(title="❌ Error", description="Self-harm detected. You cannot ban yourself from the system.", color=0xFF0000)
            return await interaction.response.send_message(embed=error_embed, ephemeral=True)
        
        # Check permissions
        if interaction.guild.me.top_role <= interaction.guild.get_member(user.id).top_role if interaction.guild.get_member(user.id) else False:
             error_embed = discord.Embed(title="❌ Permission Denied", description="Target user has a higher or equal role hierarchy. Access denied.", color=0xFF0000)
             return await interaction.response.send_message(embed=error_embed, ephemeral=True)

        try:
            await interaction.guild.ban(user, reason=f"Banned by {interaction.user}: {reason}")
            
            # Send public confirmation
            embed = discord.Embed(
                title="<a:banv2:1473339741368623196> User Banned",
                description=f"**{user}** has been permanently banned.",
                color=0xFF0000
            )
            embed.add_field(name="<a:staff1:1473339328246321282> Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="<a:note2:1473340536768004128> Reason", value=reason, inline=True)
            embed.set_thumbnail(url=user.display_avatar.url if user.display_avatar else None)
            
            await interaction.response.send_message(embed=embed)

            # Send to Ban Log Channel
            log_channel = self.bot.get_channel(1472555164685701202)
            if log_channel:
                log_embed = discord.Embed(
                    title="<a:banv2:1473339741368623196> Member Banned",
                    color=0xFF0000,
                    timestamp=discord.utils.utcnow()
                )
                log_embed.add_field(name="<:member:1472852615871205388> Member", value=f"{user.mention} (`{user.id}`)", inline=True)
                log_embed.add_field(name="<a:staff1:1473339328246321282> Banned By", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=True)
                log_embed.add_field(name="<a:note2:1473340536768004128> Reason", value=reason, inline=False)
                if user.display_avatar:
                    log_embed.set_thumbnail(url=user.display_avatar.url)
                
                await log_channel.send(embed=log_embed)
        except discord.Forbidden:
            error_embed = discord.Embed(title="❌ Permissions Failed", description="The system lacks the necessary authority to execute this ban.", color=0xFF0000)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
        except Exception as e:
            error_embed = discord.Embed(title="❌ System Error", description=f"An unexpected glitch occurred: `{e}`", color=0xFF0000)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="unban", description="Remove a ban from a user")
    @app_commands.describe(user_id="The ID of the user to unban")
    @checks.is_owner_or_admin()
    async def unban(self, interaction: discord.Interaction, user_id: str):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            
            # Send public confirmation
            embed = discord.Embed(
                title="<a:unbanv1:1473339833446187060> User Unbanned",
                description=f"**{user}** has been unbanned.",
                color=0x00FF00
            )
            embed.add_field(name="<a:staff1:1473339328246321282> Moderator", value=interaction.user.mention, inline=True)
            embed.set_thumbnail(url=user.display_avatar.url if user.display_avatar else None)
            
            await interaction.response.send_message(embed=embed)

            # Send to Ban Log Channel
            log_channel = self.bot.get_channel(1472555164685701202)
            if log_channel:
                log_embed = discord.Embed(
                    title="<a:unbanv1:1473339833446187060> Member Unbanned",
                    color=0x00FF00,
                    timestamp=discord.utils.utcnow()
                )
                log_embed.add_field(name="<:member:1472852615871205388> Member", value=f"{user.mention} (`{user.id}`)", inline=True)
                log_embed.add_field(name="<a:staff1:1473339328246321282> Unbanned By", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=True)
                if user.display_avatar:
                    log_embed.set_thumbnail(url=user.display_avatar.url)
                
                await log_channel.send(embed=log_embed)
        except discord.NotFound:
            error_embed = discord.Embed(title="❌ Error", description="Target user is not currently in the ban database.", color=0xFF0000)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
        except ValueError:
            error_embed = discord.Embed(title="❌ Error", description="Invalid User ID provided. Please check the identification digits.", color=0xFF0000)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
        except discord.Forbidden:
            error_embed = discord.Embed(title="❌ Permissions Failed", description="The system lacks the authority to modify the ban registry.", color=0xFF0000)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
        except Exception as e:
            error_embed = discord.Embed(title="❌ System Error", description=f"An unexpected glitch occurred: `{e}`", color=0xFF0000)
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="banlist", description="List all banned users in the server")
    @checks.is_owner_or_admin()
    async def banlist(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            bans = []
            async for entry in interaction.guild.bans(limit=50):
                bans.append(f"**{entry.user}** (`{entry.user.id}`)\n└ Reason: {entry.reason or 'No reason provided'}")
            
            if not bans:
                info_embed = discord.Embed(title="ℹ️ Registry Empty", description="No recent ban logs detected in the server database.", color=0x00FFFF)
                return await interaction.followup.send(embed=info_embed, ephemeral=True)
            
            embed = discord.Embed(
                title="<a:banv2:1473339741368623196> Ban List (Last 50 Banned)",
                description="\n\n".join(bans),
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.Forbidden:
            error_embed = discord.Embed(title="❌ Access Denied", description="The system lacks authority to view the server's restricted registry.", color=0xFF0000)
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            error_embed = discord.Embed(title="❌ System Error", description=f"An unexpected glitch occurred: `{e}`", color=0xFF0000)
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @app_commands.command(name="clear", description="Bulk delete messages from the current channel")
    @app_commands.describe(amount="The number of messages to delete (1-100)")
    @checks.is_owner_or_admin()
    async def clear(self, interaction: discord.Interaction, amount: int):
        if amount < 1 or amount > 100:
            error_embed = discord.Embed(title="❌ Invalid Parameter", description="Please specify a range between `1` and `100` messages.", color=0xFF0000)
            return await interaction.response.send_message(embed=error_embed, ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        
        try:
            deleted = await interaction.channel.purge(limit=amount)
            deleted_count = len(deleted)
            
            # Professional confirmation
            embed = discord.Embed(
                title="<a:broom1:1473340809221472306> Channel Cleared",
                description=f"Successfully purged **{deleted_count}** messages from this channel.",
                color=0x00FF00
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Audit Logging
            log_channel_id = 1472555175477645334
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title="<a:broom1:1473340809221472306> Messages Purged",
                    description=f"A bulk message deletion has been executed.",
                    color=0x2f3136, # Dark grey
                    timestamp=discord.utils.utcnow()
                )
                log_embed.add_field(name="<a:staff1:1473339328246321282> Moderator", value=interaction.user.mention, inline=True)
                log_embed.add_field(name="<:tag1:1473340733560553482> Channel", value=interaction.channel.mention, inline=True)
                log_embed.add_field(name="<a:clock2:1473340455582928926> Amount", value=f"`{deleted_count}` messages", inline=True)
                
                log_embed.set_footer(text="[🔹] Yet Cloud | Security & Audit System")
                await log_channel.send(embed=log_embed)

        except discord.Forbidden:
            error_embed = discord.Embed(title="❌ Permissions Failed", description="The system lacks authority to purge messages in this channel.", color=0xFF0000)
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            error_embed = discord.Embed(title="❌ System Error", description=f"An unexpected glitch occurred: `{e}`", color=0xFF0000)
            await interaction.followup.send(embed=error_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
