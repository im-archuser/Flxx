import discord
from discord import app_commands
from discord.ext import commands
import database
import config
import aiohttp
import asyncio

from utils import checks

class Pull(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="pull", description="Pulls verified members into this server")
    @checks.is_owner_or_admin()
    @app_commands.describe(server_id="The ID of the server to pull members into (defaults to current)")
    async def pull(self, interaction: discord.Interaction, server_id: str = None):

        await interaction.response.defer(ephemeral=True)
        
        target_guild_id = server_id if server_id else str(interaction.guild_id)
        
        try:
            users = await database.get_all_users()
            success_count = 0
            fail_count = 0
            
            async with aiohttp.ClientSession() as session:
                for user in users:
                    user_id = user['user_id']
                    access_token = user['access_token']
                    refresh_token = user['refresh_token']
                    
                    # Function to refresh token
                    async def refresh_access_token(current_refresh_token):
                        data = {
                            'client_id': config.CLIENT_ID,
                            'client_secret': config.CLIENT_SECRET,
                            'grant_type': 'refresh_token',
                            'refresh_token': current_refresh_token
                        }
                        async with session.post('https://discord.com/api/oauth2/token', data=data) as resp:
                            if resp.status == 200:
                                return await resp.json()
                            return None

                    # Try to pull
                    async def try_pull(token):
                        headers = {
                            'Authorization': f'Bot {config.TOKEN}',
                            'Content-Type': 'application/json'
                        }
                        data = {'access_token': token}
                        async with session.put(f'https://discord.com/api/guilds/{target_guild_id}/members/{user_id}', headers=headers, json=data) as resp:
                            return resp.status

                    status = await try_pull(access_token)
                    
                    if status == 401 or status == 403:
                        # Token might be expired, try refreshing
                        print(f"Token expired for {user_id}, refreshing...")
                        new_tokens = await refresh_access_token(refresh_token)
                        
                        if new_tokens:
                            new_access_token = new_tokens['access_token']
                            new_refresh_token = new_tokens['refresh_token']
                            new_expires_in = new_tokens['expires_in']
                            # Update DB (We need to import time)
                            import time
                            new_expires_at = int(time.time()) + new_expires_in
                            await database.save_user(user_id, new_access_token, new_refresh_token, new_expires_at)
                            
                            # Retry pull with new token
                            retry_status = await try_pull(new_access_token)
                            if retry_status in [201, 204]:
                                success_count += 1
                            else:
                                fail_count += 1
                                print(f"Failed to pull {user_id} after refresh: {retry_status}")
                        else:
                            print(f"Failed to refresh token for {user_id}")
                            fail_count += 1
                    elif status in [201, 204]:
                        success_count += 1
                    else:
                        fail_count += 1
                        print(f"Failed to pull {user_id}: {status}")

                    await asyncio.sleep(1) # Rate limit protection

            await interaction.followup.send(f"Pull operation complete.\nSuccessfully added: {success_count}\nFailed: {fail_count}")

        except Exception as e:
            print(f"Pull error: {e}")
            await interaction.followup.send("An error occurred while pulling members.")

async def setup(bot):
    await bot.add_cog(Pull(bot))
