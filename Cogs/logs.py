import discord
from discord.ext import commands
import datetime

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = 1472555175477645334
        self.boost_channel_id = 1472555166593978408
        self.ban_channel_id = 1472555164685701202
        self.owner_id = 1249726528393183363

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry):
        # --- Role Update Log ---
        if entry.action == discord.AuditLogAction.member_role_update:
            # Check if moderator is Admin or Owner
            is_owner = entry.user.id == self.owner_id
            is_admin = entry.user.guild_permissions.administrator
            
            if not (is_owner or is_admin):
                return

            log_channel = self.bot.get_channel(self.log_channel_id)
            if not log_channel:
                return

            # Identify added and removed roles
            added_roles = entry.after.roles if hasattr(entry.after, 'roles') else []
            removed_roles = entry.before.roles if hasattr(entry.before, 'roles') else []

            if not added_roles and not removed_roles:
                return

            embed = discord.Embed(
                title="<:folder1:1472852636603531274> Role Update Log",
                color=0x2f3136,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            
            embed.set_thumbnail(url=entry.target.display_avatar.url if entry.target.display_avatar else None)
            
            embed.add_field(name="<:member:1472852615871205388> Target User", value=f"{entry.target.mention} (`{entry.target.id}`)", inline=True)
            embed.add_field(name="<a:staff1:1473339328246321282> Moderator", value=f"{entry.user.mention} (`{entry.user.id}`)", inline=True)

            if added_roles:
                role_mentions = [role.mention for role in added_roles]
                embed.add_field(name="<:add:1473267423854592103> Roles Added", value="\n".join(role_mentions), inline=False)
                
            if removed_roles:
                role_mentions = [role.mention for role in removed_roles]
                embed.add_field(name="<a:broom1:1473340809221472306> Roles Removed", value="\n".join(role_mentions), inline=False)

            embed.set_footer(text=f"Server: {entry.guild.name}", icon_url=entry.guild.icon.url if entry.guild.icon else None)
            await log_channel.send(embed=embed)

        # --- Ban Log ---
        elif entry.action == discord.AuditLogAction.member_ban_add:
            ban_channel = self.bot.get_channel(self.ban_channel_id)
            if not ban_channel: return

            embed = discord.Embed(
                title="<a:banv2:1473339741368623196> Member Banned",
                color=0xFF0000,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            embed.add_field(name="<:member:1472852615871205388> Prohibid Member", value=f"{entry.target.mention} (`{entry.target.id}`)", inline=True)
            embed.add_field(name="<a:staff1:1473339328246321282> Banned By", value=f"{entry.user.mention} (`{entry.user.id}`)", inline=True)
            embed.add_field(name="<a:note2:1473340536768004128> Reason", value=entry.reason or "No reason provided", inline=False)
            
            if entry.target.display_avatar:
                embed.set_thumbnail(url=entry.target.display_avatar.url)
                
            await ban_channel.send(embed=embed)

        # --- Unban Log ---
        elif entry.action == discord.AuditLogAction.member_ban_remove:
            ban_channel = self.bot.get_channel(self.ban_channel_id)
            if not ban_channel: return

            embed = discord.Embed(
                title="<a:unbanv1:1473339833446187060> Member Unbanned",
                color=0x00FF00,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            embed.add_field(name="<:member:1472852615871205388> Member", value=f"{entry.target.mention} (`{entry.target.id}`)", inline=True)
            embed.add_field(name="<a:staff1:1473339328246321282> Unbanned By", value=f"{entry.user.mention} (`{entry.user.id}`)", inline=True)
            
            if entry.target.display_avatar:
                embed.set_thumbnail(url=entry.target.display_avatar.url)
                
            await ban_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # 1. Someone starts boosting
        if before.premium_since is None and after.premium_since is not None:
            # --- Public Celebration ---
            public_channel_id = 1472555088336781443
            public_channel = self.bot.get_channel(public_channel_id)
            if public_channel:
                embed = discord.Embed(
                    title=f"Look, {after.name} Has Boosted The Server",
                    description="**Another Cool Person Has Boosted The Server Why Can't You?**",
                    color=0xFF73FA, # Pinkish boost color
                )
                
                embed.add_field(name="Booster", value=after.name, inline=True)
                embed.add_field(name="Server Boosts", value=str(after.guild.premium_subscription_count), inline=True)
                embed.add_field(name="Boost Level", value=str(after.guild.premium_tier), inline=True)
                
                if after.display_avatar:
                    embed.set_thumbnail(url=after.display_avatar.url)
                
                embed.set_footer(text="Yet Cloud")
                
                await public_channel.send(content=after.mention, embed=embed)

            # --- Private Boost Log ---
            boost_channel = self.bot.get_channel(self.boost_channel_id)
            if boost_channel:
                log_embed = discord.Embed(
                    title="<:boost:1472906389583036528> New Server Boost!",
                    description=(
                        f"<:member:1472852615871205388> **{after.mention}** just boosted the server!\n"
                        f"<a:arrow:1472906559024664750> Total Boosts: **{after.guild.premium_subscription_count}**"
                    ),
                    color=0xFF73FA,
                    timestamp=datetime.datetime.now(datetime.timezone.utc)
                )
                if after.display_avatar:
                    log_embed.set_thumbnail(url=after.display_avatar.url)
                
                await boost_channel.send(embed=log_embed)

        # 2. Someone stops boosting (Unboost)
        elif before.premium_since is not None and after.premium_since is None:
            boost_channel = self.bot.get_channel(self.boost_channel_id)
            if boost_channel:
                embed = discord.Embed(
                    title="<a:warning1:1473339670690533518> Server Unboost",
                    description=(
                        f"<:member:1472852615871205388> **{after.mention}** stopped boosting the server.\n"
                        f"<a:arrow:1472906559024664750> Total Boosts: **{after.guild.premium_subscription_count}**"
                    ),
                    color=0x2f3136,
                    timestamp=datetime.datetime.now(datetime.timezone.utc)
                )
                if after.display_avatar:
                    embed.set_thumbnail(url=after.display_avatar.url)
                
                await boost_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logs(bot))
