from aiohttp import web
import aiohttp
import config
import database
import base64
import json
import time

async def handle_callback(request):
    code = request.query.get('code')
    state = request.query.get('state')

    if not code:
        return web.Response(text="No code provided", status=400)

    try:
        data = {
            'client_id': config.CLIENT_ID,
            'client_secret': config.CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': config.REDIRECT_URI,
            'scope': 'identify guilds.join'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post('https://discord.com/api/oauth2/token', data=data) as resp:
                token_response = await resp.json()
                
                if 'error' in token_response:
                    return web.Response(text=f"Error: {token_response.get('error_description', token_response['error'])}", status=400)

                access_token = token_response['access_token']
                refresh_token = token_response['refresh_token']
                expires_in = token_response['expires_in']
                
                # Get User ID
                async with session.get('https://discord.com/api/users/@me', headers={'Authorization': f'Bearer {access_token}'}) as user_resp:
                    user_data = await user_resp.json()
                    user_id = user_data['id']
                    
                    expires_at = int(time.time()) + expires_in
                    await database.save_user(user_id, access_token, refresh_token, expires_at)
                    
                    # Handle State (Guild Join / Role Add)
                    if state:
                        try:
                            decoded = json.loads(base64.b64decode(state).decode('utf-8'))
                            guild_id = decoded.get('g')
                            role_id = decoded.get('r')
                            unverified_role_id = decoded.get('u')
                            
                            if guild_id and role_id:
                                headers = {
                                    'Authorization': f'Bot {config.TOKEN}',
                                    'Content-Type': 'application/json'
                                }

                                # 1. Try to Join the user (if they aren't in via invite)
                                json_data = {
                                    'access_token': access_token,
                                    'roles': [role_id]
                                }
                                async with session.put(f'https://discord.com/api/guilds/{guild_id}/members/{user_id}', headers=headers, json=json_data) as add_resp:
                                    print(f"Join/Add request status: {add_resp.status}")
                                    
                                # 2. Explicitly Add Verified Role (Reliability fallback even if they are already in)
                                async with session.put(f'https://discord.com/api/guilds/{guild_id}/members/{user_id}/roles/{role_id}', headers=headers) as role_add_resp:
                                    print(f"Add Verified Role Status: {role_add_resp.status}")
                                    if role_add_resp.status == 403:
                                        print("ERROR: Bot permissions are too low to add Verified role!")

                                # 3. Explicitly Remove Unverified Role
                                if unverified_role_id:
                                    async with session.delete(f'https://discord.com/api/guilds/{guild_id}/members/{user_id}/roles/{unverified_role_id}', headers=headers) as role_del_resp:
                                        print(f"Remove Unverified Role Status: {role_del_resp.status}")
                                        if role_del_resp.status == 403:
                                            print("ERROR: Bot permissions are too low to remove Unverified role!")

                        except Exception as e:
                            print(f"State handling error: {e}")

        return web.Response(text="""
            <html>
                <body style="background-color: #2C2F33; color: #FFFFFF; font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh;">
                    <div style="text-align: center;">
                        <h1>YETCloud Verified!</h1>
                        <p>You have been verified and added to the server.</p>
                        <p>You can close this window now.</p>
                    </div>
                </body>
            </html>
        """, content_type='text/html')

    except Exception as e:
        return web.Response(text=f"Internal Error: {str(e)}", status=500)

async def start_server():
    app = web.Application()
    app.router.add_get('/callback', handle_callback)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', config.PORT)
    await site.start()
    print(f"Web server running on port {config.PORT}")


