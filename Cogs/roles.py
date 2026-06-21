import discord
from discord import app_commands
from discord.ext import commands
import database
from utils import checks
import uuid

class RoleButton(discord.ui.Button):
    def __init__(self, role_id, emoji, label):
        super().__init__(
            label=label,
            emoji=emoji,
            style=discord.ButtonStyle.secondary,
            custom_id=f"self_role:{role_id}"
        )

    async def callback(self, interaction: discord.Interaction):
        role_id = int(self.custom_id.split(":")[1])
        role = interaction.guild.get_role(role_id)
        
        if not role:
            return await interaction.response.send_message("Role not found!", ephemeral=True)
            
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"Removed role: {role.name}", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"Added role: {role.name}", ephemeral=True)

class RolePanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup-roles", description="Create a new self-role panel")
    @app_commands.describe(
        title="The title of the embed",
        description="The description of the embed",
        color="Hex color (e.g. 00FFFF)",
        thumbnail="URL to a thumbnail image",
        footer="Custom footer text"
    )
    @checks.is_owner_or_admin()
    async def setup_roles(self, interaction: discord.Interaction, title: str, description: str = None, color: str = "00FFFF", thumbnail: str = None, footer: str = None):
        try:
            embed_color = int(color.replace("#", ""), 16)
        except ValueError:
            embed_color = 0x00FFFF

        embed = discord.Embed(title=title, description=description or "", color=embed_color)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        if footer:
            embed.set_footer(text=footer)
        
        # Save placeholder info to DB to get a panel_id
        panel_id = str(uuid.uuid4())
        
        await interaction.response.send_message(f"Role panel initialized! ID: `{panel_id}`\nUse `/panel add-text` or `/add-role-option` to build your panel.", ephemeral=True)
        
        # Send the actual panel
        msg = await interaction.channel.send(embed=embed)
        
        await database.save_role_panel(
            panel_id=panel_id,
            guild_id=interaction.guild.id,
            channel_id=interaction.channel.id,
            message_id=msg.id,
            title=title,
            description=description or "",
            color=embed_color,
            thumbnail=thumbnail,
            footer=footer
        )

    async def refresh_panel(self, panel_id):
        panel = await database.get_role_panel(panel_id)
        if not panel: return
        
        channel = self.bot.get_channel(int(panel['channel_id']))
        if not channel: return
        
        try:
            message = await channel.fetch_message(int(panel['message_id']))
        except: return

        # Get Content & Options
        options = await database.get_role_options(panel_id)
        contents = await database.get_panel_content(panel_id)
        
        # Build Embed
        embed = discord.Embed(title=panel['title'], color=int(panel['color']))
        if panel['thumbnail']: embed.set_thumbnail(url=panel['thumbnail'])
        if panel['footer']: embed.set_footer(text=panel['footer'])
        
        # Description built from text entries
        desc_parts = [panel['description']] if panel['description'] else []
        for c in contents:
            if c['type'] == 'text':
                desc_parts.append(c['content'])
        
        # Add role mapping to description like in the image
        role_lines = []
        view = RolePanelView()
        for opt in options:
            view.add_item(RoleButton(opt['role_id'], opt['emoji'], opt['label']))
            role_lines.append(f"{opt['emoji']} : <@&{opt['role_id']}>")
        
        if role_lines:
            desc_parts.append("\n" + "\n".join(role_lines))
            
        embed.description = "\n".join(desc_parts)
        
        # Add Fields
        for c in contents:
            if c['type'] == 'field':
                embed.add_field(name=c['field_name'], value=c['content'], inline=False)
        
        await message.edit(embed=embed, view=view)

    @app_commands.command(name="add-role-option", description="Add a role button to a panel")
    @app_commands.describe(panel_id="The ID of the panel", role="The role to grant", emoji="The emoji for the button", label="The label for the button")
    @checks.is_owner_or_admin()
    async def add_role_option_cmd(self, interaction: discord.Interaction, panel_id: str, role: discord.Role, emoji: str, label: str):
        await database.add_role_option(panel_id, role.id, emoji, label)
        await self.refresh_panel(panel_id)
        await interaction.response.send_message(f"Added role {role.name} to panel!", ephemeral=True)

    @app_commands.command(name="remove-role-option", description="Remove a role button from a panel")
    @app_commands.describe(panel_id="The ID of the panel", role="The role to remove")
    @checks.is_owner_or_admin()
    async def remove_role_option(self, interaction: discord.Interaction, panel_id: str, role: discord.Role):
        async with database.aiosqlite.connect(database.DB_NAME) as db:
            await db.execute("DELETE FROM role_options WHERE panel_id = ? AND role_id = ?", (panel_id, str(role.id)))
            await db.commit()
        await self.refresh_panel(panel_id)
        await interaction.response.send_message(f"Removed role {role.name} from panel!", ephemeral=True)

    panel_group = app_commands.Group(name="panel", description="Manage panel content line-by-line")

    @panel_group.command(name="add-text", description="Add a line of text to the panel")
    @app_commands.describe(panel_id="The ID of the panel", text="The text line to add")
    @checks.is_owner_or_admin()
    async def add_text(self, interaction: discord.Interaction, panel_id: str, text: str):
        await database.add_panel_content(panel_id, text, type='text')
        await self.refresh_panel(panel_id)
        await interaction.response.send_message("Text line added!", ephemeral=True)

    @panel_group.command(name="add-field", description="Add an embed field to the panel")
    @app_commands.describe(panel_id="The ID of the panel", name="Field name", value="Field content")
    @checks.is_owner_or_admin()
    async def add_field(self, interaction: discord.Interaction, panel_id: str, name: str, value: str):
        await database.add_panel_content(panel_id, value, type='field', field_name=name)
        await self.refresh_panel(panel_id)
        await interaction.response.send_message("Field added!", ephemeral=True)

    @panel_group.command(name="clear", description="Clear all custom lines/fields from a panel")
    @app_commands.describe(panel_id="The ID of the panel")
    @checks.is_owner_or_admin()
    async def clear_panel(self, interaction: discord.Interaction, panel_id: str):
        await database.clear_panel_content(panel_id)
        await self.refresh_panel(panel_id)
        await interaction.response.send_message("Panel content cleared!", ephemeral=True)

    @panel_group.command(name="list", description="List all existing panels and their IDs")
    @checks.is_owner_or_admin()
    async def list_panels(self, interaction: discord.Interaction):
        async with database.aiosqlite.connect(database.DB_NAME) as db:
            db.row_factory = database.aiosqlite.Row
            async with db.execute("SELECT * FROM role_panels WHERE guild_id = ?", (str(interaction.guild.id),)) as cursor:
                rows = await cursor.fetchall()
        
        if not rows:
            return await interaction.response.send_message("No panels found in this server.", ephemeral=True)
            
        embed = discord.Embed(title="<:folder1:1472852636603531274> Existing Panels", color=0x00FFFF)
        for row in rows:
            channel = self.bot.get_channel(int(row['channel_id']))
            channel_name = channel.name if channel else "Unknown Channel"
            embed.add_field(
                name=f"Panel: {row['title']}", 
                value=f"**ID:** `{row['panel_id']}`\n**Channel:** #{channel_name}", 
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @panel_group.command(name="delete", description="Delete a panel permanently")
    @app_commands.describe(panel_id="The ID of the panel to delete")
    @checks.is_owner_or_admin()
    async def delete_panel(self, interaction: discord.Interaction, panel_id: str):
        panel = await database.get_role_panel(panel_id)
        if not panel:
            return await interaction.response.send_message("Panel not found!", ephemeral=True)
            
        # Try to delete message
        channel = self.bot.get_channel(int(panel['channel_id']))
        if channel:
            try:
                message = await channel.fetch_message(int(panel['message_id']))
                await message.delete()
            except:
                pass
                
        await database.delete_role_panel(panel_id)
        await interaction.response.send_message(f"Panel `{panel_id}` and its message have been deleted.", ephemeral=True)

async def setup(bot):
    cog = Roles(bot)
    await bot.add_cog(cog)
    
    # Reload panels for persistence
    # We need to fetch all guilds' panels
    async with database.aiosqlite.connect(database.DB_NAME) as db:
        db.row_factory = database.aiosqlite.Row
        async with db.execute("SELECT * FROM role_panels") as cursor:
            panels = await cursor.fetchall()
            for panel in panels:
                options = await database.get_role_options(panel['panel_id'])
                view = RolePanelView()
                for opt in options:
                    view.add_item(RoleButton(opt['role_id'], opt['emoji'], opt['label']))
                bot.add_view(view, message_id=int(panel['message_id']))
