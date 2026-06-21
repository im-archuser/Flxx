import discord
from discord import app_commands
from discord.ext import commands
import database
from utils import checks
import json
import asyncio
import io

class TicketCloseModal(discord.ui.Modal, title="Close Ticket"):
    reason = discord.ui.TextInput(
        label="Reason for closing",
        style=discord.TextStyle.paragraph,
        placeholder="Enter the reason here...",
        required=True,
        max_length=500
    )

    def __init__(self, channel):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="<a:lock3:1473340266205908994> Closing Ticket", description="Generating the final transcript and purging the terminal... Please wait.", color=0xFF0000)
        embed.set_footer(text="[🔹] Yet Cloud | Ticket System")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # 1. Generate Transcript
        transcript_content = f"Ticket Transcript: {self.channel.name}\n"
        transcript_content += f"Closed By: {interaction.user} ({interaction.user.id})\n"
        transcript_content += f"Reason: {self.reason.value}\n"
        transcript_content += "="*30 + "\n\n"
        
        async for message in self.channel.history(limit=None, oldest_first=True):
            time_str = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            content = message.content if message.content else "[No Text Content]"
            transcript_content += f"[{time_str}] {message.author}: {content}\n"
            if message.attachments:
                for attachment in message.attachments:
                    transcript_content += f"  > Attachment: {attachment.url}\n"
        
        binary_transcript = transcript_content.encode('utf-8')
        
        # 2. Identify Ticket Opener (for DM)
        ticket_opener = None
        for target, overwrite in self.channel.overwrites.items():
            if isinstance(target, discord.Member) and not target.bot:
                if overwrite.view_channel:
                    ticket_opener = target
                    break

        # 3. Log Ticket Close with Transcript & Reason
        log_channel_id = 1472555173770559488
        log_channel = interaction.guild.get_channel(log_channel_id)
        if log_channel:
            embed = discord.Embed(
                title="<a:lock3:1473340266205908994> Ticket Closed",
                color=0xFF0000,
                description=f"**Reason:** {self.reason.value}",
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="<a:staff1:1473339328246321282> Ticket Closed By", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=True)
            if ticket_opener:
                embed.add_field(name="<:member:1472852615871205388> Members", value=f"{ticket_opener.mention} (`{ticket_opener.id}`)", inline=True)
            embed.add_field(name="<:tag1:1473340733560553482> Channel", value=f"#{self.channel.name}", inline=True)
            
            transcript_file_log = discord.File(io.BytesIO(binary_transcript), filename=f"transcript-{self.channel.name}.txt")
            await log_channel.send(embed=embed, file=transcript_file_log)

        # 4. DM Ticket Opener
        if ticket_opener:
            try:
                dm_embed = discord.Embed(
                    title="<a:lock3:1473340266205908994> Ticket Closed",
                    description=f"Your ticket **#{self.channel.name}** has been closed.",
                    color=0x00FFFF
                )
                dm_embed.add_field(name="<a:staff1:1473339328246321282> Closed By", value=interaction.user.name, inline=True)
                dm_embed.add_field(name="<a:note2:1473340536768004128> Reason", value=self.reason.value, inline=False)
                
                transcript_file_dm = discord.File(io.BytesIO(binary_transcript), filename=f"transcript-{self.channel.name}.txt")
                await ticket_opener.send(embed=dm_embed, file=transcript_file_dm)
            except:
                pass # User might have DMs closed

        await asyncio.sleep(5)
        try:
            await self.channel.delete()
        except discord.NotFound:
            pass

class TicketActionsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket", emoji="<a:lock3:1473340266205908994>")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketCloseModal(interaction.channel))

class TicketSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(
            placeholder="Select Your Category ✨", 
            min_values=1, 
            max_values=1, 
            options=options, 
            custom_id="ticket_select"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            category_name = self.values[0]
            guild = interaction.guild
            user = interaction.user
            
            # Fetch config from DB
            config = await database.get_ticket_config(guild.id)
            target_category = None
            support_role = None
            
            if config:
                cat_id = config['category_id']
                if cat_id:
                    try:
                        target_category = guild.get_channel(int(cat_id))
                    except (ValueError, TypeError):
                        target_category = None
                        
                role_id = config['support_role_id']
                if role_id:
                    try:
                        support_role = guild.get_role(int(role_id))
                    except (ValueError, TypeError):
                        support_role = None
            
            # Create Channel Name
            channel_name = f"{category_name}-{user.name}"
            
            # Set Permissions
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True)
            }
            
            if support_role:
                overwrites[support_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
            
            channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites, category=target_category)
            
            embed = discord.Embed(
                title=f"Welcome to {category_name.capitalize()} Support",
                description=f"Hello {user.mention}, our staff will be with you shortly.\nPlease describe your issue in detail.",
                color=0x00FFFF
            )
            
            await channel.send(embed=embed, view=TicketActionsView())
            
            success_embed = discord.Embed(
                title="✅ Ticket Initialized",
                description=f"Your private support terminal has been established in {channel.mention}.",
                color=0x00FFFF
            )
            success_embed.set_footer(text="[🔹] Yet Cloud | Signal Secured")
            await interaction.followup.send(embed=success_embed, ephemeral=True)

            # Log Ticket Open
            log_channel_id = 1472555173770559488
            log_channel = guild.get_channel(log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title="<a:bell:1472906474643787786> Ticket Opened",
                    color=0x00FF00,
                    timestamp=discord.utils.utcnow()
                )
                log_embed.add_field(name="<:member:1472852615871205388> Ticket Opened By Member", value=f"{user.mention} (`{user.id}`)", inline=True)
                log_embed.add_field(name="<:folder1:1472852636603531274> Category", value=category_name.capitalize(), inline=True)
                log_embed.add_field(name="<:tag1:1473340733560553482> Channel", value=channel.mention, inline=False)
                await log_channel.send(embed=log_embed)
            
        except Exception as e:
            print(f"Ticket creation error: {e}")
            error_embed = discord.Embed(title="❌ System Breach", description=f"An error occurred while creating your ticket: `{str(e)}`", color=0xFF0000)
            await interaction.followup.send(embed=error_embed, ephemeral=True)

