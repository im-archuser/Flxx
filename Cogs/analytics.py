import discord
from discord import app_commands
from discord.ext import commands
import database
from utils import checks
import datetime

class Analytics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="analytics", description="view comprehensive server analytics and statistics")
    @checks.is_owner_or_admin()
    async def analytics(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Get Verified User Count
        verified_count = await database.get_user_count()
        
        # Get Server Stats
        guild = interaction.guild
        member_count = guild.member_count if guild else 0
        bot_latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title="<A:analysis2:1473340050866323497> YETCloud Analytics",
            color=0x00FFFF,
            timestamp=datetime.datetime.now()
        )
        
        embed.set_thumbnail(url=guild.icon.url if guild and guild.icon else None)
        
        # Verified Count
        embed.add_field(name="<a:globe1:1473339017775943711> Global Verified Users", value=f"`{verified_count}`", inline=True)
        embed.add_field(name="<:member:1472852615871205388> Server Members", value=f"`{member_count}`", inline=True)
        embed.add_field(name="<a:Bot:1472852527895548038> Bot Latency", value=f"`{bot_latency}ms`", inline=True)
        
        if guild:
            embed.add_field(name="<:server:1472852584992870497> Server ID", value=f"`{guild.id}`", inline=True)
            embed.add_field(name="<:owner:1472852555267571856> Owner", value=f"{guild.owner.mention}", inline=True)
            
        embed.set_footer(text="YET Cloud Analytics", icon_url=self.bot.user.display_avatar.url)
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Analytics(bot))
