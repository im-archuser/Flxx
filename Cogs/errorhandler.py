import discord
from discord import app_commands
from discord.ext import commands
import datetime

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_load(self):
        tree = self.bot.tree
        self._old_on_error = tree.on_error
        tree.on_error = self.on_app_command_error

    def cog_unload(self):
        tree = self.bot.tree
        tree.on_error = self._old_on_error

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            # Re-creating the exact structure from the image description
            valid_embed = discord.Embed(color=0xFF0000)
            server_icon = interaction.guild.icon.url if interaction.guild and interaction.guild.icon else self.bot.user.display_avatar.url
            valid_embed.set_author(name=f"Yet Cloud Ultimate Generator", icon_url=server_icon) 
            
            valid_embed.add_field(name="<a:warning1:1473339670690533518> Access Denied", value="<a:lock3:1473340266205908994> You don't have permission to use this command!", inline=False)
            valid_embed.add_field(name="<:folder1:1472852636603531274> Required Role(s):", value="AdminZ, ManagerZ", inline=False)
            
            valid_embed.add_field(name="<a:note2:1473340536768004128> Tip:", value="Contact an admin if you believe this is a mistake.", inline=False)
            valid_embed.add_field(name="<a:clock2:1473340455582928926> Timer:", value="This message will self-destruct in 10 seconds...", inline=False)
            
            valid_embed.set_footer(text="[🔹] Yet Cloud | #1 Generator Server", icon_url=server_icon)
            
            await interaction.response.send_message(embed=valid_embed, ephemeral=False, delete_after=10)
            return

        # Generic error handling
        print(f"Ignoring exception in command {interaction.command}: {error}")
        if not interaction.response.is_done():
            await interaction.response.send_message(f"An error occurred: {str(error)}", ephemeral=True)
        else:
            await interaction.followup.send(f"An error occurred: {str(error)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