class TicketPanelView(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=None)
        if not options:
            # Fallback default options
            options = [discord.SelectOption(label="No Categories Configured", value="none", disabled=True)]
        self.add_item(TicketSelect(options))

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    category_group = app_commands.Group(name="ticket-category", description="Manage ticket categories")

    @app_commands.command(name="setup-ticket", description="Sets up the ticket system panel")
    @app_commands.describe(
        channel="The channel to send the panel to",
        category="The category where tickets will be created",
        support_role="The role that will have access to tickets",
        title="Override the panel title",
        description="Override the panel description",
        color="Hex color (e.g. FF4500)",
        thumbnail="Thumbnail URL",
        footer="Custom footer text"
    )
    @checks.is_owner_or_admin()
    async def setup_ticket(self, interaction: discord.Interaction, channel: discord.TextChannel, category: discord.CategoryChannel = None, support_role: discord.Role = None, title: str = None, description: str = None, color: str = "FF4500", thumbnail: str = None, footer: str = None):
        # Save config
        category_id = category.id if category else None
        support_role_id = support_role.id if support_role else None
        await database.save_ticket_config(interaction.guild_id, category_id, support_role_id)
        
        # Fetch custom categories
        rows = await database.get_ticket_categories(interaction.guild_id)
        options = []
        for row in rows:
            options.append(discord.SelectOption(
                label=row['label'],
                description=row['description'],
                emoji=row['emoji'] if row['emoji'] else None,
                value=row['value']
            ))

        if not options:
            # Add defaults if empty
            defaults = [
                ("General Support", "Need help or have questions?", "👤", "general"),
                ("Perks & Rewards", "Claim Booster Perks or Rewards?", "🎁", "perks"),
                ("Generator Support", "Issues with the Generator?", "🌍", "generator")
            ]
            for label, desc, emoji, val in defaults:
                await database.add_ticket_category(interaction.guild_id, label, desc, emoji, val)
                options.append(discord.SelectOption(label=label, description=desc, emoji=emoji, value=val))
        
        t_emoji = "<a:stock2:1473339178652663959>" # Ticket category in help
        s_emoji = "<:support:1472906364270415963>"
        a_emoji = "<a:arrow:1472906559024664750>"
        g_emoji = "<a:gift:1472852654471512145>"
        happy_emoji = "<a:star2:1473340889982930985>"
        warn_emoji = "<a:warning1:1473339670690533518>"
        note_emoji = "<a:note2:1473340536768004128>"
        
        try:
            embed_color = int(color.replace("#", ""), 16)
        except ValueError:
            embed_color = 0xFF4500

        embed = discord.Embed(
            title=title or f"{t_emoji} | Yet Cloud Ticket Support!",
            color=embed_color
        )
        
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        else:
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)

        if description:
            embed.description = description
        else:
            # General Support Section
            embed.add_field(
                name=f"{s_emoji} ・ General Support",
                value=(
                    "● Need help, have questions, or want to report an issue?\n"
                    f"{a_emoji} Open this ticket for general assistance."
                ),
                inline=False
            )
            
            # Perks Section
            embed.add_field(
                name=f"{g_emoji} ・ Perks & Rewards",
                value=(
                    "● Want To Claim Booster Perks or Rewards?\n"
                    f"{a_emoji} Use This Ticket for:\n"
                    " └ <:boost:1472906389583036528> Booster Perks\n"
                    f" └ {happy_emoji} Giveaway / Drop Rewards"
                ),
                inline=False
            )
            
            # Generator Support Section
            embed.add_field(
                name="<:globle:1472906456058695823> ・ Generator Support",
                value=(
                    "● Having Issues With The Generator or Got Banned By It?\n"
                    f"{a_emoji} Use this ticket for:\n"
                    f" └ {warn_emoji} Generator Issues"
                ),
                inline=False
            )
            
            # Note Section
            embed.add_field(
                name=f"{note_emoji} | Note",
                value=(
                    f"{a_emoji} Please Make Sure To Read <#1472555068015513723> To Avoid\n"
                    "Breaking Any Rules Or Regulations & <#1472555138534211597> For Common\n"
                    "Issues!\n"
                    f"{a_emoji} For Easy Or Simple Problems Please Use <#1472555147136598051>"
                ),
                inline=False
            )
        
        embed.set_footer(text=footer or "Yet Cloud Management", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        await channel.send(embed=embed, view=TicketPanelView(options))
        
        setup_embed = discord.Embed(
            title="✅ Ticket Panel Established",
            description=f"The support terminal has been successfully deployed to {channel.mention}.",
            color=0x00FFFF
        )
        setup_embed.set_footer(text="[🔹] Yet Cloud | System Administration")
        await interaction.response.send_message(embed=setup_embed, ephemeral=True)

    @category_group.command(name="add", description="Add a new ticket category")
    @app_commands.describe(label="The name shown in the menu", description="Short description", emoji="Emoji for the menu", value="Unique ID (internal)")
    @checks.is_owner_or_admin()
    async def add_cat(self, interaction: discord.Interaction, label: str, description: str, emoji: str = None, value: str = None):
        val = value or label.lower().replace(" ", "_")
        await database.add_ticket_category(interaction.guild_id, label, description, emoji, val)
        
        cat_embed = discord.Embed(
            title="📝 Category Added",
            description=f"Successfully registered the `{label}` category in the ticket system.",
            color=0x00FFFF
        )
        cat_embed.add_field(name="🆔 Identifier", value=f"`{val}`", inline=True)
        cat_embed.set_footer(text="[🔹] Yet Cloud | Category Management")
        await interaction.response.send_message(embed=cat_embed, ephemeral=True)

    @category_group.command(name="remove", description="Remove a ticket category")
    @app_commands.describe(value="The unique ID of the category to remove")
    @checks.is_owner_or_admin()
    async def remove_cat(self, interaction: discord.Interaction, value: str):
        await database.remove_ticket_category(interaction.guild_id, value)
        
        rem_embed = discord.Embed(
            title="🗑️ Category Removed",
            description=f"Permanently purged the category with identifier `{value}` from the system.",
            color=0xFF0000
        )
        rem_embed.set_footer(text="[🔹] Yet Cloud | System Cleanup")
        await interaction.response.send_message(embed=rem_embed, ephemeral=True)

    @category_group.command(name="list", description="List all custom ticket categories")
    @checks.is_owner_or_admin()
    async def list_cats(self, interaction: discord.Interaction):
        rows = await database.get_ticket_categories(interaction.guild_id)
        if not rows:
            error_embed = discord.Embed(title="❌ Error", description="No custom categories detected in the database.", color=0xFF0000)
            return await interaction.response.send_message(embed=error_embed, ephemeral=True)
        
        embed = discord.Embed(title="Ticket Categories", color=0x00FFFF)
        for row in rows:
            embed.add_field(
                name=f"{row['emoji']} {row['label']}", 
                value=f"**Value:** `{row['value']}`\n**Description:** {row['description']}", 
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    # Register the persistent view for buttons inside tickets
    bot.add_view(TicketActionsView())
    
    # Reload ticket panels for persistence
    # To truly make the select menu persistent with dynamic options, 
    # we need to reconstruct the options for each guild.
    async with database.aiosqlite.connect(database.DB_NAME) as db:
        db.row_factory = database.aiosqlite.Row
        async with db.execute("SELECT * FROM ticket_configs") as cursor:
            configs = await cursor.fetchall()
            for config in configs:
                guild_id = int(config['guild_id'])
                rows = await database.get_ticket_categories(guild_id)
                options = []
                for row in rows:
                    options.append(discord.SelectOption(
                        label=row['label'],
                        description=row['description'],
                        emoji=row['emoji'] if row['emoji'] else None,
                        value=row['value']
                    ))
                
                if options:
                    # We don't have the message_id for the setup-ticket panel saved in ticket_configs 
                    # currently. We should probably add it or just let the user re-setup.
                    # However, we can add the view globally if custom_id is matched.
                    bot.add_view(TicketPanelView(options))
    
    await bot.add_cog(Tickets(bot))
