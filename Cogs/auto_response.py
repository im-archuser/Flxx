import discord
from discord import app_commands
from discord.ext import commands
import database
from utils import checks

class AutoResponseModal(discord.ui.Modal, title="Create Auto-Response"):
    trigger = discord.ui.TextInput(
        label="Trigger Keyword",
        placeholder="What word should trigger this response?",
        required=True,
        max_length=100
    )
    title_input = discord.ui.TextInput(
        label="Embed Title",
        placeholder="Enter the title for the response embed...",
        required=True,
        max_length=256
    )
    description = discord.ui.TextInput(
        label="Embed Description",
        style=discord.TextStyle.paragraph,
        placeholder="Enter the content of the response...",
        required=True,
        max_length=2000
    )
    color = discord.ui.TextInput(
        label="Hex Color",
        placeholder="e.g. FF4500 (without #)",
        required=False,
        default="00FFFF",
        max_length=6
    )
    footer = discord.ui.TextInput(
        label="Footer Text",
        placeholder="Optional footer text...",
        required=False,
        max_length=2000
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            embed_color = int(self.color.value.replace("#", ""), 16)
        except ValueError:
            embed_color = 0x00FFFF

        await database.save_auto_response(
            guild_id=interaction.guild_id,
            trigger=self.trigger.value,
            title=self.title_input.value,
            description=self.description.value,
            color=embed_color,
            image=None, # Image can be added via /ar update-image if needed
            footer=self.footer.value
        )
        success_embed = discord.Embed(
            title="<a:star2:1473340889982930985> Auto-Response Configured",
            description=f"System has successfully registered the trigger `{self.trigger.value}`.",
            color=0x00FFFF
        )
        success_embed.set_footer(text="[🔹] Yet Cloud | Logic Core")
        await interaction.response.send_message(embed=success_embed, ephemeral=True)

class AutoResponse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ar_group = app_commands.Group(name="ar", description="Manage auto-responses")

    @app_commands.command(name="ar_embed", description="Create a new auto-response embed")
    @checks.is_owner_or_admin()
    async def create_ar(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AutoResponseModal())

    @ar_group.command(name="list", description="List all active auto-responses")
    @checks.is_owner_or_admin()
    async def list_ars(self, interaction: discord.Interaction):
        rows = await database.get_auto_responses(interaction.guild_id)
        if not rows:
            error_embed = discord.Embed(title="❌ Error", description="No active auto-responses detected in the database.", color=0xFF0000)
            return await interaction.response.send_message(embed=error_embed, ephemeral=True)
        
        embed = discord.Embed(title="<a:note2:1473340536768004128> Auto-Responses", color=0x00FFFF)
        for row in rows:
            embed.add_field(
                name=f"Trigger: `{row['trigger']}`", 
                value=f"**Title:** {row['title']}\n**Color:** #{hex(row['color'])[2:]}", 
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ar_group.command(name="delete", description="Delete an auto-response")
    @app_commands.describe(trigger="The keyword that triggers the response")
    @checks.is_owner_or_admin()
    async def delete_ar(self, interaction: discord.Interaction, trigger: str):
        await database.delete_auto_response(interaction.guild_id, trigger)
        
        del_embed = discord.Embed(
            title="<a:broom1:1473340809221472306> Logic Purged",
            description=f"Successfully removed the auto-response trigger `{trigger}` from the system.",
            color=0x00FFFF
        )
        del_embed.set_footer(text="[🔹] Yet Cloud | System Maintenance")
        await interaction.response.send_message(embed=del_embed, ephemeral=True)

    @app_commands.command(name="list_responses", description="Professional list of all active auto-responses")
    @checks.is_owner_or_admin()
    async def list_responses_alias(self, interaction: discord.Interaction):
        await self.list_ars(interaction)

    @app_commands.command(name="delete_response", description="Delete a specific auto-response by trigger")
    @app_commands.describe(trigger="The keyword trigger to remove")
    @checks.is_owner_or_admin()
    async def delete_response_alias(self, interaction: discord.Interaction, trigger: str):
        await self.delete_ar(interaction, trigger)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        # Check if message content matches any trigger
        # We'll use exact match for now as it's safer, but could be changed to "contains"
        content = message.content.lower()
        responses = await database.get_auto_responses(message.guild.id)
        
        for res in responses:
            if res['trigger'] == content:
                embed = discord.Embed(
                    title=res['title'],
                    description=res['description'],
                    color=res['color']
                )
                if res['footer']:
                    embed.set_footer(text=res['footer'])
                if res['image']:
                    embed.set_image(url=res['image'])
                
                await message.reply(embed=embed)
                break

async def setup(bot):
    await bot.add_cog(AutoResponse(bot))
