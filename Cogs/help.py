import discord
from discord import app_commands
from discord.ext import commands
import database
import datetime

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Display the professional command galaxy menu")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📊 Yet Cloud — Command Galaxy",
            description="✨ Explore every command available across the **Yet Cloud System!**",
            color=0x00FFFF
        )
        
        # Category: Gifts & Rewards
        gifts_value = (
            "<:generator1:1473267576044736533> `/generator` — Get free/premium accounts\n"
            "<a:stock2:1473339178652663959> `/stock` — View available stocks\n"
            "<a:Drop1:1473339243765170247> `/drop` — Drop account manually\n"
            "<:gift:1472852654471512145> `/give <@user> <serv> <amt>` — Gift accounts\n"
            "<a:Drop1:1473339243765170247> `/force_drop` — Trigger a random drop"
        )
        embed.add_field(name="<a:gift:1472852654471512145> Gifts & Rewards", value=gifts_value, inline=False)
        
        # Category: General Information
        general_value = (
            "<a:book1:1473338940860534976> `/help` — Display this command menu\n"
            "<:analysis:1472853898724118548> `/gi <@user>` — Check user statistics\n"
            "<:leaderboard1:1473339049216315575> `/leaderboard` — Top 10 generator users\n"
            "<a:Report:1473339599550943264> `/report` — Report a faulty account\n"
            "<a:app:1473339414980608030> `/apply` — Apply for Yet Cloud Staff\n"
            "<:cart1:1473338870341959720> `/shop` — View pricing & buy premium"
        )
        embed.add_field(name="<a:globe1:1473339017775943711> General Information", value=general_value, inline=False)
        
        # Category: Staff Management
        staff_value = (
            "<:diamonds:1473339493456023683> `/payment <type> [@user]` — Send info\n"
            "<:configg2:1473339542038786192> `/staffapp_status` — Toggle applications\n"
            "<a:warning1:1473339670690533518> `/warn <@user>` — Issue a server warning\n"
            "<a:banv2:1473339741368623196> `/ban <@user>` — Ban from services\n"
            "<a:unbanv1:1473339833446187060> `/unban <@user>` — Remove a service ban\n"
            "<a:refresh2:1473339906649378876> `/resetcd <@user>` — Reset user cooldown\n"
            "<a:analysis2:1473340050866323497> `/analytics` — View usage & growth stats"
        )
        embed.add_field(name="<a:staff1:1473339328246321282> Staff Management", value=staff_value, inline=False)
        
        # Category: Inventory & Files (Admin)
        inventory_value = (
            "<:folder1:1472852636603531274> `/create` | `/delete` — Manage services\n"
            "<:add:1473267423854592103> `/add` | `/upload_stock` — Fill services\n"
            "<:remove:1473267385615122535> `/clear_stock` — Wipe specific categories\n"
            "<a:bell:1472906474643787786> `/restock` — Notify about stock updates\n"
            "<a:file2:1473340156948529193> `/bupload_stock` — Bulk file upload\n"
            "<:box1:1472855146957754388> `/bstock` — View bulk inventory"
        )
        embed.add_field(name="<:box1:1472855146957754388> Inventory & Files (Admin)", value=inventory_value, inline=False)
        
        # Category: Advanced Utilities
        advanced_value = (
            "<a:lock3:1473340266205908994> `/lockdown` — Restrict command access\n"
            "<:setting3:1473340356505083995> `/set_drop_channel` — Config destination\n"
            "<a:clock2:1473340455582928926> `/rm <time>` — Set an admin reminder\n"
            "<a:note2:1473340536768004128> `/embed` | `/embedlist` — Custom embeds\n"
            "<a:refresh2:1473339906649378876> `/msg <#chan> <text>` — Send signal to channel\n"
            "<a:robot1:1473340645668913253> `/ar_embed` — Setup auto-responses\n"
            "<:tag1:1473340733560553482> `/list_responses` | `/delete_response`\n"
            "<a:broom1:1473340809221472306> `/purgebot` — Clean bot messages"
        )
        embed.add_field(name="<a:star2:1473340889982930985> Advanced Utilities", value=advanced_value, inline=False)

        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
            embed.set_author(name=f"{interaction.guild.name} — Command Galaxy", icon_url=interaction.guild.icon.url)
        
        embed.set_footer(
            text="[🔹] Yet Cloud | Premium Generator Network",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="gi", description="Retrieve detailed intelligence on a user's profile")
    @app_commands.describe(user="The user to investigate")
    async def gi(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        
        embed = discord.Embed(
            title=f"<:role:1472856266417242247> User Intelligence Report — {target.name}",
            color=0x00FFFF,
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        
        roles = [role.mention for role in target.roles if role.name != "@everyone"]
        roles_str = " ".join(roles) if roles else "No specialized roles"
        
        embed.add_field(name="🆔 User Ident", value=f"`{target.id}`", inline=True)
        embed.add_field(name="🏷️ Display Name", value=f"`{target.display_name}`", inline=True)
        embed.add_field(name="📅 Joined Discord", value=f"<t:{int(target.created_at.timestamp())}:D>", inline=True)
        embed.add_field(name="🛰️ Joined Server", value=f"<t:{int(target.joined_at.timestamp())}:D>", inline=True)
        embed.add_field(name="🎭 Roles", value=roles_str, inline=False)
        
        embed.set_footer(text="[🔹] Yet Cloud | Intelligence Division", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="View the top 10 generator operators")
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        top_users = await database.get_top_users(10)
        
        if not top_users:
            embed = discord.Embed(title="📊 Yet Cloud Leaderboard", description="No operational data available yet. Start generating!", color=0x00FFFF)
            return await interaction.followup.send(embed=embed)

        leaderboard_str = ""
        for i, user_data in enumerate(top_users, 1):
            user = self.bot.get_user(int(user_data['user_id']))
            user_name = user.name if user else f"Unknown ({user_data['user_id']})"
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`#{i}`"
            leaderboard_str += f"{medal} **{user_name}** — `{user_data['count']}` units generated\n"

        embed = discord.Embed(
            title="<:ticket:1472906496462553088> Top 10 Generator Operators",
            description=leaderboard_str,
            color=0x00FFFF
        )
        embed.set_footer(text="[🔹] Yet Cloud | Performance Metrics")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="report", description="Report a faulty account or technical glitch")
    @app_commands.describe(details="Specific details about the issue")
    async def report(self, interaction: discord.Interaction, details: str):
        embed = discord.Embed(
            title="<a:Report:1473339599550943264> Transmission Received — Report Logged",
            description="Your report has been securely transmitted to the administration team.",
            color=0xFF0000
        )
        embed.add_field(name="<a:note2:1473340536768004128> Details", value=f"```{details}```")
        embed.set_footer(text="Yet Cloud Incident Management")
        await interaction.response.send_message(embed=embed, ephemeral=True)

        log_channel = self.bot.get_channel(1472555164685701202)
        if log_channel:
            log = discord.Embed(title="🚨 User Report Incoming", color=0xFF0000)
            log.add_field(name="👤 Reporter", value=interaction.user.mention)
            log.add_field(name="📄 Details", value=details)
            await report_channel.send(embed=log)

    @app_commands.command(name="apply", description="Apply for a position in Yet Cloud Staff")
    async def apply(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="<a:app:1473339414980608030> Staff Recruitment Terminal",
            description=(
                "We are looking for dedicated operators to join Yet Cloud.\n\n"
                "**Requirements:**\n"
                "- Active participation\n"
                "- Knowledge of system protocols\n"
                "- Professional demeanor\n\n"
                "[CLICK HERE TO APPLY](https://example.com/apply)"
            ),
            color=0x00FFFF
        )
        embed.set_footer(text="[🔹] Yet Cloud | HR Department")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="shop", description="View pricing and acquire premium access")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="<:cart1:1473338870341959720> Yet Cloud Marketplace",
            description="Upgrade your status to unlock high-tier accounts and exclusive features!",
            color=0x00FFFF
        )
        embed.add_field(name="<a:globe1:1473339017775943711> Premium Tier", value="`$5.00` — Unlimited 24/7 Access", inline=False)
        embed.add_field(name="<:diamonds:1473339493456023683> Supporter Tier", value="`$2.00` — Role & Badge Only", inline=False)
        embed.set_footer(text="[🔹] Yet Cloud | Premium Services")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
