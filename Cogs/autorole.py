import discord
from discord.ext import commands

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.join_role_id = 1472840083014160510

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role = member.guild.get_role(self.join_role_id)
        if role:
            try:
                await member.add_roles(role)
                print(f"Assigned auto-role {role.name} to {member.name}")
            except Exception as e:
                print(f"Failed to assign auto-role: {e}")
        else:
            print(f"Auto-role with ID {self.join_role_id} not found in guild {member.guild.name}")

async def setup(bot):
    await bot.add_cog(AutoRole(bot))
