import discord
from discord import app_commands

def is_owner_or_admin():
    def predicate(interaction: discord.Interaction) -> bool:
        # Check if user is admin OR has the specific owner ID
        is_admin = interaction.user.guild_permissions.administrator
        is_owner = interaction.user.id == 1249726528393183363
        return is_admin or is_owner
    return app_commands.check(predicate)
